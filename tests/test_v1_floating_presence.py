from __future__ import annotations

from core.events import EventBus
from core.runtime_state import RuntimeState
from desktop.floating_presence import PresenceController


def test_presence_tracks_only_canonical_runtime_state(tmp_path):
    events = EventBus()
    controller = PresenceController(events, tmp_path / 'presence.json')
    events.emit('state', state='active')
    events.emit('state', state='listening')
    assert controller.state is RuntimeState.LISTENING
    controller.close()


def test_presence_position_is_clamped_inside_available_screen():
    assert PresenceController.clamp_position(
        -500, 9000, left=0, top=0, right=1920, bottom=1080, width=118, height=118,
    ) == (0, 962)
    assert PresenceController.clamp_position(
        2500, -20, left=1920, top=0, right=3840, bottom=2160, width=330, height=230,
    ) == (3510, 0)


def test_presence_position_survives_restart(tmp_path):
    path = tmp_path / 'presence.json'
    first = PresenceController(EventBus(), path)
    first.save_position(321, 654)
    first.close()
    second = PresenceController(EventBus(), path)
    assert second.position == (321, 654)
    second.close()


def test_presence_does_not_invent_state_from_position_or_panel_state(tmp_path):
    events = EventBus()
    controller = PresenceController(events, tmp_path / 'presence.json')
    controller.save_position(10, 20)
    assert controller.state is RuntimeState.IDLE
    events.runtime_state.transition(RuntimeState.BACKGROUND, reason='real_background_work')
    assert controller.state is RuntimeState.BACKGROUND
    controller.close()
