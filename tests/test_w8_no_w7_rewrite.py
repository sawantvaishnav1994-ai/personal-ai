from pathlib import Path

def test_w8_model_modules_do_not_import_w7_operator_implementations():
    combined=Path('models/resilience.py').read_text(encoding='utf-8')+Path('models/governed_router.py').read_text(encoding='utf-8');assert 'recovery.operator_recovery' not in combined and 'browser.safe_operator' not in combined and 'desktop.safe_desktop_operator' not in combined
