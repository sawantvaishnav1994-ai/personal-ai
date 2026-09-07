from __future__ import annotations
import json,time
from dataclasses import dataclass
from typing import Any

@dataclass
class PendingRealtimeApproval:
    call_id:str
    tool_name:str
    parameters:dict[str,Any]
    created_at:float

class RealtimeToolBridge:
    """Maps Realtime function calls onto Personal AI's centralized tool/permission runtime."""
    def __init__(self,executor,events=None):
        self.executor=executor; self.tools=executor.tools; self.events=events; self.pending={}
    def definitions(self):
        return [
            {
                'type':'function',
                'name':tool.name,
                'description':tool.description,
                'parameters':{'type':'object','additionalProperties':True},
            }
            for tool in self.tools.all()
        ]
    def _emit(self,name,**data):
        if self.events:self.events.emit(name,**data)
    @staticmethod
    def parse_arguments(raw)->dict:
        if raw in (None,''):return {}
        if isinstance(raw,dict):return raw
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError('tool arguments must be a JSON object')
        return value
    def invoke(self,call_id:str,tool_name:str,arguments,*,confirmed:bool=False):
        tool=self.tools.get(tool_name); params=self.parse_arguments(arguments)
        decision=self.tools.authorize(tool,confirmed=confirmed)
        if not decision.allowed:
            self.pending[call_id]=PendingRealtimeApproval(call_id,tool_name,params,time.time())
            self.executor.memory.audit('realtime_tool','approval_required',{'call_id':call_id,'tool':tool_name,'params':params})
            self._emit('voice.tool.approval_required',call_id=call_id,tool=tool_name,parameters=params)
            return {'status':'approval_required','call_id':call_id,'tool':tool_name}
        try:
            result=tool.handler(params)
            self.executor.memory.audit('realtime_tool','execute',{'call_id':call_id,'tool':tool_name,'params':params,'ok':True})
            self._emit('voice.tool.completed',call_id=call_id,tool=tool_name)
            return {'status':'completed','ok':True,'result':result}
        except Exception as exc:
            self.executor.memory.audit('realtime_tool','execute',{'call_id':call_id,'tool':tool_name,'params':params,'ok':False,'error':str(exc)})
            self._emit('voice.tool.failed',call_id=call_id,tool=tool_name,error=str(exc))
            return {'status':'completed','ok':False,'error':str(exc)}
    def approve(self,call_id:str):
        item=self.pending.pop(call_id)
        return self.invoke(item.call_id,item.tool_name,item.parameters,confirmed=True)
    def reject(self,call_id:str):
        item=self.pending.pop(call_id)
        self.executor.memory.audit('realtime_tool','rejected',{'call_id':call_id,'tool':item.tool_name,'params':item.parameters})
        self._emit('voice.tool.rejected',call_id=call_id,tool=item.tool_name)
        return {'status':'completed','ok':False,'error':'user rejected action'}
