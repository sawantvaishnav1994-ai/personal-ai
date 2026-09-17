from pathlib import Path

import pytest

from core.events import EventBus
from core.runtime_presentation import PRESENTATIONS, presentation_for
from core.runtime_state import RuntimeState
from desktop.floating_presence import PresenceController


@pytest.mark.parametrize('state', list(RuntimeState))
def test_every_canonical_state_has_one_presentation(state):
    p = presentation_for(state)
    assert p is not None
    assert p.state is state
    assert p.label.strip()
    assert p.visual.strip()


def test_presentation_map_exactly_matches_runtime_vocabulary():
    assert set(PRESENTATIONS) == set(RuntimeState)


def test_unknown_future_state_is_not_reinterpreted():
    assert presentation_for('FUTURE_NEURAL_STATE') is None


def test_unknown_empty_state_is_not_idle():
    assert presentation_for('') is None


def test_terminal_success_is_distinct():
    assert presentation_for(RuntimeState.SUCCESS).visual == 'success'
    assert presentation_for(RuntimeState.SUCCESS).attention == 'success'


def test_warning_is_distinct_and_non_success():
    warning = presentation_for(RuntimeState.WARNING)
    assert warning.visual == 'warning'
    assert warning.visual != presentation_for(RuntimeState.SUCCESS).visual


def test_error_is_distinct_and_accessible():
    error = presentation_for(RuntimeState.ERROR)
    assert error.visual == 'error'
    assert 'continue' in error.label.lower()


def test_approval_has_explicit_non_animation_label():
    approval = presentation_for(RuntimeState.NEEDS_APPROVAL)
    assert approval.attention == 'approval'
    assert approval.label == 'Needs approval'


def test_memory_and_knowledge_remain_visually_distinct():
    assert presentation_for(RuntimeState.MEMORY_RETRIEVAL).visual != presentation_for(RuntimeState.KNOWLEDGE_RETRIEVAL).visual


def test_tool_action_is_not_approval_or_success():
    action = presentation_for(RuntimeState.TOOL_ACTION).visual
    assert action not in {'approval', 'success'}


def test_background_is_not_foreground_thinking():
    assert presentation_for(RuntimeState.BACKGROUND).visual != presentation_for(RuntimeState.THINKING).visual


def test_floating_presence_starts_from_canonical_snapshot(tmp_path):
    events = EventBus()
    events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
    controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        assert controller.state is RuntimeState.ACTIVE
        assert controller.sequence == events.runtime_state.snapshot().sequence
    finally:
        controller.close()


def test_floating_presence_tracks_canonical_sequence(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
        snapshot = events.runtime_state.snapshot()
        assert controller.state is RuntimeState.ACTIVE
        assert controller.sequence == snapshot.sequence
    finally:
        controller.close()


def test_floating_presence_rejects_duplicate_sequence(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
        before = (controller.state, controller.sequence)
        controller._on_runtime_state({'state': 'ERROR', 'sequence': controller.sequence})
        assert (controller.state, controller.sequence) == before
    finally:
        controller.close()


def test_floating_presence_rejects_out_of_order_sequence(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
        before = (controller.state, controller.sequence)
        controller._on_runtime_state({'state': 'ERROR', 'sequence': controller.sequence - 1})
        assert (controller.state, controller.sequence) == before
    finally:
        controller.close()


def test_floating_presence_unknown_state_preserves_truth(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
        before = (controller.state, controller.sequence)
        controller._on_runtime_state({'state': 'FUTURE_STATE', 'sequence': controller.sequence + 1})
        assert (controller.state, controller.sequence) == before
    finally:
        controller.close()


def test_floating_presence_missing_sequence_fails_safe(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    try:
        before = (controller.state, controller.sequence)
        controller._on_runtime_state({'state': 'ERROR'})
        assert (controller.state, controller.sequence) == before
    finally:
        controller.close()


def test_floating_presence_unsubscribes_on_close(tmp_path):
    events = EventBus(); controller = PresenceController(events, tmp_path / 'presence.json')
    controller.close()
    before = (controller.state, controller.sequence)
    events.runtime_state.transition(RuntimeState.ACTIVE, reason='owner')
    assert (controller.state, controller.sequence) == before


def test_floating_presence_is_projection_not_authority_source():
    source = Path('desktop/floating_presence.py').read_text(encoding='utf-8')
    assert 'RuntimeStateAuthority(' not in source
    assert "subscribe('runtime.state'" in source
    assert 'events.runtime_state.snapshot()' in source


def test_floating_presence_has_no_direct_provider_calls():
    source = Path('desktop/floating_presence.py').read_text(encoding='utf-8').lower()
    for provider in ('api.openai.com', 'api.anthropic.com', 'generativelanguage.googleapis.com'):
        assert provider not in source


def test_pulse_has_all_terminal_visuals():
    source = Path('ui/pulse.py').read_text(encoding='utf-8')
    assert '"success"' in source
    assert '"warning"' in source
    assert '"error"' in source


def test_pulse_reduced_motion_preserves_state_rendering():
    source = Path('ui/pulse.py').read_text(encoding='utf-8')
    assert 'set_reduce_motion' in source
    assert '120 if self.reduce_motion else 16' in source
    assert 'STATE_ENERGY[self.state]' in source


def test_pulse_unknown_visual_is_warning_not_success():
    source = Path('ui/pulse.py').read_text(encoding='utf-8')
    assert 'else "warning"' in source


def test_pwa_controller_has_single_poll_timer_and_inflight_guard():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert 'statePollTimer' in source
    assert 'stateRefreshInFlight' in source
    assert 'clearTimeout(statePollTimer)' in source


def test_pwa_hidden_tab_does_not_poll_runtime_state():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert "document.visibilityState==='hidden'" in source


def test_pwa_reconnect_backoff_is_bounded():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert 'STATE_BACKOFF_MAX_MS=12000' in source
    assert 'Math.min(STATE_BACKOFF_MAX_MS' in source


def test_pwa_pagehide_closes_state_controller():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert "addEventListener('pagehide'" in source
    assert 'stateControllerClosed=true' in source


def test_pwa_visibility_reconnect_fetches_canonical_snapshot():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert "addEventListener('visibilitychange'" in source
    assert 'refreshCanonicalState' in source


def test_pwa_unknown_state_is_rejected_before_render():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert '!CANONICAL_STATES.has(canonicalName)' in source


def test_pwa_sequence_prevents_visual_rollback():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert 'sequence<=canonicalSequence' in source


def test_pwa_runtime_snapshot_is_redacted_projection():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert 'personalAiRuntimeStateSnapshot' in source
    assert 'reason:' not in source


def test_runtime_state_api_does_not_return_internal_reason():
    source = Path('server/runtime_state_api.py').read_text(encoding='utf-8')
    assert 'project_home_state(authority.snapshot()).as_dict()' in source
    assert "'reason'" not in source


def test_runtime_presentation_has_no_execution_dependencies():
    source = Path('core/runtime_presentation.py').read_text(encoding='utf-8').lower()
    for forbidden in ('executor', 'model', 'tool', 'memory.', 'knowledge.', 'approval_id', 'oauth', 'token'):
        assert forbidden not in source


def test_desktop_legacy_home_fake_semantic_state_is_detected_until_repaired():
    # Stage-5 closure must remove these; this deliberately keeps the candidate red
    # until the desktop Home is converted to canonical runtime.state projection.
    source = Path('ui/main_window.py').read_text(encoding='utf-8')
    forbidden = ['self._set_state("listening")', 'self._set_state("thinking")', 'self._set_state("speaking")', 'QTimer.singleShot(1100, lambda: self._set_state("idle"))']
    assert not any(item in source for item in forbidden), 'desktop Home still invents semantic runtime state'
