from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from devices.presence_projection import DevicesPresenceProjection
from devices.registry import DeviceRegistry
from security.request_context import trusted_request
from server.devices_presence_api import devices_presence_router


class Gateway:
    def __init__(self, online=()):
        self.ids = list(online)
    def online(self):
        return list(self.ids)


def test_presence_projection_uses_live_gateway_and_redacts_metadata(tmp_path):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    device, _ = registry.enroll('<script>alert(1)</script>', 'ios')
    registry.set_metadata(device['id'], 'push.apns.token', 'Authorization: Bearer SECRET')
    registry.set_metadata(device['id'], 'label', 'https://x.test/?token=SECRET')
    projection = DevicesPresenceProjection(registry, Gateway([device['id']]))
    item = projection.detail(device['id'])
    assert item['trust_state'] == 'trusted'
    assert item['presence_state'] == 'online'
    assert item['connected'] is True
    assert 'push.apns.token' not in item['metadata']
    assert 'SECRET' not in repr(item)
    assert '<script>' in item['display_name']  # transport data; renderer must escape it


def test_enrolled_device_is_not_claimed_online_without_live_evidence(tmp_path):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    device, _ = registry.enroll('Phone', 'ios')
    item = DevicesPresenceProjection(registry, Gateway()).detail(device['id'])
    assert item['trust_state'] == 'trusted'
    assert item['presence_state'] == 'unknown'
    assert item['connected'] is False


def test_revoked_device_is_never_presented_connected(tmp_path):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    device, _ = registry.enroll('Phone', 'ios')
    registry.revoke(device['id'])
    item = DevicesPresenceProjection(registry, Gateway([device['id']])).detail(device['id'])
    assert item['trust_state'] == 'revoked'
    assert item['presence_state'] == 'revoked'
    assert item['connected'] is False


def test_devices_presence_api_requires_active_scoped_trusted_device(tmp_path, monkeypatch):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    caller, _ = registry.enroll('Owner', 'ios-pwa')
    target, _ = registry.enroll('Desktop', 'windows')
    current = {'value': None}
    monkeypatch.setattr(devices_api, 'current_trusted_request', lambda: current['value'])
    app = FastAPI()
    app.include_router(devices_presence_router({'device_registry': registry, 'device_gateway': Gateway([target['id']])}))
    client = TestClient(app)

    assert client.get('/iphone/api/devices-presence').status_code == 401
    current['value'] = TrustedRequestContext(device_id=caller['id'], session_id='s1')
    response = client.get('/iphone/api/devices-presence')
    assert response.status_code == 200
    assert any(row['device_id'] == target['id'] and row['presence_state'] == 'online' for row in response.json()['devices'])
    registry.set_permissions(caller['id'], {'ai:chat'})
    assert client.get('/iphone/api/devices-presence').status_code == 403
    registry.revoke(caller['id'])
    assert client.get('/iphone/api/devices-presence').status_code == 401
