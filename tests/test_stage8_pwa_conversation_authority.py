from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from devices.continuity import ContinuityService
from devices.registry import DeviceRegistry
from security.pwa_sessions import PwaSessionStore
from server.pwa_conversations import pwa_conversation_router
from server.pwa_session_middleware import PwaSessionMiddleware


def make_client(tmp_path):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    device, _ = registry.enroll('Stage8 browser', 'ios-pwa')
    registry.set_permissions(device['id'], {'ai:chat'})
    sessions = PwaSessionStore(tmp_path / 'pwa-sessions.sqlite3', ttl_seconds=600)
    continuity = ContinuityService(tmp_path / 'continuity.sqlite3')

    app = FastAPI()
    app.add_middleware(
        PwaSessionMiddleware,
        sessions=sessions,
        device_registry=registry,
        cookie_max_age=600,
    )

    @app.post('/iphone/api/access/password/login')
    def login(response: Response):
        response.set_cookie(
            'pa_device',
            device['id'],
            secure=True,
            httponly=True,
            samesite='strict',
            path='/iphone',
        )
        response.set_cookie(
            'pa_token',
            'fixture-token',
            secure=True,
            httponly=True,
            samesite='strict',
            path='/iphone',
        )
        return {'ok': True}

    app.include_router(
        pwa_conversation_router({
            'continuity': continuity,
            'device_registry': registry,
        })
    )
    client = TestClient(app, base_url='https://testserver')
    assert client.post('/iphone/api/access/password/login').status_code == 200
    return client, registry, device, continuity


def seed(continuity, device_id, title):
    thread = continuity.create_thread(title, device_id=device_id)
    continuity.append(
        thread,
        device_id=device_id,
        kind='user_message',
        payload={'text': f'{title} private owner content'},
    )
    return thread


def test_stage8_conversation_lifecycle_requires_current_ai_chat_scope(tmp_path):
    client, registry, device, continuity = make_client(tmp_path)

    export_thread = seed(continuity, device['id'], 'export')
    archive_thread = seed(continuity, device['id'], 'archive')
    delete_thread = seed(continuity, device['id'], 'delete')

    # Positive control: the live trusted browser with ai:chat can use the
    # owner conversation lifecycle surface.
    allowed = client.get(f'/iphone/api/conversations/{export_thread}/export')
    assert allowed.status_code == 200
    assert allowed.json()['conversation']['id'] == export_thread

    # Permission revocation does not revoke the device or browser session.
    # Every subsequent conversation read/mutation must re-check current
    # capability instead of treating session existence as durable authority.
    registry.set_permissions(device['id'], {'device:read'})

    blocked_export = client.get(f'/iphone/api/conversations/{export_thread}/export')
    blocked_archive = client.post(f'/iphone/api/conversations/{archive_thread}/archive')
    blocked_delete = client.delete(f'/iphone/api/conversations/{delete_thread}')

    for response in (blocked_export, blocked_archive, blocked_delete):
        assert response.status_code == 403
        assert 'ai:chat' in response.json()['detail']

    # Rejection must be side-effect free.
    assert continuity.thread(archive_thread)['closed_at'] is None
    assert continuity.thread(delete_thread) is not None
