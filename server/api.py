from __future__ import annotations
from fastapi import FastAPI,HTTPException,Header,WebSocket,WebSocketDisconnect,Request
from pydantic import BaseModel
from core.security import PairingManager
class PairConfirm(BaseModel): token:str; code:str; name:str='Device'; platform:str='unknown'
class PairedCommand(BaseModel): text:str
def create_app(executor,settings,*,device_registry=None,device_gateway=None,second_brain=None,automations=None,runtime=None):
    app=FastAPI(title='Personal AI Local Control',docs_url=None,redoc_url=None); pairing=PairingManager(settings.pairing_ttl_seconds)
    def auth_device(authorization:str|None,device_id:str|None):
        if not device_registry or not device_id: raise HTTPException(401,'Device identity required')
        token=(authorization or '').removeprefix('Bearer ').strip()
        if not token or not device_registry.authenticate(device_id,token): raise HTTPException(401,'Unauthorized')
    def require_loopback(request:Request):
        host=request.client.host if request.client else ''
        if host not in {'127.0.0.1','::1'}: raise HTTPException(403,'Pairing initiation is local-only')
    @app.get('/health')
    def health():return {'ok':True,'service':'personal-ai','version':'v4'}
    @app.post('/pair/start')
    def pair_start(request:Request): require_loopback(request); offer=pairing.create(); return {'token':offer.token,'code':offer.code,'expires_at':offer.expires_at}
    @app.post('/pair/confirm')
    def pair_confirm(body:PairConfirm):
        if not pairing.consume(body.token,body.code):raise HTTPException(401,'Invalid or expired pairing offer')
        if not device_registry:raise HTTPException(503,'Device registry unavailable')
        device,bearer=device_registry.enroll(body.name,body.platform); return {'device':device,'bearer_token':bearer}
    @app.post('/command')
    def command(body:PairedCommand,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return {'reply':executor.chat(body.text)}
    @app.get('/memory/graph')
    def memory_graph(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return second_brain.graph() if second_brain else {'nodes':[],'edges':[]}
    @app.get('/memory/related/{memory_id}')
    def memory_related(memory_id:str,depth:int=2,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return second_brain.related(memory_id,max(1,min(depth,4))) if second_brain else {'nodes':[],'edges':[]}
    @app.get('/automations')
    def automation_list(authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)): auth_device(authorization,x_device_id); return automations.list() if automations else []
    @app.websocket('/device/ws/{device_id}')
    async def device_ws(ws:WebSocket,device_id:str):
        token=ws.headers.get('authorization','').removeprefix('Bearer ').strip()
        if not device_registry or not token or not device_registry.authenticate(device_id,token):await ws.close(code=4401); return
        await ws.accept()
        if device_gateway:device_gateway.connect(device_id,ws)
        try:
            while True: msg=await ws.receive_json(); await ws.send_json({'type':'ack','message_id':msg.get('message_id')})
        except WebSocketDisconnect:pass
        finally:
            if device_gateway:device_gateway.disconnect(device_id)
    if runtime:
        from dashboard.api import dashboard_router
        app.include_router(dashboard_router(runtime,auth_device))
    return app
