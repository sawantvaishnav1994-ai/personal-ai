from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from devices.presence_projection import DevicesPresenceProjection
from security.request_context import current_trusted_request


def devices_presence_router(runtime):
    """Read-only owner transport over canonical device trust and presence."""
    router = APIRouter(prefix='/iphone/api/devices-presence', tags=['devices-presence'])
    devices = runtime['device_registry']
    projection = DevicesPresenceProjection(devices, runtime.get('device_gateway'))

    def require_owner():
        context = current_trusted_request()
        if context is None:
            raise HTTPException(401, 'Trusted owner session required')
        if not devices.is_active(context.device_id):
            raise HTTPException(401, 'Trusted device is revoked')
        if not hasattr(devices, 'authorize') or not devices.authorize(context.device_id, 'device:read'):
            raise HTTPException(403, 'This device is not permitted to read devices')
        return context

    @router.get('')
    def list_devices():
        require_owner()
        return {'devices': projection.list()}

    @router.get('/{device_id}')
    def device_detail(device_id: str = Path(..., min_length=1, max_length=200)):
        require_owner()
        item = projection.detail(device_id)
        if item is None:
            raise HTTPException(404, 'Device not found')
        return {'device': item}

    return router
