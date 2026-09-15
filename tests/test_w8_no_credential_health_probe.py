from pathlib import Path

def test_health_probe_does_not_construct_new_auth_logic():
    health=Path('models/governed_router.py').read_text(encoding='utf-8').split('def health_status',1)[1]
    assert 'Authorization' not in health and 'api_key' not in health
