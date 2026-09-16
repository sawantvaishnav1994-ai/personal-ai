from __future__ import annotations

from agent.executor import ReauthenticationRequired
from models.router import ModelError
from security.request_context import current_trusted_request


class OwnerReauthenticationRequired(ModelError):
    code = 'reauthentication_required'
    status_code = 401
    user_message = 'This critical action requires a recent owner verification. Verify your owner password or passkey and try again.'


class SessionBoundExecutor:
    """Bind an authenticated browser session to the canonical Personal AI runtime.

    Authentication/device trust remain authoritative in the PWA security layer.
    Turn/conversation orchestration is delegated to CanonicalTurnRuntime so every
    interaction surface uses the same conversation and replay-safety path.
    """

    def __init__(self, executor, *, continuity=None, surface: str = 'pwa'):
        self._executor = executor
        self._surface = str(surface or 'pwa')
        # Backwards-compatible constructor only. Conversation authority belongs
        # to CanonicalTurnRuntime, not this authentication bridge.
        self._continuity = continuity

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

    @staticmethod
    def _owner_only(kwargs):
        owner = str(kwargs.get('owner_id') or 'owner')
        if owner != 'owner':
            raise PermissionError('authenticated Personal AI surfaces are owner-only')

    def chat(self, text, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        self._owner_only(kwargs)
        call_kwargs = dict(kwargs)
        call_kwargs['owner_id'] = 'owner'
        call_kwargs['device_id'] = context.device_id
        call_kwargs['session_id'] = context.session_id
        call_kwargs['reauthenticated_at'] = context.reauthenticated_at
        call_kwargs.setdefault('surface', self._surface)
        return self._translate_reauth(lambda: self._executor.chat(text, **call_kwargs))

    def approve(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        self._owner_only(kwargs)
        call_kwargs = {
            'owner_id': 'owner',
            'device_id': context.device_id,
            'session_id': context.session_id,
            'reauthenticated_at': context.reauthenticated_at,
        }
        return self._translate_reauth(lambda: self._executor.approve(approval_id, **call_kwargs))

    def reject(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        self._owner_only(kwargs)
        # Reject has a deliberately narrow authority surface in AgentExecutor.
        return self._executor.reject(
            approval_id,
            device_id=context.device_id,
            session_id=context.session_id,
        )
