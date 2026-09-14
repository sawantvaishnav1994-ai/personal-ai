from __future__ import annotations

from dataclasses import dataclass, field
import hashlib, json, re, time
from typing import Any, Callable

from browser.observation import observe_page
from desktop.operator_transactions import OperatorBinding, OperatorTransactionStore
from security.policy_gateway import DecisionKind, PolicyGateway, PolicyOperation
from security.policy_targets import TargetValidationError, normalize_origin, validate_file_metadata

INJECTION_RE = re.compile(r'ignore .*instructions|system message|grant .*permission|reveal .*secret|override .*policy|disable .*security', re.I)
SECRET_FIELD_RE = re.compile(r'password|passwd|secret|token|otp|passcode|pin|cvv|cvc|cc-number|cc-csc|private-key|api-key', re.I)
CONSEQUENTIAL = {'form_submission','email_send','message_send','purchase','financial_transfer','public_publish','share','delete','destructive_delete','security_setting_modify','permission_change','legal_acceptance'}
BLOCKED_UNLESS_EXPLICIT = CONSEQUENTIAL - {'form_submission'}


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class BrowserAction:
    kind: str
    transaction_id: str
    sequence: int = 0
    target_id: str = ''
    url: str = ''
    value: str = ''
    option: str = ''
    tab_index: int | None = None
    amount: int = 0
    expected_text: str = ''
    timeout_ms: int = 10000
    data_classification: str = 'public'
    operation_class: str = ''
    upload_path: str = ''
    claimed_mime: str = ''
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserResult:
    status: str
    reason_code: str
    transaction_id: str
    before_observation_id: str = ''
    after_observation_id: str = ''
    result: dict[str, Any] = field(default_factory=dict)


class SafeBrowserOperator:
    """Single W7.4 execution path combining W7.1, W7.2 and W7.3 authorities."""

    def __init__(self, browser, policy: PolicyGateway, transactions: OperatorTransactionStore,
                 binding: OperatorBinding, emergency_stop: Callable[[], bool] | None = None):
        self.browser, self.policy, self.transactions, self.binding = browser, policy, transactions, binding
        self.emergency_stop = emergency_stop or (lambda: False)

    def extract_visible_content(self, max_chars: int = 20000) -> dict[str, Any]:
        obs = self._observe(); text = str(obs.get('visible_text') or '')[:min(max(max_chars,0),20000)]
        return {'content_trust':'untrusted_web_content','prompt_injection_detected':bool(INJECTION_RE.search(text)),
                'text':text,'origin':obs.get('origin',''),'normalized_url':obs.get('normalized_url',''),'tab_id':obs.get('tab_id','')}

    def find_visible(self, text: str = '', role: str = '', tag: str = '') -> list[dict[str, Any]]:
        out=[]
        for e in self._observe().get('elements') or []:
            if not e.get('actionable'): continue
            hay=' '.join(str(e.get(k) or '') for k in ('text','label','placeholder')).casefold()
            if text and text.casefold() not in hay: continue
            if role and str(e.get('role') or '').casefold()!=role.casefold(): continue
            if tag and str(e.get('tag') or '').casefold()!=tag.casefold(): continue
            out.append({'target_id':e['target_id'],'tag':e.get('tag',''),'role':e.get('role',''),'text':str(e.get('text') or '')[:300]})
        return out[:50]

    def execute(self, action: BrowserAction, *, approved: bool=False, reauthenticated: bool=False) -> BrowserResult:
        self._validate(action); tx=self._ensure_tx(action)
        if tx.get('cancel_requested'): return self._cancel(action,'cancelled')
        if self.emergency_stop(): return self._cancel(action,'emergency_stop_active')

        first=self._capture(action,'policy_evaluation'); op_class=self._classify(action,first['raw'])
        if op_class in BLOCKED_UNLESS_EXPLICIT and action.operation_class!=op_class:
            return self._deny(action,first,'approval_required')

        ops=self._policy_ops(action,first,op_class)
        decisions=[]
        for op in ops:
            d=self.policy.evaluate(op,approved=approved,reauthenticated=reauthenticated); decisions.append((op,d))
            if d.decision is DecisionKind.REAUTHENTICATION_REQUIRED:
                self._approval_state(action.transaction_id); return self._result(action,'reauthentication_required',d.reason_code,first)
            if d.decision is DecisionKind.APPROVAL_REQUIRED:
                self._approval_state(action.transaction_id); return self._result(action,'approval_required',d.reason_code,first)
            if d.decision is DecisionKind.RECOVERY_REVIEW_REQUIRED:
                self._recovery(action.transaction_id,d.reason_code); return self._result(action,'recovery_review_required',d.reason_code,first)
            if d.decision is not DecisionKind.ALLOW: return self._deny(action,first,d.reason_code)

        self._permit_state(action.transaction_id)
        fresh=self._capture(action,'pre_dispatch'); self._assert_fresh(first['raw'],fresh['raw'],action)
        if self.emergency_stop(): return self._deny(action,fresh,'emergency_stop_active')
        self.transactions.assert_dispatchable(action.transaction_id,self.binding)

        permits=[]
        for old_op,old_decision in decisions:
            op=self._bind_observation(old_op,fresh)
            d=self.policy.evaluate(op,approved=approved,reauthenticated=reauthenticated,expected_policy_digest=old_decision.policy_digest)
            if d.decision is not DecisionKind.ALLOW: return self._deny(action,fresh,d.reason_code)
            permit=self.policy.issue_temporary_permit(op,d,ttl_seconds=120)
            if not self.policy.consume_temporary_permit(permit['permit_id'],op,d): return self._deny(action,fresh,'policy_changed')
            permits.append(permit)

        target=self._target(fresh['raw'],action.target_id) if action.target_id else None
        self.transactions.transition(action.transaction_id,'executing')
        row,created=self.transactions.start_action(action.transaction_id,action.sequence,kind=action.kind,
            parameter_hash=digest(self._safe_params(action)),expected_postcondition=self._expected(action,op_class),
            before_observation_id=fresh['observation_id'],target_identity=(target or {}).get('target_id',''),
            plan_digest=digest({'kind':action.kind,'target':action.target_id,'url':action.url,'class':op_class}),observation_digest=fresh['digest'])
        if not created:
            self._recovery(action.transaction_id,'duplicate_dispatch_uncertain')
            return self._result(action,'recovery_review_required','recovery_review_required',fresh)

        try: raw=self._dispatch(action,fresh['raw'])
        except Exception:
            if op_class in CONSEQUENTIAL:
                for p in permits: self.policy.mark_unknown_outcome(p['permit_id'],'browser_dispatch_exception')
                self._recovery(action.transaction_id,'browser_dispatch_exception')
                return self._result(action,'recovery_review_required','recovery_review_required',fresh)
            self.transactions.finish_action(row['action_id'],verified=False,error_code='browser_dispatch_failed')
            self.transactions.transition(action.transaction_id,'failed',error_code='browser_dispatch_failed')
            return self._result(action,'failed','verification_failed',fresh)

        self.transactions.transition(action.transaction_id,'verifying'); after=self._capture(action,'postcondition_verification')
        ok,reason=self._verify(action,fresh['raw'],after['raw'],raw)
        self.transactions.finish_action(row['action_id'],verified=ok,evidence={'postcondition':reason},error_code='' if ok else reason,after_observation_id=after['observation_id'])
        if not ok:
            if op_class in CONSEQUENTIAL:
                self._recovery(action.transaction_id,reason); return self._result(action,'recovery_review_required','recovery_review_required',fresh,after)
            self.transactions.transition(action.transaction_id,'failed',error_code=reason); return self._result(action,'failed','verification_failed',fresh,after)
        self.transactions.transition(action.transaction_id,'completed')
        return self._result(action,'completed','allow',fresh,after,{'origin':after['raw'].get('origin',''),'url':after['raw'].get('normalized_url',''),'tab_id':after['raw'].get('tab_id','')})

    def _observe(self): self.browser.start(); return observe_page(self.browser.page)

    def _capture(self, action, reason):
        obs=self._observe(); now=time.time(); d=digest({'ctx':obs.get('browser_context_id'),'tab':obs.get('tab_id'),'origin':obs.get('origin'),'url':obs.get('normalized_url'),'dom':obs.get('dom_sha256'),'a11y':obs.get('accessibility_sha256'),'act':obs.get('actionable_digest'),'frames':obs.get('frame_origins_digest')})
        oid=f'w74-{d[:20]}-{int(now*1000)}'
        self.transactions.save_observation({'observation_id':oid,'transaction_id':action.transaction_id,'owner_id':self.binding.owner_id,'device_id':self.binding.device_id,'session_id':self.binding.session_id,'security_epoch':self.binding.security_epoch,'application_identity':'browser:chromium','application_name':'Chromium','process_identity':obs.get('browser_context_id') or 'browser-context-unavailable','window_identity':obs.get('tab_id') or 'browser-tab-unavailable','browser_context_identity':obs.get('browser_context_id',''),'browser_tab_identity':obs.get('tab_id',''),'browser_origin':obs.get('origin',''),'normalized_url':obs.get('normalized_url',''),'captured_at':now,'expires_at':now+120,'screenshot_evidence_ref':'visual_evidence_unavailable','screen_fingerprint':digest({'dom':obs.get('dom_sha256'),'a11y':obs.get('accessibility_sha256'),'act':obs.get('actionable_digest')}),'sanitized_dom_digest':obs.get('dom_sha256',''),'accessibility_tree_digest':obs.get('accessibility_sha256',''),'actionable_element_digest':obs.get('actionable_digest',''),'frame_origins_digest':obs.get('frame_origins_digest',''),'active_target_id':obs.get('active_target_id',''),'sensitivity':{'sensitive_region_count':obs.get('sensitive_region_count',0)},'capture_reason':reason,'capture_initiator':'w7.4_safe_browser_operator','observation_digest':d})
        return {'observation_id':oid,'digest':d,'raw':obs}

    def _ensure_tx(self,a):
        tx=self.transactions.transaction(a.transaction_id); plan={'steps':[{'sequence':a.sequence,'kind':a.kind,'target_id':a.target_id,'url':a.url,'operation_class':a.operation_class}]}
        if tx is None: tx,_=self.transactions.propose(a.transaction_id,self.binding,goal=f'W7.4 browser action: {a.kind}',action_plan=plan)
        else: self.transactions.assert_binding(a.transaction_id,self.binding)
        if tx['state']=='proposed': tx=self.transactions.transition(a.transaction_id,'policy_check')
        return tx

    def _approval_state(self,txid):
        tx=self.transactions.transaction(txid)
        if tx and tx['state']=='policy_check': self.transactions.transition(txid,'approval_required')

    def _permit_state(self,txid):
        tx=self.transactions.transaction(txid)
        if tx['state'] in {'policy_check','approval_required'}: self.transactions.transition(txid,'permitted')
        elif tx['state']!='permitted': raise RuntimeError(f'invalid browser transaction state {tx["state"]}')

    def _policy_ops(self,a,obs,op_class):
        url=a.url or obs['normalized_url']; ops=[PolicyOperation(op_class,self.binding.owner_id,self.binding.device_id,self.binding.session_id,self.binding.security_epoch,'domain',{'url':url},None,url,self._safe_params(a),a.data_classification)]
        if a.upload_path:
            validate_file_metadata(a.upload_path,claimed_mime=a.claimed_mime,max_bytes=int(a.parameters.get('max_bytes') or 50*1024*1024))
            ops.append(PolicyOperation('external_upload',self.binding.owner_id,self.binding.device_id,self.binding.session_id,self.binding.security_epoch,'path',{'path':a.upload_path,'approved_roots':list(a.parameters.get('approved_roots') or []),'file_for_validation':a.upload_path,'claimed_mime':a.claimed_mime,'max_bytes':int(a.parameters.get('max_bytes') or 50*1024*1024)},None,a.upload_path,{'file_digest':self._file_digest(a.upload_path)},a.data_classification))
        return ops

    def _bind_observation(self,op,c):
        return PolicyOperation(op.operation,op.owner_id,op.device_id,op.session_id,op.security_epoch,op.target_type,op.target_identity,op.application,op.destination,op.parameters,op.data_classification,c['observation_id'],c['digest'],op.outcome_state)

    def _classify(self,a,obs):
        if a.operation_class:return a.operation_class
        if a.upload_path:return 'external_upload'
        if a.kind in {'open_url','back','forward','refresh','create_tab','select_tab','close_tab'}:return 'navigate'
        if a.kind=='click':
            t=self._target(obs,a.target_id) or {}; s=' '.join(str(t.get(k) or '') for k in ('text','label','name')).casefold()
            if str(t.get('type') or '').casefold()=='submit' or any(x in s for x in ('submit','send','publish','buy','purchase','pay','delete','accept terms','agree')):return 'form_submission'
        return 'application_input' if a.kind in {'click','type','select','check','uncheck'} else 'read'

    def _assert_fresh(self,old,new,a):
        if old.get('browser_context_id')!=new.get('browser_context_id') or old.get('tab_id')!=new.get('tab_id'):raise PermissionError('browser session or tab changed')
        if a.kind not in {'open_url','back','forward','refresh','create_tab','select_tab'} and (old.get('origin')!=new.get('origin') or old.get('normalized_url')!=new.get('normalized_url')):raise PermissionError('browser page changed')
        if a.target_id:
            x,y=self._target(old,a.target_id),self._target(new,a.target_id)
            if not x or not y or not y.get('actionable') or x.get('geometry_digest')!=y.get('geometry_digest'):raise PermissionError('browser target changed')

    def _dispatch(self,a,obs):
        self.browser.start(); p=self.browser.page
        if a.kind=='open_url':p.goto(a.url,wait_until='domcontentloaded',timeout=a.timeout_ms);return {'url':p.url}
        if a.kind=='back':p.go_back(wait_until='domcontentloaded',timeout=a.timeout_ms);return {'url':p.url}
        if a.kind=='forward':p.go_forward(wait_until='domcontentloaded',timeout=a.timeout_ms);return {'url':p.url}
        if a.kind=='refresh':p.reload(wait_until='domcontentloaded',timeout=a.timeout_ms);return {'url':p.url}
        if a.kind=='create_tab':self.browser.page=self.browser.context.new_page();self.browser.page.goto(a.url,wait_until='domcontentloaded',timeout=a.timeout_ms);return {'url':self.browser.page.url}
        if a.kind=='select_tab':pages=list(self.browser.context.pages);idx=int(a.tab_index if a.tab_index is not None else -1);self.browser.page=pages[idx];self.browser.page.bring_to_front();return {'url':self.browser.page.url}
        if a.kind=='close_tab':
            if len(self.browser.context.pages)<=1:raise RuntimeError('refusing to close only tab')
            p.close();self.browser.page=self.browser.context.pages[0];return {'url':self.browser.page.url}
        if a.kind=='scroll':p.mouse.wheel(0,int(a.amount));return {'scrolled':a.amount}
        if a.kind=='wait_for':
            end=time.monotonic()+a.timeout_ms/1000
            while time.monotonic()<end:
                if a.expected_text in str(observe_page(p).get('visible_text') or ''):return {'condition_met':True}
                time.sleep(.05)
            raise TimeoutError('bounded wait expired')
        t=self._target(obs,a.target_id)
        if not t or not t.get('actionable') or t.get('sensitive') or SECRET_FIELD_RE.search(' '.join(str(t.get(k) or '') for k in ('type','name','label','placeholder'))):raise PermissionError('protected or changed target')
        path=str(t.get('path') or '');loc=p.locator(path)
        if not path or int(loc.count())!=1:raise PermissionError('ambiguous or detached target')
        if a.kind=='click':loc.click(timeout=a.timeout_ms);return {'clicked':True}
        if a.kind=='type':loc.fill(a.value,timeout=a.timeout_ms);return {'typed':True}
        if a.kind=='select':loc.select_option(label=a.option,timeout=a.timeout_ms);return {'selected':True}
        if a.kind=='check':loc.check(timeout=a.timeout_ms);return {'checked':True}
        if a.kind=='uncheck':loc.uncheck(timeout=a.timeout_ms);return {'unchecked':True}
        raise ValueError('unsupported action')

    def _verify(self,a,before,after,raw):
        if before.get('browser_context_id')!=after.get('browser_context_id'):return False,'browser_session_changed'
        if a.kind in {'open_url','create_tab'}:
            try: expected,actual=normalize_origin(a.url),normalize_origin(after.get('normalized_url') or after.get('origin') or '')
            except TargetValidationError:return False,'redirect_not_allowed'
            if expected['scheme']=='https' and actual['scheme']!='https':return False,'redirect_not_allowed'
            return (actual['origin']==expected['origin'],'navigation_verified' if actual['origin']==expected['origin'] else 'redirect_not_allowed')
        if a.kind=='close_tab':return (before.get('tab_id')!=after.get('tab_id'),'tab_close_verified')
        if a.kind=='wait_for':return (bool(raw.get('condition_met')),'wait_condition_verified')
        if a.expected_text and a.expected_text not in str(after.get('visible_text') or ''):return False,'expected_postcondition_missing'
        if a.kind in {'click','select','check','uncheck'} and before.get('dom_sha256')==after.get('dom_sha256') and before.get('normalized_url')==after.get('normalized_url'):return False,'expected_postcondition_missing'
        return True,'dom_accessibility_readback_verified'

    @staticmethod
    def _target(obs,target_id):return next((e for e in obs.get('elements') or [] if e.get('target_id')==target_id),None)
    @staticmethod
    def _safe_params(a):
        d={'kind':a.kind,'target_id':a.target_id,'url':a.url,'tab_index':a.tab_index,'amount':a.amount,'operation_class':a.operation_class}
        if a.value:d['value_digest']=digest(a.value)
        if a.option:d['option_digest']=digest(a.option)
        if a.upload_path:d['upload_path_digest']=digest(a.upload_path)
        return d
    @staticmethod
    def _expected(a,op):return 'observable verified postcondition or recovery review' if op in CONSEQUENTIAL else 'DOM/accessibility readback'
    @staticmethod
    def _file_digest(path):
        h=hashlib.sha256();f=open(path,'rb')
        try:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        finally:f.close()
        return h.hexdigest()

    def _validate(self,a):
        allowed={'open_url','back','forward','refresh','create_tab','select_tab','close_tab','click','type','select','check','uncheck','scroll','wait_for'}
        if a.kind not in allowed or not a.transaction_id:raise ValueError('invalid browser action')
        if a.kind in {'open_url','create_tab'} and not a.url:raise ValueError('URL required')
        if a.kind in {'click','type','select','check','uncheck'} and not a.target_id:raise ValueError('stable target_id required')
        if not 0<=a.timeout_ms<=30000:raise ValueError('timeout must be bounded')

    def _deny(self,a,before,reason):
        tx=self.transactions.transaction(a.transaction_id)
        if tx and tx['state'] in {'policy_check','approval_required','permitted'}:
            try:self.transactions.transition(a.transaction_id,'failed',error_code=reason)
            except Exception:pass
        return self._result(a,'denied',reason,before)
    def _cancel(self,a,reason):
        tx=self.transactions.transaction(a.transaction_id)
        if tx and tx['state'] not in {'completed','failed','cancelled','recovery_review_required'}:
            try:self.transactions.transition(a.transaction_id,'cancelled',error_code=reason)
            except Exception:pass
        return BrowserResult('cancelled' if reason=='cancelled' else 'denied',reason,a.transaction_id)
    def _recovery(self,txid,reason):
        tx=self.transactions.transaction(txid)
        if tx and tx['state'] in {'executing','verifying'}:
            try:self.transactions.transition(txid,'recovery_review_required',recovery_reason=reason)
            except Exception:pass
    @staticmethod
    def _result(a,status,reason,before,after=None,result=None):return BrowserResult(status,reason,a.transaction_id,before.get('observation_id',''),(after or {}).get('observation_id',''),result or {})
