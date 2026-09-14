from __future__ import annotations

import hashlib, json, random, time
from dataclasses import dataclass
from typing import Any, Callable
import requests

from integrations.contracts import ConnectorOperation

@dataclass
class ConnectorError(RuntimeError):
    code: str
    safe_message: str
    health_state: str = 'degraded'
    http_status: int = 502
    retryable: bool = False
    retry_after: float | None = None
    def __post_init__(self): RuntimeError.__init__(self,self.safe_message)
    def safe_dict(self): return {'code':self.code,'message':self.safe_message,'state':self.health_state,'retryable':self.retryable}

class ConnectorRecoveryRequired(ConnectorError):
    def __init__(self,message='The provider outcome is uncertain. Review recovery before retrying.'):
        super().__init__('connector_recovery_required',message,'verification_failed',409,False)

def parameter_hash(parameters: dict[str,Any]):
    return hashlib.sha256(json.dumps(parameters or {},sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

class ConnectorGateway:
    def __init__(self,state_store,*,session=None,sleep=time.sleep,random_fn=random.random):
        self.state=state_store; self.session=session or requests.Session(); self.sleep=sleep; self.random_fn=random_fn
    @staticmethod
    def _response_error(response):
        code=int(response.status_code)
        if code==401:return ConnectorError('authentication_required','The connector needs to be reconnected.','authentication_expired',401,False)
        if code==403:return ConnectorError('permission_denied','The connected account does not have permission for this action.','insufficient_scope',403,False)
        if code==429:
            raw=response.headers.get('Retry-After','') if hasattr(response,'headers') else ''
            try:after=max(0.0,float(raw))
            except Exception:after=None
            return ConnectorError('rate_limited','The provider is temporarily rate limiting requests.','rate_limited',429,True,after)
        if code>=500:return ConnectorError('provider_unavailable','The provider is temporarily unavailable.','provider_unavailable',503,True)
        return ConnectorError('provider_error','The provider rejected the request.','degraded',400,False)
    def request(self,adapter,operation:ConnectorOperation,method,path,*,parameters=None,headers=None,json_body=None,params=None,timeout=30,cancelled:Callable[[],bool]|None=None,deadline:float|None=None,owner_id='owner',device_id=None,session_id=None,destination='',idempotency_key=None):
        parameters=dict(parameters or {}); ph=parameter_hash(parameters)
        consequential=operation.effect in {'write','consequential','destructive'}
        ledger=None
        if consequential:
            ledger,created=self.state.propose_operation(owner_id=owner_id,device_id=device_id,session_id=session_id,connector_id=operation.name.split('.',1)[0],operation_name=operation.name,parameter_hash=ph,destination=destination,idempotency_key=idempotency_key,rollback_available=operation.rollback_available)
            if not created:
                state=ledger['state']
                if state in {'verified','confirmed'}: return ledger.get('result') or json.loads(ledger.get('result_json') or '{}')
                raise ConnectorRecoveryRequired('A matching connector operation already exists and must be reviewed before redispatch.')
            self.state.transition_operation(ledger['operation_id'],'approved')
        max_attempts=operation.retry.max_attempts if (not consequential or operation.idempotency_supported) else 1
        for attempt in range(1,max_attempts+1):
            if cancelled and cancelled():
                if ledger:self.state.transition_operation(ledger['operation_id'],'failed',retry_decision='cancelled')
                raise ConnectorError('cancelled','The connector action was cancelled.','degraded',409,False)
            if deadline is not None and time.time()>=deadline:
                if ledger:self.state.transition_operation(ledger['operation_id'],'failed',retry_decision='deadline')
                raise ConnectorError('deadline_exceeded','The connector action exceeded its execution deadline.','timeout',408,False)
            if ledger:
                self.state.transition_operation(ledger['operation_id'],'dispatched',retry_decision=f'attempt:{attempt}')
                self.state.audit('operation.dispatched',connector_id=operation.name.split('.',1)[0],owner_id=owner_id,device_id=device_id,session_id=session_id,correlation_id=ledger['operation_id'],payload={'operation':operation.name,'attempt':attempt,'destination':destination})
            try:
                response=self.session.request(method,adapter.base_url.rstrip('/')+'/'+path.lstrip('/'),headers=headers,params=params,json=json_body,timeout=timeout)
            except requests.Timeout as exc:
                self.state.set_health(operation.name.split('.',1)[0],'timeout',error_code='timeout',error_message='Provider request timed out')
                if consequential and not operation.idempotency_supported:
                    if ledger:self.state.transition_operation(ledger['operation_id'],'recovery_review_required',verification_state='outcome_unknown',retry_decision='no_blind_retry')
                    self.state.audit('operation.outcome_unknown',connector_id=operation.name.split('.',1)[0],owner_id=owner_id,device_id=device_id,session_id=session_id,correlation_id=ledger['operation_id'],payload={'operation':operation.name,'decision':'recovery_review_required'})
                    raise ConnectorRecoveryRequired() from exc
                error=ConnectorError('timeout','The provider did not respond in time.','timeout',504,True)
            except requests.RequestException as exc:
                error=ConnectorError('network_error','The provider could not be reached.','provider_unavailable',503,True)
            else:
                if response.status_code>=400:error=self._response_error(response)
                else:
                    if not response.content: data={}
                    else:
                        try:data=response.json()
                        except Exception as exc:
                            if ledger:self.state.transition_operation(ledger['operation_id'],'failed',verification_state='invalid_response')
                            self.state.set_health(operation.name.split('.',1)[0],'invalid_response',error_code='invalid_response',error_message='Provider returned an invalid response')
                            raise ConnectorError('invalid_response','The provider returned an invalid response.','invalid_response',502,False) from exc
                    connector=operation.name.split('.',1)[0]; self.state.set_health(connector,'healthy',success=True)
                    if ledger:
                        rid=''
                        if isinstance(data,dict): rid=str(data.get('id') or data.get('messageId') or '')
                        data=dict(data); data['_personal_ai_operation_id']=ledger['operation_id']; self.state.audit('operation.confirmed',connector_id=connector,owner_id=owner_id,device_id=device_id,session_id=session_id,correlation_id=ledger['operation_id'],payload={'operation':operation.name,'provider_resource_id':rid}); self.state.transition_operation(ledger['operation_id'],'verification_pending',provider_resource_id=rid or None,result=data)
                    return data
            self.state.set_health(operation.name.split('.',1)[0],error.health_state,error_code=error.code,error_message=error.safe_message)
            if attempt>=max_attempts or not error.retryable:
                if ledger:self.state.transition_operation(ledger['operation_id'],'failed',retry_decision='retry_exhausted' if error.retryable else 'permanent_failure')
                raise error
            delay=error.retry_after if error.retry_after is not None and operation.rate_limit.respects_retry_after else min(operation.retry.max_delay_seconds,operation.retry.base_delay_seconds*(2**(attempt-1)))
            delay=min(float(delay),float(operation.rate_limit.max_retry_after_seconds));
            if operation.retry.jitter: delay*=0.75+0.5*self.random_fn()
            if deadline is not None and time.time()+delay>=deadline: raise ConnectorError('deadline_exceeded','The connector action cannot retry before its deadline.','timeout',408,False)
            self.sleep(delay)
        raise ConnectorError('connector_failed','The connector action failed.','degraded',502,False)
    def paginate(self,fetch_page:Callable[[str|None],dict],operation:ConnectorOperation,*,cancelled=None,deadline=None):
        policy=operation.pagination
        if not policy.supported:return fetch_page(None)
        cursor=None; seen=set(); items=[]; pages=0
        while pages<policy.max_pages and len(items)<policy.max_items:
            if cancelled and cancelled(): raise ConnectorError('cancelled','Pagination was cancelled.','degraded',409,False)
            if deadline and time.time()>=deadline: raise ConnectorError('deadline_exceeded','Pagination exceeded its deadline.','timeout',408,False)
            page=fetch_page(cursor)
            if not isinstance(page,dict): raise ConnectorError('invalid_response','The provider returned an invalid page.','invalid_response',502,False)
            batch=page.get('items') or page.get('messages') or []
            if not isinstance(batch,list): raise ConnectorError('invalid_response','The provider returned invalid paginated items.','invalid_response',502,False)
            items.extend(batch[:max(0,policy.max_items-len(items))]); pages+=1
            nxt=page.get(policy.cursor_field)
            if not nxt: break
            nxt=str(nxt)
            if len(nxt)>4096: raise ConnectorError('invalid_cursor','The provider returned an invalid continuation cursor.','invalid_response',502,False)
            if nxt in seen: raise ConnectorError('cursor_cycle','The provider repeated a continuation cursor.','invalid_response',502,False)
            seen.add(nxt); cursor=nxt
        return {'items':items,'next_cursor':cursor if pages>=policy.max_pages else None,'pages':pages}
