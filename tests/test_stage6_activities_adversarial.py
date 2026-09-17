from __future__ import annotations

import base64
import json

import pytest

from activities.projection import ActivitiesProjection
from memory.store import MemoryStore


def _ids(page):
    return [row['id'] for row in page['activities']]


def test_pagination_has_no_duplicate_or_missing_rows(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    written = [store.audit('tool', 'completed', {'execution_id': f'e-{i}'}) for i in range(23)]
    projection = ActivitiesProjection(store)
    seen = []
    cursor = None
    while True:
        page = projection.page(limit=5, cursor=cursor)
        seen.extend(_ids(page))
        if not page['has_more']:
            break
        cursor = page['next_cursor']
    assert len(seen) == len(set(seen)) == 23
    assert set(seen) == set(written)


def test_snapshot_cursor_excludes_concurrent_newer_audit_writes(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    original = [store.audit('tool', 'completed', {'execution_id': f'e-{i}'}) for i in range(12)]
    projection = ActivitiesProjection(store)
    first = projection.page(limit=4)
    assert first['next_cursor']
    new_ids = [store.audit('tool', 'completed', {'execution_id': f'new-{i}'}) for i in range(3)]
    second = projection.page(limit=4, cursor=first['next_cursor'])
    assert not set(_ids(second)) & set(new_ids)
    assert not set(_ids(first)) & set(_ids(second))
    assert set(_ids(first) + _ids(second)).issubset(set(original))


def test_cursor_fails_closed_when_snapshot_falls_out_of_bounded_window(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    for i in range(20):
        store.audit('tool', 'completed', {'execution_id': f'e-{i}'})
    projection = ActivitiesProjection(store)
    first = projection.page(limit=5)
    for i in range(projection.MAX_SCAN):
        store.audit('tool', 'completed', {'execution_id': f'new-{i}'})
    with pytest.raises(ValueError, match='stale'):
        projection.page(limit=5, cursor=first['next_cursor'])


def test_tampered_and_malformed_cursors_are_rejected(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    for i in range(4):
        store.audit('tool', 'completed', {'execution_id': str(i)})
    projection = ActivitiesProjection(store)
    page = projection.page(limit=2)
    raw = page['next_cursor']
    padded = raw + '=' * (-len(raw) % 4)
    data = json.loads(base64.urlsafe_b64decode(padded).decode())
    data['after'] = 'not-a-real-audit-id'
    tampered = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip('=')
    with pytest.raises(ValueError):
        projection.page(limit=2, cursor=tampered)
    with pytest.raises(ValueError):
        projection.page(limit=2, cursor='not-json')


def test_equal_timestamps_have_deterministic_id_tiebreak():
    class Store:
        def audit_entries(self, category=None, limit=1000):
            return [
                {'id': 'b', 'category': 'tool', 'action': 'completed', 'payload': {}, 'created_at': 'same'},
                {'id': 'a', 'category': 'tool', 'action': 'completed', 'payload': {}, 'created_at': 'same'},
                {'id': 'c', 'category': 'tool', 'action': 'completed', 'payload': {}, 'created_at': 'same'},
            ]
    projection = ActivitiesProjection(Store())
    assert _ids(projection.page(limit=3)) == ['c', 'b', 'a']
    detail = projection.detail('b')
    assert [row['id'] for row in detail['timeline']] == ['b']


def test_recursive_redaction_depth_and_oversized_payload_are_bounded():
    nested = {'password': 'top-secret'}
    for _ in range(12):
        nested = {'safe': nested}
    projected = ActivitiesProjection.project_entry({
        'id': 'x', 'category': 'tool', 'action': 'completed', 'created_at': 'now',
        'payload': {
            'authorization': 'Bearer secret',
            'nested': nested,
            'items': [{'access_token': 'secret', 'safe': i} for i in range(250)],
            'text': 'x' * 5000,
        },
    })
    assert projected['details']['authorization'] == '[redacted]'
    assert len(projected['details']['items']) == 100
    assert all(item['access_token'] == '[redacted]' for item in projected['details']['items'])
    assert len(projected['details']['text']) == 1000
    value = projected['details']['nested']
    for _ in range(8):
        value = value['safe']
    assert value == '[bounded]'


def test_detail_correlates_only_matching_canonical_identifiers():
    rows = [
        {'id': 'a1', 'category': 'agent', 'action': 'started', 'created_at': '1', 'payload': {'request_id': 'r1', 'execution_id': 'e1'}},
        {'id': 'a2', 'category': 'tool', 'action': 'completed', 'created_at': '2', 'payload': {'request_id': 'r1', 'execution_id': 'e1'}},
        {'id': 'a3', 'category': 'tool', 'action': 'completed', 'created_at': '3', 'payload': {'request_id': 'r2', 'execution_id': 'e2'}},
    ]
    class Store:
        def audit_entries(self, category=None, limit=1000):
            return list(reversed(rows))
    detail = ActivitiesProjection(Store()).detail('a1')
    assert detail['correlations'] == {'request_id': 'r1', 'execution_id': 'e1'}
    assert [event['id'] for event in detail['timeline']] == ['a1', 'a2']
    assert ActivitiesProjection(Store()).detail('missing') is None


def test_reload_reconstructs_same_snapshot_cursor_from_canonical_audit(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    for i in range(9):
        store.audit('tool', 'completed', {'execution_id': f'e-{i}'})
    first_projection = ActivitiesProjection(store)
    first = first_projection.page(limit=3)
    reloaded_projection = ActivitiesProjection(MemoryStore(store.path))
    second = reloaded_projection.page(limit=3, cursor=first['next_cursor'])
    assert not set(_ids(first)) & set(_ids(second))
