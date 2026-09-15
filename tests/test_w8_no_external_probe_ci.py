from pathlib import Path

def test_w8_ci_tests_mock_requests_for_probe_paths():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('tests').glob('test_w8_*.py'));assert 'requests.get(' not in combined and 'requests.post(' not in combined
