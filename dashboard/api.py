from __future__ import annotations
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
import uuid
from devices.gateway import DeviceCommand
from agent.executor import ConfirmationRequired
class ActionRequest(BaseModel):tool:str;parameters:dict=Field(default_factory=dict)
class DeviceActionRequest(BaseModel):action:str;parameters:dict=Field(default_factory=dict);timeout:float=15
class ChatRequest(BaseModel):text:str=Field(min_length=1,max_length=12000)
class AutonomyRequest(BaseModel):mode:str

def dashboard_router(runtime,auth_device):
    r=APIRouter(prefix='/dashboard',tags=['dashboard'])
    def auth(a,d):auth_device(a,d)
    def credentials(authorization,x_device_id):auth(authorization,x_device_id)
    @r.get('/status')
    def status(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id)
        approvals=runtime['executor'].pending_approvals();automations=runtime['automations'].list();devices=runtime['device_registry'].list();online=runtime['device_gateway'].online();graph=runtime['second_brain'].graph();integrations=runtime.get('integrations').list() if runtime.get('integrations') else []
        voice=runtime.get('voice');native=getattr(voice,'native',None);metrics=getattr(native,'metrics',{}) if native else {}
        return {'automations':len(automations),'devices':len(devices),'online_devices':online,'integrations':integrations,'memory_nodes':len(graph.get('nodes',[])),'memory_edges':len(graph.get('edges',graph.get('relations',[]))),'voice_state':'active' if getattr(voice,'thread',None) and voice.thread.is_alive() else 'idle','voice_metrics':metrics,'pending_approvals':len(approvals),'needs_you':len(approvals),'handled_for_you':sum(1 for a in automations if a.get('enabled',True)),'security':{'vault':'keychain-backed' if runtime.get('vault') else 'unavailable','autonomy':runtime['tools'].permissions.mode,'apns':'configured' if runtime.get('apns') and runtime['apns'].configured else 'not-configured'}}
    @r.post('/chat')
    def chat(req:ChatRequest,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id)
        try:return {'status':'completed','answer':runtime['executor'].chat(req.text)}
        except ConfirmationRequired as e:return {'status':'approval_required','execution_id':e.execution_id,'tool':e.tool_name,'parameters':e.parameters,'description':e.description}
    @r.get('/approvals')
    def approvals(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id);return runtime['executor'].pending_approvals()
    @r.post('/approvals/{execution_id}/approve')
    def approve(execution_id:str,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id)
        try:return runtime['executor'].resume(execution_id,True)
        except ConfirmationRequired as e:return {'status':'approval_required','execution_id':e.execution_id,'tool':e.tool_name,'parameters':e.parameters,'description':e.description}
        except KeyError:raise HTTPException(404,'unknown approval execution_id')
        except (RuntimeError,PermissionError) as e:raise HTTPException(409,str(e))
    @r.post('/approvals/{execution_id}/reject')
    def reject(execution_id:str,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id)
        try:return runtime['executor'].resume(execution_id,False)
        except KeyError:raise HTTPException(404,'unknown approval execution_id')
        except RuntimeError as e:raise HTTPException(409,str(e))
    @r.get('/autonomy')
    def autonomy(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id);return {'mode':runtime['tools'].permissions.mode,'modes':['observe','suggest','ask','act']}
    @r.post('/autonomy')
    def set_autonomy(req:AutonomyRequest,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id);mode=req.mode.lower().strip()
        if mode not in {'observe','suggest','ask','act'}:raise HTTPException(422,'invalid autonomy mode')
        old=runtime['tools'].permissions.mode;runtime['tools'].permissions.mode=mode;runtime['memory'].audit('security','autonomy_changed',{'from':old,'to':mode,'device_id':x_device_id});return {'mode':mode}
    @r.get('/devices')
    def devices(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):credentials(authorization,x_device_id);return runtime['device_registry'].list()
    @r.get('/automations')
    def automations(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):credentials(authorization,x_device_id);return runtime['automations'].list()
    @r.get('/memory')
    def memory(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):credentials(authorization,x_device_id);return runtime['second_brain'].graph()
    @r.post('/tool')
    def tool(req:ActionRequest,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id)
        try:t=runtime['tools'].get(req.tool)
        except Exception:raise HTTPException(404,'unknown tool')
        if not runtime['tools'].automatic(t):raise HTTPException(409,'tool requires interactive confirmation')
        return {'result':t.handler(req.parameters)}
    @r.post('/device/{device_id}/command')
    async def device_command(device_id:str,req:DeviceActionRequest,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        credentials(authorization,x_device_id);cmd=DeviceCommand(req.action,req.parameters,str(uuid.uuid4()))
        try:return await runtime['device_gateway'].request(device_id,cmd,max(1,min(req.timeout,60)))
        except Exception as e:raise HTTPException(409,str(e))
    return r
