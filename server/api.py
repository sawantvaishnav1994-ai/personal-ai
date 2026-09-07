from __future__ import annotations
from fastapi import FastAPI,HTTPException,Header,WebSocket,WebSocketDisconnect,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel
from core.security import PairingManager
from cloud_runtime import CloudSessionStore,OwnerAuthenticator,SecureCloudRelay

class PairConfirm(BaseModel):token:str;code:str;name:str='Device';platform:str='unknown'
class PairedCommand(BaseModel):text:str
class SessionStart(BaseModel):device_id:str;device_token:str
class CloudCommand(BaseModel):text:str;nonce:str
class MemoryQuery(BaseModel):query:str='';include_sensitive:bool=False
class ApprovalDecision(BaseModel):approval_id:str;decision:str;nonce:str
class EmergencyStopBody(BaseModel):enabled:bool


def create_app(executor,settings,*,device_registry=None,device_gateway=None,second_brain=None,automations=None,runtime=None):
    app=FastAPI(title='Personal AI Control',docs_url=None,redoc_url=None);pairing=PairingManager(settings.pairing_ttl_seconds)
    cloud=None
    if getattr(settings,'cloud_runtime_enabled',False):
        if not runtime or not device_registry:raise RuntimeError('Cloud runtime requires the full Personal AI runtime and device registry')
        owner=OwnerAuthenticator(getattr(settings,'cloud_owner_secret',''))
        if not owner.configured:raise RuntimeError('CLOUD_RUNTIME_ENABLED requires PERSONAL_AI_CLOUD_OWNER_SECRET with at least 32 characters')
        origins=list(getattr(settings,'cloud_allowed_origins',()) or ())
        if not origins:raise RuntimeError('CLOUD_RUNTIME_ENABLED requires explicit CLOUD_ALLOWED_ORIGINS')
        if '*' in origins:raise RuntimeError('Wildcard cloud CORS origins are forbidden')
        app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type','X-Personal-AI-Nonce','X-Personal-AI-Owner-Key'])
        sessions=CloudSessionStore(settings.data_dir/'cloud-sessions.sqlite3',getattr(settings,'cloud_session_ttl_seconds',900))
        cloud=SecureCloudRelay(executor=executor,memory=runtime['memory'],second_brain=second_brain,device_registry=device_registry,sessions=sessions,owner=owner,events=runtime.get('events'))
        runtime['cloud_sessions']=sessions;runtime['cloud_relay']=cloud
    def auth_device(authorization,device_id):
        if not device_registry or not device_id:raise HTTPException(401,'Device identity required')
        token=(authorization or '').removeprefix('Bearer ').strip()
        if not token or not device_registry.authenticate(device_id,token):raise HTTPException(401,'Unauthorized')
    def require_loopback(request):
        host=request.client.host if request.client else ''
        if host not in {'127.0.0.1','::1'}:raise HTTPException(403,'Local-only operation')
    def bearer(value):return (value or '').removeprefix('Bearer ').strip()
    def require_cloud():
        if cloud is None:raise HTTPException(404,'Cloud runtime disabled')
        return cloud
    def cloud_auth(authorization,scope,nonce=None):
        relay=require_cloud();error,session=relay.authenticate(bearer(authorization),scope,nonce)
        if error:raise HTTPException(error.status,error.payload['error'])
        return relay,session
    def result(response):return JSONResponse(status_code=response.status,content=response.payload)

    @app.get('/health')
    def health():return {'ok':True,'service':'personal-ai','version':'v12','cloud_runtime':cloud is not None}
    @app.post('/pair/start')
    def pair_start(request:Request):require_loopback(request);o=pairing.create();return {'token':o.token,'code':o.code,'expires_at':o.expires_at}
    @app.post('/pair/confirm')
    def pair_confirm(body:PairConfirm):
        if not pairing.consume(body.token,body.code):raise HTTPException(401,'Invalid or expired pairing offer')
        if not device_registry:raise HTTPException(503,'Device registry unavailable')
        device,device_token=device_registry.enroll(body.name,body.platform);return {'device':device,'bearer_token':device_token}
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

    @app.post('/cloud/session')
    def cloud_session(body:SessionStart):return result(require_cloud().issue_session(body.device_id,body.device_token))
    @app.post('/cloud/session/revoke')
    def cloud_revoke(authorization:str|None=Header(default=None)):
        relay,session=cloud_auth(authorization,'status:read');return result(relay.revoke_session(session.id,session.device_id))
    @app.post('/cloud/command')
    def cloud_command(body:CloudCommand,authorization:str|None=Header(default=None)):
        relay,session=cloud_auth(authorization,'ai:chat',body.nonce);return result(relay.command(session,body.text,body.nonce))
    @app.post('/cloud/memory/search')
    def cloud_memory(body:MemoryQuery,authorization:str|None=Header(default=None)):
        relay,session=cloud_auth(authorization,'memory:read');return result(relay.memory_search(session,body.query,body.include_sensitive))
    @app.get('/cloud/status')
    def cloud_status(authorization:str|None=Header(default=None)):
        relay,session=cloud_auth(authorization,'status:read');return result(relay.status(session))
    @app.post('/cloud/approval')
    def cloud_approval(body:ApprovalDecision,authorization:str|None=Header(default=None)):
        relay,session=cloud_auth(authorization,'approval:write',body.nonce);return result(relay.approval(session,body.approval_id,body.decision))
    @app.post('/cloud/emergency-stop')
    def cloud_emergency_stop(body:EmergencyStopBody,x_personal_ai_owner_key:str|None=Header(default=None)):
        return result(require_cloud().set_emergency_stop(x_personal_ai_owner_key or '',body.enabled))

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
