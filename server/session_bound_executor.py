from __future__ import annotations

from security.request_context import current_trusted_request


class SessionBoundExecutor:
    """Bind legacy PWA executor calls to the middleware-authenticated session."""

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

    def chat(self, text, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        kwargs['device_id'] = context.device_id
        kwargs['session_id'] = context.session_id
        kwargs['reauthenticated_at'] = context.reauthenticated_at
        return self._executor.chat(text, **kwargs)

    def approve(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        kwargs['device_id'] = context.device_id
        kwargs['session_id'] = context.session_id
        kwargs['reauthenticated_at'] = context.reauthenticated_at
        return self._executor.approve(approval_id, **kwargs)

    def reject(self, approval_id: str, **kwargs):
        context = self._context()
        self._check_device(kwargs.get('device_id'), context)
        kwargs['device_id'] = context.device_id
        kwargs['session_id'] = context.session_id
        return self._executor.reject(approval_id, **kwargs)
