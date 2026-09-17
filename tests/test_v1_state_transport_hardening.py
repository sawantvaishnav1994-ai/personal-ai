from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.events import EventBus
from server.logical_request_middleware import LogicalRequestMiddleware, MAX_LOGICAL_TURN_BODY


def test_runtime_state_sequence_is_monotonic_and_duplicate_is_idempotent():
    events = EventBus()
    authority = events.runtime_state
    first = authority.transition('ACTIVE', reason='test')
    duplicate = authority.transition('ACTIVE', reason='duplicate')
    second = authority.transition('UNDERSTANDING', reason='turn', request_id='r1')
    assert duplicate.sequence == first.sequence
    assert second.sequence == first.sequence + 1
    assert authority.snapshot().sequence == second.sequence


def test_logical_request_middleware_rejects_oversized_turn_before_downstream():
    calls = []
    app = FastAPI()

    @app.post('/iphone/api/voice/turn')
    async def downstream():
        calls.append(True)
        return {'ok': True}

    app.add_middleware(LogicalRequestMiddleware)
    client = TestClient(app)
    response = client.post('/iphone/api/voice/turn', content=b'{' + b'x' * MAX_LOGICAL_TURN_BODY + b'}')
    assert response.status_code == 413
    assert calls == []


def test_v1_browser_adapter_has_secure_uuid_and_no_network_semantic_state_invention():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert "typeof c.getRandomValues!=='function'" in source
    assert 'Math.random' not in source
    assert 'Date.now()' in source  # bounded retention timestamp only, never identity
    assert "setState('understanding')" not in source
    assert "setState('thinking')" not in source
    assert "setState('error'" not in source
    assert "api('/runtime-state')" in source
    assert 'sequence<=canonicalSequence' in source
    assert 'MAX_PENDING_AGE_MS' in source


def test_activities_projection_contract_is_the_ui_safe_shape():
    from activities.projection import ActivitiesProjection
    projected = ActivitiesProjection.project_entry({
        'id': 'a1', 'category': 'tool', 'action': 'completed', 'created_at': 'now',
        'payload': {'authorization': 'secret', 'nested': {'cookie': 'secret', 'safe': 'ok'}},
    })
    assert set(projected) == {'id', 'kind', 'label', 'action', 'status', 'created_at', 'details'}
    assert projected['details']['authorization'] == '[redacted]'
    assert projected['details']['nested']['cookie'] == '[redacted]'
    assert projected['details']['nested']['safe'] == 'ok'
