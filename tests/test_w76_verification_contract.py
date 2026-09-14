from types import SimpleNamespace
import time
import pytest

from desktop.verification import VerificationOutcome, build_record, evidence_checksum, normalize_operator_result, sanitize_evidence


def test_verification_outcomes_are_exact_contract():
    assert {x.value for x in VerificationOutcome}=={'verified_success','verified_no_effect','verified_partial','verified_failure','unknown_outcome','cancelled_before_dispatch','blocked_before_dispatch','recovery_review_required'}

@pytest.mark.parametrize(('status','consequential','expected'),[
    ('verified',True,VerificationOutcome.VERIFIED_SUCCESS),
    ('verified_no_effect',True,VerificationOutcome.VERIFIED_NO_EFFECT),
    ('verified_partial',True,VerificationOutcome.VERIFIED_PARTIAL),
    ('cancelled',True,VerificationOutcome.CANCELLED_BEFORE_DISPATCH),
    ('blocked_by_policy',True,VerificationOutcome.BLOCKED_BEFORE_DISPATCH),
    ('approval_required',True,VerificationOutcome.BLOCKED_BEFORE_DISPATCH),
    ('reauthentication_required',True,VerificationOutcome.BLOCKED_BEFORE_DISPATCH),
    ('recovery_review_required',True,VerificationOutcome.RECOVERY_REVIEW_REQUIRED),
    ('verification_failed',True,VerificationOutcome.UNKNOWN_OUTCOME),
    ('verification_failed',False,VerificationOutcome.VERIFIED_FAILURE),
])
def test_operator_result_normalization(status,consequential,expected):
    result,_=normalize_operator_result(SimpleNamespace(status=status,reason_code=''),consequential=consequential)
    assert result is expected


def test_handler_success_without_postcondition_is_not_proof():
    result,_=normalize_operator_result({'status':'handler_returned'},consequential=True)
    assert result is VerificationOutcome.UNKNOWN_OUTCOME


def test_evidence_redacts_secret_bearing_fields():
    safe=sanitize_evidence({'sha256':'abc','password':'p','token':'t','raw_text':'secret','nested':{'secret_value':'x','size':4}})
    assert safe=={'sha256':'abc','nested':{'size':4}}


def test_evidence_checksum_is_stable_and_sensitive_to_observation():
    a=evidence_checksum(['ref:a'],{'size':2,'sha256':'x'})
    assert a==evidence_checksum(['ref:a'],{'sha256':'x','size':2})
    assert a!=evidence_checksum(['ref:a'],{'size':3,'sha256':'x'})


def test_build_record_has_freshness_and_bounded_confidence():
    record=build_record(transaction_id='t',action_id='a',dispatch_id='d',idempotency_key='i',operation_class='copy',target='file',precondition={'x':1},expected_postcondition='exists',observed_postcondition={'exists':True},result='verified_success',explanation='ok',now=100,freshness_seconds=30,confidence=2)
    assert record.verification_timestamp==100 and record.verification_fresh_until==130 and record.confidence==1.0
    assert len(record.evidence_checksum)==64


def test_record_safe_dict_never_contains_raw_secret_content():
    record=build_record(transaction_id='t',action_id='a',dispatch_id='d',idempotency_key='i',operation_class='read',target='x',precondition={'token':'hidden'},expected_postcondition='read',observed_postcondition={'content':'hidden','sha256':'ok'},result='verified_success',explanation='ok')
    data=record.safe_dict()
    assert data['precondition']=={} and data['observed_postcondition']=={'sha256':'ok'} and data['result']=='verified_success'
