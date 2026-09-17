from core.events import EventBus
from core.runtime_state import RuntimeState


def _r2_thinking(events: EventBus):
    events.emit('turn.started', request_id='r2')
    events.runtime_state.transition(RuntimeState.THINKING, reason='r2-thinking', request_id='r2')
    snapshot = events.runtime_state.snapshot()
    assert snapshot.request_id == 'r2'
    assert snapshot.state is RuntimeState.THINKING
    return snapshot


def test_unscoped_workflow_started_from_idle_projects_background_without_foreground_owner():
    events = EventBus()
    events.emit('workflow.started', run_id='w1')
    snapshot = events.runtime_state.snapshot()
    assert snapshot.state is RuntimeState.BACKGROUND
    assert snapshot.request_id is None


def test_unscoped_background_start_cannot_take_over_active_r2_thinking():
    events = EventBus()
    before = _r2_thinking(events)
    events.emit('workflow.started', run_id='w1')
    assert events.runtime_state.snapshot() == before


def test_unscoped_background_agent_states_do_not_escape_background_projection():
    events = EventBus()
    events.emit('workflow.started', run_id='w1')
    before = events.runtime_state.snapshot()
    assert before.state is RuntimeState.BACKGROUND
    assert before.request_id is None

    for state in ('thinking', 'acting', 'speaking', 'success', 'error'):
        events.emit('state', state=state)
        assert events.runtime_state.snapshot() == before
    events.emit('tool.unverified', reason='background verification unavailable')
    assert events.runtime_state.snapshot() == before


def test_active_r2_survives_late_unscoped_background_events_after_takeover():
    events = EventBus()
    events.emit('workflow.started', run_id='w1')
    events.emit('turn.started', request_id='r2')
    before = events.runtime_state.snapshot()
    assert before.state is RuntimeState.UNDERSTANDING
    assert before.request_id == 'r2'

    events.emit('workflow.started', run_id='w2')
    events.emit('state', state='thinking')
    events.emit('tool.unverified', reason='background warning')
    assert events.runtime_state.snapshot() == before


def test_scoped_foreground_request_can_intentionally_detach_to_background():
    events = EventBus()
    _r2_thinking(events)
    events.emit('workflow.started', request_id='r2', run_id='w1')
    detached = events.runtime_state.snapshot()
    assert detached.state is RuntimeState.BACKGROUND
    assert detached.request_id == 'r2'

    events.emit('state', state='thinking')
    events.emit('tool.unverified', reason='unscoped background work')
    assert events.runtime_state.snapshot() == detached


def test_terminal_foreground_owner_can_yield_to_unscoped_background_and_cannot_resurrect():
    events = EventBus()
    events.emit('turn.started', request_id='r1')
    events.runtime_state.transition(RuntimeState.RESPONDING, reason='reply', request_id='r1')
    events.emit('turn.completed', request_id='r1')
    terminal = events.runtime_state.snapshot()
    assert terminal.state is RuntimeState.SUCCESS
    assert terminal.request_id == 'r1'

    events.emit('workflow.started', run_id='w1')
    background = events.runtime_state.snapshot()
    assert background.state is RuntimeState.BACKGROUND
    assert background.request_id is None

    events.emit('state', state='thinking', request_id='r1')
    events.emit('tool.unverified', request_id='r1', reason='late-r1')
    events.emit('turn.started', request_id='r1')
    assert events.runtime_state.snapshot() == background


def test_stale_r1_scoped_background_start_cannot_move_r2():
    events = EventBus()
    events.emit('turn.started', request_id='r1')
    events.emit('turn.started', request_id='r2')
    events.runtime_state.transition(RuntimeState.THINKING, reason='r2-thinking', request_id='r2')
    before = events.runtime_state.snapshot()

    events.emit('workflow.started', request_id='r1', run_id='late-r1')
    assert events.runtime_state.snapshot() == before
