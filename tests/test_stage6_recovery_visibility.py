from __future__ import annotations

from recovery.visibility_projection import ExecutionRecoveryProjection


class Authority:
    def __init__(self,view):self.view=view
    def owner_view(self,transaction_id):
        if transaction_id!='tx1':raise KeyError(transaction_id)
        return self.view


def base(state='active',uncertain=None,verified=None):
    return {'transaction_id':'tx1','transaction_state':'active','recovery_state':state,'completed_steps':[],
            'current_step':'a1','affected_targets':[],'verified':verified or [],'uncertain':uncertain or [],
            'redacted_evidence':[],'proposed_recovery_options':[],'rollback_limitations':[],
            'recovery_reason':'','timestamps':{},'audit_references':[]}


def test_dispatch_is_never_projected_as_success():
    item=ExecutionRecoveryProjection(Authority(base('dispatched'))).detail('tx1')
    assert item['owner_status']=='UNVERIFIED_OR_RECOVERY_REQUIRED'
    assert item['verified_success'] is False
    assert item['verification_required_for_success'] is True


def test_unknown_or_partial_verification_stays_degraded():
    uncertain=[{'verification_id':'v1','result':'unknown_outcome','explanation':'uncertain'}]
    item=ExecutionRecoveryProjection(Authority(base('partially_completed',uncertain=uncertain))).detail('tx1')
    assert item['owner_status']=='UNVERIFIED_OR_RECOVERY_REQUIRED'
    assert not item['verified_success']


def test_only_canonical_verified_success_projects_success():
    item=ExecutionRecoveryProjection(Authority(base('verified_success',verified=[{'verification_id':'v1','result':'verified_success'}]))).detail('tx1')
    assert item['owner_status']=='VERIFIED_SUCCESS'
    assert item['verified_success'] is True
    assert item['verification_required_for_success'] is False


def test_compensation_is_distinct_and_not_rollback_success():
    item=ExecutionRecoveryProjection(Authority(base('compensation_requires_approval'))).detail('tx1')
    assert item['owner_status']=='COMPENSATION_PENDING'
    assert item['verified_success'] is False


def test_projection_recursively_redacts_sensitive_owner_view_fields():
    view=base('recovery_review_required',uncertain=[{'error':{'access_token':'x','safe':'ok'}}])
    view['extra']={'private_key':'pem','nested':[{'client_secret':'y'}]}
    item=ExecutionRecoveryProjection(Authority(view)).detail('tx1')
    assert item['uncertain'][0]['error']['access_token']=='[redacted]'
    assert item['extra']['private_key']=='[redacted]'
    assert item['extra']['nested'][0]['client_secret']=='[redacted]'


def test_missing_transaction_is_safe_none():
    assert ExecutionRecoveryProjection(Authority(base())).detail('missing') is None


def test_projection_cannot_execute_verify_retry_or_compensate():
    projection=ExecutionRecoveryProjection(Authority(base()))
    for name in ('begin_dispatch','record_verification','retry_decision','authorize_compensation','record_compensation_result'):
        assert not hasattr(projection,name)
