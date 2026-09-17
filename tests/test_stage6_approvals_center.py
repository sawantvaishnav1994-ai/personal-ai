from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from approvals.projection import ApprovalsProjection
from security.approvals import ApprovalManager
from security.request_context import TrustedRequestContext, set_trusted_request, reset_trusted_request
from server.approvals_center_api import approvals_center_router


class Devices:
    def __init__(self, active=True, allowed=True): self.active=active; self.allowed=allowed
    def is_active(self, device_id): return self.active and device_id == 'd'
    def authorize(self, device_id, scope): return self.allowed and device_id == 'd' and scope == 'ai:chat'

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token=set_trusted_request(TrustedRequestContext('d','s'))
        try:return await call_next(request)
        finally:reset_trusted_request(token)


def manager(tmp_path): return ApprovalManager(path=tmp_path/'trusted-actions.sqlite3')

def test_projection_uses_canonical_id_and_redacts_outcome(tmp_path):
    m=manager(tmp_path); t=m.create('e1','mail_send',{},device_id='d',session_id='s',destination='a@example.com')
    m.approve(t.id,'e1','mail_send',{},device_id='d',session_id='s');m.begin_dispatch(t.id);m.complete_dispatch(t.id,{'access_token':'no','nested':{'password':'no'},'reply':'ok'})
    x=ApprovalsProjection(m).detail(t.id,device_id='d',session_id='s')
    assert x['approval_id']==t.id and x['status']=='completed' and x['outcome']['access_token']=='[redacted]' and x['outcome']['nested']['password']=='[redacted]'

def test_projection_scope_hides_other_device_or_session(tmp_path):
    m=manager(tmp_path);t=m.create('e','tool',{},device_id='other',session_id='other')
    p=ApprovalsProjection(m);assert p.detail(t.id,device_id='d',session_id='s') is None

def test_pending_is_bounded_and_contains_no_parameter_hash(tmp_path):
    m=manager(tmp_path)
    for i in range(120):m.create(str(i),'tool',{'password':'secret'},device_id='d',session_id='s')
    rows=ApprovalsProjection(m).pending(device_id='d',session_id='s',limit=1000)
    assert len(rows)==100 and 'parameter_hash' not in str(rows) and 'secret' not in str(rows)

def make_client(tmp_path, devices, context=True):
    m=manager(tmp_path);agent=SimpleNamespace(approvals=m)
    app=FastAPI()
    if context:app.add_middleware(ContextMiddleware)
    app.include_router(approvals_center_router({'device_registry':devices,'agent_executor':agent}))
    return TestClient(app),m

def test_api_requires_trusted_active_authorized_owner(tmp_path):
    c,_=make_client(tmp_path/'a',Devices(),False);assert c.get('/iphone/api/approvals-center').status_code==401
    c,_=make_client(tmp_path/'b',Devices(active=False));assert c.get('/iphone/api/approvals-center').status_code==401
    c,_=make_client(tmp_path/'c',Devices(allowed=False));assert c.get('/iphone/api/approvals-center').status_code==403

def test_api_pending_and_detail_are_same_canonical_approval(tmp_path):
    c,m=make_client(tmp_path,Devices());t=m.create('e','tool',{},device_id='d',session_id='s',destination='dest')
    rows=c.get('/iphone/api/approvals-center').json()['approvals'];assert rows[0]['approval_id']==t.id
    detail=c.get('/iphone/api/approvals-center/'+t.id);assert detail.status_code==200 and detail.json()['approval_id']==t.id

def test_api_missing_and_cross_session_are_safe_not_found(tmp_path):
    c,m=make_client(tmp_path,Devices());assert c.get('/iphone/api/approvals-center/missing').status_code==404
    t=m.create('e','tool',{},device_id='d',session_id='other');assert c.get('/iphone/api/approvals-center/'+t.id).status_code==404

def test_read_api_exposes_no_decision_or_dispatch_route(tmp_path):
    # Test the router object itself. TestClient middleware may replace app.routes
    # with a wrapper in this dependency version, which is not an API contract.
    m=manager(tmp_path);agent=SimpleNamespace(approvals=m)
    router=approvals_center_router({'device_registry':Devices(),'agent_executor':agent})
    paths={route.path for route in router.routes}
    methods={route.path:set(route.methods or ()) for route in router.routes}
    assert paths=={'/iphone/api/approvals-center','/iphone/api/approvals-center/{approval_id}'}
    assert methods['/iphone/api/approvals-center']=={'GET'}
    assert methods['/iphone/api/approvals-center/{approval_id}']=={'GET'}
