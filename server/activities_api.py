from __future__ import annotations

from fastapi import APIRouter, HTTPException

from activities.projection import ActivitiesProjection
from security.request_context import current_trusted_request


def activities_router(runtime):
    """Least-privilege owner-safe Activities view over canonical Audit."""
    router = APIRouter(prefix='/iphone/api/activities', tags=['activities'])
    registry = runtime['device_registry']
    projection = ActivitiesProjection(runtime['memory'])

    def require_owner():
        context = current_trusted_request()
        if context is None:
            raise HTTPException(401, 'Trusted owner session required')
        if not registry.is_active(context.device_id):
            raise HTTPException(401, 'Trusted device is revoked')
        # Activities is a bounded projection, not generic chat authority. The
        # device registry already provisions the dedicated activities:read scope.
        # Never fall back to ai:chat: chat permission must not expose operational
        # activity metadata.
        if not hasattr(registry, 'authorize') or not registry.authorize(context.device_id, 'activities:read'):
            raise HTTPException(403, 'This device is not permitted to read Activities')
        return context

    @router.get('')
    def list_activities(limit: int = 100, category: str | None = None):
        require_owner()
        return {'activities': projection.list(limit=max(1, min(int(limit), 500)), category=category)}

    return router
