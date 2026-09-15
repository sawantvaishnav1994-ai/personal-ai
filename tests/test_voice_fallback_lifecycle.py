from __future__ import annotations

import threading
from types import SimpleNamespace

from agent.executor import ExecutionCancelled
from voice.full_duplex import FullDuplexVoiceSession


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


def test_cancelled_turn_suppresses_late_reply_and_tts():
    events = Events()
    session = FullDuplexVoiceSession(Models(), CancelAfterReturnExecutor(), events)
    cancel = threading.Event()
    session._turn_cancel = cancel

    session._respond('hello', cancel)

    names = [name for name, _ in events.rows]
    assert 'voice.reply' not in names
    assert 'state' in names
    assert session._turn_cancel is None


def test_execution_cancelled_returns_to_listening_when_session_remains_active():
    events = Events()
    session = FullDuplexVoiceSession(Models(), CancelledExecutor(), events)
    cancel = threading.Event()
    session._turn_cancel = cancel

    session._respond('hello', cancel)

    assert ('voice.turn.cancelled', {}) in events.rows
    assert any(name == 'state' and payload.get('state') == 'listening' for name, payload in events.rows)
    assert session._turn_cancel is None


def test_stop_cancels_turn_and_drains_pending_audio_blocks():
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
    assert any(name == 'state' and payload.get('state') == 'idle' for name, payload in events.rows)
