from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.events import EventBus
from server.iphone_pwa import iphone_pwa_router
from models.router import ModelTimeout, ModelUnavailable


class Registry:
    def __init__(self):
        self.tokens = {}
        self.active = set()
    def enroll(self, name, platform):
        device_id = 'iphone-1'
        token = 'token-1'
        self.tokens[device_id] = token
        self.active.add(device_id)
        return {'id': device_id, 'name': name, 'platform': platform}, token
    def authenticate(self, device_id, token):
        return self.tokens.get(device_id) == token
    def is_active(self, device_id):
        return device_id in self.active


class Executor:
    def chat(self, text, cancel_event=None, device_id=None):
        return f'reply:{text}:{device_id}'


class Continuity:
    def resume(self, device_id):
        return {'device_id': device_id}


class Recorder:
    def __init__(self):
        self.started = False
    def start_session(self, **kwargs):
        self.started = True
        self.kwargs = kwargs
        return 'session-1'
    def stop_session(self):
        if not self.started:
            raise RuntimeError('no active voice qualification session')
        self.started = False
        return {'turns': 1, 'barge_trials': 0, 'barge_success_rate': 0.0, 'passed': False}
    def sessions(self):
        return [{'id': 'session-1'}]


def make_client(tmp_path: Path, allow_insecure=False):
    settings = SimpleNamespace(
        base_dir=Path(__file__).resolve().parent.parent,
        iphone_owner_enrollment_code='this-is-a-long-owner-code',
        iphone_pwa_allow_insecure=allow_insecure,
    )
    events = EventBus()
    runtime = {
        'device_registry': Registry(),
        'executor': Executor(),
        'events': events,
        'continuity': Continuity(),
        'voice_qualification': Recorder(),
    }
    app = FastAPI()
    app.include_router(iphone_pwa_router(runtime, settings))
    return TestClient(app, base_url='https://testserver'), runtime


def test_owner_enrollment_requires_correct_code_and_sets_secure_cookies(tmp_path):
    client, _ = make_client(tmp_path)
    bad = client.post('/iphone/api/enroll', json={'code': 'wrong'})
    assert bad.status_code == 401
    response = client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    assert response.status_code == 200
    assert response.json()['device_id'] == 'iphone-1'
    cookies = response.headers.get_list('set-cookie')
    assert any('pa_device=' in c and 'HttpOnly' in c and 'Secure' in c and 'SameSite=strict' in c for c in cookies)
    assert any('pa_token=' in c and 'HttpOnly' in c and 'Secure' in c and 'SameSite=strict' in c for c in cookies)


def test_voice_turn_uses_enrolled_device_and_existing_executor(tmp_path):
    client, _ = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    response = client.post('/iphone/api/voice/turn', json={'transcript': 'hello'})
    assert response.status_code == 200
    assert response.json()['reply'] == 'reply:hello:iphone-1'


def test_p3_session_records_ios_pwa_environment_but_does_not_self_award(tmp_path):
    client, runtime = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    start = client.post('/iphone/api/qualification/start', json={'environment': {'noise': 'quiet'}})
    assert start.status_code == 200
    recorder = runtime['voice_qualification']
    assert recorder.kwargs['evidence_class'] == 'real_device'
    assert recorder.kwargs['environment']['platform'] == 'ios-pwa'
    stop = client.post('/iphone/api/qualification/stop', json={})
    assert stop.status_code == 200
    assert stop.json()['passed'] is False


def test_second_stop_is_idempotent_and_user_safe(tmp_path):
    client, _ = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    client.post('/iphone/api/qualification/start', json={'environment': {}})
    assert client.post('/iphone/api/qualification/stop', json={}).status_code == 200
    second = client.post('/iphone/api/qualification/stop', json={})
    assert second.status_code == 200
    assert second.json() == {
        'ok': True,
        'status': 'already_stopped',
        'message': 'Session already stopped',
    }


def test_model_unavailable_is_a_safe_explicit_state(tmp_path):
    client, runtime = make_client(tmp_path)

    class UnavailableExecutor:
        def chat(self, *args, **kwargs):
            raise ModelUnavailable('connection refused', provider='self_hosted')

    runtime['executor'] = UnavailableExecutor()
    app = FastAPI()
    app.include_router(iphone_pwa_router(runtime, SimpleNamespace(
        base_dir=Path(__file__).resolve().parent.parent,
        iphone_owner_enrollment_code='this-is-a-long-owner-code',
        iphone_pwa_allow_insecure=False,
    )))
    client = TestClient(app, base_url='https://testserver')
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    response = client.post('/iphone/api/voice/turn', json={'transcript': 'hello'})
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'model_unavailable'
    assert '127.0.0.1' not in response.text


def test_model_timeout_is_not_reported_as_http_500(tmp_path):
    client, runtime = make_client(tmp_path)

    class TimeoutExecutor:
        def chat(self, *args, **kwargs):
            raise ModelTimeout('timed out', provider='self_hosted')

    runtime['executor'] = TimeoutExecutor()
    app = FastAPI()
    app.include_router(iphone_pwa_router(runtime, SimpleNamespace(
        base_dir=Path(__file__).resolve().parent.parent,
        iphone_owner_enrollment_code='this-is-a-long-owner-code',
        iphone_pwa_allow_insecure=False,
    )))
    client = TestClient(app, base_url='https://testserver')
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    response = client.post('/iphone/api/voice/turn', json={'transcript': 'hello'})
    assert response.status_code == 504
    assert response.json()['detail']['code'] == 'model_timeout'


def test_plain_http_enrollment_fails_closed(tmp_path):
    settings = SimpleNamespace(
        base_dir=Path(__file__).resolve().parent.parent,
        iphone_owner_enrollment_code='this-is-a-long-owner-code',
        iphone_pwa_allow_insecure=False,
    )
    runtime = {'device_registry': Registry(), 'executor': Executor(), 'events': EventBus(), 'continuity': Continuity(), 'voice_qualification': Recorder()}
    app = FastAPI(); app.include_router(iphone_pwa_router(runtime, settings))
    client = TestClient(app, base_url='http://testserver')
    response = client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    assert response.status_code == 400
