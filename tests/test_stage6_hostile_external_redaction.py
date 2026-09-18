from types import SimpleNamespace

from activities.projection import ActivitiesProjection
from approvals.projection import ApprovalsProjection
from automation.projection import AutomationWorkflowProjection
from recovery.visibility_projection import ExecutionRecoveryProjection
from security.projection_redaction import sanitize_sensitive_text

HOSTILE = 'Authorization: Bearer abcdefghijklmnop api_key=AKIASECRET123 cookie=session-secret https://provider.invalid/?access_token=querysecret password=hunter2 -----BEGIN PRIVATE KEY-----\\nTOPSECRET\\n-----END PRIVATE KEY-----'


def assert_clean(value):
    text=str(value)
    for secret in ('abcdefghijklmnop','AKIASECRET123','session-secret','querysecret','hunter2','TOPSECRET'):
        assert secret not in text


def test_sensitive_value_redaction_preserves_normal_owner_text():
    normal='Owner note: call Alice tomorrow about the quarterly report.'
    assert sanitize_sensitive_text(normal)==normal
    assert_clean(sanitize_sensitive_text(HOSTILE))


def test_activities_redact_hostile_ordinary_external_fields_without_mutating_source():
    source={'message':HOSTILE,'detail':{'description':HOSTILE},'owner_note':'Owner-authored normal text'}
    entry={'id':'a','category':'tool','action':'failed','created_at':'now','payload':source}
    projected=ActivitiesProjection.project_entry(entry)
    assert_clean(projected)
    assert source['message']==HOSTILE
    assert projected['details']['owner_note']=='Owner-authored normal text'


def test_approval_outcome_and_destination_redact_credential_shaped_values():
    ticket=SimpleNamespace(id='a',execution_id='e',tool_name='t',created_at=1,expires_at=9999999999,destination='https://x.invalid/?access_token=querysecret',data_classification='internal',device_id=None,session_id=None)
    manager=SimpleNamespace(record=lambda _: {'ticket':ticket,'status':'completed','outcome':{'message':HOSTILE},'dispatch_started_at':2,'completed_at':3,'failure_code':None})
    item=ApprovalsProjection(manager).detail('a')
    assert_clean(item)


def test_automation_safe_value_redacts_hostile_nested_text():
    assert_clean(AutomationWorkflowProjection._safe({'result':{'message':HOSTILE},'status_text':HOSTILE}))


def test_recovery_safe_value_redacts_hostile_nested_text():
    assert_clean(ExecutionRecoveryProjection._safe({'error':{'message':HOSTILE},'evidence':[{'detail':HOSTILE}]}))
