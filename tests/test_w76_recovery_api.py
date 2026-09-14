from fastapi import FastAPI
from fastapi.testclient import TestClient

from desktop.operator_recovery import OperatorRecoveryStore
from desktop.operator_transactions import OperatorBinding,OperatorTransactionStore
from server.recovery_api import create_recovery_router


def setup(tmp_path):
    txs=OperatorTransactionStore(tmp_path/'tx.sqlite3');binding=OperatorBinding('owner','device','session',0)
    txs.propose('tx',binding,goal='recover this',action_plan={'steps':[{'sequence':0,'kind':'copy'}]})
    store=OperatorRecoveryStore(tmp_path/'r.sqlite3',txs);store.ensure_transaction('tx',binding)
    def auth(token,device):
        if token!='Bearer good' or device!='device':raise PermissionError('bad')
        return {'owner_id':'owner'}
    app=FastAPI();app.include_router(create_recovery_router(store,auth,current_security_epoch=lambda:0))
    return TestClient(app),store,binding


def headers():return {'Authorization':'Bearer good','X-Device-ID':'device','X-Session-ID':'session','X-Security-Epoch':'0'}


def test_owner_recovery_report_is_visible_with_binding(tmp_path):
    client,store,binding=setup(tmp_path);response=client.get('/activities/recovery/tx',headers=headers())
    assert response.status_code==200 and response.json()['transaction_id']=='tx' and response.json()['goal']=='recover this'


def test_recovery_report_rejects_unauthenticated(tmp_path):
    client,_,_=setup(tmp_path);response=client.get('/activities/recovery/tx')
    assert response.status_code==401 and response.json()['detail']=='authentication_required'


def test_recovery_report_rejects_missing_session_binding(tmp_path):
    client,_,_=setup(tmp_path);h=headers();h.pop('X-Session-ID');response=client.get('/activities/recovery/tx',headers=h)
    assert response.status_code==401


def test_recovery_report_rejects_security_epoch_change(tmp_path):
    client,_,_=setup(tmp_path);h=headers();h['X-Security-Epoch']='1';response=client.get('/activities/recovery/tx',headers=h)
    assert response.status_code==409 and response.json()['detail']=='security_epoch_changed'


def test_consequential_owner_decision_requires_reauth(tmp_path):
    client,_,_=setup(tmp_path);response=client.post('/activities/recovery/tx/decision',headers=headers(),json={'decision':'resume_safe_checkpoint','decision_id':'d','security_epoch':0,'reauthenticated':False})
    assert response.status_code==409 and response.json()['detail']=='reauthentication_required'


def test_owner_can_abandon(tmp_path):
    client,store,_=setup(tmp_path);response=client.post('/activities/recovery/tx/decision',headers=headers(),json={'decision':'abandon_transaction','decision_id':'d','security_epoch':0,'reauthenticated':False})
    assert response.status_code==200 and store.snapshot('tx')['state']=='abandoned_by_owner'


def test_verify_again_returns_safe_pending_state_not_dispatch(tmp_path):
    client,store,binding=setup(tmp_path);lease=store.acquire_lease('tx','w');dispatch,_=store.begin_dispatch(lease,action_id='tx:0',idempotency_key='i',operation_class='copy')
    response=client.post('/activities/recovery/tx/verify-again',headers=headers(),json={'dispatch_id':dispatch['dispatch_id']})
    assert response.status_code==200 and response.json()['state']=='verification_pending'
    assert store.dispatch(dispatch['dispatch_id'])['state']=='dispatching'


def test_export_recovery_report_is_redacted_json(tmp_path):
    client,_,_=setup(tmp_path);response=client.get('/activities/recovery/tx/export',headers=headers())
    assert response.status_code==200 and response.json()['media_type']=='application/json'
    assert 'password' not in response.json()['content'].lower()
