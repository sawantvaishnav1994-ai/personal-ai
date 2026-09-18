from __future__ import annotations

import threading
from types import SimpleNamespace

from agent.executor import ExecutionCancelled
from voice.full_duplex import FullDuplexVoiceSession
from voice.realtime import RealtimeVoiceSession


class Events:
    def __init__(self):
        self.rows = []

    def emit(self, name, **payload):
        self.rows.append((name, payload))


class Models:
    def __init__(self):
        self.settings = SimpleNamespace(
            voice_personality='calm',
            voice_speaking_rate=1.0,
            voice_min_endpoint_ms=420,
            voice_max_endpoint_ms=1100,
            voice_noise_multiplier=2.4,
            voice_min_threshold=0.008,
            voice_max_utterance_seconds=45.0,
            voice_input_device='',
            voice_output_device='',
        )

    def synthesize(self, text):
        raise AssertionError('cancelled turn must never synthesize stale speech')


class CancelAfterReturnExecutor:
    def chat(self, text, cancel_event=None):
        cancel_event.set()
        return 'stale response'


class CancelledExecutor:
    def chat(self, text, cancel_event=None):
        raise ExecutionCancelled('cancelled')


class CanonicalCancelProbe:
    def __init__(self):
        self.cancelled = []

    def chat(self, text, cancel_event=None, **kwargs):
        return 'ok'

    def cancel_turn(self, request_id, device_id=None):
        self.cancelled.append((request_id, device_id))
        return {'request_id': request_id, 'status': 'cancelled'}


class AliveThread:
    def is_alive(self):
        return True


def test_cancelled_turn_suppresses_late_reply_and_tts_without_legacy_state_writer():
    events = Events()
    session = FullDuplexVoiceSession(Models(), CancelAfterReturnExecutor(), events)
    cancel = threading.Event()
    session._turn_cancel = cancel

    session._respond('hello', cancel)

    names = [name for name, _ in events.rows]
    assert 'voice.reply' not in names
    assert 'voice.output.stale_ignored' in names
    assert 'state' not in names
    assert session._turn_cancel is None


def test_execution_cancelled_returns_to_factual_listening_lifecycle():
    events = Events()
    session = FullDuplexVoiceSession(Models(), CancelledExecutor(), events)
    cancel = threading.Event()
    session._turn_cancel = cancel

    session._respond('hello', cancel)

    names = [name for name, _ in events.rows]
    assert 'voice.turn.cancelled' in names
    assert 'voice.listening.started' in names
    assert 'state' not in names
    assert session._turn_cancel is None


def test_stop_cancels_turn_drains_audio_and_emits_factual_session_stop():
    events = Events()
    session = FullDuplexVoiceSession(Models(), CancelAfterReturnExecutor(), events)
    cancel = threading.Event()
    session._turn_cancel = cancel
    session._q.put_nowait(b'old-audio')

    session.stop()
    session.stop()

    assert cancel.is_set()
    assert session._turn_cancel is None
    assert session._q.empty()
    assert any(name == 'voice.session.stopped' for name, _ in events.rows)
    assert not any(name == 'state' for name, _ in events.rows)


def test_public_barge_in_interrupts_and_durably_cancels_inflight_canonical_turn():
    events = Events()
    executor = CanonicalCancelProbe()
    session = FullDuplexVoiceSession(Models(), executor, events)
    cancel = threading.Event()
    session._current_request_id = 'voice-request-1'
    session._turn_cancel = cancel

    result = session.barge_in()

    assert cancel.is_set()
    assert executor.cancelled == [('voice-request-1', 'desktop')]
    assert result == {
        'interrupted': True,
        'request_id': 'voice-request-1',
        'canonical_turn_cancelled': True,
    }
    barge = next(payload for name, payload in events.rows if name == 'voice.barge_in')
    assert barge['request_id'] == 'voice-request-1'
    assert barge['canonical_turn_cancelled'] is True


def test_playback_only_barge_in_does_not_retroactively_cancel_completed_turn():
    events = Events()
    executor = CanonicalCancelProbe()
    session = FullDuplexVoiceSession(Models(), executor, events)
    session._current_request_id = 'completed-request'
    session._play_thread = AliveThread()

    result = session.barge_in()

    assert result['interrupted'] is True
    assert result['canonical_turn_cancelled'] is False
    assert executor.cancelled == []
    assert session._barge.is_set()


def test_stop_durably_cancels_inflight_canonical_voice_turn():
    executor = CanonicalCancelProbe()
    session = FullDuplexVoiceSession(Models(), executor, Events())
    cancel = threading.Event()
    session._current_request_id = 'voice-request-stop'
    session._turn_cancel = cancel

    session.stop()

    assert cancel.is_set()
    assert executor.cancelled == [('voice-request-stop', 'desktop')]
    assert session.running is False


def test_realtime_voice_facade_exposes_truthful_running_and_public_barge_in():
    executor = CanonicalCancelProbe()
    voice = RealtimeVoiceSession(Models(), executor, Events())
    voice.backend.thread = AliveThread()
    voice.backend._current_request_id = 'voice-request-2'
    voice.backend._turn_cancel = threading.Event()

    assert voice.running is True
    result = voice.barge_in()

    assert result['interrupted'] is True
    assert result['canonical_turn_cancelled'] is True
    assert executor.cancelled == [('voice-request-2', 'desktop')]
