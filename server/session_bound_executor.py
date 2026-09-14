from __future__ import annotations

from agent.executor import ReauthenticationRequired
from desktop.operator_context import OperatorRequestContext, reset_operator_request, set_operator_request
from models.router import ModelError
from security.request_context import current_trusted_request


class OwnerReauthenticationRequired(ModelError):
    code = 'reauthentication_required'
    status_code = 401
    user_message = 'This critical action requires a recent owner verification. Verify your owner password or passkey and try again.'


class SessionBoundExecutor:
    """Bind PWA executor calls and consequential operator work to the authenticated session."""

    def __init__(self, executor):
        self._executor = executor

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

    def _bound(self, context, metadata, callback):
        token = set_operator_request(self._operator_context(context, metadata))
        try:
            return callback()
        finally:
            reset_operator_request(token)

    def chat(self, text, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        metadata = dict(kwargs)
        call_kwargs = dict(kwargs)
        call_kwargs.pop('workflow_id', None)
        call_kwargs['device_id'] = context.device_id
        call_kwargs['session_id'] = context.session_id
        call_kwargs['reauthenticated_at'] = context.reauthenticated_at
        metadata.update(call_kwargs)
        return self._bound(
            context,
            metadata,
            lambda: self._translate_reauth(lambda: self._executor.chat(text, **call_kwargs)),
        )

    def approve(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        approval_context = self._executor.approval_context(approval_id) or {}
        metadata = dict(kwargs)
        metadata.setdefault('conversation_id', approval_context.get('conversation_id') or '')
        metadata.setdefault('owner_id', 'owner')
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
        approval_context = self._executor.approval_context(approval_id) or {}
        metadata = dict(kwargs)
        metadata.setdefault('conversation_id', approval_context.get('conversation_id') or '')
        metadata.setdefault('owner_id', 'owner')
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
