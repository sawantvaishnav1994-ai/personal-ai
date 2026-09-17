from __future__ import annotations

import threading

import pytest

from security.approvals import ApprovalManager


def make_ticket(manager: ApprovalManager, *, execution='e1', device='d1', session='s1', params=None):
    params = params or {'recipient': 'owner@example.com', 'body': 'hello'}
    ticket = manager.create(
        execution,
        'send_message',
        params,
        owner_id='owner',
        device_id=device,
        session_id=session,
        destination=params['recipient'],
        data_classification='internal',
    )
    manager.save_context(ticket.id, {
        'execution_id': execution,
        'plan': {'steps': [{'tool': 'send_message', 'parameters': params}]},
        'index': 0,
        'results': {},
        'history': [],
        'device_id': device,
        'session_id': session,
        'owner_id': 'owner',
        'conversation_id': 'c1',
        'sensitivity': 'internal',
    })
    return ticket, params


def approve(manager, ticket, params, *, device='d1', session='s1'):
    return manager.approve(
        ticket.id,
        ticket.execution_id,
        ticket.tool_name,
        params,
        owner_id='owner',
        device_id=device,
        session_id=session,
        destination=params['recipient'],
        data_classification='internal',
    )


def test_pending_approval_survives_real_runtime_reconstruction(tmp_path):
    path = tmp_path / 'trusted-actions.sqlite3'
    first = ApprovalManager(path=path)
    ticket, params = make_ticket(first)
    assert first.record(ticket.id)['status'] == 'pending'
    assert first.context(ticket.id)['execution_id'] == 'e1'

    second = ApprovalManager(path=path)
    record = second.record(ticket.id)
    assert record['ticket'].id == ticket.id
    assert record['status'] == 'pending'
    assert second.context(ticket.id)['plan']['steps'][0]['parameters'] == params


def test_duplicate_and_concurrent_approval_has_one_dispatch_owner(tmp_path):
    path = tmp_path / 'trusted-actions.sqlite3'
    seed = ApprovalManager(path=path)
    ticket, params = make_ticket(seed)
    approve(seed, ticket, params)

    winners = []
    statuses = []
    barrier = threading.Barrier(2)

    def contender(worker):
        runtime = ApprovalManager(path=path)
        barrier.wait()
        result = runtime.begin_dispatch(ticket.id, worker_id=worker, lease_seconds=60)
        statuses.append(result['status'])
        if result['dispatch']:
            winners.append(worker)

    a = threading.Thread(target=contender, args=('worker-a',))
    b = threading.Thread(target=contender, args=('worker-b',))
    a.start(); b.start(); a.join(); b.join()
    assert len(winners) == 1
    assert statuses.count('dispatching') == 2


def test_lost_approval_response_replays_completed_result_without_new_dispatch(tmp_path):
    path = tmp_path / 'trusted-actions.sqlite3'
    first = ApprovalManager(path=path)
    ticket, params = make_ticket(first)
    approve(first, ticket, params)
    claim = first.begin_dispatch(ticket.id, worker_id='worker-a')
    assert claim['dispatch'] is True
    first.complete_dispatch(ticket.id, {'status': 'completed', 'reply': 'sent', 'verified': True})

    restarted = ApprovalManager(path=path)
    record = restarted.record(ticket.id)
    assert record['status'] == 'completed'
    assert record['outcome']['reply'] == 'sent'
    replay = restarted.begin_dispatch(ticket.id, worker_id='worker-b')
    assert replay['dispatch'] is False
    assert replay['status'] == 'completed'
    assert replay['outcome']['reply'] == 'sent'


def test_expired_dispatch_lease_fails_closed_to_recovery(tmp_path):
    manager = ApprovalManager(path=tmp_path / 'trusted-actions.sqlite3')
    ticket, params = make_ticket(manager)
    approve(manager, ticket, params)
    first = manager.begin_dispatch(ticket.id, worker_id='worker-a', now=10, lease_seconds=5)
    assert first['dispatch'] is True
    second = manager.begin_dispatch(ticket.id, worker_id='worker-b', now=16, lease_seconds=5)
    assert second['dispatch'] is False
    assert second['status'] == 'recovery_required'
    assert manager.record(ticket.id)['failure_code'] == 'dispatch_lease_expired'


def test_security_epoch_invalidates_pending_and_fences_dispatch(tmp_path):
    path = tmp_path / 'trusted-actions.sqlite3'
    manager = ApprovalManager(path=path)
    pending, pending_params = make_ticket(manager, execution='pending')
    dispatching, dispatch_params = make_ticket(manager, execution='dispatch')
    approve(manager, dispatching, dispatch_params)
    assert manager.begin_dispatch(dispatching.id, worker_id='w')['dispatch'] is True

    manager.advance_security_epoch()
    assert manager.record(pending.id)['status'] == 'invalidated'
    assert manager.record(dispatching.id)['status'] == 'recovery_required'
    with pytest.raises(PermissionError):
        approve(manager, pending, pending_params)


def test_scope_tampering_device_session_owner_and_payload_fail_closed(tmp_path):
    manager = ApprovalManager(path=tmp_path / 'trusted-actions.sqlite3')
    ticket, params = make_ticket(manager)
    changed = dict(params); changed['recipient'] = 'other@example.com'
    with pytest.raises(PermissionError):
        manager.approve(ticket.id, 'e1', 'send_message', changed, owner_id='owner', device_id='d1', session_id='s1', destination=changed['recipient'], data_classification='internal')
    with pytest.raises(PermissionError):
        manager.approve(ticket.id, 'e1', 'send_message', params, owner_id='owner', device_id='d2', session_id='s1', destination=params['recipient'], data_classification='internal')
    with pytest.raises(PermissionError):
        manager.approve(ticket.id, 'e1', 'send_message', params, owner_id='owner', device_id='d1', session_id='s2', destination=params['recipient'], data_classification='internal')
    with pytest.raises(PermissionError):
        manager.approve(ticket.id, 'e1', 'send_message', params, owner_id='attacker', device_id='d1', session_id='s1', destination=params['recipient'], data_classification='internal')
    assert manager.record(ticket.id)['status'] == 'pending'


def test_denial_is_durable_and_cannot_be_reapproved(tmp_path):
    path = tmp_path / 'trusted-actions.sqlite3'
    manager = ApprovalManager(path=path)
    ticket, params = make_ticket(manager)
    assert manager.reject(ticket.id, device_id='d1', session_id='s1') is True
    assert ApprovalManager(path=path).record(ticket.id)['status'] == 'rejected'
    with pytest.raises(PermissionError):
        approve(ApprovalManager(path=path), ticket, params)


def test_safe_pending_query_exposes_no_raw_parameters(tmp_path):
    manager = ApprovalManager(path=tmp_path / 'trusted-actions.sqlite3')
    ticket, _ = make_ticket(manager)
    rows = manager.list_pending(owner_id='owner', device_id='d1', session_id='s1')
    assert len(rows) == 1 and rows[0]['approval_id'] == ticket.id
    assert 'parameters' not in rows[0]
    assert 'payload_json' not in rows[0]
