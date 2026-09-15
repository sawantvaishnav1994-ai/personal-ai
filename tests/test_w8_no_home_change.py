from pathlib import Path

def test_w8_owner_visibility_is_settings_based():
    text=Path('ui/settings_panel.py').read_text(encoding='utf-8')
    assert 'Models — Health & routing' in text
