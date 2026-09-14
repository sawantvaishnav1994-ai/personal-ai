from __future__ import annotations
import requests
from integrations.contracts import gmail_manifest, calendar_manifest, slack_manifest, home_assistant_manifest
from integrations.gateway import ConnectorError

class IntegrationError(RuntimeError):pass

class BearerREST:
    def __init__(self,base_url,token,timeout=30,*,gateway=None,connector_id=''):
        self.base_url=base_url.rstrip('/'); self.token=token; self.timeout=timeout; self.gateway=gateway; self.connector_id=connector_id
    def set_token(self,token):self.token=token
    def request(self,method,path,**kwargs):
        op=kwargs.pop('operation',None); operation_parameters=kwargs.pop('operation_parameters',{}); owner_id=kwargs.pop('owner_id','owner'); device_id=kwargs.pop('device_id',None); session_id=kwargs.pop('session_id',None); destination=kwargs.pop('destination',''); idempotency_key=kwargs.pop('idempotency_key',None)
        h={'Authorization':f'Bearer {self.token}','Accept':'application/json',**kwargs.pop('headers',{})}
        if self.gateway and op:
            return self.gateway.request(self,op,method,path,parameters=operation_parameters,headers=h,json_body=kwargs.pop('json',None),params=kwargs.pop('params',None),timeout=kwargs.pop('timeout',self.timeout),owner_id=owner_id,device_id=device_id,session_id=session_id,destination=destination,idempotency_key=idempotency_key)
        try:r=requests.request(method,f'{self.base_url}/{path.lstrip("/")}',headers=h,timeout=self.timeout,**kwargs)
        except requests.RequestException as exc:raise IntegrationError('provider unavailable') from exc
        if r.status_code>=400:raise IntegrationError(f'provider request failed with status {r.status_code}')
        return r.json() if r.content else {}

class GmailAdapter(BearerREST):
    manifest=gmail_manifest()
    def __init__(self,token,*,gateway=None):super().__init__('https://gmail.googleapis.com/gmail/v1',token,gateway=gateway,connector_id='gmail')
    def list_messages(self,q='',max_results=20,page_token=None,**ctx):
        params={'q':q,'maxResults':max(1,min(int(max_results),100))};
        if page_token:params['pageToken']=page_token
        return self.request('GET','users/me/messages',params=params,operation=self.manifest.operation('gmail.search' if q else 'gmail.read'),operation_parameters={'query':q,'max_results':max_results},**ctx)
    def search_messages(self,q,max_results=20,**ctx):return self.list_messages(q=q,max_results=max_results,**ctx)
    def get_message(self,message_id,format='metadata',**ctx):return self.request('GET',f'users/me/messages/{message_id}',params={'format':format},operation=self.manifest.operation('gmail.read'),operation_parameters={'message_id':message_id},**ctx)
    def send_raw(self,raw_base64url,**ctx):return self.request('POST','users/me/messages/send',json={'raw':raw_base64url},operation=self.manifest.operation('gmail.send'),operation_parameters={'raw_hash':__import__('hashlib').sha256(raw_base64url.encode()).hexdigest()},**ctx)
    def create_draft(self,raw_base64url,**ctx):return self.request('POST','users/me/drafts',json={'message':{'raw':raw_base64url}},operation=self.manifest.operation('gmail.draft'),operation_parameters={'raw_hash':__import__('hashlib').sha256(raw_base64url.encode()).hexdigest()},**ctx)
    def modify_message(self,message_id,add_labels=None,remove_labels=None,**ctx):return self.request('POST',f'users/me/messages/{message_id}/modify',json={'addLabelIds':add_labels or [],'removeLabelIds':remove_labels or []},operation=self.manifest.operation('gmail.modify'),operation_parameters={'message_id':message_id,'add':add_labels or [],'remove':remove_labels or []},**ctx)
    def delete_message(self,message_id,**ctx):raise PermissionError('Gmail delete is prohibited by default')
    def verify_message(self,message_id):
        try:return bool(self.get_message(message_id,format='minimal'))
        except Exception:return False

class GoogleCalendarAdapter(BearerREST):
    manifest=calendar_manifest()
    def __init__(self,token,*,gateway=None):super().__init__('https://www.googleapis.com/calendar/v3',token,gateway=gateway,connector_id='calendar')
    def list_events(self,calendar_id='primary',**params):
        ctx={k:params.pop(k) for k in list(params) if k in {'owner_id','device_id','session_id','destination','idempotency_key'}}
        return self.request('GET',f'calendars/{calendar_id}/events',params=params,operation=self.manifest.operation('calendar.search' if params.get('q') else 'calendar.read'),operation_parameters={'calendar_id':calendar_id,**params},destination=calendar_id,**ctx)
    def get_event(self,event_id,calendar_id='primary',**ctx):return self.request('GET',f'calendars/{calendar_id}/events/{event_id}',operation=self.manifest.operation('calendar.read'),operation_parameters={'calendar_id':calendar_id,'event_id':event_id},destination=calendar_id,**ctx)
    def create_event(self,event,calendar_id='primary',**ctx):return self.request('POST',f'calendars/{calendar_id}/events',json=event,operation=self.manifest.operation('calendar.create'),operation_parameters={'calendar_id':calendar_id,'event':event},destination=calendar_id,**ctx)
    def update_event(self,event_id,event,calendar_id='primary',**ctx):return self.request('PATCH',f'calendars/{calendar_id}/events/{event_id}',json=event,operation=self.manifest.operation('calendar.update'),operation_parameters={'calendar_id':calendar_id,'event_id':event_id,'event':event},destination=calendar_id,**ctx)
    def delete_event(self,event_id,calendar_id='primary',**ctx):return self.request('DELETE',f'calendars/{calendar_id}/events/{event_id}',operation=self.manifest.operation('calendar.delete'),operation_parameters={'calendar_id':calendar_id,'event_id':event_id},destination=calendar_id,**ctx)
    def verify_event(self,event_id,calendar_id='primary',expected=None):
        try:
            data=self.get_event(event_id,calendar_id)
            if expected:
                for k,v in expected.items():
                    if k in {'id','etag','updated'}:continue
                    if data.get(k)!=v:return False
            return True
        except Exception:return False

class SlackAdapter(BearerREST):
    manifest=slack_manifest()
    def __init__(self,token,*,gateway=None):super().__init__('https://slack.com/api',token,gateway=gateway,connector_id='slack')
    def _ok(self,data):
        if not data.get('ok'):raise IntegrationError('Slack rejected the request')
        return data
    def auth_test(self):return self._ok(self.request('POST','auth.test'))
    def history(self,channel,limit=50):return self._ok(self.request('GET','conversations.history',params={'channel':channel,'limit':limit}))
    def post_message(self,channel,text):return self._ok(self.request('POST','chat.postMessage',json={'channel':channel,'text':text}))
class HomeAssistantAdapter(BearerREST):
    manifest=home_assistant_manifest()
    def __init__(self,base_url,token,*,gateway=None):super().__init__(f'{base_url.rstrip("/")}/api',token,gateway=gateway,connector_id='home_assistant')
    def states(self):return self.request('GET','states')
    def state(self,entity_id):return self.request('GET',f'states/{entity_id}')
    def call_service(self,domain,service,data):return self.request('POST',f'services/{domain}/{service}',json=data)
