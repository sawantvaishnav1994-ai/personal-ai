from types import SimpleNamespace
import pytest
from security.approvals import ApprovalManager
from tools.registry import ToolRegistry,Tool,Risk
from voice.realtime_tools import RealtimeToolBridge
from voice.openai_realtime import OpenAIRealtimeVoiceSession

class Memory:
    def __init__(self):self.rows=[]
    def audit(self,*args):self.rows.append(args)
class Executor:
    pass

def build_executor(mode='ask'):
    settings=SimpleNamespace(autonomy_mode=mode)
    tools=ToolRegistry(settings)
    tools.register(Tool('read_status','read',lambda p:{'ok':'read'},Risk.READ_ONLY))
    tools.register(Tool('change_state','change',lambda p:{'changed':p['value']},Risk.EXTERNAL_SIDE_EFFECT))
    ex=Executor();ex.tools=tools;ex.memory=Memory();ex.approvals=ApprovalManager();return ex

def test_realtime_read_only_executes_automatically():
    bridge=RealtimeToolBridge(build_executor('ask'))
    result=bridge.invoke('c1','read_status','{}')
    assert result['status']=='completed' and result['ok'] is True

def test_realtime_side_effect_requires_then_accepts_approval():
    bridge=RealtimeToolBridge(build_executor('ask'))
    result=bridge.invoke('c2','change_state','{"value":7}')
    assert result['status']=='approval_required' and 'c2' in bridge.pending
    approved=bridge.approve('c2')
    assert approved['ok'] is True and approved['result']['changed']==7

def test_realtime_reject_blocks_action():
    bridge=RealtimeToolBridge(build_executor('ask'))
    bridge.invoke('c3','change_state','{"value":9}')
    rejected=bridge.reject('c3')
    assert rejected['ok'] is False and 'c3' not in bridge.pending

def test_native_session_exposes_tools_and_records_metrics():
    s=SimpleNamespace(openai_api_key='x',realtime_provider='openai',realtime_model='gpt-realtime',realtime_safety_identifier='',realtime_instructions='x',realtime_reasoning_effort='low',realtime_sample_rate=24000,realtime_voice='alloy')
    ex=build_executor('ask'); session=OpenAIRealtimeVoiceSession(s,executor=ex)
    update=session.session_update()
    assert any(t['name']=='read_status' for t in update['session']['tools'])
    session.handle_event({'type':'response.created'})
    session.handle_event({'type':'response.output_audio.delta','delta':'AA=='})
    assert session.metrics['response_count']==1 and session.metrics['audio_chunks_out']==1


def test_realtime_bridge_fails_closed_without_canonical_approval_authority():
    ex=Executor()
    ex.tools=build_executor('ask').tools
    ex.memory=Memory()
    with pytest.raises(RuntimeError, match='canonical approval authority'):
        RealtimeToolBridge(ex)


def test_realtime_approval_survives_bridge_reconstruction_and_dispatches_once():
    ex=build_executor('ask')
    first=RealtimeToolBridge(ex)
    required=first.invoke('reload-call','change_state','{"value":11}')
    approval_id=required['approval_id']
    reloaded=RealtimeToolBridge(ex)
    approved=reloaded.approve('reload-call',approval_id=approval_id)
    assert approved['ok'] is True
    assert approved['result']['changed']==11
    assert approved['verified'] is True
    replay=reloaded.approve('reload-call',approval_id=approval_id)
    assert replay['status']=='completed'
    assert replay['result']['changed']==11


def test_realtime_reconnect_requires_exact_approval_identity():
    ex=build_executor('ask')
    first=RealtimeToolBridge(ex)
    required=first.invoke('bound-call','change_state','{"value":12}')
    reloaded=RealtimeToolBridge(ex)
    with pytest.raises(PermissionError):
        reloaded.approve('bound-call')
    with pytest.raises(PermissionError):
        reloaded.approve('wrong-call',approval_id=required['approval_id'])
