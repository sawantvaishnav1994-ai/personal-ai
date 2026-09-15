from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
import time

from future_intelligence.multimodal import SimulatedObservationAdapter, WorldUnderstanding
from recovery.backup import BACKUP_MAGIC, BackupService


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


class Gate:
    def decision(self, phase):
        assert phase == 'p7'
        return type('Decision', (), {'allowed': True, 'reason': 'ok'})()


class FixedKeyStore:
    def get_or_create(self):
        return b'P' * 32


def _world(path):
    return WorldUnderstanding(gate=Gate(), path=path, clock=lambda: NOW)


def test_p7_encrypted_backup_restore_preserves_governed_observation_state(tmp_path):
    source = tmp_path / 'source'
    target = tmp_path / 'target'
    source.mkdir()
    target.mkdir()
    source_db = source / 'future-intelligence' / 'world.sqlite3'
    source_db.parent.mkdir(parents=True)

    w = _world(source_db)
    screen = SimulatedObservationAdapter('screen-fixture', 'screen')
    active = screen.ingest(w, {'title': 'Home'}, source_event_id='active-event')
    w.record_capability('physical-offline', 'camera', 'offline', device_id='device-offline')

    raw = w.ingest(
        'document', {'name': 'source'}, source='owner-upload', source_event_id='raw-source',
        retention_policy='long', privacy_classification='internal',
    )
    child = w.ingest(
        'document', {'facts': ['one']}, source='extractor', source_event_id='derived-source',
        lineage_stage='derived', parent_observation_ids=[raw['id']], derivation_type='extract',
        retention_policy='long', privacy_classification='internal',
    )

    deleted = w.ingest('image', {'fixture': 'delete-me'}, source='fixture', source_event_id='delete-source')
    deleted_child = w.ingest(
        'image', {'facts': ['x']}, source='extractor', source_event_id='delete-child',
        lineage_stage='derived', parent_observation_ids=[deleted['id']], derivation_type='extract',
    )
    assert w.delete(deleted['id']) is True
    assert w.get(deleted_child['id']) is None

    backup = BackupService(source, root_key_store=FixedKeyStore())
    archive = backup.create('p7-state.paibackup')
    assert archive.read_bytes().startswith(BACKUP_MAGIC)
    manifest = backup.inspect(archive)
    assert manifest['encrypted'] is True
    assert any(row['path'] == 'future-intelligence/world.sqlite3' for row in manifest['files'])

    result = BackupService(target, root_key_store=FixedKeyStore()).restore(archive)
    assert result['ok'] is True
    assert result['encrypted'] is True

    restored_db = target / 'future-intelligence' / 'world.sqlite3'
    with sqlite3.connect(restored_db) as con:
        assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'

    restored = _world(restored_db)
    assert restored.storage_status()['loaded_observations_in_memory'] == 0
    assert restored.get(active['id'])['source_event_id'] == 'active-event'
    assert restored.get(raw['id'], allowed_classifications={'internal'})['retention_policy'] == 'long'
    assert restored.get(child['id'], allowed_classifications={'internal'})['parent_observation_ids'] == [raw['id']]
    assert [row['observation_id'] for row in restored.lineage(child['id'], allowed_classifications={'internal'})] == [child['id'], raw['id']]
    assert restored.capability('physical-offline')['state'] == 'offline'
    assert restored.get(deleted['id']) is None
    assert restored.get(deleted_child['id']) is None
    assert restored._get_unfiltered(deleted_child['id'])['retention_state'] == 'deleted'

    duplicate = SimulatedObservationAdapter('screen-fixture', 'screen').ingest(
        restored, {'title': 'Home'}, source_event_id='active-event'
    )
    assert duplicate['id'] == active['id']
    assert duplicate['duplicate'] is True


def test_p7_indexed_queries_and_startup_are_bounded(tmp_path):
    db = tmp_path / 'world.sqlite3'
    w = _world(db)
    for index in range(1200):
        modality = 'screen' if index % 2 == 0 else 'document'
        w.ingest(
            modality,
            {'index': index},
            source=f'source-{index % 5}',
            source_event_id=f'event-{index}',
            device_id=None,
        )

    status = w.storage_status()
    assert status['observation_count'] == 1200
    assert status['loaded_observations_in_memory'] == 0
    assert status['database_bytes'] > 0

    restarted = _world(db)
    assert restarted.storage_status()['loaded_observations_in_memory'] == 0
    assert len(restarted.recent(limit=11)) == 11
    assert len(restarted.recent(limit=13, modality='screen')) == 13
    assert len(restarted.recent(limit=17, source='source-2')) == 17
    first = restarted.recent(limit=1)[0]
    assert restarted.get(first['id'])['id'] == first['id']

    with sqlite3.connect(db) as con:
        index_names = {row[1] for row in con.execute('PRAGMA index_list(observations)').fetchall()}
        assert 'idx_observations_time' in index_names
        assert 'idx_observations_modality_time' in index_names
        assert 'idx_observations_source_time' in index_names
        assert 'idx_observations_device_time' in index_names
        assert 'idx_observations_source_event' in index_names
        plan = ' '.join(
            str(cell)
            for row in con.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM observations WHERE modality='screen' ORDER BY observed_at DESC LIMIT 10"
            ).fetchall()
            for cell in row
        )
        assert 'idx_observations_modality_time' in plan
        assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_p7_performance_envelope_is_bounded_and_reported(tmp_path, capsys):
    measurements = []
    for label, volume in [('small', 100), ('medium', 600), ('large', 1800)]:
        db = tmp_path / f'{label}.sqlite3'
        started = time.perf_counter()
        w = _world(db)
        for index in range(volume):
            w.ingest(
                'document', {'index': index, 'bucket': index % 10},
                source=f'perf-{index % 10}', source_event_id=f'{label}-{index}',
            )
        ingest_seconds = time.perf_counter() - started

        restart_started = time.perf_counter()
        restarted = _world(db)
        restart_seconds = time.perf_counter() - restart_started

        query_started = time.perf_counter()
        rows = restarted.recent(limit=25, source='perf-3')
        query_seconds = time.perf_counter() - query_started

        duplicate_started = time.perf_counter()
        duplicate = restarted.ingest(
            'document', {'index': 3, 'bucket': 3}, source='perf-3', source_event_id=f'{label}-3'
        )
        duplicate_seconds = time.perf_counter() - duplicate_started

        status = restarted.storage_status()
        assert status['observation_count'] == volume
        assert status['loaded_observations_in_memory'] == 0
        assert 0 < len(rows) <= 25
        assert duplicate['duplicate'] is True
        measurements.append({
            'label': label,
            'observations': volume,
            'ingest_seconds': round(ingest_seconds, 6),
            'restart_seconds': round(restart_seconds, 6),
            'bounded_query_seconds': round(query_seconds, 6),
            'duplicate_seconds': round(duplicate_seconds, 6),
            'database_bytes': status['database_bytes'],
            'loaded_observations_in_memory': status['loaded_observations_in_memory'],
        })

    assert measurements[0]['database_bytes'] < measurements[-1]['database_bytes']
    assert all(row['loaded_observations_in_memory'] == 0 for row in measurements)
    print('P7_PERFORMANCE_RESULTS=' + json.dumps(measurements, sort_keys=True))
    captured = capsys.readouterr().out
    assert 'P7_PERFORMANCE_RESULTS=' in captured
