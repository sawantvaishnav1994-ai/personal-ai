from fastapi import FastAPI
from fastapi.testclient import TestClient

from knowledge.store import KnowledgeStore
from memory.second_brain import MemoryCandidate, SecondBrain
from memory.store import MemoryStore
from server.memory_knowledge_inspection import memory_knowledge_inspection_router


class FakeRegistry:
    def authenticate(self, device_id, token):
        return device_id == 'dev-1' and token == 'token-1'

    def authorize(self, device_id, scope):
        if device_id != 'dev-1':
            return False
        return scope in {'memory:read', 'knowledge:read', 'knowledge:write'}


def client(tmp_path):
    memory = MemoryStore(tmp_path / 'memory.sqlite3')
    second_brain = SecondBrain(memory)
    knowledge = KnowledgeStore(tmp_path / 'knowledge.sqlite3', tmp_path / 'objects')
    runtime = {
        'device_registry': FakeRegistry(),
        'memory': memory,
        'second_brain': second_brain,
        'knowledge': knowledge,
    }
    app = FastAPI()
    app.include_router(memory_knowledge_inspection_router(runtime))
    browser = TestClient(app)
    browser.cookies.set('pa_device', 'dev-1')
    browser.cookies.set('pa_token', 'token-1')
    return browser, second_brain, knowledge


def test_memory_explanation_api_filters_sensitive_before_selection(tmp_path):
    browser, second_brain, _ = client(tmp_path)
    normal_id = second_brain.remember(
        MemoryCandidate(type='fact', subject='Atlas', content='Atlas is the current project codename.', confidence=.9)
    )
    secret_id = second_brain.remember(
        MemoryCandidate(type='fact', subject='Atlas secret', content='Atlas secret budget is confidential.', confidence=.9, sensitivity='secret')
    )

    response = browser.get('/iphone/api/memory/retrieval', params={'q': 'Atlas'})
    assert response.status_code == 200
    rows = response.json()['memories']
    assert {row['id'] for row in rows} == {normal_id}
    assert rows[0]['retrieval_explanation']['retrieved'] is True

    hidden = browser.get(
        f'/iphone/api/memory/{secret_id}/retrieval-explanation',
        params={'q': 'Atlas'},
    )
    assert hidden.status_code == 404


def test_knowledge_version_history_api_is_owner_inspectable(tmp_path):
    browser, _, knowledge = client(tmp_path)
    first = knowledge.ingest(filename='manual.txt', data=b'first manual', source='owner-upload')
    second = knowledge.ingest(filename='manual.txt', data=b'second manual', source='owner-upload')

    response = browser.get(f"/iphone/api/knowledge/{second['id']}/versions")
    assert response.status_code == 200
    payload = response.json()
    assert payload['lineage_id'] == first['lineage_id'] == second['lineage_id']
    assert [item['version'] for item in payload['versions']] == [2, 1]


def test_inspection_api_requires_trusted_browser(tmp_path):
    browser, _, _ = client(tmp_path)
    browser.cookies.clear()
    response = browser.get('/iphone/api/memory/retrieval', params={'q': 'Atlas'})
    assert response.status_code == 401
