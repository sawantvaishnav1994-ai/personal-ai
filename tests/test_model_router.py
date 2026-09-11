from types import SimpleNamespace

import pytest
import requests

from models.router import (
    InvalidModelResponse,
    ModelAuthenticationError,
    ModelRouter,
    ModelTimeout,
    ModelUnavailable,
)


def settings(**overrides):
    values = {
        'ai_provider': 'local',
        'cloud_runtime_enabled': True,
        'local_ai_explicit': False,
        'local_ai_url': 'http://127.0.0.1:11434/v1',
        'local_ai_model': 'llama3.2',
        'self_hosted_ai_url': '',
        'self_hosted_ai_api_key': '',
        'self_hosted_ai_model': 'owner-model',
        'model_fallback_providers': (),
        'model_request_timeout_seconds': 2,
        'model_health_timeout_seconds': 1,
        'allow_external_for_sensitive': False,
        'openrouter_api_key': '',
        'openrouter_model': 'remote-model',
        'openai_api_key': '',
        'openai_base_url': 'https://api.openai.com/v1',
        'openai_model': 'cloud-model',
        'embedding_model': 'embed-model',
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class Response:
    def __init__(self, status_code=200, payload=None, content=b''):
        self.status_code = status_code
        self.payload = payload or {}
        self.content = content

    def json(self):
        return self.payload


def test_cloud_runtime_does_not_silently_call_loopback(monkeypatch):
    called = False

    def request(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(requests, 'request', request)
    router = ModelRouter(settings())
    assert router.status()['state'] == 'not_configured'
    with pytest.raises(ModelUnavailable):
        router.chat('hello')
    assert called is False


def test_public_status_does_not_expose_endpoint_credentials():
    router = ModelRouter(settings(
        self_hosted_ai_url='https://owner:password@gpu.example/v1?token=secret',
        self_hosted_ai_api_key='api-secret',
    ))
    serialized = repr(router.status())
    assert 'gpu.example' in serialized
    assert 'password' not in serialized
    assert 'token=secret' not in serialized
    assert 'api-secret' not in serialized


def test_self_hosted_openai_compatible_endpoint_is_used(monkeypatch):
    seen = {}

    def request(method, url, **kwargs):
        seen.update(method=method, url=url, headers=kwargs['headers'], payload=kwargs['json'])
        return Response(payload={'choices': [{'message': {'content': 'owner-controlled reply'}}]})

    monkeypatch.setattr(requests, 'request', request)
    router = ModelRouter(settings(self_hosted_ai_url='https://gpu.example/v1'))
    assert router.chat('hello') == 'owner-controlled reply'
    assert seen['url'] == 'https://gpu.example/v1/chat/completions'
    assert 'Authorization' not in seen['headers']


def test_allowed_fallback_is_recorded(monkeypatch):
    events = []
    audit = []

    class Events:
        def emit(self, name, **payload):
            events.append((name, payload))

    def request(method, url, **kwargs):
        if url.startswith('https://gpu.example'):
            raise requests.ConnectionError('offline')
        return Response(payload={'choices': [{'message': {'content': 'fallback reply'}}]})

    monkeypatch.setattr(requests, 'request', request)
    router = ModelRouter(
        settings(
            self_hosted_ai_url='https://gpu.example/v1',
            openrouter_api_key='secret',
            model_fallback_providers=('openrouter',),
        ),
        events=Events(),
        audit=lambda *args: audit.append(args),
    )
    assert router.chat('hello') == 'fallback reply'
    assert any(name == 'model.fallback' and payload['provider'] == 'openrouter' for name, payload in events)
    assert any(item[1] == 'fallback' for item in audit)
    assert all('secret' not in repr(item) for item in audit)


@pytest.mark.parametrize(
    ('effect', 'expected'),
    [
        (requests.Timeout('slow'), ModelTimeout),
        (requests.ConnectionError('offline'), ModelUnavailable),
    ],
)
def test_transport_failures_have_typed_errors(monkeypatch, effect, expected):
    def request(*args, **kwargs):
        raise effect

    monkeypatch.setattr(requests, 'request', request)
    router = ModelRouter(settings(self_hosted_ai_url='https://gpu.example/v1'))
    with pytest.raises(expected):
        router.chat('hello')


def test_authentication_and_invalid_payload_are_distinct(monkeypatch):
    monkeypatch.setattr(requests, 'request', lambda *args, **kwargs: Response(status_code=401))
    router = ModelRouter(settings(self_hosted_ai_url='https://gpu.example/v1'))
    with pytest.raises(ModelAuthenticationError):
        router.chat('hello')

    monkeypatch.setattr(requests, 'request', lambda *args, **kwargs: Response(payload={'choices': []}))
    with pytest.raises(InvalidModelResponse):
        router.chat('hello')


def test_sensitive_content_cannot_fall_back_to_external_provider(monkeypatch):
    called = []

    def request(method, url, **kwargs):
        called.append(url)
        raise requests.ConnectionError('private model offline')

    monkeypatch.setattr(requests, 'request', request)
    router = ModelRouter(settings(
        self_hosted_ai_url='https://gpu.example/v1',
        openrouter_api_key='secret',
        model_fallback_providers=('openrouter',),
    ))
    with pytest.raises(ModelUnavailable):
        router.chat('private fact', sensitivity='sensitive')
    assert called == ['https://gpu.example/v1/chat/completions']
