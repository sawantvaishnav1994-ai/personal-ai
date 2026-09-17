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
        if not hasattr(registry, 'authorize') or not registry.authorize(context.device_id, 'activities:read'):
            raise HTTPException(403, 'This device is not permitted to read Activities')
        return context

    @router.get('')
    def list_activities(
        limit: int = 50,
        category: str | None = None,
        status: str | None = None,
        cursor: str | None = None,
    ):
        require_owner()
        try:
            return projection.page(
                limit=max(1, min(int(limit), projection.MAX_PAGE)),
                category=category,
                status=status,
                cursor=cursor,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.get('/{activity_id}')
    def activity_detail(activity_id: str):
        require_owner()
        detail = projection.detail(activity_id)
        if detail is None:
            raise HTTPException(404, 'Activity not found')
        return {'activity': detail}

    return router
