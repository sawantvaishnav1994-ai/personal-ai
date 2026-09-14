from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Callable

from browser.observation import observe_page
from desktop.operator_transactions import OperatorBinding, OperatorTransactionStore
from security.policy_gateway import DecisionKind, PolicyDecision, PolicyGateway, PolicyOperation
from security.policy_targets import TargetValidationError, normalize_origin, validate_file_metadata


_CONSEQUENTIAL = {'form_submission','email_send','message_send','purchase','financial_transfer','public_publish','share','delete','destructive_delete','security_setting_modify','permission_change','legal_acceptance'}
_STRONGLY_BLOCKED_WITHOUT_EXPLICIT_CLASS = {'email_send','message_send','purchase','financial_transfer','public_publish','share','delete','destructive_delete','security_setting_modify','permission_change','legal_acceptance'}
_PROMPT_INJECTION = re.compile(r'ignore (?:all |the )?(?:previous|prior) instructions|system message|developer message|grant (?:me |this page )?permission|reveal (?:your |the )?(?:secret|token|password)|override (?:policy|permission)|disable (?:safety|security)', re.I)
_SECRET_FIELD = re.compile(r'password|passwd|secret|token|otp|passcode|one[-_ ]?time|pin|cvv|cvc|cc[-_ ]?(?:number|csc|exp)|private[-_ ]?key|api[-_ ]?key', re.I)


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


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
    upload_path: str = ''
    download_root: str = ''
    claimed_mime: str = ''
    operation_class: str = ''
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserActionResult:
    status: str
    reason_code: str
    explanation: str
    transaction_id: str
    before_observation_id: str = ''
    after_observation_id: str = ''
    policy_digest: str = ''
    result: dict[str, Any] = field(default_factory=dict)


class SafeBrowserOperator:
    """W7.4 browser operator: W7.1 transaction + W7.2 observation + W7.3 policy.

    Browser page content is always untrusted data. Authorization can only come from
    the owner-bound policy/approval arguments supplied to this object.
    """

    def __init__(self, browser, policy_gateway: PolicyGateway, transaction_store: OperatorTransactionStore,
                 binding: OperatorBinding, *, emergency_stop: Callable[[], bool] | None = None):
        self.browser = browser
        self.policy = policy_gateway
        self.transactions = transaction_store
        self.binding = binding
        self._emergency_stop = emergency_stop or (lambda: False)

    def execute(self, action: BrowserAction, *, approved: bool = False, reauthenticated: bool = False) -> BrowserActionResult:
        self._validate_action_shape(action)
        tx = self._ensure_transaction(action)
        if tx.get('cancel_requested'):
            return self._stop(action, 'cancelled', 'cancelled', 'The browser action was cancelled.')
        if self._emergency_stop():
            return self._stop(action, 'denied', 'emergency_stop_active', 'The owner Emergency Stop is active.')

        before = self._capture_observation(action, 'policy_evaluation')
        initial = before['raw']
        operation_class = self._operation_class(action, initial)
        if operation_class in _STRONGLY_BLOCKED_WITHOUT_EXPLICIT_CLASS and action.operation_class != operation_class:
            return self._fail(action, 'denied', 'approval_required', 'A consequential browser action must be explicitly classified by the caller.', before)

        checks = self._policy_operations(action, initial, operation_class)
        decisions: list[tuple[PolicyOperation, PolicyDecision]] = []
        for op in checks:
            decision = self.policy.evaluate(op, approved=approved, reauthenticated=reauthenticated)
            decisions.append((op, decision))
            if decision.decision is DecisionKind.REAUTHENTICATION_REQUIRED:
                self._move_to_approval_state(action.transaction_id)
                return self._result(action, 'reauthentication_required', decision.reason_code, decision.explanation, before, policy_digest=decision.policy_digest)
            if decision.decision is DecisionKind.APPROVAL_REQUIRED:
                self._move_to_approval_state(action.transaction_id)
                return self._result(action, 'approval_required', decision.reason_code, decision.explanation, before, policy_digest=decision.policy_digest)
            if decision.decision is DecisionKind.RECOVERY_REVIEW_REQUIRED:
                self._recovery(action.transaction_id, decision.reason_code)
                return self._result(action, 'recovery_review_required', decision.reason_code, decision.explanation, before, policy_digest=decision.policy_digest)
            if decision.decision is not DecisionKind.ALLOW:
                return self._fail(action, 'denied', decision.reason_code, decision.explanation, before, policy_digest=decision.policy_digest)

        permits = [(op, decision, self.policy.issue_temporary_permit(op, decision, ttl_seconds=120)) for op, decision in decisions]
        self._permit_transaction(action.transaction_id)

        predispatch = self._capture_observation(action, 'pre_dispatch')
        self._assert_fresh_context(action, initial, predispatch['raw'], operation_class)
        if self._emergency_stop():
            return self._fail(action, 'denied', 'emergency_stop_active', 'The owner Emergency Stop is active.', predispatch)
        self.transactions.assert_dispatchable(action.transaction_id, self.binding)

        # Re-evaluate the exact policy snapshot immediately before input, then consume one-use permits.
        for op, prior, permit in permits:
            fresh_op = self._rebind_operation(op, predispatch)
            current = self.policy.evaluate(fresh_op, approved=approved, reauthenticated=reauthenticated, expected_policy_digest=prior.policy_digest)
            if current.decision is not DecisionKind.ALLOW:
                return self._fail(action, 'denied', current.reason_code, current.explanation, predispatch, policy_digest=current.policy_digest)
            if not self.policy.consume_temporary_permit(permit['permit_id'], fresh_op, current):
                return self._fail(action, 'denied', 'policy_changed', 'The one-use browser permission is no longer valid.', predispatch, policy_digest=current.policy_digest)

        target = self._target(initial, action.target_id) if action.target_id else None
        param_hash = _digest(self._safe_action_parameters(action))
        plan_digest = _digest({'kind': action.kind, 'target_id': action.target_id, 'url': action.url, 'operation_class': operation_class})
        self.transactions.transition(action.transaction_id, 'executing')
        action_row, created = self.transactions.start_action(
            action.transaction_id, action.sequence, kind=action.kind, parameter_hash=param_hash,
            expected_postcondition=self._expected_postcondition(action, operation_class),
            before_observation_id=predispatch['observation_id'], target_identity=(target or {}).get('target_id',''),
            plan_digest=plan_digest, observation_digest=predispatch['digest'])
        if not created:
            self._recovery(action.transaction_id, 'duplicate_dispatch_uncertain')
            return self._result(action, 'recovery_review_required', 'recovery_review_required', 'This action sequence was already dispatched or recorded.', predispatch)

        try:
            raw_result = self._dispatch(action, predispatch['raw'], operation_class)
        except Exception as exc:
            if operation_class in _CONSEQUENTIAL:
                self.policy.mark_unknown_outcome(permits[0][2]['permit_id'], 'browser_dispatch_exception')
                self._recovery(action.transaction_id, 'browser_dispatch_exception')
                return self._result(action, 'recovery_review_required', 'recovery_review_required', 'The browser action outcome is uncertain and will not be retried automatically.', predispatch)
            self.transactions.finish_action(action_row['action_id'], verified=False, evidence={'kind': action.kind}, error_code='browser_dispatch_failed')
            self.transactions.transition(action.transaction_id, 'failed', error_code='browser_dispatch_failed')
            return self._result(action, 'failed', 'verification_failed', 'The browser action failed before it could be verified.', predispatch)

        self.transactions.transition(action.transaction_id, 'verifying')
        after = self._capture_observation(action, 'postcondition_verification')
        verified, verify_reason = self._verify(action, predispatch['raw'], after['raw'], operation_class, raw_result)
        self.transactions.finish_action(action_row['action_id'], verified=verified,
            evidence={'before_observation_id': predispatch['observation_id'], 'after_observation_id': after['observation_id'], 'postcondition': verify_reason},
            error_code='' if verified else verify_reason, after_observation_id=after['observation_id'])
        if not verified:
            if operation_class in _CONSEQUENTIAL:
                self._recovery(action.transaction_id, verify_reason)
                return self._result(action, 'recovery_review_required', 'recovery_review_required', 'The consequential browser outcome could not be verified; automatic retry is blocked.', predispatch, after)
            self.transactions.transition(action.transaction_id, 'failed', error_code=verify_reason)
            return self._result(action, 'failed', 'verification_failed', 'The browser postcondition was not verified.', predispatch, after)
        self.transactions.transition(action.transaction_id, 'completed')
        return self._result(action, 'completed', 'allow', 'Browser action completed and was verified.', predispatch, after, result=self._safe_result(raw_result, after['raw']))

    def find_visible(self, *, text: str = '', role: str = '', tag: str = '') -> list[dict[str, Any]]:
        obs = self._observe()
        out = []
        for element in obs.get('elements') or []:
            if not element.get('actionable'): continue
            hay = ' '.join(str(element.get(k) or '') for k in ('text','label','placeholder')).casefold()
            if text and text.casefold() not in hay: continue
            if role and str(element.get('role') or '').casefold() != role.casefold(): continue
            if tag and str(element.get('tag') or '').casefold() != tag.casefold(): continue
            out.append({'target_id': element['target_id'], 'tag': element.get('tag',''), 'role': element.get('role',''), 'label': element.get('label',''), 'text': element.get('text','')[:300]})
        return out[:50]

    def extract_visible_content(self, max_chars: int = 20000) -> dict[str, Any]:
        obs = self._observe()
        text = str(obs.get('visible_text') or '')[:max(0, min(int(max_chars), 20000))]
        return {'content_trust':'untrusted_web_content','prompt_injection_detected':bool(_PROMPT_INJECTION.search(text)), 'text':text,
                'origin':obs.get('origin',''),'normalized_url':obs.get('normalized_url',''),'tab_id':obs.get('tab_id','')}

    def _observe(self) -> dict[str, Any]:
        self.browser.start()
        return observe_page(self.browser.page)

    def _capture_observation(self, action: BrowserAction, reason: str) -> dict[str, Any]:
        obs = self._observe(); now = time.time()
        digest = _digest({'context':obs.get('browser_context_id'),'tab':obs.get('tab_id'),'origin':obs.get('origin'),'url':obs.get('normalized_url'),
                          'dom':obs.get('dom_sha256'),'a11y':obs.get('accessibility_sha256'),'actionable':obs.get('actionable_digest'),'frames':obs.get('frame_origins_digest')})
        observation_id = f'w74-{digest[:24]}-{int(now*1000)}'
        record = {
            'observation_id':observation_id,'transaction_id':action.transaction_id,'owner_id':self.binding.owner_id,'device_id':self.binding.device_id,
            'session_id':self.binding.session_id,'security_epoch':self.binding.security_epoch,'application_identity':'browser:chromium',
            'application_name':'Chromium','process_identity':obs.get('browser_context_id') or 'browser-context-unavailable','window_identity':obs.get('tab_id') or 'browser-tab-unavailable',
            'browser_context_identity':obs.get('browser_context_id',''),'browser_tab_identity':obs.get('tab_id',''),'browser_origin':obs.get('origin',''),
            'normalized_url':obs.get('normalized_url',''),'captured_at':now,'expires_at':now+120,'screenshot_evidence_ref':'visual_evidence_unavailable',
            'screen_fingerprint':_digest({'dom':obs.get('dom_sha256'),'a11y':obs.get('accessibility_sha256'),'actionable':obs.get('actionable_digest')}),
            'sanitized_dom_digest':obs.get('dom_sha256',''),'accessibility_tree_digest':obs.get('accessibility_sha256',''),
            'actionable_element_digest':obs.get('actionable_digest',''),'frame_origins_digest':obs.get('frame_origins_digest',''),
            'active_target_id':obs.get('active_target_id',''),'sensitivity':{'sensitive_region_count':int(obs.get('sensitive_region_count') or 0)},
            'capture_reason':reason,'capture_initiator':'w7.4_safe_browser_operator','observation_digest':digest,
        }
        self.transactions.save_observation(record)
        return {'observation_id':observation_id,'digest':digest,'raw':obs}

    def _ensure_transaction(self, action: BrowserAction) -> dict[str, Any]:
        tx = self.transactions.transaction(action.transaction_id)
        plan = {'steps':[{'sequence':action.sequence,'kind':action.kind,'target_id':action.target_id,'url':action.url,'operation_class':action.operation_class}]}
        if tx is None:
            tx,_ = self.transactions.propose(action.transaction_id, self.binding, goal=f'W7.4 browser action: {action.kind}', action_plan=plan)
        else:
            self.transactions.assert_binding(action.transaction_id, self.binding)
        if tx['state']=='proposed': tx = self.transactions.transition(action.transaction_id,'policy_check')
        return tx

    def _move_to_approval_state(self, txid: str) -> None:
        tx = self.transactions.transaction(txid)
        if tx and tx['state']=='policy_check': self.transactions.transition(txid,'approval_required')

    def _permit_transaction(self, txid: str) -> None:
        tx = self.transactions.transaction(txid)
        if not tx: raise KeyError(txid)
        if tx['state'] in {'policy_check','approval_required'}: self.transactions.transition(txid,'permitted')
        elif tx['state'] != 'permitted': raise RuntimeError(f'browser transaction cannot be permitted from {tx["state"]}')

    def _policy_operations(self, action: BrowserAction, obs: dict[str, Any], operation_class: str) -> list[PolicyOperation]:
        destination = action.url or obs.get('normalized_url') or obs.get('origin') or ''
        target_url = action.url or obs.get('normalized_url') or ''
        op = PolicyOperation(operation=operation_class, owner_id=self.binding.owner_id, device_id=self.binding.device_id, session_id=self.binding.session_id,
            security_epoch=self.binding.security_epoch, target_type='domain', target_identity={'url':target_url}, destination=destination,
            parameters=self._safe_action_parameters(action), data_classification=action.data_classification,
            observation_id='', observation_digest='')
        checks=[op]
        if action.upload_path:
            validate_file_metadata(action.upload_path, claimed_mime=action.claimed_mime or '', max_bytes=int(action.parameters.get('max_bytes') or 50*1024*1024))
            checks.append(PolicyOperation(operation='external_upload', owner_id=self.binding.owner_id, device_id=self.binding.device_id, session_id=self.binding.session_id,
                security_epoch=self.binding.security_epoch, target_type='path', target_identity={'path':action.upload_path,'approved_roots':list(action.parameters.get('approved_roots') or []), 'file_for_validation':action.upload_path,'claimed_mime':action.claimed_mime or '', 'max_bytes':int(action.parameters.get('max_bytes') or 50*1024*1024)},
                destination=action.upload_path, parameters={'file_digest':self._file_digest(action.upload_path)}, data_classification=action.data_classification))
        return checks

    def _rebind_operation(self, op: PolicyOperation, observation: dict[str, Any]) -> PolicyOperation:
        return PolicyOperation(operation=op.operation, owner_id=op.owner_id, device_id=op.device_id, session_id=op.session_id, security_epoch=op.security_epoch,
            target_type=op.target_type, target_identity=op.target_identity, application=op.application, destination=op.destination, parameters=op.parameters,
            data_classification=op.data_classification, observation_id=observation['observation_id'], observation_digest=observation['digest'], outcome_state=op.outcome_state)

    def _assert_fresh_context(self, action: BrowserAction, old: dict[str, Any], fresh: dict[str, Any], operation_class: str) -> None:
        if old.get('browser_context_id') != fresh.get('browser_context_id') or old.get('tab_id') != fresh.get('tab_id'):
            raise PermissionError('browser session or tab changed before dispatch')
        if action.kind not in {'open_url','back','forward','refresh','create_tab','select_tab'}:
            if old.get('origin') != fresh.get('origin') or old.get('normalized_url') != fresh.get('normalized_url'):
                raise PermissionError('browser origin or page changed before dispatch')
        if action.target_id:
            old_target=self._target(old,action.target_id); new_target=self._target(fresh,action.target_id)
            if not old_target or not new_target or not new_target.get('actionable'): raise PermissionError('browser target changed before dispatch')
            if old_target.get('geometry_digest') != new_target.get('geometry_digest'): raise PermissionError('browser target moved before dispatch')

    def _dispatch(self, action: BrowserAction, obs: dict[str, Any], operation_class: str) -> dict[str, Any]:
        self.browser.start(); page=self.browser.page
        if action.kind=='open_url': page.goto(action.url,wait_until='domcontentloaded',timeout=action.timeout_ms); return {'url':page.url}
        if action.kind=='back': page.go_back(wait_until='domcontentloaded',timeout=action.timeout_ms); return {'url':page.url}
        if action.kind=='forward': page.go_forward(wait_until='domcontentloaded',timeout=action.timeout_ms); return {'url':page.url}
        if action.kind=='refresh': page.reload(wait_until='domcontentloaded',timeout=action.timeout_ms); return {'url':page.url}
        if action.kind=='create_tab': page=self.browser.context.new_page(); self.browser.page=page; page.goto(action.url,wait_until='domcontentloaded',timeout=action.timeout_ms); return {'url':page.url}
        if action.kind=='select_tab':
            pages=list(self.browser.context.pages); idx=int(action.tab_index if action.tab_index is not None else -1)
            if idx<0 or idx>=len(pages): raise IndexError('tab index out of range')
            self.browser.page=pages[idx]; self.browser.page.bring_to_front(); return {'url':self.browser.page.url}
        if action.kind=='close_tab':
            if len(self.browser.context.pages)<=1: raise RuntimeError('refusing to close the only browser tab')
            page.close(); self.browser.page=self.browser.context.pages[0]; return {'url':self.browser.page.url}
        if action.kind=='scroll': page.mouse.wheel(0, int(action.amount)); return {'scrolled':int(action.amount)}
        if action.kind=='wait_for':
            deadline=time.monotonic()+min(max(action.timeout_ms,0),30000)/1000
            while time.monotonic()<deadline:
                if action.expected_text and action.expected_text in str(observe_page(page).get('visible_text') or ''): return {'condition_met':True}
                time.sleep(.05)
            raise TimeoutError('bounded browser wait expired')
        target=self._target(obs,action.target_id)
        if not target or not target.get('actionable'): raise PermissionError('browser target is not safely actionable')
        if target.get('sensitive') or self._field_is_secret(target): raise PermissionError('protected browser field cannot be automated')
        locator=self._locator_for(page,target)
        if action.kind=='click': locator.click(timeout=action.timeout_ms); return {'clicked':True}
        if action.kind=='type': locator.fill(action.value,timeout=action.timeout_ms); return {'typed':True}
        if action.kind=='select': locator.select_option(label=action.option,timeout=action.timeout_ms); return {'selected':True}
        if action.kind=='check': locator.check(timeout=action.timeout_ms); return {'checked':True}
        if action.kind=='uncheck': locator.uncheck(timeout=action.timeout_ms); return {'unchecked':True}
        raise ValueError('unsupported browser action')

    def _verify(self, action: BrowserAction, before: dict[str, Any], after: dict[str, Any], operation_class: str, result: dict[str, Any]) -> tuple[bool,str]:
        if after.get('browser_context_id') != before.get('browser_context_id'): return False,'browser_session_changed'
        if action.kind in {'open_url','back','forward','refresh','create_tab'}:
            try:
                actual=normalize_origin(after.get('normalized_url') or after.get('origin') or '')
            except TargetValidationError: return False,'redirect_not_allowed'
            if action.kind in {'open_url','create_tab'}:
                try: expected=normalize_origin(action.url)
                except TargetValidationError: return False,'domain_not_allowed'
                if actual['scheme']=='http' and expected['scheme']=='https': return False,'redirect_not_allowed'
                if actual['origin'] != expected['origin']: return False,'redirect_not_allowed'
            return True,'navigation_verified'
        if action.kind=='close_tab': return bool(after.get('tab_id') != before.get('tab_id')),'tab_close_verified'
        if action.kind=='select_tab': return bool(after.get('tab_id')),'tab_select_verified'
        if action.kind=='scroll': return True,'bounded_scroll_dispatched'
        if action.kind=='wait_for': return bool(result.get('condition_met')),'wait_condition_verified'
        if action.expected_text and action.expected_text not in str(after.get('visible_text') or ''): return False,'expected_postcondition_missing'
        if action.kind in {'click','select','check','uncheck'} and before.get('dom_sha256')==after.get('dom_sha256') and before.get('normalized_url')==after.get('normalized_url'):
            return False,'expected_postcondition_missing'
        return True,'dom_accessibility_readback_verified'

    def _operation_class(self, action: BrowserAction, obs: dict[str, Any]) -> str:
        if action.operation_class: return action.operation_class
        if action.upload_path: return 'external_upload'
        if action.kind in {'open_url','back','forward','refresh','create_tab','select_tab','close_tab'}: return 'navigate'
        if action.kind in {'type','select','check','uncheck'}: return 'application_input'
        if action.kind=='click':
            target=self._target(obs,action.target_id) or {}; text=' '.join(str(target.get(k) or '') for k in ('text','label','name')).casefold()
            typ=str(target.get('type') or '').casefold()
            if typ=='submit' or any(word in text for word in ('submit','send','publish','buy','purchase','pay','delete','accept terms','agree')): return 'form_submission'
            return 'application_input'
        return 'read'

    @staticmethod
    def _target(obs: dict[str, Any], target_id: str) -> dict[str, Any] | None:
        return next((e for e in (obs.get('elements') or []) if e.get('target_id')==target_id),None)

    @staticmethod
    def _locator_for(page, target: dict[str, Any]):
        path=str(target.get('path') or '')
        if not path: raise PermissionError('stable browser element path is unavailable')
        locator=page.locator(path)
        if int(locator.count())!=1: raise PermissionError('stable browser element is ambiguous or detached')
        return locator

    @staticmethod
    def _field_is_secret(target: dict[str, Any]) -> bool:
        return bool(_SECRET_FIELD.search(' '.join(str(target.get(k) or '') for k in ('type','name','label','placeholder'))))

    @staticmethod
    def _expected_postcondition(action: BrowserAction, operation_class: str) -> str:
        if action.expected_text: return f'visible text contains digest:{_digest(action.expected_text)}'
        return {'navigate':'approved final origin and live tab','form_submission':'observable verified postcondition or recovery review'}.get(operation_class,'DOM/accessibility readback')

    @staticmethod
    def _safe_action_parameters(action: BrowserAction) -> dict[str, Any]:
        out={'kind':action.kind,'target_id':action.target_id,'url':action.url,'tab_index':action.tab_index,'amount':action.amount,'operation_class':action.operation_class}
        if action.value: out['value_digest']=_digest(action.value)
        if action.option: out['option_digest']=_digest(action.option)
        if action.upload_path: out['upload_path_digest']=_digest(action.upload_path)
        return out

    @staticmethod
    def _file_digest(path: str) -> str:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _safe_result(raw: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
        return {'operation':{k:v for k,v in raw.items() if k not in {'text','content','value'}}, 'origin':obs.get('origin',''), 'normalized_url':obs.get('normalized_url',''), 'tab_id':obs.get('tab_id','')}

    def _validate_action_shape(self, action: BrowserAction) -> None:
        allowed={'open_url','back','forward','refresh','create_tab','select_tab','close_tab','click','type','select','check','uncheck','scroll','wait_for'}
        if action.kind not in allowed: raise ValueError('unsupported browser action')
        if not action.transaction_id: raise ValueError('transaction_id is required')
        if action.kind in {'open_url','create_tab'} and not action.url: raise ValueError('approved URL is required')
        if action.kind in {'click','type','select','check','uncheck'} and not action.target_id: raise ValueError('stable target_id is required')
        if action.timeout_ms<0 or action.timeout_ms>30000: raise ValueError('browser wait timeout must be bounded to 30 seconds')

    def _fail(self, action: BrowserAction, status: str, reason: str, explanation: str, before: dict[str, Any], after: dict[str, Any] | None=None, *, policy_digest: str='') -> BrowserActionResult:
        tx=self.transactions.transaction(action.transaction_id)
        if tx and tx['state'] in {'policy_check','approval_required','permitted'}:
            try:self.transactions.transition(action.transaction_id,'failed',error_code=reason)
            except Exception:pass
        return self._result(action,status,reason,explanation,before,after,policy_digest=policy_digest)

    def _stop(self, action: BrowserAction, status: str, reason: str, explanation: str) -> BrowserActionResult:
        tx=self.transactions.transaction(action.transaction_id)
        if tx and tx['state'] not in {'completed','failed','cancelled','recovery_review_required'}:
            try:self.transactions.transition(action.transaction_id,'cancelled',error_code=reason)
            except Exception:pass
        return BrowserActionResult(status,reason,explanation,action.transaction_id)

    def _recovery(self, txid: str, reason: str) -> None:
        tx=self.transactions.transaction(txid)
        if tx and tx['state'] in {'executing','verifying'}:
            try:self.transactions.transition(txid,'recovery_review_required',recovery_reason=reason)
            except Exception:pass

    @staticmethod
    def _result(action: BrowserAction, status: str, reason: str, explanation: str, before: dict[str, Any], after: dict[str, Any] | None=None, *, policy_digest: str='', result: dict[str, Any] | None=None) -> BrowserActionResult:
        return BrowserActionResult(status,reason,explanation,action.transaction_id,before.get('observation_id',''),(after or {}).get('observation_id',''),policy_digest,result or {})
