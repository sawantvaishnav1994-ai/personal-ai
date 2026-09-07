from __future__ import annotations
from fastapi import FastAPI,HTTPException,Header,WebSocket,WebSocketDisconnect,Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from core.security import PairingManager
class PairConfirm(BaseModel):token:str;code:str;name:str='Device';platform:str='unknown'
class PairedCommand(BaseModel):text:str
def create_app(executor,settings,*,device_registry=None,device_gateway=None,second_brain=None,automations=None,runtime=None):
    app=FastAPI(title='Personal AI Local Control',docs_url=None,redoc_url=None);pairing=PairingManager(settings.pairing_ttl_seconds)
    def auth_device(authorization,device_id):
        if not device_registry or not device_id:raise HTTPException(401,'Device identity required')
        token=(authorization or '').removeprefix('Bearer ').strip()
        if not token or not device_registry.authenticate(device_id,token):raise HTTPException(401,'Unauthorized')
    def require_loopback(request):
        host=request.client.host if request.client else ''
        if host not in {'127.0.0.1','::1'}:raise HTTPException(403,'Local-only operation')
    @app.get('/health')
    def health():return {'ok':True,'service':'personal-ai','version':'v9'}
    @app.post('/pair/start')
    def pair_start(request:Request):require_loopback(request);o=pairing.create();return {'token':o.token,'code':o.code,'expires_at':o.expires_at}
    @app.post('/pair/confirm')
    def pair_confirm(body:PairConfirm):
        if not pairing.consume(body.token,body.code):raise HTTPException(401,'Invalid or expired pairing offer')
        if not device_registry:raise HTTPException(503,'Device registry unavailable')
        device,bearer=device_registry.enroll(body.name,body.platform);return {'device':device,'bearer_token':bearer}
    @app.get('/oauth/start/{provider_id}')
    def oauth_start(provider_id:str,request:Request):
        require_loopback(request)
        if not runtime or provider_id not in runtime.get('oauth_providers',{}):raise HTTPException(404,'OAuth provider not configured')
        return runtime['oauth'].begin(runtime['oauth_providers'][provider_id])
    @app.get('/oauth/callback')
    def oauth_callback(state:str,code:str,request:Request):
        require_loopback(request)
        if not runtime or not runtime.get('oauth'):raise HTTPException(503,'OAuth unavailable')
        runtime['oauth'].complete(state,code);return HTMLResponse('<h2>Personal AI account linked. You can close this window.</h2>')
    @app.post('/command')
    def command(body:PairedCommand,authorization:str|None=Header(default=None),x_device_id:str|None=Header(default=None)):auth_device(authorization,x_device_id);return {'reply':executor.chat(body.text)}
    @app.websocket('/device/ws/{device_id}')
    async def device_ws(ws:WebSocket,device_id:str):
        token=ws.headers.get('authorization','').removeprefix('Bearer ').strip()
        if not device_registry or not token or not device_registry.authenticate(device_id,token):await ws.close(code=4401);return
        await ws.accept();device_gateway.connect(device_id,ws) if device_gateway else None
        try:
            while True:
                msg=await ws.receive_json()
                if msg.get('type')=='push_registration' and msg.get('provider')=='apns' and msg.get('token'):
                    device_registry.set_metadata(device_id,'push.apns.token',str(msg['token']).strip())
                    if msg.get('environment'):device_registry.set_metadata(device_id,'push.apns.environment',str(msg['environment']).strip().lower())
                if device_gateway:device_gateway.receive(device_id,msg)
                if msg.get('type') not in {'result'}:await ws.send_json({'type':'ack','message_id':msg.get('message_id')})
        except WebSocketDisconnect:pass
        finally:
            if device_gateway:device_gateway.disconnect(device_id)
    if runtime:
        from dashboard.api import dashboard_router
        from dashboard.web import dashboard_html
        app.include_router(dashboard_router(runtime,auth_device))
        @app.get('/dashboard-ui',include_in_schema=False)
        def dashboard_ui(request:Request):require_loopback(request);return dashboard_html()
    return app
