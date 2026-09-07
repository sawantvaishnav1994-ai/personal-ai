from __future__ import annotations
import hashlib,json,time,uuid
from dataclasses import dataclass
from agent.planner import Planner

@dataclass
class PendingExecution:
    execution_id:str
    created_at:float
    expires_at:float
    text:str
    plan:dict
    step_index:int
    results:dict
    tool_name:str
    parameters:dict
    parameter_hash:str
    description:str
    consumed:bool=False

class ConfirmationRequired(RuntimeError):
    def __init__(self,tool_name,parameters,description="",execution_id=""):
        super().__init__(f"Confirmation required for {tool_name}")
        self.tool_name=tool_name; self.parameters=parameters; self.description=description; self.execution_id=execution_id

class AgentExecutor:
    def __init__(self,*,models,tools,memory,events,second_brain=None,approval_ttl_seconds:int=600):
        self.models=models; self.tools=tools; self.memory=memory; self.events=events
        self.second_brain=second_brain; self.approval_ttl_seconds=max(30,int(approval_ttl_seconds));self._pending={}
        self.planner=Planner(models,tools)

    @staticmethod
    def _parameter_hash(parameters:dict)->str:
        raw=json.dumps(parameters,sort_keys=True,separators=(',',':'),default=str).encode();return hashlib.sha256(raw).hexdigest()

    def pending_approvals(self):
        self._expire_pending();return [self._public_pending(p) for p in self._pending.values() if not p.consumed]

    def _public_pending(self,p:PendingExecution):
        return {'execution_id':p.execution_id,'tool':p.tool_name,'parameters':p.parameters,'parameter_hash':p.parameter_hash,'description':p.description,'created_at':p.created_at,'expires_at':p.expires_at}

    def _expire_pending(self):
        now=time.time()
        for p in list(self._pending.values()):
            if not p.consumed and p.expires_at<=now:
                p.consumed=True;self.memory.audit('approval','expired',{'execution_id':p.execution_id,'tool':p.tool_name,'parameter_hash':p.parameter_hash})

    def _create_pending(self,text,plan,step_index,results,step):
        execution_id=str(uuid.uuid4());params=json.loads(json.dumps(step.get('parameters',{}),default=str));now=time.time();p=PendingExecution(execution_id,now,now+self.approval_ttl_seconds,text,plan,step_index,json.loads(json.dumps(results,default=str)),step['tool'],params,self._parameter_hash(params),step.get('description',''))
        self._pending[execution_id]=p;self.memory.audit('approval','required',self._public_pending(p));self.events.emit('approval.required',**self._public_pending(p));return p

    def chat(self,text,*,confirmed_tools:set[str]|None=None):
        confirmed_tools=confirmed_tools or set();self.memory.add_message('user',text)
        memories=self.second_brain.context(text,6) if self.second_brain else [];history=self.memory.recent_messages(16);context=json.dumps(memories,default=str)[:8000] if memories else ''
        self.events.emit('state',state='thinking')
        try:plan=self.planner.plan(text,context=context)
        except Exception:
            answer=self.models.chat(text,history=history[:-1]);self.memory.add_message('assistant',answer);self.events.emit('state',state='speaking');return answer
        return self._run_plan(text,plan,{},0,legacy_confirmed=confirmed_tools)

    def _run_plan(self,text,plan,results,start_index,legacy_confirmed:set[str]|None=None):
        legacy_confirmed=legacy_confirmed or set()
        steps=plan.get('steps',[])
        for idx in range(start_index,len(steps)):
            step=steps[idx];tool=self.tools.get(step['tool']);params=step.get('parameters',{});decision=self.tools.authorize(tool,confirmed=tool.name in legacy_confirmed)
            if not decision.allowed:
                pending=self._create_pending(text,plan,idx,results,step)
                raise ConfirmationRequired(tool.name,params,step.get('description',''),pending.execution_id)
            self._execute_step(results,idx,tool,params)
        return self._finish(text,results)

    def _execute_step(self,results,idx,tool,params):
        self.events.emit('state',state='acting',tool=tool.name)
        try:
            result=tool.handler(params);results[f'step{idx+1}']={'ok':True,'result':result};self.memory.audit('tool','execute',{'tool':tool.name,'params':params,'parameter_hash':self._parameter_hash(params),'ok':True})
        except Exception as exc:
            self.memory.audit('tool','execute',{'tool':tool.name,'params':params,'parameter_hash':self._parameter_hash(params),'ok':False,'error':str(exc)});raise

    def resume(self,execution_id:str,approve:bool):
        self._expire_pending();p=self._pending.get(execution_id)
        if not p:raise KeyError('unknown approval execution_id')
        if p.consumed:raise RuntimeError('approval is expired or already used')
        p.consumed=True
        if not approve:
            self.memory.audit('approval','rejected',{'execution_id':p.execution_id,'tool':p.tool_name,'parameter_hash':p.parameter_hash});self.events.emit('approval.rejected',execution_id=p.execution_id,tool=p.tool_name);return {'status':'rejected','execution_id':p.execution_id}
        step=p.plan.get('steps',[])[p.step_index]
        current_hash=self._parameter_hash(step.get('parameters',{}))
        if step.get('tool')!=p.tool_name or current_hash!=p.parameter_hash:
            self.memory.audit('approval','integrity_failed',{'execution_id':p.execution_id});raise RuntimeError('approval payload integrity check failed')
        tool=self.tools.get(p.tool_name);decision=self.tools.authorize(tool,confirmed=True)
        if not decision.allowed:raise PermissionError(decision.reason)
        results=dict(p.results);self.memory.audit('approval','approved',{'execution_id':p.execution_id,'tool':p.tool_name,'parameter_hash':p.parameter_hash});self._execute_step(results,p.step_index,tool,p.parameters)
        return {'status':'completed','execution_id':p.execution_id,'answer':self._run_plan(p.text,p.plan,results,p.step_index+1)}

    def _finish(self,text,results):
        if results:answer=self.models.chat(f"User request: {text}\nTool results: {json.dumps(results,default=str)[:12000]}\nSummarize what was completed and mention any limitations.",system='You are a concise personal AI assistant.')
        else:answer=self.models.chat(text,history=self.memory.recent_messages(16)[:-1])
        self.memory.add_message('assistant',answer)
        if self.second_brain:
            for candidate in self.second_brain.extract_candidates(text,answer):self.second_brain.remember(candidate)
        self.events.emit('state',state='speaking');return answer
