from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from security.request_context import TrustedRequestContext, reset_trusted_request, set_trusted_request
from server.personal_operations_api import personal_operations_router
from tests.p6_support import Harness


class Registry:
    def authenticate(self, device_id, token):
        return device_id == 'device-1' and token == 'token-1'

    def authorize(self, device_id, scope):
        return device_id == 'device-1' and scope in {'ai:chat', 'memory:sensitive'}


def client_for(h):
    app = FastAPI()

    @app.middleware('http')
    async def trusted_context(request, call_next):
        token = set_trusted_request(TrustedRequestContext('device-1', 'session-1'))
        try:
            return await call_next(request)
        finally:
            reset_trusted_request(token)

    app.include_router(personal_operations_router({
        'device_registry': Registry(),
        'personal_operations': h.operations,
    }))
    return TestClient(app)


def test_owner_operations_api_requires_trusted_device_and_exposes_safe_state(tmp_path):
    h = Harness(tmp_path)
    try:
        h.read_tool()
        client = client_for(h)
        assert client.get('/iphone/api/operations').status_code == 401
        client.cookies.set('pa_device', 'device-2')
        client.cookies.set('pa_token', 'token-1')
        assert client.get('/iphone/api/operations').status_code == 401
        client.cookies.clear()
        client.cookies.set('pa_device', 'device-1')
        client.cookies.set('pa_token', 'token-1')
        created = client.post('/iphone/api/operations/plans', json={
            'title': 'API read',
            'steps': [{'requested_tool': 'read_context', 'parameters': {'value': 'safe'}}],
        })
        assert created.status_code == 200
        created_payload = created.json()
        assert 'parameters' not in json.dumps(created_payload)
        assert 'value' not in created_payload
        plan_id = created_payload['id']
        executed = client.post(f'/iphone/api/operations/plans/{plan_id}/execute', json={'background': False})
        assert executed.status_code == 200
        operation = executed.json()['operation']
        assert operation['status'] == 'verified'
        detail = client.get(f"/iphone/api/operations/{operation['operation_id']}")
        assert detail.status_code == 200
        payload = detail.json()
        serialized = json.dumps(payload)
        assert 'session-1' not in serialized
        assert 'idempotency_key' not in serialized
        assert 'approval_id' not in serialized
        assert 'security_epoch' not in serialized
        assert 'budget_run_id' not in serialized
        assert 'workflow_id' not in serialized
        assert 'dispatches' not in serialized
        assert '"run_id"' not in serialized
        assert 'parameters' not in serialized
        listing = client.get('/iphone/api/operations')
        assert listing.status_code == 200
        assert listing.json()['status']['verified'] == 1
    finally:
        h.close()


def test_owner_api_consequential_approval_uses_existing_ticket(tmp_path):
    h = Harness(tmp_path)
    try:
        counter = h.side_tool()
        client = client_for(h)
        client.cookies.set('pa_device', 'device-1')
        client.cookies.set('pa_token', 'token-1')
        created = client.post('/iphone/api/operations/plans', json={
            'title': 'API send',
            'steps': [{
                'requested_tool': 'send_action',
                'parameters': {'recipient': 'api.example', 'reference': 'fixture'},
            }],
        }).json()
        waiting = client.post(f"/iphone/api/operations/plans/{created['id']}/execute", json={'background': False}).json()['operation']
        assert waiting['status'] == 'waiting_approval'
        assert counter.value == 0
        approved = client.post(f"/iphone/api/operations/{waiting['operation_id']}/approve")
        assert approved.status_code == 200
        assert approved.json()['status'] == 'verified'
        assert counter.value == 1
    finally:
        h.close()
