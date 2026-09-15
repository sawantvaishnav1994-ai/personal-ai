from pathlib import Path

def test_w8_tests_do_not_require_optional_local_model_process():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('tests').glob('test_w8_*.py'));assert 'subprocess.run' not in combined and 'ollama pull' not in combined
