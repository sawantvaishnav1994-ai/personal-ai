from pathlib import Path

from core.events import EventBus
from core.runtime_state import RuntimeState
from desktop.floating_presence import PresenceController


def test_presence_controller_reconstructs_canonical_snapshot_and_ignores_stale_events(tmp_path):
    events = EventBus()
    events.runtime_state.transition(RuntimeState.ACTIVE, reason='ready')
    controller = PresenceController(events, tmp_path / 'presence.json')
    assert controller.state == RuntimeState.ACTIVE
    assert controller.sequence == events.runtime_state.snapshot().sequence

    events.runtime_state.transition(RuntimeState.LISTENING, reason='voice')
    assert controller.state == RuntimeState.LISTENING
    sequence = controller.sequence
    events.emit('runtime.state', state='ERROR', sequence=sequence)
    assert controller.state == RuntimeState.LISTENING
    assert controller.sequence == sequence
    controller.close()


def test_presence_controller_follows_all_canonical_runtime_states(tmp_path):
    events = EventBus()
    controller = PresenceController(events, tmp_path / 'presence.json')
    sequence = controller.sequence
    states = [
        RuntimeState.ACTIVE, RuntimeState.LISTENING, RuntimeState.UNDERSTANDING,
        RuntimeState.THINKING, RuntimeState.MEMORY_RETRIEVAL,
        RuntimeState.KNOWLEDGE_RETRIEVAL, RuntimeState.TOOL_ACTION,
        RuntimeState.RESPONDING, RuntimeState.NEEDS_APPROVAL,
        RuntimeState.BACKGROUND, RuntimeState.SUCCESS, RuntimeState.WARNING,
        RuntimeState.ERROR, RuntimeState.IDLE,
    ]
    for state in states:
        sequence += 1
        events.emit('runtime.state', state=state.value, sequence=sequence)
        assert controller.state == state
        assert controller.sequence == sequence
    controller.close()


def test_presence_controller_ignores_unknown_duplicate_and_malformed_events(tmp_path):
    events = EventBus()
    controller = PresenceController(events, tmp_path / 'presence.json')
    initial = controller.state
    sequence = controller.sequence
    events.emit('runtime.state', state='NOT_A_STATE', sequence=sequence + 1)
    events.emit('runtime.state', state='ERROR', sequence='bad')
    events.emit('runtime.state', state='ERROR', sequence=sequence)
    assert controller.state == initial
    assert controller.sequence == sequence
    controller.close()


def test_presence_position_persistence_is_bounded_on_restore(tmp_path):
    path = tmp_path / 'presence.json'
    events = EventBus()
    controller = PresenceController(events, path)
    controller.save_position(9000, -500)
    controller.close()

    restored = PresenceController(events, path)
    assert restored.position == (9000, -500)
    assert restored.clamp_position(
        *restored.position, left=0, top=0, right=1920, bottom=1080, width=118, height=118,
    ) == (1802, 0)
    restored.close()


def test_presence_controller_unsubscribes_on_close(tmp_path):
    events = EventBus()
    controller = PresenceController(events, tmp_path / 'presence.json')
    state = controller.state
    sequence = controller.sequence
    controller.close()
    events.emit('runtime.state', state='ERROR', sequence=sequence + 1)
    assert controller.state == state
    assert controller.sequence == sequence


def test_floating_presence_source_uses_canonical_turn_cancellation():
    source = Path('desktop/floating_presence.py').read_text(encoding='utf-8')
    assert "request_id=request_id" in source
    assert "cancel_event=cancel_event" in source
    assert "self.executor.cancel_turn(request_id, device_id='desktop')" in source
    assert "presence.cancel.requested" not in source
