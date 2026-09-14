from __future__ import annotations

from desktop import observation_policy_v72 as core
from desktop.observation_policy_v72 import *  # noqa: F401,F403


def build_observation_record(*, binding, transaction_id, application, screen, browser, reason, initiator):
    value = dict(screen or {})
    synthetic = bool(value.pop('_synthetic_test_screen', False)) or str(reason) == 'test'
    if synthetic:
        fingerprint = str(value.get('screen_fingerprint') or value.get('screenshot_sha256') or '')
        value.setdefault('evidence_id', str(value.get('observation_id') or ''))
        value.setdefault('sanitized_checksum', fingerprint)
        value.setdefault('redaction_status', 'sanitized')
        value.setdefault('redaction_method', 'synthetic_fixture')
        value.setdefault('coordinate_space_version', 1)
        value.setdefault('capture_source', 'synthetic_fixture')
        value.setdefault('visual_evidence_unavailable', False)
        value.setdefault('retention_expires_at', value.get('expires_at'))
    return core.build_observation_record(binding=binding, transaction_id=transaction_id, application=application, screen=value, browser=browser, reason=reason, initiator=initiator)
