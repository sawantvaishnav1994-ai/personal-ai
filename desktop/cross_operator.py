from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable

from desktop.operator_recovery import OperatorRecoveryStore, RecoveryLease
from desktop.operator_transactions import OperatorBinding
from desktop.verification import VerificationOutcome, build_record, normalize_operator_result, sanitize_evidence


@dataclass(frozen=True)
class RecoveryStep:
    sequence: int
    operator: str
    operation_class: str
    target: str
    idempotency_key: str
    expected_postcondition: str
    parameters: dict[str, Any]
    consequential: bool = False
    idempotent: bool = False
    compensation_category: str = 'manual_recovery_only'


class CrossOperatorCoordinator:
    """W7.6 orchestration over existing W7.4/W7.5 execution callbacks only.

    Callers supply browser/desktop execution and read-only verifier callbacks. This class does not
    synthesize browser, desktop, file, clipboard or shell capabilities.
    """
    def __init__(self, recovery: OperatorRecoveryStore, binding: OperatorBinding, *,
                 browser_execute: Callable[[RecoveryStep], Any] | None=None,
                 desktop_execute: Callable[[RecoveryStep], Any] | None=None,
                 verify: Callable[[RecoveryStep, Any], dict[str,Any]] | None=None,
                 authority: Callable[[RecoveryStep, str], bool] | None=None,
                 emergency_stop: Callable[[], bool] | None=None):
        self.recovery=recovery;self.binding=binding
        self.browser_execute=browser_execute;self.desktop_execute=desktop_execute
        self.verify=verify or self._default_verify
        self.authority=authority or (lambda step,purpose: True)
        self.emergency_stop=emergency_stop or (lambda:False)

    def run_step(self, transaction_id: str, step: RecoveryStep, *, worker_id: str='w76-worker') -> dict[str,Any]:
        self.recovery.ensure_transaction(transaction_id,self.binding)
        if self.emergency_stop():
            self.recovery.emergency_stop();return {'status':'emergency_stop_active','transaction_id':transaction_id}
        if not self.authority(step,'original'):
            return {'status':'blocked_before_dispatch','reason':'blocked_by_policy'}
        lease=self.recovery.acquire_lease(transaction_id,worker_id)
        try:
            action_id=f'{transaction_id}:{int(step.sequence)}'
            dispatch,created=self.recovery.begin_dispatch(lease,action_id=action_id,idempotency_key=step.idempotency_key,
                                                          operation_class=step.operation_class,target=step.target,
                                                          parameter_digest=self._digest(step.parameters))
            if not created:
                latest=self.recovery.latest_verification(dispatch['dispatch_id'])
                return {'status':'already_recorded','dispatch':dispatch,'verification':latest}
            if self.emergency_stop():
                self.recovery.emergency_stop();return {'status':'emergency_stop_active','dispatch_id':dispatch['dispatch_id']}
            # The durable dispatch marker is written immediately before invoking the existing operator surface.
            self.recovery.mark_dispatched(lease,dispatch['dispatch_id'])
            try:
                raw=self._execute(step)
            except Exception:
                self.recovery.transition(transaction_id,'recovery_review_required',reason='dispatch_exception_outcome_unknown')
                return {'status':'recovery_review_required','dispatch_id':dispatch['dispatch_id']}
            self.recovery.mark_verifying(lease,dispatch['dispatch_id'])
            observed=sanitize_evidence(self.verify(step,raw))
            outcome,explanation=normalize_operator_result(raw,consequential=step.consequential)
            if observed.get('result'):
                try:outcome=VerificationOutcome(str(observed['result']))
                except Exception:pass
            record=build_record(transaction_id=transaction_id,action_id=action_id,dispatch_id=dispatch['dispatch_id'],
                                idempotency_key=step.idempotency_key,operation_class=step.operation_class,target=step.target,
                                precondition={'sequence':step.sequence,'operator':step.operator},expected_postcondition=step.expected_postcondition,
                                observed_postcondition=observed,result=outcome,explanation=explanation,
                                evidence_references=tuple(observed.get('evidence_references') or ()),
                                verifier_identity=str(observed.get('verifier_identity') or 'w7.6.cross-operator'),
                                verifier_version=str(observed.get('verifier_version') or '1'),
                                confidence=observed.get('confidence'))
            saved=self.recovery.record_verification(lease,record)
            if outcome is VerificationOutcome.VERIFIED_SUCCESS:
                self.recovery.transition(transaction_id,'active',checkpoint={'last_verified_action':action_id},resume_position=step.sequence+1)
            elif outcome is VerificationOutcome.VERIFIED_PARTIAL:
                self.recovery.transition(transaction_id,'partially_completed',reason='postcondition_partial',resume_position=step.sequence)
            elif outcome in {VerificationOutcome.UNKNOWN_OUTCOME,VerificationOutcome.RECOVERY_REVIEW_REQUIRED}:
                self.recovery.transition(transaction_id,'recovery_review_required',reason='outcome_unknown',resume_position=step.sequence)
            return {'status':saved['result'],'dispatch_id':dispatch['dispatch_id'],'verification_id':saved['verification_id']}
        finally:
            try:self.recovery.release_lease(lease)
            except Exception:pass

    def retry_step(self, transaction_id: str, dispatch_id: str, step: RecoveryStep, *, worker_id='w76-retry') -> dict[str,Any]:
        decision=self.recovery.retry_decision(dispatch_id,idempotent=step.idempotent)
        if not decision['allowed']:return {'status':'retry_not_safe','reason':decision['reason']}
        if not self.authority(step,'retry'):return {'status':'blocked_before_dispatch','reason':'blocked_by_policy'}
        # Retry receives a distinct idempotency key; original dispatch identity is retained separately.
        retried=RecoveryStep(step.sequence,step.operator,step.operation_class,step.target,
                            f'{step.idempotency_key}:retry:{self._digest({"dispatch_id":dispatch_id})[:12]}',
                            step.expected_postcondition,step.parameters,step.consequential,step.idempotent,step.compensation_category)
        return self.run_step(transaction_id,retried,worker_id=worker_id)

    def compensation(self, transaction_id: str, compensation_id: str, step: RecoveryStep, *, approved=False, reauthenticated=False, worker_id='w76-compensate') -> dict[str,Any]:
        item=self.recovery.compensation(compensation_id)
        if not item or item['transaction_id']!=transaction_id:return {'status':'compensation_failed','reason':'missing_compensation'}
        if item['category']=='irreversible':return {'status':'compensation_failed','reason':'irreversible'}
        if item['requires_approval'] and not approved:return {'status':'compensation_requires_approval'}
        if item['requires_reauth'] and not reauthenticated:return {'status':'reauthentication_required'}
        if not self.authority(step,'compensation'):return {'status':'blocked_before_dispatch','reason':'blocked_by_policy'}
        if self.emergency_stop():self.recovery.emergency_stop();return {'status':'emergency_stop_active'}
        result=self.run_step(transaction_id,step,worker_id=worker_id)
        verified=result.get('status')=='verified_success'
        lease=self.recovery.acquire_lease(transaction_id,worker_id+'-record')
        try:self.recovery.record_compensation_result(lease,compensation_id,compensation_action_id=f'{transaction_id}:{step.sequence}',result=result,verified=verified)
        finally:
            try:self.recovery.release_lease(lease)
            except Exception:pass
        return {'status':'verified_success' if verified else 'compensation_failed','result':result}

    def recover_after_crash(self, transaction_id: str, *, read_only_verify: Callable[[dict[str,Any]], dict[str,Any]]) -> dict[str,Any]:
        report=self.recovery.recovery_report(transaction_id)
        uncertain=[d for d in report['dispatches'] if d['state'] in {'dispatched','verifying'}]
        if not uncertain:return {'status':'verified_no_effect','reason':'no_unverified_dispatch'}
        outcomes=[]
        for dispatch in uncertain:
            observation=sanitize_evidence(read_only_verify(dispatch))
            outcomes.append({'dispatch_id':dispatch['dispatch_id'],'observation':observation})
        return {'status':'recovery_review_required','reason':'read_only_evidence_collected_owner_review_required','outcomes':outcomes}

    def _execute(self, step: RecoveryStep):
        if step.operator=='browser':
            if not self.browser_execute:raise RuntimeError('unsupported_operator')
            return self.browser_execute(step)
        if step.operator in {'desktop','application','file','clipboard'}:
            if not self.desktop_execute:raise RuntimeError('unsupported_operator')
            return self.desktop_execute(step)
        raise PermissionError('unapproved_operator')

    @staticmethod
    def _default_verify(step: RecoveryStep, raw: Any) -> dict[str,Any]:
        if isinstance(raw,dict):
            return {'status':raw.get('status',''),'reason_code':raw.get('reason_code',''),'evidence_references':raw.get('evidence_references',[])}
        return {'status':getattr(raw,'status',''),'reason_code':getattr(raw,'reason_code','')}

    @staticmethod
    def _digest(value:Any)->str:
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
