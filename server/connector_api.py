from __future__ import annotations
from fastapi import APIRouter,Cookie,HTTPException
from pydantic import BaseModel,Field
from security.request_context import current_trusted_request
from integrations.gateway import ConnectorError

class OAuthStartBody(BaseModel):
    scopes:list[str]=Field(default_factory=list,max_length=30)
    intent:str='connect'
class OAuthCompleteBody(BaseModel):
    state:str=Field(min_length=16,max_length=4096)
    code:str=Field(min_length=1,max_length=8192)

def connector_router(runtime):
    router=APIRouter(prefix='/iphone/api/connectors',tags=['connectors']); devices=runtime['device_registry']; integrations=runtime['integrations']; oauth=runtime.get('oauth'); providers=runtime.get('oauth_providers') or {}
    def auth(device_id,token,scope):
        if not device_id or not token or not devices.authenticate(device_id,token):raise HTTPException(401,'This browser is not trusted or its session was revoked')
        if hasattr(devices,'authorize') and not devices.authorize(device_id,scope):raise HTTPException(403,f'This device is not permitted to use {scope}')
        ctx=current_trusted_request()
        if ctx is None or ctx.device_id!=device_id:raise HTTPException(401,'An authenticated browser session is required')
        return ctx
    def item(connector_id):
        found=next((x for x in integrations.list() if x['id']==connector_id),None)
        if not found:raise HTTPException(404,'Connector not found')
        return found
    @router.get('')
    def list_connectors(pa_device:str|None=Cookie(default=None),pa_token:str|None=Cookie(default=None)):
        auth(pa_device,pa_token,'device:read'); return {'connectors':integrations.list()}
    @router.get('/{connector_id}')
    def get_connector(connector_id:str,pa_device:str|None=Cookie(default=None),pa_token:str|None=Cookie(default=None)):
        auth(pa_device,pa_token,'device:read'); return item(connector_id)
    @router.post('/{connector_id}/oauth/start')
    def oauth_start(connector_id:str,body:OAuthStartBody,pa_device:str|None=Cookie(default=None),pa_token:str|None=Cookie(default=None)):
        ctx=auth(pa_device,pa_token,'device:admin'); info=item(connector_id)
        if not oauth or info.get('auth_type')!='oauth2_pkce':raise HTTPException(409,'This connector is not configured for OAuth')
        provider=providers.get(info['provider'])
        if provider is None:raise HTTPException(409,'OAuth client configuration is not available for this connector')
        manifest=integrations.manifests.get(connector_id); requested=body.scopes or list(manifest.required_oauth_scopes)
        allowed=set(manifest.required_oauth_scopes)|set(manifest.optional_oauth_scopes)
        if not set(requested).issubset(allowed):raise HTTPException(422,'One or more requested OAuth scopes are not allowed by the connector manifest')
        try:return oauth.begin(provider,owner_id='owner',device_id=pa_device,session_id=ctx.session_id,connector_id=connector_id,scopes=requested,security_epoch=runtime['executor'].approvals.current_security_epoch(),relink_intent=body.intent)
        except (ValueError,PermissionError) as exc:raise HTTPException(422,str(exc)) from exc
    @router.post('/{connector_id}/oauth/complete')
    def oauth_complete(connector_id:str,body:OAuthCompleteBody,pa_device:str|None=Cookie(default=None),pa_token:str|None=Cookie(default=None)):
        ctx=auth(pa_device,pa_token,'device:admin'); info=item(connector_id); provider=providers.get(info['provider'])
        if not oauth or not provider:raise HTTPException(409,'OAuth client configuration is not available for this connector')
        try:return oauth.complete(body.state,body.code,provider,owner_id='owner',device_id=pa_device,session_id=ctx.session_id,connector_id=connector_id,security_epoch=runtime['executor'].approvals.current_security_epoch())
        except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        except Exception as exc:raise HTTPException(502,'The provider could not complete account connection') from exc
    @router.post('/{connector_id}/revoke')
    def revoke(connector_id:str,pa_device:str|None=Cookie(default=None),pa_token:str|None=Cookie(default=None)):
        ctx=auth(pa_device,pa_token,'device:admin'); info=item(connector_id)
        if not oauth:raise HTTPException(409,'Connector credential management is unavailable')
        provider=providers.get(info['provider'])
        try:return oauth.unlink(info['provider'],provider=provider,connector_id=connector_id,owner_id='owner',device_id=pa_device,session_id=ctx.session_id,attempt_provider_revocation=True)
        except Exception as exc:raise HTTPException(502,'Local access was revoked but provider confirmation could not be completed') from exc
    return router
