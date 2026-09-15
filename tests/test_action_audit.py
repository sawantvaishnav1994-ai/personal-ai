from __future__ import annotations

import sqlite3

from security.action_audit import REDACTED, TrustedActionAudit


def test_trusted_action_audit_redacts_sensitive_values(tmp_path):
    audit = TrustedActionAudit(tmp_path / 'trusted-action-audit.sqlite3')
    audit.append('tool', 'execute', {
        'recipient': 'person@example.com',
        'authorization': 'Bearer abc123',
        'nested': {'api_key': 'secret-value', 'safe': 'visible'},
        'cookie': 'session=value',
    })

    payload = audit.entries(1)[0]['payload']
    assert payload['recipient'] == 'person@example.com'
    assert payload['authorization'] == REDACTED
    assert payload['nested']['api_key'] == REDACTED
    assert payload['nested']['safe'] == 'visible'
    assert payload['cookie'] == REDACTED
    assert audit.verify_chain()['ok'] is True


def test_trusted_action_audit_detects_row_tampering(tmp_path):
    path = tmp_path / 'trusted-action-audit.sqlite3'
    audit = TrustedActionAudit(path)
    audit.append('approval', 'required', {'tool': 'send'})
    audit.append('approval', 'approved', {'tool': 'send'})

    with sqlite3.connect(path) as con:
        con.execute("UPDATE action_audit SET action='forged' WHERE sequence=1")

    result = audit.verify_chain()
    assert result['ok'] is False
    assert result['reason'] == 'entry hash mismatch'


def test_trusted_action_audit_detects_tail_deletion_via_anchor(tmp_path):
    path = tmp_path / 'trusted-action-audit.sqlite3'
    audit = TrustedActionAudit(path)
    audit.append('tool', 'one', {'ok': True})
    audit.append('tool', 'two', {'ok': True})

    with sqlite3.connect(path) as con:
        con.execute('DELETE FROM action_audit WHERE sequence=2')

    result = audit.verify_chain()
    assert result['ok'] is False
    assert result['reason'] == 'audit anchor mismatch'
