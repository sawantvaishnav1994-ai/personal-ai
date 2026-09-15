from pathlib import Path

def test_existing_provider_adapter_remains_separate_from_w8_governance():
    assert Path('models/router.py').exists() and Path('models/governed_router.py').exists()
    assert 'class GovernedModelRouter(ModelRouter)' in Path('models/governed_router.py').read_text(encoding='utf-8')
