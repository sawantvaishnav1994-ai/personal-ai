from types import SimpleNamespace
import time
import pytest

from browser.safe_operator import BrowserRecoveryRequired
from browser.transactional_operator import TransactionalBrowserOperator
from desktop.operator_context import OperatorRequestContext,set_operator_request,reset_operator_request
from security.policy_gateway import DecisionKind
from tools.registry import Risk,Tool,ToolRegistry


CTX={'owner_id':'owner','device_id':'device-1','session_id':'session-1','security_epoch':0,'conversation_id':'c','workflow_id':''}

class FakeSafe:
    def __init__(self):self.calls=0;self.fail=None
    def prepare(self,action,parameters):
        p={k:v for k,v in dict(parameters).items() if not str(k).startswith('_')}
        p.update({'destination':'https://example.com','_observation_digest':'obs-1','_observation_captured_at':time.time(),'_browser_context_id':'b','_tab_id':'t','_origin':'https://example.com','_application':{'canonical_path':'/browser','sha256':'a'*64}});return p
    def execute(self,action,parameters):
        self.calls+=1
        if self.fail:raise self.fail
        return {'verified':True,'reason':'ok','evidence':{'before':{'browser_context_id':'b','tab_id':'t'},'after':{'browser_context_id':'b','tab_id':'t'}}}


def prepared(tx,action='click',approval=True):
    p={'_trusted_context':dict(CTX),'_trusted_reauthenticated':True,'target_id':'x'}
    out=tx.prepare(action,p,requires_approval=approval);out['_personal_ai_prepared']=True;return out


def test_side_effect_transaction_starts_approval_required(tmp_path):
    tx=TransactionalBrowserOperator(FakeSafe(),tmp_path);p=prepared(tx);row=tx.store.transaction(p['_browser_transaction_id']);assert row['state']=='approval_required'

def test_read_transaction_can_be_permitted_without_approval(tmp_path):
    tx=TransactionalBrowserOperator(FakeSafe(),tmp_path);p=prepared(tx,'extract_visible',False);assert tx.store.transaction(p['_browser_transaction_id'])['state']=='permitted'

def test_execute_completes_and_is_idempotent(tmp_path):
    safe=FakeSafe();tx=TransactionalBrowserOperator(safe,tmp_path);p=prepared(tx);first=tx.execute('click',p);second=tx.execute('click',p);assert first['verified'] and second['deduplicated'] and safe.calls==1

def test_owner_device_session_epoch_mismatch_blocks(tmp_path):
    tx=TransactionalBrowserOperator(FakeSafe(),tmp_path);p=prepared(tx)
    for key,value in [('owner_id','other'),('device_id','other'),('session_id','other'),('security_epoch',9)]:
        bad=dict(p);bad['_trusted_context']={**CTX,key:value}
        with pytest.raises(PermissionError):tx.execute('click',bad)

def test_plan_change_after_approval_blocks(tmp_path):
    tx=TransactionalBrowserOperator(FakeSafe(),tmp_path);p=prepared(tx);p['_browser_plan_digest']='changed'
    with pytest.raises(PermissionError):tx.execute('click',p)

def test_cancelled_transaction_never_dispatches(tmp_path):
    safe=FakeSafe();tx=TransactionalBrowserOperator(safe,tmp_path);p=prepared(tx);assert tx.cancel(p)
    with pytest.raises(RuntimeError):tx.execute('click',p)
    assert safe.calls==0

def test_emergency_stop_race_blocks_before_dispatch(tmp_path):
    safe=FakeSafe();state={'stop':False};tx=TransactionalBrowserOperator(safe,tmp_path,emergency_stop=lambda:state['stop']);p=prepared(tx);state['stop']=True
    with pytest.raises(Exception):tx.execute('click',p)
    assert safe.calls==0 and tx.store.transaction(p['_browser_transaction_id'])['state']=='cancelled'

def test_uncertain_outcome_enters_recovery_and_cannot_blind_retry(tmp_path):
    safe=FakeSafe();safe.fail=BrowserRecoveryRequired('uncertain submission');tx=TransactionalBrowserOperator(safe,tmp_path);p=prepared(tx)
    with pytest.raises(BrowserRecoveryRequired):tx.execute('click',p)
    assert tx.store.transaction(p['_browser_transaction_id'])['state']=='recovery_review_required'
    safe.fail=None
    with pytest.raises(BrowserRecoveryRequired):tx.execute('click',p)
    assert safe.calls==1

def test_restart_recovers_interrupted_browser_transaction(tmp_path):
    safe=FakeSafe();tx=TransactionalBrowserOperator(safe,tmp_path);p=prepared(tx);tx.store.transition(p['_browser_transaction_id'],'permitted');tx.store.transition(p['_browser_transaction_id'],'executing')
    restarted=TransactionalBrowserOperator(safe,tmp_path);assert restarted.store.transaction(p['_browser_transaction_id'])['state']=='recovery_review_required'

def test_transaction_audit_contains_hashes_not_typed_content(tmp_path):
    safe=FakeSafe();tx=TransactionalBrowserOperator(safe,tmp_path);p=prepared(tx);p['text']='TOP-SECRET-TEXT';tx.execute('click',p)
    raw=' '.join(row['payload_json'] for row in tx.store.audit(p['_browser_transaction_id']));assert 'TOP-SECRET-TEXT' not in raw


def registry(tmp_path,mode='act'):
    return ToolRegistry(SimpleNamespace(autonomy_mode=mode,data_dir=tmp_path))

def app_rule():return {'canonical_path':'/browser','sha256':'a'*64,'publisher':'','version':''}

def domain_rule():return {'scheme':'https','host':'example.com','port':443,'include_subdomains':False,'allow_ip_literal':False,'allow_private_network':False}

def add_browser_policies(reg,operation='read',approval_rule='none'):
    epoch=reg.current_security_epoch()
    reg.policy_gateway.add_policy(owner_id='owner',target_type='application',target_identity=app_rule(),allowed_operations=[operation,'control','application_input','form_submission','external_upload','navigate'],security_epoch=epoch,reauthenticated=True)
    return reg.policy_gateway.add_policy(owner_id='owner',target_type='domain',target_identity=domain_rule(),allowed_operations=[operation],approval_rule=approval_rule,security_epoch=epoch,reauthenticated=True)

def dummy_tool(reg,operation='read',risk=Risk.READ_ONLY):
    def prepare(p):
        ctx=dict(p['_trusted_context']);return {'destination':'https://example.com','_trusted_context':ctx,'_trusted_reauthenticated':p.get('_trusted_reauthenticated',False),'_application':app_rule(),'_observation_digest':'obs','_policy_tool_name':'dummy'}
    tool=Tool('dummy','dummy',lambda p:{'verified':True},risk,prepare=prepare,requires_trusted_context=True,policy_operation=operation,policy_target_type='domain');reg.register(tool);return tool

def context(reg,reauth=True):
    return OperatorRequestContext('owner','device-1','session-1',reg.current_security_epoch(),reauthenticated_at=time.time() if reauth else None)

def test_browser_policy_is_default_deny_even_for_read_only_tool(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='public');assert not d.allowed and d.reason=='application_not_allowed' or d.reason=='domain_not_allowed'
    finally:reset_operator_request(token)

def test_app_and_domain_both_must_be_allowed(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);epoch=reg.current_security_epoch();reg.policy_gateway.add_policy(owner_id='owner',target_type='domain',target_identity=domain_rule(),allowed_operations=['read'],security_epoch=epoch,reauthenticated=True);token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='public');assert not d.allowed and d.reason=='application_not_allowed'
    finally:reset_operator_request(token)

def test_allowed_read_policy_can_pass_permission_engine(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);add_browser_policies(reg);token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='public');assert d.allowed
    finally:reset_operator_request(token)

def test_policy_approval_rule_is_not_bypassed_by_act_mode(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);add_browser_policies(reg,approval_rule='always');token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='public');assert not d.allowed and d.requires_confirmation and d.reason=='approval_required'
    finally:reset_operator_request(token)

def test_sensitive_external_form_requires_approval(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg,'form_submission',Risk.EXTERNAL_SIDE_EFFECT);add_browser_policies(reg,'form_submission');token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='sensitive');assert not d.allowed and d.requires_confirmation
    finally:reset_operator_request(token)

def test_secret_external_upload_is_blocked_not_approvable(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg,'external_upload',Risk.EXTERNAL_SIDE_EFFECT);add_browser_policies(reg,'external_upload');token=set_operator_request(context(reg))
    try:d=reg.authorize(tool,parameters={},data_classification='secret');assert not d.allowed and not d.requires_confirmation and d.reason=='secret_transfer_blocked'
    finally:reset_operator_request(token)

def test_model_cannot_inject_trusted_context_or_prepared_flag(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);add_browser_policies(reg)
    with pytest.raises(PermissionError):reg.authorize(tool,parameters={'_trusted_context':CTX,'_personal_ai_prepared':True},data_classification='public')

def test_policy_permit_is_one_use_and_data_classification_bound(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);add_browser_policies(reg);token=set_operator_request(context(reg))
    try:
        params={};assert reg.authorize(tool,parameters=params,data_classification='public').allowed;permit=reg.issue_tool_policy_permit(params);assert permit['operation'].data_classification=='public';assert reg.consume_tool_policy_permit(params,permit);assert not reg.policy_gateway.consume_temporary_permit(permit['permit_id'],permit['operation'],permit['decision'])
    finally:reset_operator_request(token)

def test_policy_change_after_authorization_invalidates_execution_permit(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);p=add_browser_policies(reg);token=set_operator_request(context(reg))
    try:
        params={};assert reg.authorize(tool,parameters=params,data_classification='public').allowed;reg.policy_gateway.revoke_policy(p['policy_id'],owner_id='owner',reauthenticated=True)
        with pytest.raises(PermissionError):reg.issue_tool_policy_permit(params)
    finally:reset_operator_request(token)

def test_security_epoch_change_invalidates_browser_authority(tmp_path):
    reg=registry(tmp_path);tool=dummy_tool(reg);add_browser_policies(reg);token=set_operator_request(context(reg));params={}
    try:assert reg.authorize(tool,parameters=params,data_classification='public').allowed
    finally:reset_operator_request(token)
    reg.set_emergency_stop(True);reg.set_emergency_stop(False);token=set_operator_request(OperatorRequestContext('owner','device-1','session-1',0,reauthenticated_at=time.time()))
    try:d=reg.authorize(tool,parameters={},data_classification='public');assert not d.allowed
    finally:reset_operator_request(token)
