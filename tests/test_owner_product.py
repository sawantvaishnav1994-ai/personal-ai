from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from automation.engine import AutomationEngine
from devices.registry import DeviceRegistry
from knowledge.store import KnowledgeStore
from memory.second_brain import SecondBrain
from memory.store import MemoryStore
from qualification.program import P3QualificationProgram
from server.owner_product import owner_product_router


class Executor:
    def chat(self, prompt, cancel_event=None):
        return f'done:{prompt}'


class Models:
    def status(self):
        return {'state': 'configured', 'primary_provider': 'test'}


class Tools:
    emergency_stop = False

    def all(self):
        return []


def make_client(tmp_path):
    registry = DeviceRegistry(tmp_path / 'devices.sqlite3')
    device, token = registry.enroll('Owner iPhone', 'ios-pwa')
    registry.set_permissions(device['id'], registry.OWNER_SCOPES)
    memory = MemoryStore(tmp_path / 'memory.sqlite3')
    automations = AutomationEngine(tmp_path / 'workflows.sqlite3', executor=Executor())
    runtime = {
        'device_registry': registry,
        'memory': memory,
        'second_brain': SecondBrain(memory),
        'knowledge': KnowledgeStore(tmp_path / 'knowledge.sqlite3', tmp_path / 'objects'),
        'automations': automations,
        'p3_qualification': P3QualificationProgram(tmp_path / 'qualification.sqlite3'),
        'models': Models(),
        'tools': Tools(),
        'integrations': SimpleNamespace(list=lambda: []),
        'future_intelligence': SimpleNamespace(status=lambda: {}),
    }
    app = FastAPI()
    app.include_router(owner_product_router(runtime))
    client = TestClient(app, base_url='https://testserver')
    client.cookies.set('pa_device', device['id'])
    client.cookies.set('pa_token', token)
    return client, runtime, device


def test_owner_memory_lifecycle_and_audit(tmp_path):
    client, runtime, _ = make_client(tmp_path)
    created = client.post('/iphone/api/memory', json={
        'type': 'project',
        'subject': 'Aurora',
        'content': 'Aurora is active',
        'sensitivity': 'normal',
    })
    assert created.status_code == 200
    memory_id = created.json()['id']
    assert client.get('/iphone/api/memory/graph').json()['nodes'][0]['id'] == memory_id
    assert client.get('/iphone/api/memory/tree').json()['roots'][0]['id'] == memory_id
    corrected = client.patch(f'/iphone/api/memory/{memory_id}', json={'content': 'Aurora is paused'})
    assert corrected.status_code == 200
    assert corrected.json()['content'] == 'Aurora is paused'
    assert client.get('/iphone/api/memory/export').json()['memories'][0]['id'] == memory_id
    assert client.delete(f'/iphone/api/memory/{memory_id}').status_code == 409
    assert client.delete(f'/iphone/api/memory/{memory_id}?confirm=true').status_code == 200
    actions = [row['action'] for row in runtime['memory'].audit_entries('owner-product')]
    assert 'memory.created' in actions
    assert 'memory.corrected' in actions
    assert 'memory.deleted' in actions


def test_owner_knowledge_lifecycle_and_citations(tmp_path):
    client, _, _ = make_client(tmp_path)
    created = client.post('/iphone/api/knowledge', json={
        'filename': 'facts.txt',
        'text': 'The approved launch city is Berlin.',
        'source': 'owner:test-case',
    })
    assert created.status_code == 200
    document_id = created.json()['id']
    search = client.get('/iphone/api/knowledge/search?q=launch+city').json()['results'][0]
    assert search['citation']['document_id'] == document_id
    assert search['citation']['source'] == 'owner:test-case'
    assert client.patch(f'/iphone/api/knowledge/{document_id}', json={'title': 'Launch facts'}).json()['title'] == 'Launch facts'
    assert client.delete(f'/iphone/api/knowledge/{document_id}').status_code == 409
    assert client.delete(f'/iphone/api/knowledge/{document_id}?confirm=true').status_code == 200


def test_owner_can_manage_other_device_and_revocation_is_immediate(tmp_path):
    client, runtime, owner = make_client(tmp_path)
    other, other_token = runtime['device_registry'].enroll('Desktop browser', 'web')

    listed = client.get('/iphone/api/devices')
    assert listed.status_code == 200
    assert listed.json()['current_device_id'] == owner['id']
    assert {row['id'] for row in listed.json()['devices']} == {owner['id'], other['id']}

    scopes = client.patch(
        f"/iphone/api/devices/{other['id']}/permissions",
        json={'scopes': ['ai:chat', 'memory:read']},
    )
    assert scopes.status_code == 200
    assert scopes.json()['scopes'] == ['ai:chat', 'memory:read']
    revoked = client.post(f"/iphone/api/devices/{other['id']}/revoke", json={'confirm': True})
    assert revoked.status_code == 200
    assert runtime['device_registry'].authenticate(other['id'], other_token) is False


def test_p3_stage_evidence_endpoint_records_but_does_not_self_award(tmp_path):
    client, _, _ = make_client(tmp_path)
    started = client.post('/iphone/api/qualification/stages', json={
        'stage': 'P3.5',
        'evidence_class': 'real_device',
        'environment': {'os': 'iOS 26.6.1', 'browser': 'Safari'},
    })
    assert started.status_code == 200
    session_id = started.json()['session_id']
    trial = client.post(f'/iphone/api/qualification/sessions/{session_id}/trials', json={
        'task': 'recall owner project',
        'passed': True,
        'latency_ms': 120,
        'metrics': {
            'recall_relevant': True,
            'conflict_resolved': True,
            'temporal_answer_correct': True,
            'source_traceable': True,
            'fabricated_memory': False,
            'deleted_history_on_supersession': False,
        },
        'evidence': {'artifact': 'owner-screen-recording-1'},
    })
    assert trial.status_code == 200
    client.post(f'/iphone/api/qualification/sessions/{session_id}/finish', json={'duration_seconds': 60})
    result = client.get('/iphone/api/qualification').json()['P3.5']
    assert result['trials'] == 1
    assert result['passed'] is False
    assert any('need 50 trials' in item for item in result['failures'])


def test_limited_trusted_device_cannot_read_sensitive_memory_or_private_knowledge(tmp_path):
    owner_client, runtime, _ = make_client(tmp_path)
    sensitive = owner_client.post('/iphone/api/memory', json={
        'type': 'fact',
        'subject': 'Private fact',
        'content': 'Owner-only memory',
        'sensitivity': 'sensitive',
    })
    assert sensitive.status_code == 200
    private = owner_client.post('/iphone/api/knowledge', json={
        'filename': 'private.txt',
        'text': 'Owner-only document',
        'access_class': 'private',
    })
    assert private.status_code == 200

    limited, token = runtime['device_registry'].enroll('Limited browser', 'web')
    limited_client = TestClient(owner_client.app, base_url='https://testserver')
    limited_client.cookies.set('pa_device', limited['id'])
    limited_client.cookies.set('pa_token', token)

    assert limited_client.get('/iphone/api/memory').json()['memories'] == []
    assert limited_client.get('/iphone/api/knowledge').json()['documents'] == []
    assert limited_client.get(f"/iphone/api/memory/{sensitive.json()['id']}").status_code == 404
    assert limited_client.get(f"/iphone/api/knowledge/{private.json()['id']}").status_code == 404
    assert limited_client.post('/iphone/api/memory', json={
        'type': 'fact', 'subject': 'Blocked', 'content': 'Sensitive', 'sensitivity': 'sensitive',
    }).status_code == 403
    assert limited_client.get('/iphone/api/qualification').status_code == 403


def test_legacy_owner_pwa_permissions_migrate_without_new_login(tmp_path):
    path = tmp_path / 'devices.sqlite3'
    registry = DeviceRegistry(path)
    device, token = registry.enroll('Legacy owner iPhone', 'ios-pwa')
    with registry._con() as con:
        con.execute('DELETE FROM device_permissions WHERE device_id=?', (device['id'],))
    restarted = DeviceRegistry(path)
    assert restarted.authenticate(device['id'], token) is True
    assert restarted.authorize(device['id'], 'device:admin') is True


def test_retention_removes_memory_and_vector(tmp_path):
    class Vector:
        def __init__(self): self.deleted = []
        def delete(self, memory_id): self.deleted.append(memory_id)

    store = MemoryStore(tmp_path / 'retention.sqlite3')
    vector = Vector()
    brain = SecondBrain(store, vector_store=vector)
    memory_id = store.remember(type='note', subject='old', content='old', source='test')
    with store.con() as con:
        con.execute("UPDATE memories SET created_at='2000-01-01T00:00:00+00:00' WHERE id=?", (memory_id,))
    result = brain.apply_retention(older_than_days=1, dry_run=False)
    assert result['matched'] == 1
    assert store.get(memory_id) is None
    assert vector.deleted == [memory_id]
