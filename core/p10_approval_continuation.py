from __future__ import annotations

from agent.executor import ConfirmationRequired, ReauthenticationRequired


def install(cls):
    """Install P10 turn continuation without creating approval authority.

    P6/W7 remains the approval/execution authority.  This adapter only binds the
    governed operation outcome back into the existing P10 plan and canonical turn.
    """
    if getattr(cls, '_p10_approval_continuation_installed', False):
        return

    original_approve = cls.approve
    original_reject = cls.reject

    def _bound(self, approval_id, kwargs):
        turn = self._turn_by_approval(approval_id)
        if not turn or not turn.get('p10_plan_id') or self.autonomy is None:
            return None, None
        owner_id = self._owner(kwargs.get('owner_id', self.CANONICAL_OWNER))
        if turn.get('owner_id') != owner_id:
            raise PermissionError('approval is not bound to this owner')
        if not kwargs.get('device_id') or kwargs.get('device_id') != turn.get('device_id'):
            raise PermissionError('approval is not bound to this trusted device')
        if not kwargs.get('session_id') or kwargs.get('session_id') != turn.get('session_id'):
            raise PermissionError('approval is not bound to this trusted session')
        plan = self.autonomy.plan(turn['p10_plan_id'], owner_id=owner_id)
        task = next((item for item in plan.get('tasks', []) if item.get('status') == 'WAITING_APPROVAL' and item.get('approval_ref') == approval_id), None)
        if task is None:
            raise PermissionError('approval is not bound to a waiting P10 task')
        return turn, task

    def _continue_plan(self, turn, *, owner_id, device_id, session_id, reauthenticated_at=None):
        plan_id = turn['p10_plan_id']
        while True:
            plan = self.autonomy.plan(plan_id, owner_id=owner_id)
            if plan.get('state') in {'COMPLETED', 'FAILED', 'CANCELLED', 'UNCERTAIN', 'BLOCKED'}:
                break
            ready = self.autonomy.ready_tasks(plan_id, owner_id=owner_id)
            if not ready:
                break
            for task in ready:
                plan = self.autonomy.execute_task(
                    plan_id,
                    task['id'],
                    owner_id=owner_id,
                    device_id=device_id,
                    session_id=session_id,
                    reauthenticated_at=reauthenticated_at,
                )
                current = next(item for item in plan['tasks'] if item['id'] == task['id'])
                if current.get('status') == 'WAITING_APPROVAL':
                    approval = current.get('approval_ref')
                    self._update(turn['request_id'], 'needs_approval', approval_id=approval, p10_goal_id=turn.get('p10_goal_id'), p10_plan_id=plan_id)
                    self._emit('turn.needs_approval', request_id=turn['request_id'], conversation_id=turn.get('conversation_id'), approval_id=approval, goal_id=turn.get('p10_goal_id'), plan_id=plan_id)
                    raise ConfirmationRequired(str(current.get('requested_tool') or current.get('action') or 'governed action'), dict(current.get('parameters') or {}), str(current.get('objective') or ''), approval_id=approval, execution_id=str(current.get('operation_id') or ''), expires_at=0)
                if plan.get('state') in {'FAILED', 'CANCELLED', 'UNCERTAIN', 'BLOCKED'}:
                    break
        return self.autonomy.plan(plan_id, owner_id=owner_id)

    def _complete(self, turn, plan):
        if plan.get('state') != 'COMPLETED':
            return None
        completed = [item for item in plan.get('tasks', []) if item.get('status') == 'COMPLETED']
        refs = [str(item.get('result_ref')) for item in completed if item.get('result_ref')]
        answer = 'Completed the governed request successfully.'
        if refs:
            answer += f' Verified operation references: {", ".join(refs[:8])}.'
        self._update(turn['request_id'], 'completed', assistant_text=answer, p10_goal_id=turn.get('p10_goal_id'), p10_plan_id=turn.get('p10_plan_id'))
        self._append(str(turn.get('conversation_id') or ''), device_id=turn.get('device_id'), kind='assistant_message', text=answer, event_id=f"{turn['request_id']}:assistant")
        self._emit('turn.completed', request_id=turn['request_id'], conversation_id=turn.get('conversation_id'))
        return answer

    def approve(self, approval_id, **kwargs):
        turn, task = _bound(self, approval_id, kwargs)
        if turn is None:
            return original_approve(self, approval_id, **kwargs)
        owner_id = turn['owner_id']
        try:
            plan = self.autonomy.approve_task(
                turn['p10_plan_id'],
                task['id'],
                owner_id=owner_id,
                device_id=kwargs['device_id'],
                session_id=kwargs['session_id'],
                reauthenticated_at=kwargs.get('reauthenticated_at'),
            )
        except ReauthenticationRequired:
            self._update(turn['request_id'], 'needs_reauthentication', error_code='reauthentication_required')
            raise
        if plan.get('state') == 'CANCELLED':
            self._update(turn['request_id'], 'cancelled', error_code='cancelled')
            return 'Action cancelled.'
        if plan.get('state') in {'FAILED', 'UNCERTAIN', 'BLOCKED'}:
            self._update(turn['request_id'], 'failed', error_code=f"p10_{str(plan.get('state')).lower()}")
            return f"The governed request stopped in {plan.get('state')} state."
        plan = _continue_plan(turn, owner_id=owner_id, device_id=kwargs['device_id'], session_id=kwargs['session_id'], reauthenticated_at=kwargs.get('reauthenticated_at'))
        completed = _complete(self, turn, plan)
        return completed if completed is not None else 'The governed plan is still in progress.'

    def reject(self, approval_id, **kwargs):
        turn, task = _bound(self, approval_id, kwargs)
        if turn is None:
            return original_reject(self, approval_id, **kwargs)
        plan = self.autonomy.deny_task(
            turn['p10_plan_id'],
            task['id'],
            owner_id=turn['owner_id'],
            device_id=kwargs['device_id'],
            session_id=kwargs['session_id'],
        )
        self._update(turn['request_id'], 'cancelled', error_code='approval_denied', p10_goal_id=turn.get('p10_goal_id'), p10_plan_id=turn.get('p10_plan_id'))
        answer = 'Action cancelled by owner approval decision.'
        self._append(str(turn.get('conversation_id') or ''), device_id=turn.get('device_id'), kind='assistant_message', text=answer, event_id=f"{turn['request_id']}:assistant")
        self._emit('turn.cancelled', request_id=turn['request_id'], conversation_id=turn.get('conversation_id'), plan_id=plan.get('id'), reason='approval_denied')
        return answer

    cls.approve = approve
    cls.reject = reject
    cls._p10_approval_continuation_installed = True
