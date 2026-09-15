from pathlib import Path

def test_w8_tests_contain_no_real_paid_provider_key_environment_reads():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('tests').glob('test_w8_*.py'));assert 'OPENAI_API_KEY' not in combined and 'GEMINI_API_KEY' not in combined and 'OPENROUTER_API_KEY' not in combined
