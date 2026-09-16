from __future__ import annotations

import pytest

from core.turn_context import current_turn_context
from devices.continuity import ContinuityService
from security.request_context import TrustedRequestContext, reset_trusted_request, set_trusted_request
from server.session_bound_executor import SessionBoundExecutor


class Approvals:
    @staticmethod
    def current_security_epoch():
        return 9


class Executor:
    def __init__(self):
        self.approvals = Approvals()
        self.calls = []
        self.turns = []

    def chat(self, text, **kwargs):
        self.calls.append((text, kwargs))
        self.turns.append(current_turn_context())
        return 'reply'


def test_session_bound_turn_uses_continuity_history_and_canonical_context(tmp_path):
    continuity = ContinuityService(tmp_path / 'continuity.sqlite3')
    thread = continuity.create_thread('Owner conversation', device_id='device-1')
    continuity.append(thread, device_id='device-1', kind='user_message', payload={'text': 'first question'})
    continuity.append(thread, device_id='device-1', kind='assistant_message', payload={'text': 'first answer'})

    raw = Executor()
    bound = SessionBoundExecutor(raw, continuity=continuity, surface='iphone-pwa')
    token = set_trusted_request(TrustedRequestContext('device-1', 'session-1', 123.0))
    try:
        assert bound.chat('follow up', request_id='request-1', input_modality='voice') == 'reply'
    finally:
        reset_trusted_request(token)

    _, kwargs = raw.calls[0]
    assert kwargs['conversation_id'] == thread
    assert kwargs['conversation_history'] == [
        {'role': 'user', 'content': 'first question'},
        {'role': 'assistant', 'content': 'first answer'},
    ]
    turn = raw.turns[0]
    assert turn.request_id == 'request-1'
    assert turn.conversation_id == thread
    assert turn.device_id == 'device-1'
    assert turn.session_id == 'session-1'
    assert turn.security_epoch == 9
    assert turn.surface == 'iphone-pwa'
    assert turn.input_modality == 'voice'
    assert turn.p8_continuity_refs == (thread,)
    assert current_turn_context() is None


def test_explicit_history_remains_bounded(tmp_path):
    continuity = ContinuityService(tmp_path / 'continuity.sqlite3')
    thread = continuity.create_thread('Bounded', device_id='device-1')
    raw = Executor()
    bound = SessionBoundExecutor(raw, continuity=continuity)
    supplied = [{'role': 'user', 'content': f'message-{index}'} for index in range(30)]
    token = set_trusted_request(TrustedRequestContext('device-1', 'session-1', None))
    try:
        bound.chat('latest', conversation_id=thread, conversation_history=supplied)
    finally:
        reset_trusted_request(token)
    assert len(raw.calls[0][1]['conversation_history']) == 16
    assert raw.calls[0][1]['conversation_history'][0]['content'] == 'message-14'


def test_continuity_event_id_is_idempotent_and_conflicts_fail_closed(tmp_path):
    continuity = ContinuityService(tmp_path / 'continuity.sqlite3')
    thread = continuity.create_thread('Durable', device_id='device-1')
    first = continuity.append(
        thread,
        device_id='device-1',
        kind='user_message',
        payload={'text': 'hello'},
        event_id='request-1:user',
    )
    retried = continuity.append(
        thread,
        device_id='device-1',
        kind='user_message',
        payload={'text': 'hello'},
        event_id='request-1:user',
    )

    assert first['duplicate'] is False
    assert retried['duplicate'] is True
    assert retried['sequence'] == first['sequence']
    assert len(continuity.events_for_thread(thread)) == 1

    with pytest.raises(ValueError, match='different content'):
        continuity.append(
            thread,
            device_id='device-1',
            kind='user_message',
            payload={'text': 'tampered'},
            event_id='request-1:user',
        )


def test_continuity_history_returns_latest_bounded_turns(tmp_path):
    continuity = ContinuityService(tmp_path / 'continuity.sqlite3')
    thread = continuity.create_thread('History', device_id='device-1')
    for index in range(20):
        continuity.append(
            thread,
            device_id='device-1',
            kind='user_message' if index % 2 == 0 else 'assistant_message',
            payload={'text': f'message-{index}'},
        )
    history = continuity.conversation_history(thread, limit=6)
    assert [item['content'] for item in history] == [f'message-{index}' for index in range(14, 20)]
    assert [item['role'] for item in history] == ['user', 'assistant', 'user', 'assistant', 'user', 'assistant']
