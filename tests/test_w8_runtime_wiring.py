from pathlib import Path


def test_runtime_constructs_governed_router_once():
    text=Path('app/main.py').read_text(encoding='utf-8')
    assert text.count('GovernedModelRouter(settings')==1
    assert 'ModelRouter(settings' not in text


def test_model_status_is_owner_visible_in_settings_only():
    text=Path('ui/settings_panel.py').read_text(encoding='utf-8')
    assert 'model_view' in text and 'health_status' in text
