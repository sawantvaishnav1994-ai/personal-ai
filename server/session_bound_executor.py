from __future__ import annotations

from agent.executor import ReauthenticationRequired
from core.turn_context import new_turn_context, reset_turn_context, set_turn_context
from desktop.operator_context import OperatorRequestContext, reset_operator_request, set_operator_request
from models.router import ModelError
from security.request_context import current_trusted_request


class OwnerReauthenticationRequired(ModelError):
    code = 'reauthentication_required'
    status_code = 401
    user_message = 'This critical action requires a recent owner verification. Verify your owner password or passkey and try again.'


class SessionBoundExecutor:
    """Bind authenticated surfaces to the canonical executor and continuity ledger.

    This adapter does not become a new authority. It binds trusted request/session
    identity, bounded P8 conversation history and turn metadata before delegating
    intelligence/action authority to the existing AgentExecutor.
    """

    def __init__(self, executor, *, continuity=None, surface: str = 'pwa'):
        self._executor = executor
        self._continuity = continuity
        self._surface = str(surface or 'pwa')

    def __getattr__(self, name):
        return getattr(self._executor, name)

    @staticmethod
    def _context():
        context = current_trusted_request()
        if context is None:
            raise PermissionError('trusted browser session is required')
        return context

    @staticmethod
    def _check_device(explicit_device_id, context):
        if explicit_device_id is not None and explicit_device_id != context.device_id:
            raise PermissionError('trusted browser session device mismatch')

    @staticmethod
    def _translate_reauth(callback):
        try:
            return callback()
        except ReauthenticationRequired as exc:
            raise OwnerReauthenticationRequired(exc.reason) from exc

    def _security_epoch(self) -> int:
        approvals = getattr(self._executor, 'approvals', None)
        current = getattr(approvals, 'current_security_epoch', None)
        return int(current()) if callable(current) else 0

    def _approval_context(self, approval_id: str) -> dict:
        lookup = getattr(self._executor, 'approval_context', None)
        return dict(lookup(approval_id) or {}) if callable(lookup) else {}

    def _operator_context(self, context, metadata):
        return OperatorRequestContext(
            owner_id=str(metadata.get('owner_id') or 'owner'),
            device_id=context.device_id,
            session_id=context.session_id,
            security_epoch=self._security_epoch(),
            conversation_id=str(metadata.get('conversation_id') or ''),
            workflow_id=str(metadata.get('workflow_id') or ''),
            reauthenticated_at=context.reauthenticated_at,
        )

    def _canonical_turn_context(self, context, metadata):
        conversation_id = str(metadata.get('conversation_id') or '')
        return new_turn_context(
            request_id=metadata.get('request_id'),
            conversation_id=conversation_id,
            owner_id=str(metadata.get('owner_id') or 'owner'),
            device_id=context.device_id,
            session_id=context.session_id,
            security_epoch=self._security_epoch(),
            surface=str(metadata.get('surface') or self._surface),
            input_modality=str(metadata.get('input_modality') or 'text'),
            privacy_level=str(metadata.get('privacy_level') or 'normal'),
            risk_level=str(metadata.get('risk_level') or 'low'),
            memory_refs=metadata.get('memory_refs') or (),
            knowledge_refs=metadata.get('knowledge_refs') or (),
            p7_observation_refs=metadata.get('p7_observation_refs') or (),
            p8_continuity_refs=(conversation_id,) if conversation_id else (),
            model_routing_refs=metadata.get('model_routing_refs') or (),
            p10_goal_refs=metadata.get('p10_goal_refs') or (),
            tool_refs=metadata.get('tool_refs') or (),
            approval_refs=metadata.get('approval_refs') or (),
            verification_refs=metadata.get('verification_refs') or (),
            recovery_refs=metadata.get('recovery_refs') or (),
        )

    def _bound(self, context, metadata, callback):
        operator_token = set_operator_request(self._operator_context(context, metadata))
        turn_token = set_turn_context(self._canonical_turn_context(context, metadata))
        try:
            return callback()
        finally:
            reset_turn_context(turn_token)
            reset_operator_request(operator_token)

    def _conversation(self, context, explicit_conversation_id):
        if self._continuity is None:
            return str(explicit_conversation_id or '')
        if explicit_conversation_id:
            thread = self._continuity.thread(str(explicit_conversation_id))
            if not thread or thread.get('closed_at'):
                raise PermissionError('active conversation is unavailable')
            self._continuity.set_active(context.device_id, thread['id'])
            return str(thread['id'])
        bundle = self._continuity.resume(context.device_id, event_limit=32)
        thread = bundle.get('thread') or {}
        conversation_id = str(thread.get('id') or '')
        if not conversation_id:
            raise RuntimeError('continuity failed to establish a conversation')
        return conversation_id

    def _conversation_history(self, conversation_id: str, explicit_history):
        if explicit_history is not None:
            return list(explicit_history)[-16:]
        if not self._continuity or not conversation_id:
            return None
        history = getattr(self._continuity, 'conversation_history', None)
        if callable(history):
            return history(conversation_id, limit=16)
        return None

    def chat(self, text, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        metadata = dict(kwargs)
        conversation_id = self._conversation(context, kwargs.get('conversation_id'))
        conversation_history = self._conversation_history(conversation_id, kwargs.get('conversation_history'))

        call_kwargs = dict(kwargs)
        metadata_only = {
            'workflow_id', 'request_id', 'surface', 'input_modality', 'privacy_level', 'risk_level',
            'memory_refs', 'knowledge_refs', 'p7_observation_refs', 'model_routing_refs',
            'p10_goal_refs', 'tool_refs', 'approval_refs', 'verification_refs', 'recovery_refs',
        }
        for key in metadata_only:
            call_kwargs.pop(key, None)
        call_kwargs['device_id'] = context.device_id
        call_kwargs['session_id'] = context.session_id
        call_kwargs['reauthenticated_at'] = context.reauthenticated_at
        if conversation_id:
            call_kwargs['conversation_id'] = conversation_id
        if conversation_history is not None:
            call_kwargs['conversation_history'] = conversation_history

        metadata.update(call_kwargs)
        metadata['conversation_id'] = conversation_id
        metadata.setdefault('surface', self._surface)
        return self._bound(
            context,
            metadata,
            lambda: self._translate_reauth(lambda: self._executor.chat(text, **call_kwargs)),
        )

    def approve(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        approval_context = self._approval_context(approval_id)
        metadata = dict(kwargs)
        metadata.setdefault('conversation_id', approval_context.get('conversation_id') or '')
        metadata.setdefault('owner_id', 'owner')
        metadata.setdefault('surface', self._surface)
        metadata.setdefault('input_modality', 'approval')
        metadata.setdefault('approval_refs', (approval_id,))
        call_kwargs = {key: value for key, value in kwargs.items() if key in {'device_id', 'session_id', 'owner_id', 'reauthenticated_at'}}
        call_kwargs['device_id'] = context.device_id
        call_kwargs['session_id'] = context.session_id
        call_kwargs['reauthenticated_at'] = context.reauthenticated_at
        return self._bound(
            context,
            metadata,
            lambda: self._translate_reauth(lambda: self._executor.approve(approval_id, **call_kwargs)),
        )

    def reject(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        approval_context = self._approval_context(approval_id)
        metadata = dict(kwargs)
        metadata.setdefault('conversation_id', approval_context.get('conversation_id') or '')
        metadata.setdefault('owner_id', 'owner')
        metadata.setdefault('surface', self._surface)
        metadata.setdefault('input_modality', 'approval')
        metadata.setdefault('approval_refs', (approval_id,))
        paused = self._executor._load_paused(approval_id) if hasattr(self._executor, '_load_paused') else None
        tool = None; params = None
        if paused:
            step = paused['plan']['steps'][paused['index']]
            tool = self._executor.tools.get(step['tool'])
            params = step.get('parameters', {})
        call_kwargs = {key: value for key, value in kwargs.items() if key in {'device_id', 'session_id'}}
        call_kwargs['device_id'] = context.device_id
        call_kwargs['session_id'] = context.session_id
        result = self._bound(context, metadata, lambda: self._executor.reject(approval_id, **call_kwargs))
        if tool is not None and tool.on_reject is not None:
            tool.on_reject(params or {})
        return result
