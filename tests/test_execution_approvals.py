import time
from types import SimpleNamespace
import pytest
from agent.executor import AgentExecutor,ConfirmationRequired
from tools.registry import ToolRegistry,Tool,Risk

class Models:
    def chat(self,prompt,history=None,system=None):return 'done'
class Memory:
    def __init__(self):self.rows=[];self.messages=[]
    def add_message(self,role,text):self.messages.append({'role':role,'content':text})
    def recent_messages(self,n):return self.messages[-n:]
    def audit(self,*args):self.rows.append(args)
class Events:
    def __init__(self):self.rows=[]
    def emit(self,name,**payload):self.rows.append((name,payload))
class Planner:
    def __init__(self,plan):self.value=plan
    def plan(self,text,context=''):return self.value

def build(plan,ttl=600):
    calls=[];settings=SimpleNamespace(autonomy_mode='ask');tools=ToolRegistry(settings)
    tools.register(Tool('read','read',lambda p:calls.append(('read',dict(p))) or {'read':True},Risk.READ_ONLY))
    tools.register(Tool('side','side',lambda p:calls.append(('side',dict(p))) or {'value':p.get('value')},Risk.EXTERNAL_SIDE_EFFECT))
    ex=AgentExecutor(models=Models(),tools=tools,memory=Memory(),events=Events(),approval_ttl_seconds=ttl);ex.planner=Planner(plan);return ex,calls

def test_side_effect_creates_exact_pending_execution():
    ex,calls=build({'steps':[{'tool':'side','parameters':{'value':7},'description':'change'}]})
    with pytest.raises(ConfirmationRequired) as err:ex.chat('do it')
    p=ex.pending_approvals()[0]
    assert err.value.execution_id==p['execution_id'] and p['tool']=='side' and p['parameters']=={'value':7}
    assert len(p['parameter_hash'])==64 and calls==[] and p['expires_at']>p['created_at']

def test_approve_executes_once_and_reuse_is_rejected():
    ex,calls=build({'steps':[{'tool':'side','parameters':{'value':3}}]})
    with pytest.raises(ConfirmationRequired) as err:ex.chat('do it')
    result=ex.resume(err.value.execution_id,True)
    assert result['status']=='completed' and calls==[('side',{'value':3})]
    with pytest.raises(RuntimeError):ex.resume(err.value.execution_id,True)
    assert calls==[('side',{'value':3})]

def test_rejection_never_executes():
    ex,calls=build({'steps':[{'tool':'side','parameters':{'value':9}}]})
    with pytest.raises(ConfirmationRequired) as err:ex.chat('do it')
    result=ex.resume(err.value.execution_id,False)
    assert result['status']=='rejected' and calls==[]
    with pytest.raises(RuntimeError):ex.resume(err.value.execution_id,True)

def test_mutated_plan_payload_fails_integrity_check():
    plan={'steps':[{'tool':'side','parameters':{'value':5}}]};ex,calls=build(plan)
    with pytest.raises(ConfirmationRequired) as err:ex.chat('do it')
    ex._pending[err.value.execution_id].plan['steps'][0]['parameters']['value']=500
    with pytest.raises(RuntimeError,match='integrity'):ex.resume(err.value.execution_id,True)
    assert calls==[]

def test_expired_approval_cannot_execute():
    ex,calls=build({'steps':[{'tool':'side','parameters':{'value':1}}]},ttl=30)
    with pytest.raises(ConfirmationRequired) as err:ex.chat('do it')
    ex._pending[err.value.execution_id].expires_at=time.time()-1
    with pytest.raises(RuntimeError):ex.resume(err.value.execution_id,True)
    assert calls==[]

def test_resumed_plan_requires_new_approval_for_next_side_effect():
    ex,calls=build({'steps':[{'tool':'read','parameters':{}},{'tool':'side','parameters':{'value':1}},{'tool':'side','parameters':{'value':2}}]})
    with pytest.raises(ConfirmationRequired) as first:ex.chat('multi')
    assert calls==[('read',{})]
    with pytest.raises(ConfirmationRequired) as second:ex.resume(first.value.execution_id,True)
    assert second.value.execution_id!=first.value.execution_id
    assert calls==[('read',{}),('side',{'value':1})]
    final=ex.resume(second.value.execution_id,True)
    assert final['status']=='completed' and calls[-1]==('side',{'value':2})
