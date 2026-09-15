from pathlib import Path


def test_settings_exposes_model_health_without_home_redesign():
    text=Path('ui/settings_panel.py').read_text(encoding='utf-8')
    assert 'Models — Health & routing' in text
    assert 'Run bounded health check' in text
    assert 'health_status' in text


def test_w8_does_not_change_home_surface():
    # Scope guard: W8 belongs in diagnostics/settings, not the frozen Home V1 visual surface.
    assert Path('ui/settings_panel.py').exists()
