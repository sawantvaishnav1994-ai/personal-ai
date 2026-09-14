from types import SimpleNamespace

import pytest

from desktop.operator_context import OperatorRequestContext, reset_operator_request, set_operator_request
from security.approvals import parameter_hash
from tools.computer import register as register_computer
from tools.registry import ToolRegistry
from vision.computer_intelligence import ComputerIntelligence


class Models:
    def json(self, prompt, system=''):
        return {
            'summary': 'click the safe test button',
            'steps': [
                {'kind': 'click', 'params': {'x': 10, 'y': 20}, 'reason': 'test action', 'verify': 'the test state changed'}
            ],
        }


class Screen:
    def __init__(self, verified=True): self.verified=verified
    def analyze(self, prompt, monitor=1):
        if str(prompt).startswith('Verify this UI postcondition:'):
            return {'analysis': 'VERIFIED test state changed' if self.verified else 'NOT_VERIFIED test state unchanged', 'screenshot': 'screen-after'}
        return {'analysis': 'safe test screen with one button', 'screenshot': 'screen-before'}


class Controller:
    def __init__(self): self.version=0; self.clicks=0; self.rollbacks=0
    def snapshot(self): return {'x':0,'y':0,'screen_sha256':f'screen-{self.version}'}
    def click(self, x=None, y=None, button='left'):
        self.clicks += 1; self.version += 1; return {'ok':True,'x':x,'y':y}
    def move(self, x, y, duration=.2): self.version += 1; return {'x':x,'y':y}
    def type_text(self, text, interval=.01): self.version += 1; return {'ok':True}
    def hotkey(self, *keys): self.version += 1; return {'ok':True}
    def verify_change(self, before, after, kind): return before['screen_sha256'] != after['screen_sha256'] or kind == 'move'
    def undo_descriptor(self, kind, before, params): return {'kind':'undo'}
    def apply_undo(self, descriptor): self.rollbacks += 1; return {'ok':True}


def trusted():
    return {'owner_id':'owner','device_id':'device-1','session_id':'session-1','security_epoch':9,'conversation_id':'conversation-1','workflow_id':'workflow-1'}


def computer(tmp_path, *, verified=True, stopped=None):
    ctl=Controller(); c=ComputerIntelligence(Models(),tmp_path,controller=ctl,emergency_stop=(stopped or (lambda:False)))
    c.screen=Screen(verified=verified)
    return c,ctl


def prepare(c, **extra):
    params={'goal':'click the safe test button','max_steps':4,'monitor':1,'timeout_seconds':60,'_trusted_context':trusted(),**extra}
    out=c.prepare_execution(params); out['_personal_ai_prepared']=True; return out


def test_prepare_binds_goal_plan_authority_and_conversation(tmp_path):
    c,_=computer(tmp_path); params=prepare(c); tx=c.operator_transactions.transaction(params['_operator_transaction_id'])
    assert tx['state']=='approval_required'
    assert tx['owner_id']=='owner' and tx['device_id']=='device-1' and tx['session_id']=='session-1'
    assert tx['security_epoch']==9
    assert tx['conversation_id']=='conversation-1' and tx['workflow_id']=='workflow-1'
    assert tx['plan']==params['_operator_plan']
    before=parameter_hash(params)
    params['_operator_plan']['steps'][0]['params']['x']=11
    assert parameter_hash(params)!=before


def test_prepared_execution_completes_only_after_verification(tmp_path):
    c,ctl=computer(tmp_path); params=prepare(c); result=c.execute_prepared(params)
    assert result['ok'] is True and result['verified'] is True
    assert ctl.clicks==1
    tx=c.operator_transactions.transaction(params['_operator_transaction_id'])
    assert tx['state']=='completed' and tx['checkpoint_index']==1
    assert c.operator_transactions.actions(tx['transaction_id'])[0]['verified'] is True
    dedup=c.execute_prepared(params)
    assert dedup['deduplicated'] is True and ctl.clicks==1


def test_semantic_verification_failure_requires_recovery_review(tmp_path):
    c,ctl=computer(tmp_path,verified=False); params=prepare(c)
    with pytest.raises(RuntimeError,match='postcondition failed'):
        c.execute_prepared(params)
    tx=c.operator_transactions.transaction(params['_operator_transaction_id'])
    assert tx['state']=='recovery_review_required'
    assert c.operator_transactions.actions(tx['transaction_id'])[0]['state']=='verification_failed'
    assert ctl.rollbacks>=1
    with pytest.raises(RuntimeError,match='recovery review'):
        c.execute_prepared(params)
    assert ctl.clicks==1


def test_emergency_stop_blocks_before_first_dispatch(tmp_path):
    flag={'on':False}; c,ctl=computer(tmp_path,stopped=lambda:flag['on']); params=prepare(c); flag['on']=True
    with pytest.raises(PermissionError,match='emergency stop'):
        c.execute_prepared(params)
    assert ctl.clicks==0
    assert c.operator_transactions.transaction(params['_operator_transaction_id'])['state']=='cancelled'


def test_unprepared_or_wrong_binding_execution_fails_closed(tmp_path):
    c,_=computer(tmp_path)
    with pytest.raises(PermissionError,match='prepared and approved'):
        c.execute_prepared({'goal':'x','_trusted_context':trusted()})
    params=prepare(c); params['_trusted_context']={**trusted(),'session_id':'wrong'}
    with pytest.raises(PermissionError,match='binding mismatch'):
        c.execute_prepared(params)


def test_tool_registry_prepares_exact_plan_under_trusted_request_context(tmp_path):
    settings=SimpleNamespace(data_dir=tmp_path,autonomy_mode='ask')
    registry=ToolRegistry(settings); comp=register_computer(registry,Models(),settings); comp.screen=Screen(); comp.controller=Controller(); comp.transactions.controller=comp.controller
    tool=registry.get('computer_execute')
    assert tool.requires_trusted_context is True and tool.requires_reauth is True and tool.verification_required is True
    params={'goal':'click the safe test button','max_steps':4,'monitor':1}
    context=OperatorRequestContext('owner','device-1','session-1',3,'conversation-1','workflow-1')
    token=set_operator_request(context)
    try: decision=registry.authorize(tool,parameters=params,data_classification='internal')
    finally: reset_operator_request(token)
    assert decision.allowed is False and decision.requires_confirmation is True
    assert params['_trusted_context']['device_id']=='device-1'
    assert params['_operator_plan']['steps'][0]['kind']=='click'
    assert params['_operator_transaction_id']
    assert params['_personal_ai_prepared'] is True


def test_tool_registry_rejects_computer_control_without_trusted_context(tmp_path):
    settings=SimpleNamespace(data_dir=tmp_path,autonomy_mode='ask')
    registry=ToolRegistry(settings); register_computer(registry,Models(),settings)
    with pytest.raises(PermissionError,match='trusted browser/session context'):
        registry.authorize(registry.get('computer_execute'),parameters={'goal':'test'})
