from __future__ import annotations

from fastapi import APIRouter, HTTPException

from activities.projection import ActivitiesProjection
from security.request_context import current_trusted_request


def activities_router(runtime):
    """Owner-authorized user-safe Activities view over canonical audit."""
    router = APIRouter(prefix='/iphone/api/activities', tags=['activities'])
    registry = runtime['device_registry']
    projection = ActivitiesProjection(runtime['memory'])

    def require_owner():
        context = current_trusted_request()
        if context is None:
            raise HTTPException(401, 'Trusted owner session required')
        if not registry.is_active(context.device_id):
            raise HTTPException(401, 'Trusted device is revoked')
        # Activities can reveal operational metadata; use the existing audit/read
        # capability when present and otherwise require owner-level chat trust.
        if hasattr(registry, 'authorize'):
            allowed = registry.authorize(context.device_id, 'audit:read') or registry.authorize(context.device_id, 'ai:chat')
            if not allowed:
                raise HTTPException(403, 'This device is not permitted to read Activities')
        return context

    @router.get('')
    def list_activities(limit: int = 100, category: str | None = None):
        require_owner()
        return {'activities': projection.list(limit=max(1, min(int(limit), 500)), category=category)}

    return router
