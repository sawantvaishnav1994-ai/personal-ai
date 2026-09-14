import sqlite3
import time
import pytest

from desktop.operator_transactions import OperatorBinding,OperatorTransactionStore
from desktop.operator_recovery import OperatorRecoveryStore,RECOVERY_STATES
from desktop.verification import build_record


def setup(tmp_path,*,stop=None):
    txs=OperatorTransactionStore(tmp_path/'operator-transactions.sqlite3')
    binding=OperatorBinding('owner','device','session',3)
    txs.propose('tx',binding,goal='W7.6 test',action_plan={'steps':[{'sequence':0,'kind':'copy'}]})
    store=OperatorRecoveryStore(tmp_path/'operator-recovery.sqlite3',txs,emergency_stop=stop)
    store.ensure_transaction('tx',binding)
    return txs,store,binding


def dispatched(store,binding):
    lease=store.acquire_lease('tx','worker')
    d,created=store.begin_dispatch(lease,action_id='tx:0',idempotency_key='idem',operation_class='copy',target='file')
    assert created
    store.mark_dispatched(lease,d['dispatch_id'])
    return lease,d


def verify(store,lease,d,result='verified_success'):
    rec=build_record(transaction_id='tx',action_id='tx:0',dispatch_id=d['dispatch_id'],idempotency_key='idem',operation_class='copy',target='file',precondition={'exists':True},expected_postcondition='destination checksum matches',observed_postcondition={'exists':True,'sha256':'abc'},result=result,explanation='verified',now=time.time())
    return store.record_verification(lease,rec)


def test_recovery_states_exact_contract():
    assert RECOVERY_STATES=={'active','waiting_for_approval','dispatching','dispatched','verifying','verified_success','verified_no_effect','partially_completed','compensation_available','compensation_requires_approval','recovery_review_required','cancelled','failed','completed','abandoned_by_owner'}


def test_recovery_schema_fresh_create_and_repeat_init(tmp_path):
    txs,store,binding=setup(tmp_path)
    assert store.schema_version()==1
    again=OperatorRecoveryStore(store.path,txs)
    assert again.schema_version()==1 and again.snapshot('tx')['state']=='active'


def test_existing_w71_data_survives_recovery_store_creation(tmp_path):
    txs,store,binding=setup(tmp_path)
    assert txs.transaction('tx')['goal']=='W7.6 test'
    assert txs.actions('tx')==[]


def test_lease_excludes_second_worker(tmp_path):
    _,store,_=setup(tmp_path)
    a=store.acquire_lease('tx','a',ttl_seconds=30)
    with pytest.raises(RuntimeError,match='recovery_lease_held'):store.acquire_lease('tx','b')
    assert store.release_lease(a)


def test_expired_lease_can_be_fenced_by_new_worker(tmp_path,monkeypatch):
    _,store,_=setup(tmp_path)
    a=store.acquire_lease('tx','a',ttl_seconds=1)
    with store._con() as con:con.execute('UPDATE recovery_transactions SET lease_expires_at=? WHERE transaction_id=?',(time.time()-1,'tx'))
    b=store.acquire_lease('tx','b')
    assert b.fencing_token>a.fencing_token
    with pytest.raises(PermissionError,match='fencing_token_mismatch'):store.assert_fence(a)


def test_stale_fencing_token_cannot_dispatch(tmp_path):
    _,store,_=setup(tmp_path)
    a=store.acquire_lease('tx','a');store.release_lease(a);b=store.acquire_lease('tx','b')
    with pytest.raises(PermissionError):store.begin_dispatch(a,action_id='tx:0',idempotency_key='x',operation_class='copy')
    assert store.assert_fence(b)


def test_duplicate_idempotency_key_same_action_is_not_redispatched(tmp_path):
    _,store,_=setup(tmp_path)
    lease=store.acquire_lease('tx','w')
    first,created=store.begin_dispatch(lease,action_id='tx:0',idempotency_key='same',operation_class='copy')
    second,created2=store.begin_dispatch(lease,action_id='tx:0',idempotency_key='same',operation_class='copy')
    assert created and not created2 and second['dispatch_id']==first['dispatch_id']


def test_duplicate_idempotency_key_cannot_rebind(tmp_path):
    _,store,_=setup(tmp_path);lease=store.acquire_lease('tx','w')
    store.begin_dispatch(lease,action_id='tx:0',idempotency_key='same',operation_class='copy')
    with pytest.raises(PermissionError,match='idempotency_key_rebound'):
        store.begin_dispatch(lease,action_id='tx:1',idempotency_key='same',operation_class='upload')


def test_verified_success_is_durable(tmp_path):
    _,store,binding=setup(tmp_path);lease,d=dispatched(store,binding);store.mark_verifying(lease,d['dispatch_id'])
    out=verify(store,lease,d)
    assert out['result']=='verified_success' and store.snapshot('tx')['state']=='verified_success'
    restarted=OperatorRecoveryStore(store.path,store.transactions)
    assert restarted.snapshot('tx')['state']=='verified_success'


def test_unknown_outcome_requires_review(tmp_path):
    _,store,binding=setup(tmp_path);lease,d=dispatched(store,binding);store.mark_verifying(lease,d['dispatch_id'])
    verify(store,lease,d,'unknown_outcome')
    assert store.snapshot('tx')['state']=='recovery_review_required'
    assert store.retry_decision(d['dispatch_id'],idempotent=True)['allowed'] is False


def test_verified_no_effect_allows_retry_only_when_idempotent(tmp_path):
    _,store,binding=setup(tmp_path);lease,d=dispatched(store,binding);store.mark_verifying(lease,d['dispatch_id']);verify(store,lease,d,'verified_no_effect')
    assert not store.retry_decision(d['dispatch_id'],idempotent=False)['allowed']
    assert store.retry_decision(d['dispatch_id'],idempotent=True)=={'allowed':True,'reason':'verified_no_effect'}

@pytest.mark.parametrize('operation', ['purchase','financial_transfer','email_send','message_send','public_publish','share','upload','delete','destructive_delete','permission_change','security_setting_modify','legal_acceptance'])
def test_consequential_external_classes_never_auto_retry(tmp_path,operation):
    _,store,_=setup(tmp_path);lease=store.acquire_lease('tx','w');d,_=store.begin_dispatch(lease,action_id='tx:0',idempotency_key='i',operation_class=operation);store.mark_dispatched(lease,d['dispatch_id']);store.mark_verifying(lease,d['dispatch_id'])
    rec=build_record(transaction_id='tx',action_id='tx:0',dispatch_id=d['dispatch_id'],idempotency_key='i',operation_class=operation,target='',precondition={},expected_postcondition='',observed_postcondition={},result='verified_no_effect',explanation='none')
    store.record_verification(lease,rec)
    assert not store.retry_decision(d['dispatch_id'],idempotent=True)['allowed']


def test_restart_before_dispatch_is_safe_to_replan(tmp_path):
    txs,store,binding=setup(tmp_path);lease=store.acquire_lease('tx','w');store.begin_dispatch(lease,action_id='tx:0',idempotency_key='i',operation_class='copy')
    restarted=OperatorRecoveryStore(store.path,txs)
    assert restarted.snapshot('tx')['state']=='active'
    assert restarted.snapshot('tx')['recovery_reason']=='restart_before_dispatch_safe_to_replan'


def test_restart_after_dispatch_never_blind_retries(tmp_path):
    txs,store,binding=setup(tmp_path);lease,d=dispatched(store,binding)
    restarted=OperatorRecoveryStore(store.path,txs)
    assert restarted.snapshot('tx')['state']=='recovery_review_required'
    restarted2=OperatorRecoveryStore(store.path,txs)
    assert restarted2.snapshot('tx')['state']=='recovery_review_required'


def test_evidence_checksum_tamper_rejected(tmp_path):
    _,store,binding=setup(tmp_path);lease,d=dispatched(store,binding);store.mark_verifying(lease,d['dispatch_id'])
    rec=build_record(transaction_id='tx',action_id='tx:0',dispatch_id=d['dispatch_id'],idempotency_key='idem',operation_class='copy',target='',precondition={},expected_postcondition='',observed_postcondition={'sha256':'x'},result='verified_success',explanation='ok')
    object.__setattr__(rec,'evidence_checksum','0'*64)
    with pytest.raises(PermissionError,match='evidence_checksum_mismatch'):store.record_verification(lease,rec)


def test_owner_decision_requires_exact_binding_and_reauth(tmp_path):
    _,store,binding=setup(tmp_path)
    with pytest.raises(PermissionError,match='reauthentication_required'):store.owner_decision('tx',binding,decision='resume_safe_checkpoint',decision_id='d1')
    result,created=store.owner_decision('tx',binding,decision='resume_safe_checkpoint',decision_id='d1',reauthenticated=True)
    assert created and result['decision']=='resume_safe_checkpoint'
    wrong=OperatorBinding('owner','other','session',3)
    with pytest.raises(PermissionError):store.owner_decision('tx',wrong,decision='verify_again',decision_id='d2')


def test_recovery_decision_replay_is_idempotent_but_cannot_rebind(tmp_path):
    _,store,binding=setup(tmp_path)
    _,created=store.owner_decision('tx',binding,decision='verify_again',decision_id='same')
    _,created2=store.owner_decision('tx',binding,decision='verify_again',decision_id='same')
    assert created and not created2
    with pytest.raises(PermissionError,match='recovery_decision_replay'):store.owner_decision('tx',binding,decision='cancel_remaining',decision_id='same')


def test_unknown_outcome_blocks_compensation(tmp_path):
    _,store,binding=setup(tmp_path);lease,d=dispatched(store,binding);store.mark_verifying(lease,d['dispatch_id']);verify(store,lease,d,'unknown_outcome')
    with pytest.raises(RuntimeError,match='unknown outcome'):store.plan_compensation('tx',original_action_id='tx:0',category='compensation_available',plan={'kind':'delete'})


def test_irreversible_compensation_cannot_claim_plan(tmp_path):
    _,store,_=setup(tmp_path)
    with pytest.raises(ValueError,match='irreversible'):store.plan_compensation('tx',original_action_id='tx:0',category='irreversible',plan={'kind':'undo'})


def test_compensation_is_separate_record_and_can_require_approval(tmp_path):
    _,store,_=setup(tmp_path)
    item=store.plan_compensation('tx',original_action_id='tx:0',category='compensation_available',operation_class='delete',plan={'target_digest':'abc'},requires_approval=True,requires_reauth=True)
    assert item['original_action_id']=='tx:0' and item['requires_approval'] and item['requires_reauth']
    assert store.snapshot('tx')['state']=='compensation_requires_approval'


def test_emergency_stop_blocks_dispatch_and_recovery_lease(tmp_path):
    flag={'on':False};_,store,binding=setup(tmp_path,stop=lambda:flag['on']);flag['on']=True
    with pytest.raises(PermissionError,match='emergency_stop_active'):store.acquire_lease('tx','w')
    assert store.emergency_stop()==1 and store.snapshot('tx')['state']=='recovery_review_required'
    flag['on']=False
    assert store.snapshot('tx')['state']=='recovery_review_required'


def test_audit_redacts_sensitive_payload(tmp_path):
    _,store,_=setup(tmp_path)
    with store._con() as con:
        con.execute('BEGIN IMMEDIATE');store._audit(con,'tx','test',{'token':'secret','content':'raw','sha256':'ok'});con.commit()
    joined=' '.join(x['payload_json'] for x in store.audit('tx'))
    assert 'secret' not in joined and 'raw' not in joined and 'sha256' in joined


def test_recovery_report_is_owner_safe(tmp_path):
    _,store,_=setup(tmp_path)
    report=store.recovery_report('tx')
    assert report['goal']=='W7.6 test' and 'rollback_limitations' in report
    assert 'password' not in str(report).lower()
