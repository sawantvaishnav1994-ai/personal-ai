from pathlib import Path


def test_w8_runtime_uses_existing_router_extension_not_parallel_model_stack():
    text=Path('app/main.py').read_text(encoding='utf-8')
    assert 'GovernedModelRouter' in text
    assert 'models.governed_router' in text


def test_w8_does_not_modify_frozen_w7_authority_modules():
    # Release evidence compares the branch against dad974fc; this sentinel prevents W8 tests
    # from normalizing direct imports of recovery/browser/desktop as a new model authority.
    text=Path('models/governed_router.py').read_text(encoding='utf-8')
    assert 'recovery.' not in text and 'browser.' not in text and 'desktop.' not in text


def test_w8_telemetry_allowlist_excludes_sensitive_payload_names():
    text=Path('models/resilience.py').read_text(encoding='utf-8')
    for forbidden in ("'prompt'", "'messages'", "'api_key'", "'authorization'", "'cookie'", "'password'", "'response'"):
        assert forbidden not in text.split('SAFE_FIELDS =',1)[1].split('}',1)[0]


def test_no_real_provider_credentials_or_paid_probe_in_tests():
    combined='\n'.join(path.read_text(encoding='utf-8') for path in Path('tests').glob('test_w8_*.py'))
    assert 'api.openai.com' not in combined
    assert 'generativelanguage.googleapis.com' not in combined
    assert 'sk-' not in combined
