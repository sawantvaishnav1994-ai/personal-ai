from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from threading import RLock

from memory.policy import is_never_store
from memory.second_brain import MemoryCandidate


class GovernedMemory:
    """Owner-control gate around the canonical SecondBrain.

    Unverified model/agent/proactive suggestions are candidates, not durable
    Personal Memory. Only explicitly verified/owner-supported candidates are
    allowed to enter the canonical memory store. Normal unverified suggestions
    are quarantined for owner review; sensitive/never-store suggestions are not
    persisted as candidates at all.
    """

    CANONICAL_OWNER = 'owner'
    EXPLICIT_SOURCES = frozenset({
        'user', 'user-message', 'explicit-user', 'explicit-owner',
        'owner-confirmed', 'owner-import',
    })

    def __init__(self, brain, path: Path, *, events=None):
        self._brain = brain
        self.events = events
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        with self._con() as con:
            con.executescript(
                '''
                CREATE TABLE IF NOT EXISTS memory_candidates(
                    id TEXT PRIMARY KEY,
                    candidate_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_memory_candidates_status
                    ON memory_candidates(status,created_at);
                '''
            )
        try:
            self._brain.store.second_brain = self
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._brain, name)

    def _con(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _emit(self, name: str, **payload):
        if self.events:
            self.events.emit(name, **payload)

    @staticmethod
    def _normalize(candidate: MemoryCandidate) -> dict:
        return {
            'type': str(candidate.type),
            'subject': str(candidate.subject),
            'content': str(candidate.content),
            'confidence': max(0.0, min(1.0, float(candidate.confidence))),
            'source': str(candidate.source or 'unknown'),
            'verified': bool(candidate.verified),
            'tags': list(candidate.tags or []),
            'importance': max(0.0, min(1.0, float(candidate.importance))),
            'sensitivity': str(candidate.sensitivity or 'normal').strip().lower(),
            'occurred_at': candidate.occurred_at,
            'evidence': list(candidate.evidence or []),
            'metadata': dict(candidate.metadata or {}),
            'relationships': list(candidate.relationships or []),
        }

    @classmethod
    def _authoritative(cls, data: dict) -> bool:
        source = str(data.get('source') or '').strip().lower()
        return bool(data.get('verified')) and (
            source in cls.EXPLICIT_SOURCES
            or source.startswith('owner-confirmed:')
            or source.startswith('owner-import:')
        )

    def remember(self, candidate: MemoryCandidate) -> str | None:
        data = self._normalize(candidate)
        sensitivity = data['sensitivity']
        if is_never_store(sensitivity=sensitivity, metadata=data.get('metadata')):
            self._emit('memory.candidate.blocked', reason='never_store', source=data['source'])
            return None
        if self._authoritative(data):
            memory_id = self._brain.remember(candidate)
            self._emit('memory.committed', memory_id=memory_id, source=data['source'], verified=True)
            return memory_id
        if sensitivity != 'normal':
            self._emit('memory.candidate.blocked', reason='sensitive_requires_explicit_owner_write', source=data['source'])
            return None
        candidate_id = str(uuid.uuid4())
        stamp = time.time()
        with self.lock, self._con() as con:
            con.execute(
                '''INSERT INTO memory_candidates(id,candidate_json,source,status,reason,created_at,updated_at)
                   VALUES(?,?,?,'pending','owner_confirmation_required',?,?)''',
                (candidate_id, json.dumps(data, sort_keys=True, default=str), data['source'], stamp, stamp),
            )
        self._emit('memory.candidate.pending', candidate_id=candidate_id, source=data['source'])
        return candidate_id

    def candidates(self, *, status: str = 'pending', limit: int = 100) -> list[dict]:
        bounded = max(1, min(int(limit), 500))
        with self._con() as con:
            rows = con.execute(
                '''SELECT id,candidate_json,source,status,reason,created_at,updated_at
                   FROM memory_candidates WHERE status=? ORDER BY created_at DESC LIMIT ?''',
                (str(status), bounded),
            ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            candidate = json.loads(item.pop('candidate_json'))
            output.append({**item, 'candidate': candidate})
        return output

    def approve_candidate(self, candidate_id: str, *, owner_id: str = CANONICAL_OWNER) -> str:
        if str(owner_id) != self.CANONICAL_OWNER:
            raise PermissionError('only the canonical owner may confirm Personal Memory')
        with self.lock, self._con() as con:
            row = con.execute(
                "SELECT * FROM memory_candidates WHERE id=? AND status='pending'",
                (str(candidate_id),),
            ).fetchone()
            if row is None:
                raise KeyError('pending memory candidate not found')
            data = json.loads(row['candidate_json'])
            con.execute(
                "UPDATE memory_candidates SET status='promoting',updated_at=? WHERE id=?",
                (time.time(), str(candidate_id)),
            )
        candidate = MemoryCandidate(
            type=data['type'],
            subject=data['subject'],
            content=data['content'],
            confidence=float(data.get('confidence', 1.0)),
            source=f"owner-confirmed:{data.get('source') or 'candidate'}",
            verified=True,
            tags=list(data.get('tags') or []),
            importance=float(data.get('importance', 0.5)),
            sensitivity=str(data.get('sensitivity') or 'normal'),
            occurred_at=data.get('occurred_at'),
            evidence=list(data.get('evidence') or []),
            metadata=dict(data.get('metadata') or {}),
            relationships=list(data.get('relationships') or []),
        )
        try:
            memory_id = self._brain.remember(candidate)
        except Exception:
            with self.lock, self._con() as con:
                con.execute(
                    "UPDATE memory_candidates SET status='pending',updated_at=? WHERE id=?",
                    (time.time(), str(candidate_id)),
                )
            raise
        with self.lock, self._con() as con:
            con.execute('DELETE FROM memory_candidates WHERE id=?', (str(candidate_id),))
        self._emit('memory.candidate.approved', candidate_id=str(candidate_id), memory_id=memory_id)
        return memory_id

    def reject_candidate(self, candidate_id: str, *, owner_id: str = CANONICAL_OWNER) -> bool:
        if str(owner_id) != self.CANONICAL_OWNER:
            raise PermissionError('only the canonical owner may reject Personal Memory candidates')
        with self.lock, self._con() as con:
            cur = con.execute('DELETE FROM memory_candidates WHERE id=?', (str(candidate_id),))
        if cur.rowcount:
            self._emit('memory.candidate.rejected', candidate_id=str(candidate_id))
        return cur.rowcount == 1
