from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.events import EventBus
from agent.executor import ConfirmationRequired
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
        self.environment = None
    def start_session(self, **kwargs):
        if self.started:
            raise RuntimeError('voice qualification session already active')
        self.started = True
        self.kwargs = kwargs
        self.environment = kwargs.get('environment')
        return 'session-1'
    def active_session(self):
        if not self.started:
            return None
        return {
            'id': 'session-1',
            'evidence_class': 'real_device',
            'environment': self.environment or {},
        }
    def stop_session(self):
        if not self.started:
            raise RuntimeError('no active voice qualification session')
        self.started = False
        return {'turns': 1, 'barge_trials': 0, 'barge_success_rate': 0.0, 'passed': False}
    def close_active_sessions(self, *, reason):
        closed = ['session-1'] if self.started else []
        self.started = False
        self.closed_reason = reason
        return closed
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


def test_voice_tool_request_returns_owner_approval_instead_of_http_500(tmp_path):
    client, runtime = make_client(tmp_path)

    class ApprovalExecutor:
        def chat(self, text, cancel_event=None, device_id=None):
            raise ConfirmationRequired(
                'web_search_browser',
                {'query': text},
                'Search the web for the requested information',
                approval_id='approval-1',
                execution_id='execution-1',
                expires_at=12345.0,
            )

        def approve(self, approval_id):
            assert approval_id == 'approval-1'
            return 'The approved search completed.'

        def reject(self, approval_id):
            assert approval_id == 'approval-1'
            return 'Action cancelled.'

    runtime['executor'] = ApprovalExecutor()
    app = FastAPI()
    app.include_router(iphone_pwa_router(runtime, SimpleNamespace(
        base_dir=Path(__file__).resolve().parent.parent,
        iphone_owner_enrollment_code='this-is-a-long-owner-code',
        iphone_pwa_allow_insecure=False,
    )))
    client = TestClient(app, base_url='https://testserver')
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})

    response = client.post('/iphone/api/voice/turn', json={'transcript': 'search the web'})

    assert response.status_code == 202
    assert response.json()['status'] == 'approval_required'
    assert response.json()['approval']['tool'] == 'web_search_browser'
    assert 'query' not in response.json()['approval']
    approved = client.post('/iphone/api/approval/approval-1/approve', json={})
    assert approved.status_code == 200
    assert approved.json()['reply'] == 'The approved search completed.'


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


def test_repeated_start_resumes_active_session_after_page_refresh(tmp_path):
    client, _ = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    first = client.post('/iphone/api/qualification/start', json={'environment': {'noise': 'quiet'}})
    assert first.status_code == 200
    assert first.json()['status'] == 'started'

    resumed = client.post('/iphone/api/qualification/start', json={'environment': {'noise': 'quiet'}})
    assert resumed.status_code == 200
    assert resumed.json() == {
        'session_id': 'session-1',
        'evidence_class': 'real_device',
        'status': 'already_active',
        'message': 'Existing session resumed',
    }


def test_status_restores_the_active_session_for_hands_free_ui(tmp_path):
    client, _ = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    client.post('/iphone/api/qualification/start', json={'environment': {}})

    status = client.get('/iphone/api/status')

    assert status.status_code == 200
    assert status.json()['active_qualification']['session_id'] == 'session-1'


def test_trusted_owner_can_explicitly_replace_other_device_stale_session(tmp_path):
    client, runtime = make_client(tmp_path)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    recorder = runtime['voice_qualification']
    recorder.started = True
    recorder.environment = {'device_id': 'old-browser'}

    blocked = client.post('/iphone/api/qualification/start', json={'environment': {}})
    assert blocked.status_code == 409
    takeover = client.post('/iphone/api/qualification/takeover', json={
        'confirm': True,
        'environment': {'noise': 'quiet'},
    })

    assert takeover.status_code == 200
    assert takeover.json()['closed_session_ids'] == ['session-1']
    assert recorder.environment['device_id'] == 'iphone-1'
    assert 'Owner-confirmed takeover' in recorder.closed_reason


def test_home_uses_one_touch_voice_instead_of_four_test_buttons(tmp_path):
    client, _ = make_client(tmp_path)
    page = client.get('/iphone/')

    assert page.status_code == 200
    assert 'id="micButton"' in page.text
    assert 'Tap once to talk continuously' in page.text
    assert '>Start Session<' not in page.text
    assert '>Start Listening<' not in page.text
    assert '>Interrupt<' not in page.text
    assert 'Continue here' in page.text


def test_client_tts_failure_is_recorded_as_voice_error(tmp_path):
    client, runtime = make_client(tmp_path)
    errors = []
    runtime['events'].subscribe('voice.error', errors.append)
    client.post('/iphone/api/enroll', json={'code': 'this-is-a-long-owner-code'})
    client.post('/iphone/api/qualification/start', json={'environment': {}})

    response = client.post('/iphone/api/voice/client-event', json={
        'event': 'tts_error',
        'detail': 'start_timeout',
    })

    assert response.status_code == 200
    assert errors[0]['error'] == 'tts_error'
    assert errors[0]['detail'] == 'start_timeout'


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
