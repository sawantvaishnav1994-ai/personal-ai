from pathlib import Path


def test_w8_implementation_does_not_contain_deployment_actions():
    files=[Path('models/resilience.py'),Path('models/governed_router.py'),Path('app/main.py')]
    combined='\n'.join(p.read_text(encoding='utf-8') for p in files).lower()
    for forbidden in ('railway up','railway deploy','vercel deploy','kubectl apply','terraform apply'):
        assert forbidden not in combined
