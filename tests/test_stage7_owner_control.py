from pathlib import Path


def test_owner_control_device_view_is_safe_live_presence_projection():
    source = Path('ui/control_panel.py').read_text(encoding='utf-8')
    assert "OWNER CONTROL CENTER" in source
    assert "Devices & Presence" in source
    assert "device_gateway'].online()" in source
    assert "'presence_state':'online'" in source
    assert "'trust_state':'trusted'" in source
    assert "self.views['Devices'].setPlainText(json.dumps(rt['device_registry'].list()" not in source


def test_owner_control_does_not_invent_stage7_privacy_authority():
    source = Path('ui/control_panel.py').read_text(encoding='utf-8')
    assert 'LOCAL_ONLY' not in source
    assert 'LOCAL_PREFERRED' not in source
    assert 'EXTERNAL_ALLOWED' not in source
