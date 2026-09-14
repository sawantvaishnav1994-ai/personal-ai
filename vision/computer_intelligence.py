from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import threading
import time
from typing import Any

from desktop.controller import DesktopController
from desktop.operator_transactions import OperatorBinding, OperatorTransactionStore, new_transaction_id
from desktop.transactions import DesktopTransactionManager
from security.approvals import parameter_hash
from vision.screen_understanding import ScreenUnderstanding


ALLOWED_DESKTOP_ACTIONS = {'move', 'click', 'type_text', 'hotkey'}


@dataclass(frozen=True)
class ComputerPlanStep:
    kind: str
    params: dict[str, Any]
    reason: str = ''
    verify: str = ''


class ComputerIntelligence:
    """Observe → Understand → Act → Verify computer-control runtime.

    The enclosing ToolRegistry/ApprovalManager remains authoritative for owner
    permission. This runtime adds a durable operator journal and never blindly
    redispatches a computer action whose external/UI outcome may be uncertain.
    """

    def __init__(self, models, data_dir, *, second_brain=None, events=None, controller=None, emergency_stop=None):
        self.models = models
        self.second_brain = second_brain
        self.events = events
        self.data_dir = Path(data_dir)
        self.screen = ScreenUnderstanding(models, data_dir)
        self.controller = controller or DesktopController()
        self.transactions = DesktopTransactionManager(self.controller)
        self.operator_transactions = OperatorTransactionStore(self.data_dir / 'operator-transactions.sqlite3')
        self.emergency_stop = emergency_stop or (lambda: False)
        self._lock = threading.RLock()

    def _emit(self, name, **payload):
        if self.events:
            self.events.emit(name, **payload)

    def observe(self, question: str = 'Describe the visible screen and the actionable UI elements relevant to the user.', monitor: int = 1):
        self._emit('state', state='understanding')
        result = self.screen.analyze(question, monitor=monitor)
        self._emit('computer.observed', screenshot=result.get('screenshot'))
        return result

    def _memory_context(self, goal: str):
        if not self.second_brain:
            return []
        try:
            return self.second_brain.context(goal, limit=5)
        except Exception:
            return []

    def plan(self, goal: str, *, observation: dict | None = None, max_steps: int = 8):
        max_steps = max(1, min(int(max_steps), 12))
        observation = observation or self.observe(
            f'Describe the current UI and identify only elements relevant to this goal: {goal}'
        )
        memory = self._memory_context(goal)
        prompt = f'''Create a cautious desktop action plan for this goal:\n{goal}\n\nCURRENT SCREEN ANALYSIS:\n{observation.get('analysis', observation)}\n\nRELEVANT PERSONAL CONTEXT:\n{json.dumps(memory, default=str)[:5000]}\n\nReturn JSON only with this shape:\n{{"summary":"...","steps":[{{"kind":"move|click|type_text|hotkey","params":{{}},"reason":"...","verify":"what should be visibly true after this action"}}]}}\nRules: at most {max_steps} steps; do not invent coordinates unless supported by the screen analysis; do not submit purchases, send messages, delete data, change security settings, or type secrets unless the user's goal explicitly requires it. Prefer the smallest reversible sequence.'''
        data = self.models.json(prompt, system='You are Personal AI computer-control planner. Return bounded JSON only.')
        raw_steps = list(data.get('steps', []))[:max_steps]
        steps = []
        for row in raw_steps:
            kind = str(row.get('kind', '')).strip()
            if kind not in ALLOWED_DESKTOP_ACTIONS:
                raise ValueError(f'unsupported computer action: {kind}')
            params = dict(row.get('params') or {})
            self._validate_params(kind, params)
            steps.append(
                ComputerPlanStep(
                    kind=kind,
                    params=params,
                    reason=str(row.get('reason', '')),
                    verify=str(row.get('verify', '')),
                )
            )
        if not steps:
            raise ValueError('computer plan contained no executable steps')
        plan = {'summary': str(data.get('summary', '')), 'steps': [step.__dict__ for step in steps]}
        self._emit('computer.planned', goal=goal, step_count=len(steps))
        return plan

    @staticmethod
    def _validate_params(kind: str, params: dict):
        if kind in {'move', 'click'}:
            for key in ('x', 'y'):
                if key in params:
                    value = int(params[key])
                    if value < -10000 or value > 10000:
                        raise ValueError(f'{key} is outside the allowed coordinate range')
                    params[key] = value
        if kind == 'type_text':
            text = str(params.get('text', ''))
            if not text or len(text) > 8000:
                raise ValueError('type_text requires 1-8000 characters')
            params['text'] = text
        if kind == 'hotkey':
            keys = list(params.get('keys') or [])
            if not 1 <= len(keys) <= 5 or any(len(str(key)) > 24 for key in keys):
                raise ValueError('hotkey requires 1-5 bounded key names')
            params['keys'] = [str(key).lower() for key in keys]

    @staticmethod
    def _binding(context: dict) -> OperatorBinding:
        required = ('owner_id', 'device_id', 'session_id', 'security_epoch')
        if not isinstance(context, dict) or any(context.get(key) in (None, '') for key in required):
            raise PermissionError('trusted operator authority binding is required')
        return OperatorBinding(
            owner_id=str(context['owner_id']),
            device_id=str(context['device_id']),
            session_id=str(context['session_id']),
            security_epoch=int(context['security_epoch']),
            conversation_id=str(context.get('conversation_id') or ''),
            workflow_id=str(context.get('workflow_id') or ''),
        )

    def prepare_execution(self, parameters: dict) -> dict:
        params = dict(parameters or {})
        context = dict(params.get('_trusted_context') or {})
        binding = self._binding(context)
        goal = str(params.get('goal') or '').strip()
        if not goal:
            raise ValueError('computer execution goal is required')
        max_steps = max(1, min(int(params.get('max_steps', 8)), 12))
        monitor = int(params.get('monitor', 1))
        timeout_seconds = max(5, min(int(params.get('timeout_seconds', 120)), 600))
        plan = params.get('_operator_plan')
        if not isinstance(plan, dict):
            observation = self.observe(f'Describe the screen before preparing this goal: {goal}', monitor=monitor)
            plan = self.plan(goal, observation=observation, max_steps=max_steps)
        steps = list(plan.get('steps') or [])
        if not steps or len(steps) > max_steps:
            raise ValueError('prepared operator plan is invalid')
        for row in steps:
            kind = str(row.get('kind', ''))
            if kind not in ALLOWED_DESKTOP_ACTIONS:
                raise ValueError(f'unsupported computer action: {kind}')
            self._validate_params(kind, row.setdefault('params', {}))
        txid = str(params.get('_operator_transaction_id') or new_transaction_id())
        record, created = self.operator_transactions.propose(
            txid,
            binding,
            goal=goal,
            action_plan=plan,
            deadline_at=time.time() + timeout_seconds,
        )
        if created:
            self.operator_transactions.transition(txid, 'policy_check')
            self.operator_transactions.transition(txid, 'approval_required')
        elif record['state'] not in {'approval_required', 'permitted', 'completed'}:
            raise RuntimeError(f'operator transaction cannot be prepared from state {record["state"]}')
        params['goal'] = goal
        params['max_steps'] = max_steps
        params['monitor'] = monitor
        params['timeout_seconds'] = timeout_seconds
        params['_trusted_context'] = context
        params['_operator_plan'] = plan
        params['_operator_transaction_id'] = txid
        return params

    def reject_execution(self, parameters: dict):
        txid = str((parameters or {}).get('_operator_transaction_id') or '')
        if not txid:
            return False
        tx = self.operator_transactions.transaction(txid)
        if tx and tx['state'] == 'approval_required':
            self.operator_transactions.transition(txid, 'cancelled', error_code='approval_rejected')
            return True
        return False

    def _semantic_verify(self, question: str, monitor: int = 1):
        if not question:
            return {'checked': False, 'verified': True, 'analysis': ''}
        prompt = (
            f'Verify this UI postcondition: {question}. '
            'Start the answer with VERIFIED or NOT_VERIFIED, then give one short reason.'
        )
        result = self.screen.analyze(prompt, monitor=monitor)
        analysis = str(result.get('analysis', ''))
        normalized = analysis.strip().upper()
        return {
            'checked': True,
            'verified': normalized.startswith('VERIFIED') and not normalized.startswith('VERIFIED NOT'),
            'analysis': analysis,
            'screenshot': result.get('screenshot'),
        }

    def _guard(self, txid: str, binding: OperatorBinding, cancel_event=None):
        tx = self.operator_transactions.assert_binding(txid, binding)
        if self.emergency_stop():
            if tx['state'] not in {'completed', 'failed', 'cancelled', 'recovery_review_required'}:
                self.operator_transactions.transition(txid, 'cancelled', error_code='emergency_stop')
            raise PermissionError('owner emergency stop is active')
        if cancel_event is not None and cancel_event.is_set():
            self.operator_transactions.request_cancel(txid)
        tx = self.operator_transactions.transaction(txid)
        if tx and tx['cancel_requested']:
            if tx['state'] not in {'completed', 'failed', 'cancelled', 'recovery_review_required'}:
                self.operator_transactions.transition(txid, 'cancelled', error_code='cancelled')
            raise RuntimeError('computer execution cancelled by user')
        if tx and tx.get('deadline_at') is not None and time.time() >= float(tx['deadline_at']):
            if tx['state'] not in {'completed', 'failed', 'cancelled', 'recovery_review_required'}:
                self.operator_transactions.transition(txid, 'failed', error_code='deadline_exceeded')
            raise TimeoutError('computer execution deadline exceeded')
        return tx

    def execute_prepared(self, parameters: dict, *, cancel_event=None):
        params = dict(parameters or {})
        if not params.get('_personal_ai_prepared'):
            raise PermissionError('computer execution requires a Personal AI prepared and approved plan')
        context = dict(params.get('_trusted_context') or {})
        binding = self._binding(context)
        txid = str(params.get('_operator_transaction_id') or '')
        plan = params.get('_operator_plan')
        if not txid or not isinstance(plan, dict):
            raise PermissionError('computer execution is missing its approved operator transaction')
        goal = str(params.get('goal') or '')
        monitor = int(params.get('monitor', 1))

        with self._lock:
            tx = self.operator_transactions.assert_binding(txid, binding)
            if tx['state'] == 'completed':
                return {'ok': True, 'verified': True, 'transaction_id': txid, 'deduplicated': True, 'state': 'completed'}
            if tx['state'] == 'approval_required':
                self.operator_transactions.transition(txid, 'permitted')
            self.operator_transactions.assert_dispatchable(txid, binding)
            self._guard(txid, binding, cancel_event)
            self.operator_transactions.transition(txid, 'executing')

            physical_tx = self.transactions.begin()
            evidence = []
            dispatched = False
            self._emit('state', state='acting')
            self._emit('computer.execution.started', transaction_id=txid, goal=goal, step_count=len(plan.get('steps', [])))
            try:
                for index, row in enumerate(list(plan.get('steps', [])), start=1):
                    self._guard(txid, binding, cancel_event)
                    step = ComputerPlanStep(**row)
                    self._validate_params(step.kind, step.params)
                    action, created = self.operator_transactions.start_action(
                        txid,
                        index,
                        kind=step.kind,
                        parameter_hash=parameter_hash(step.params),
                        expected_postcondition=step.verify,
                    )
                    if not created:
                        if action.get('state') == 'verified':
                            evidence.append({'step': index, 'kind': step.kind, 'deduplicated': True, 'verified': True})
                            continue
                        raise RuntimeError('operator action requires recovery review before redispatch')
                    dispatched = True
                    try:
                        result = self.transactions.execute(physical_tx, step.kind, **step.params)
                    except Exception as exc:
                        self.operator_transactions.transition(txid, 'recovery_review_required', error_code=type(exc).__name__, recovery_reason='desktop_dispatch_outcome_uncertain')
                        self.transactions.rollback(physical_tx)
                        raise
                    if not result.get('verified'):
                        self.operator_transactions.finish_action(action['action_id'], verified=False, evidence={'action_verified': False}, error_code='screen_change_unverified')
                        self.operator_transactions.transition(txid, 'recovery_review_required', error_code='verification_failed', recovery_reason='desktop_action_change_unverified')
                        self.transactions.rollback(physical_tx)
                        raise RuntimeError(f'computer action did not produce a verifiable change: step {index}')
                    semantic = self._semantic_verify(step.verify, monitor=monitor)
                    if semantic['checked'] and not semantic['verified']:
                        self.operator_transactions.finish_action(action['action_id'], verified=False, evidence={'action_verified': True, 'semantic_checked': True}, error_code='semantic_verification_failed')
                        self.operator_transactions.transition(txid, 'recovery_review_required', error_code='verification_failed', recovery_reason='semantic_postcondition_failed')
                        self.transactions.rollback(physical_tx)
                        raise RuntimeError(f'computer postcondition failed at step {index}: {semantic["analysis"]}')
                    safe_evidence = {'action_verified': True, 'semantic_checked': bool(semantic['checked']), 'semantic_verified': bool(semantic['verified'])}
                    self.operator_transactions.finish_action(action['action_id'], verified=True, evidence=safe_evidence)
                    evidence.append({'step': index, 'kind': step.kind, **safe_evidence})
                    self._emit('computer.step.verified', transaction_id=txid, step=index, kind=step.kind)

                self.operator_transactions.transition(txid, 'verifying')
                self._guard(txid, binding, cancel_event)
                final = self.observe(f'Describe the completed state for this goal: {goal}', monitor=monitor)
                committed = self.transactions.commit(physical_tx)
                self.operator_transactions.transition(txid, 'completed')
                output = {
                    'ok': True,
                    'verified': True,
                    'goal': goal,
                    'transaction_id': txid,
                    'plan': plan,
                    'evidence': evidence,
                    'final': final,
                    **committed,
                }
                self._emit('computer.execution.completed', transaction_id=txid, goal=goal)
                return output
            except Exception as exc:
                current = self.operator_transactions.transaction(txid)
                if current and current['state'] in {'executing', 'verifying'}:
                    target = 'recovery_review_required' if dispatched else 'failed'
                    self.operator_transactions.transition(txid, target, error_code=type(exc).__name__, recovery_reason='execution_failed_after_dispatch' if dispatched else '')
                    try: self.transactions.rollback(physical_tx)
                    except Exception: pass
                self._emit('computer.execution.failed', transaction_id=txid, goal=goal, error_type=type(exc).__name__)
                raise

    def execute(self, goal: str, *, plan: dict | None = None, max_steps: int = 8, monitor: int = 1, cancel_event=None):
        """Legacy direct runtime entry retained for isolated tests; exposed tools use execute_prepared."""
        with self._lock:
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError('computer execution cancelled before start')
            initial = self.observe(f'Describe the screen before executing this goal: {goal}', monitor=monitor)
            plan = plan or self.plan(goal, observation=initial, max_steps=max_steps)
            steps = [ComputerPlanStep(**row) for row in list(plan.get('steps', []))[:max_steps]]
            tx = self.transactions.begin(); evidence=[]
            try:
                for index, step in enumerate(steps):
                    if cancel_event is not None and cancel_event.is_set():raise RuntimeError('computer execution cancelled by user')
                    self._validate_params(step.kind, step.params); result=self.transactions.execute(tx, step.kind, **step.params)
                    if not result.get('verified'):raise RuntimeError(f'computer action did not produce a verifiable change: step {index + 1}')
                    semantic=self._semantic_verify(step.verify, monitor=monitor)
                    if semantic['checked'] and not semantic['verified']:raise RuntimeError(f'computer postcondition failed at step {index + 1}: {semantic["analysis"]}')
                    evidence.append({'step':index+1,'kind':step.kind,'action_verified':True,'semantic_verify':semantic})
                final=self.observe(f'Describe the completed state for this goal: {goal}', monitor=monitor); committed=self.transactions.commit(tx)
                return {'ok':True,'verified':True,'goal':goal,'transaction_id':tx.id,'plan':plan,'evidence':evidence,'final':final,**committed}
            except Exception:
                self.transactions.rollback(tx); raise
