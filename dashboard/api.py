from __future__ import annotations
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
class ActionRequest(BaseModel): tool:str; parameters:dict=Field(default_factory=dict)
def dashboard_router(runtime,auth_device):
    r=APIRouter(prefix='/dashboard',tags=['dashboard'])
    @r.get('/status')
    def status(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        auth_device(authorization,x_device_id); return {'automations':len(runtime['automations'].list()),'devices':len(runtime['device_registry'].list()),'integrations':runtime.get('integrations').list() if runtime.get('integrations') else [],'memory_nodes':len(runtime['second_brain'].graph().get('nodes',[]))}
    @r.get('/devices')
    def devices(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return runtime['device_registry'].list()
    @r.get('/automations')
    def automations(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return runtime['automations'].list()
    @r.get('/memory')
    def memory(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return runtime['second_brain'].graph()
    @r.post('/tool')
    def tool(req:ActionRequest,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):
        auth_device(authorization,x_device_id)
        try:t=runtime['tools'].get(req.tool)
        except Exception: raise HTTPException(404,'unknown tool')
        if not runtime['tools'].automatic(t): raise HTTPException(409,'tool requires interactive confirmation')
        return {'result':t.handler(req.parameters)}
    return r
