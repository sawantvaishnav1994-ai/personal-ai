from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.logical_request_middleware import LogicalRequestMiddleware
from server.session_bound_executor import SessionBoundExecutor
import server.session_bound_executor as session_module


RID = '550e8400-e29b-41d4-a716-446655440000'


class Lower:
    def __init__(self): self.calls=[]
    def chat(self, text, **kwargs): self.calls.append((text, kwargs)); return 'durable answer'


def test_session_bound_executor_propagates_request_id_but_not_client_authority(monkeypatch):
    lower=Lower(); bridge=SessionBoundExecutor(lower, surface='iphone-pwa')
    trusted=SimpleNamespace(device_id='trusted-device',session_id='trusted-session',reauthenticated_at=123.0)
    monkeypatch.setattr(session_module, 'current_trusted_request', lambda: trusted)
    monkeypatch.setattr(session_module, 'current_logical_request_id', lambda: RID)
    assert bridge.chat('hello', device_id='trusted-device') == 'durable answer'
    _,kwargs=lower.calls[0]
    assert kwargs['request_id']==RID
    assert kwargs['owner_id']=='owner'
    assert kwargs['device_id']=='trusted-device'
    assert kwargs['session_id']=='trusted-session'
    assert kwargs['reauthenticated_at']==123.0


def test_session_bound_executor_rejects_request_identity_mismatch(monkeypatch):
    lower=Lower(); bridge=SessionBoundExecutor(lower)
    trusted=SimpleNamespace(device_id='d1',session_id='s1',reauthenticated_at=None)
    monkeypatch.setattr(session_module, 'current_trusted_request', lambda: trusted)
    monkeypatch.setattr(session_module, 'current_logical_request_id', lambda: RID)
    try: bridge.chat('hello', request_id='123e4567-e89b-42d3-a456-426614174000')
    except PermissionError: pass
    else: raise AssertionError('wire identity mismatch must fail closed')
    assert lower.calls==[]


def test_pwa_middleware_requires_client_uuid_on_turn_and_injects_adapter():
    app=FastAPI()
    app.add_middleware(LogicalRequestMiddleware)
    @app.post('/iphone/api/voice/turn')
    def turn(): return {'ok':True}
    @app.get('/iphone/')
    def home(): return __import__('fastapi').responses.HTMLResponse('<html><body>home</body></html>')
    client=TestClient(app)
    assert client.post('/iphone/api/voice/turn',json={'transcript':'hello'}).status_code==422
    assert client.post('/iphone/api/voice/turn',json={'request_id':'unsafe','transcript':'hello'}).status_code==422
    assert client.post('/iphone/api/voice/turn',json={'request_id':RID,'transcript':'hello'}).status_code==200
    page=client.get('/iphone/')
    assert page.status_code==200
    assert '<script src="/iphone/v1-runtime.js"></script>' in page.text
    adapter=client.get('/iphone/v1-runtime.js')
    assert adapter.status_code==200
    # The transport contract is semantic, not tied to one browser UUID API.
    # Native randomUUID is preferred, while the fallback must require the Web
    # Crypto CSPRNG and construct RFC-4122 UUID-v4 variant/version bits.
    assert "typeof c.randomUUID==='function'" in adapter.text
    assert "typeof c.getRandomValues!=='function'" in adapter.text
    assert 'c.getRandomValues(b)' in adapter.text
    assert 'b[6]=(b[6]&15)|64' in adapter.text
    assert 'b[8]=(b[8]&63)|128' in adapter.text
    assert 'Secure request identity is unavailable' in adapter.text
    assert 'Math.random' not in adapter.text
    assert 'Date.now()' not in adapter.text.split('const uuid=()=>{',1)[1].split('};',1)[0]
    assert 'request_id:pending.request_id' in adapter.text


def test_client_adapter_keeps_pending_request_until_terminal_result():
    text=(Path(__file__).resolve().parent.parent/'pwa'/'v1-runtime.js').read_text()
    assert "sessionStorage.setItem(PENDING_KEY" in text
    assert "samePending" in text
    assert "for(let attempt=0;attempt<2;attempt++)" in text
    assert "clearPending(pending.request_id)" in text
    assert "if(!samePending)appendMessage('user_message',clean)" in text
