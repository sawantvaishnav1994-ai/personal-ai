from __future__ import annotations
import json,uuid,threading
from agent.planner import Planner
from security.approvals import ApprovalManager,parameter_hash

class ConfirmationRequired(RuntimeError):
    def __init__(self,tool_name,parameters,description='',*,approval_id:str,execution_id:str,expires_at:float):
        super().__init__(f'Confirmation required for {tool_name}')
        self.tool_name=tool_name;self.parameters=parameters;self.description=description;self.approval_id=approval_id;self.execution_id=execution_id;self.expires_at=expires_at

class AgentExecutor:
    def __init__(self,*,models,tools,memory,events,second_brain=None,approval_ttl_seconds:int=300):
        self.models=models;self.tools=tools;self.memory=memory;self.events=events;self.second_brain=second_brain;self.planner=Planner(models,tools);self.approvals=ApprovalManager(approval_ttl_seconds);self._paused={};self._lock=threading.RLock()

    def chat(self,text,*,confirmed_tools:set[str]|None=None):
        if confirmed_tools:
            raise PermissionError('tool-name approvals are disabled; use the execution-scoped approval flow')
        self.memory.add_message('user',text);memories=self.second_brain.context(text,6) if self.second_brain else [];history=self.memory.recent_messages(16);context=json.dumps(memories,default=str)[:8000] if memories else ''
        self.events.emit('state',state='thinking')
        try:plan=self.planner.plan(text,context=context)
        except Exception:
            answer=self.models.chat(text,history=history[:-1]);self.memory.add_message('assistant',answer);self.events.emit('state',state='speaking');return answer
        return self._continue(str(uuid.uuid4()),text,plan,0,{},history)

    def _continue(self,execution_id,text,plan,index,results,history):
        steps=plan.get('steps',[])
        while index<len(steps):
            step=steps[index];tool=self.tools.get(step['tool']);params=step.get('parameters',{});decision=self.tools.authorize(tool,confirmed=False)
            if not decision.allowed:
                ticket=self.approvals.create(execution_id,tool.name,params)
                with self._lock:self._paused[ticket.id]={'execution_id':execution_id,'text':text,'plan':plan,'index':index,'results':dict(results),'history':history}
                audit={'approval_id':ticket.id,'execution_id':execution_id,'tool':tool.name,'parameter_hash':ticket.parameter_hash,'expires_at':ticket.expires_at}
                self.memory.audit('approval','required',audit);self.events.emit('approval.required',**audit)
                raise ConfirmationRequired(tool.name,params,step.get('description',''),approval_id=ticket.id,execution_id=execution_id,expires_at=ticket.expires_at)
            self._execute_step(execution_id,index,tool,params,results);index+=1
        return self._finalize(text,results,history)

    def _execute_step(self,execution_id,index,tool,params,results):
        self.events.emit('state',state='acting',tool=tool.name,execution_id=execution_id)
        try:
            result=tool.handler(params);results[f'step{index+1}']={'ok':True,'result':result};self.memory.audit('tool','execute',{'execution_id':execution_id,'tool':tool.name,'params':params,'parameter_hash':parameter_hash(params),'ok':True})
        except Exception as exc:
            self.memory.audit('tool','execute',{'execution_id':execution_id,'tool':tool.name,'params':params,'parameter_hash':parameter_hash(params),'ok':False,'error':str(exc)});raise

    def approve(self,approval_id:str):
        with self._lock:paused=self._paused.get(approval_id)
        if not paused:raise PermissionError('approval is missing, expired, rejected, or already used')
        index=paused['index'];step=paused['plan']['steps'][index];tool=self.tools.get(step['tool']);params=step.get('parameters',{})
        self.approvals.consume(approval_id,paused['execution_id'],tool.name,params)
        with self._lock:self._paused.pop(approval_id,None)
        self.memory.audit('approval','approved',{'approval_id':approval_id,'execution_id':paused['execution_id'],'tool':tool.name,'parameter_hash':parameter_hash(params)})
        self.events.emit('approval.approved',approval_id=approval_id,execution_id=paused['execution_id'],tool=tool.name)
        results=paused['results'];self._execute_step(paused['execution_id'],index,tool,params,results)
        return self._continue(paused['execution_id'],paused['text'],paused['plan'],index+1,results,paused['history'])

    def reject(self,approval_id:str):
        with self._lock:paused=self._paused.pop(approval_id,None)
        self.approvals.reject(approval_id)
        if paused:
            step=paused['plan']['steps'][paused['index']];self.memory.audit('approval','rejected',{'approval_id':approval_id,'execution_id':paused['execution_id'],'tool':step['tool'],'parameter_hash':parameter_hash(step.get('parameters',{}))});self.events.emit('approval.rejected',approval_id=approval_id,execution_id=paused['execution_id'],tool=step['tool'])
        self.events.emit('state',state='idle');return 'Action cancelled.'

    def _finalize(self,text,results,history):
        if results:answer=self.models.chat(f"User request: {text}\nTool results: {json.dumps(results,default=str)[:12000]}\nSummarize what was completed and mention any limitations.",system='You are a concise personal AI assistant.')
        else:answer=self.models.chat(text,history=history[:-1])
        self.memory.add_message('assistant',answer)
        if self.second_brain:
            for candidate in self.second_brain.extract_candidates(text,answer):self.second_brain.remember(candidate)
        self.events.emit('state',state='speaking');return answer
