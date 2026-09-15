from pathlib import Path

def test_w8_config_has_bounded_operational_defaults():
    text=Path('core/config.py').read_text(encoding='utf-8')
    assert "MODEL_RETRY_ATTEMPTS','1'" in text
    assert "MODEL_MAX_FAILOVERS','3'" in text
    assert "MODEL_RETRY_BACKOFF_SECONDS','0.05'" in text
