from pathlib import Path

def test_w8_tests_use_test_domains_or_loopback_only():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('tests').glob('test_w8_*.py'))
    assert 'api.openai.com' not in combined
    assert 'openrouter.ai/api' not in combined
    assert 'generativelanguage.googleapis.com' not in combined
