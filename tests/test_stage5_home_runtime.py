from pathlib import Path

import pytest

from core.events import EventBus
from core.home_state_projection import SAFE_STATE_LABELS, project_home_state
from core.runtime_state import RuntimeState, RuntimeStateAuthority


ALL_STATES = list(RuntimeState)


def authority():
    events = EventBus()
    state = RuntimeStateAuthority(events)
    return events, state


def test_single_runtime_state_authority_is_event_bus_authority():
    events = EventBus()
    assert isinstance(events.runtime_state, RuntimeStateAuthority)
    assert events.runtime_state is events.runtime_state


@pytest.mark.parametrize('state', ALL_STATES)
def test_home_projection_covers_every_canonical_state(state):
    events, runtime = authority()
    snapshot = runtime.transition(state, reason='qualification', force=True)
    projected = project_home_state(snapshot).as_dict()
    assert projected['state'] == state.value
    assert projected['label'] == SAFE_STATE_LABELS[state]
    assert projected['schema_version'] == 1


def test_home_projection_rejects_noncanonical_state():
    class Unsafe:
        state = 'SUCCESS'
        sequence = 9
        request_id = 'r1'
    with pytest.raises(ValueError):
        project_home_state(Unsafe())


def test_sequence_is_monotonic_and_duplicate_is_idempotent():
    _, runtime = authority()
    a = runtime.transition(RuntimeState.ACTIVE, reason='a', force=True)
    b = runtime.transition(RuntimeState.ACTIVE, reason='duplicate', force=True)
    c = runtime.transition(RuntimeState.THINKING, reason='c', force=True)
    assert a.sequence == b.sequence
    assert c.sequence == a.sequence + 1


def test_request_r1_r2_isolation_rejects_late_r1():
    _, runtime = authority()
    runtime.transition(RuntimeState.UNDERSTANDING, reason='r1', request_id='r1', activate_request=True)
    runtime.transition(RuntimeState.UNDERSTANDING, reason='r2', request_id='r2', activate_request=True)
    before = runtime.snapshot()
    late = runtime.transition(RuntimeState.RESPONDING, reason='late-r1', request_id='r1')
    assert late.sequence == before.sequence
    assert late.request_id == 'r2'
    assert runtime.snapshot().state == RuntimeState.UNDERSTANDING


def test_memory_and_knowledge_late_request_states_are_rejected():
    _, runtime = authority()
    runtime.transition(RuntimeState.UNDERSTANDING, reason='r1', request_id='r1', activate_request=True)
    runtime.transition(RuntimeState.MEMORY_RETRIEVAL, reason='memory', request_id='r1')
    runtime.transition(RuntimeState.UNDERSTANDING, reason='r2', request_id='r2', activate_request=True)
    seq = runtime.snapshot().sequence
    runtime.transition(RuntimeState.MEMORY_RETRIEVAL, reason='late-memory', request_id='r1')
    runtime.transition(RuntimeState.KNOWLEDGE_RETRIEVAL, reason='late-knowledge', request_id='r1')
    assert runtime.snapshot().sequence == seq
    assert runtime.snapshot().request_id == 'r2'


def test_illegal_transition_fails_closed():
    _, runtime = authority()
    with pytest.raises(ValueError):
        runtime.transition(RuntimeState.SUCCESS, reason='invented-success')


def test_estop_is_canonical_event_not_home_authority():
    events, runtime = authority()
    events.emit('emergency_stop', request_id=None)
    assert runtime.snapshot().state == RuntimeState.ERROR


def test_voice_listening_and_responding_are_canonical_events():
    events, runtime = authority()
    events.emit('voice.listening.started', request_id='r1')
    assert runtime.snapshot().state == RuntimeState.LISTENING
    runtime.transition(RuntimeState.UNDERSTANDING, reason='heard', request_id='r1', force=True)
    events.emit('voice.tts.started', request_id='r1')
    assert runtime.snapshot().state == RuntimeState.RESPONDING


def test_approval_state_is_canonical_event():
    events, runtime = authority()
    runtime.transition(RuntimeState.UNDERSTANDING, reason='turn', request_id='r1', activate_request=True)
    events.emit('approval.required', request_id='r1')
    assert runtime.snapshot().state == RuntimeState.NEEDS_APPROVAL


def test_background_state_is_canonical_event():
    events, runtime = authority()
    events.emit('automation.started', request_id=None)
    assert runtime.snapshot().state == RuntimeState.BACKGROUND


def test_home_projection_payload_is_redacted():
    _, runtime = authority()
    projected = project_home_state(runtime.snapshot()).as_dict()
    forbidden = {'reason', 'prompt', 'transcript', 'tool_args', 'memory', 'knowledge', 'credentials', 'token'}
    assert forbidden.isdisjoint(projected)


def test_pwa_semantic_state_is_projection_only():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert 'if(!applyingCanonicalState)return;' in source
    assert "api('/runtime-state')" in source
    assert 'sequence<=canonicalSequence' in source
    assert 'network status is not semantic AI state' in source


def test_home_uses_canonical_turn_and_voice_transport():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8')
    assert "api('/voice/turn'" in source
    assert "api('/voice/client-event'" in source
    assert "api('/voice/barge'" in source


def test_home_has_no_direct_provider_or_privileged_tool_transport():
    source = Path('pwa/v1-runtime.js').read_text(encoding='utf-8').lower()
    assert 'api.openai.com' not in source
    assert 'generativelanguage.googleapis.com' not in source
    assert 'api.anthropic.com' not in source
    assert "api('/tool" not in source
    assert "api('/audit" not in source


def test_home_state_endpoint_is_authenticated_and_redacted():
    source = Path('server/runtime_state_api.py').read_text(encoding='utf-8')
    assert 'current_trusted_request' in source
    assert "registry.authorize(context.device_id, 'ai:chat')" in source
    assert 'project_home_state(authority.snapshot()).as_dict()' in source
    assert "'reason'" not in source
