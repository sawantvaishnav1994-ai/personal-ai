from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
import time
from typing import Any


class VerificationOutcome(str, Enum):
    VERIFIED_SUCCESS = 'verified_success'
    VERIFIED_NO_EFFECT = 'verified_no_effect'
    VERIFIED_PARTIAL = 'verified_partial'
    VERIFIED_FAILURE = 'verified_failure'
    UNKNOWN_OUTCOME = 'unknown_outcome'
    CANCELLED_BEFORE_DISPATCH = 'cancelled_before_dispatch'
    BLOCKED_BEFORE_DISPATCH = 'blocked_before_dispatch'
    RECOVERY_REVIEW_REQUIRED = 'recovery_review_required'


@dataclass(frozen=True)
class VerificationRecord:
    transaction_id: str
    action_id: str
    dispatch_id: str
    idempotency_key: str
    operation_class: str
    target: str
    precondition: dict[str, Any]
    expected_postcondition: str
    observed_postcondition: dict[str, Any]
    verifier_identity: str
    verifier_version: str
    evidence_references: tuple[str, ...]
    evidence_checksum: str
    verification_timestamp: float
    verification_fresh_until: float
    result: VerificationOutcome
    explanation: str
    confidence: float | None = None

    def safe_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value['result'] = self.result.value
        return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def checksum(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def sanitize_evidence(value: dict[str, Any] | None) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    forbidden = ('password','secret','token','content','text','clipboard','cookie','authorization','dom','screenshot_data','image_data')
    for key, item in dict(value or {}).items():
        low = str(key).lower()
        if any(word in low for word in forbidden):
            continue
        if isinstance(item, str):
            safe[str(key)] = item[:500]
        elif isinstance(item, (int, float, bool)) or item is None:
            safe[str(key)] = item
        elif isinstance(item, (list, tuple)):
            safe[str(key)] = [str(x)[:300] for x in item[:50]]
        elif isinstance(item, dict):
            safe[str(key)] = sanitize_evidence(item)
    return safe


def evidence_checksum(references: list[str] | tuple[str, ...], observed_postcondition: dict[str, Any]) -> str:
    return checksum({'references': [str(x) for x in references], 'observed': sanitize_evidence(observed_postcondition)})


def build_record(*, transaction_id: str, action_id: str, dispatch_id: str, idempotency_key: str,
                 operation_class: str, target: str, precondition: dict[str, Any] | None,
                 expected_postcondition: str, observed_postcondition: dict[str, Any] | None,
                 result: VerificationOutcome | str, explanation: str, evidence_references=(),
                 verifier_identity: str='w7.6.shared-verifier', verifier_version: str='1',
                 freshness_seconds: int=120, confidence: float | None=None, now: float | None=None) -> VerificationRecord:
    ts = time.time() if now is None else float(now)
    outcome = result if isinstance(result, VerificationOutcome) else VerificationOutcome(str(result))
    observed = sanitize_evidence(observed_postcondition)
    refs = tuple(str(x) for x in evidence_references if str(x))
    conf = None if confidence is None else max(0.0, min(1.0, float(confidence)))
    return VerificationRecord(
        str(transaction_id), str(action_id), str(dispatch_id), str(idempotency_key), str(operation_class),
        str(target)[:500], sanitize_evidence(precondition), str(expected_postcondition)[:2000], observed,
        str(verifier_identity)[:160], str(verifier_version)[:80], refs,
        evidence_checksum(refs, observed), ts, ts + max(1, int(freshness_seconds)), outcome,
        str(explanation)[:1000], conf,
    )


def normalize_operator_result(result: Any, *, consequential: bool) -> tuple[VerificationOutcome, str]:
    status = str(getattr(result, 'status', None) or (result or {}).get('status','') if isinstance(result, dict) else '').strip()
    reason = str(getattr(result, 'reason_code', None) or (result or {}).get('reason_code','') if isinstance(result, dict) else '').strip()
    if status in {'verified','verified_success','completed'}:
        return VerificationOutcome.VERIFIED_SUCCESS, 'The expected postcondition was independently verified.'
    if status in {'verified_no_effect','no_effect'}:
        return VerificationOutcome.VERIFIED_NO_EFFECT, 'Verification established that no side effect occurred.'
    if status in {'verified_partial','partially_completed'}:
        return VerificationOutcome.VERIFIED_PARTIAL, 'Only part of the expected postcondition was verified.'
    if status in {'cancelled'}:
        return VerificationOutcome.CANCELLED_BEFORE_DISPATCH, 'The action was cancelled before a consequential dispatch.'
    if status in {'blocked_by_policy','approval_required','reauthentication_required'}:
        return VerificationOutcome.BLOCKED_BEFORE_DISPATCH, 'The action was blocked before dispatch by an authority gate.'
    if status in {'recovery_review_required','uncertain_outcome','unknown_outcome'}:
        return VerificationOutcome.RECOVERY_REVIEW_REQUIRED, 'The outcome cannot be safely inferred and requires recovery review.'
    if status in {'verification_failed','failed'}:
        return (VerificationOutcome.UNKNOWN_OUTCOME if consequential else VerificationOutcome.VERIFIED_FAILURE,
                'Consequential dispatch cannot be treated as failed without evidence of no effect.' if consequential else 'Verification established failure.')
    if reason == 'verification_failed' and consequential:
        return VerificationOutcome.UNKNOWN_OUTCOME, 'Verification failed after a consequential dispatch; retry is not safe.'
    return VerificationOutcome.UNKNOWN_OUTCOME, 'No authoritative postcondition evidence establishes the outcome.'
