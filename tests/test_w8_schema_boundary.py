from pathlib import Path


def test_w8_introduces_no_database_schema_migration():
    for path in (Path('models/resilience.py'),Path('models/governed_router.py')):
        text=path.read_text(encoding='utf-8').lower()
        assert 'create table' not in text and 'alter table' not in text and 'schema_version' not in text
