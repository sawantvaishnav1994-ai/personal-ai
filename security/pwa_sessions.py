from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PwaSession:
    id: str
    device_id: str
    created_at: float
    last_seen_at: float
    expires_at: float
    reauthenticated_at: float | None


class PwaSessionStore:
    """Opaque, durable browser sessions bound to one trusted device."""

    def __init__(self, path: Path, *, ttl_seconds: int = 60 * 60 * 24 * 30):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = max(300, min(int(ttl_seconds), 60 * 60 * 24 * 365))
        with self._con() as con:
            con.execute(
                '''CREATE TABLE IF NOT EXISTS pwa_sessions(
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at REAL NOT NULL,
                    last_seen_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    reauthenticated_at REAL,
                    revoked_at REAL
                )'''
            )
            con.execute('CREATE INDEX IF NOT EXISTS idx_pwa_sessions_device ON pwa_sessions(device_id,revoked_at)')

    def _con(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(str(token).encode('utf-8')).hexdigest()

    @staticmethod
    def _row(row) -> PwaSession:
        return PwaSession(
            id=row['id'],
            device_id=row['device_id'],
            created_at=float(row['created_at']),
            last_seen_at=float(row['last_seen_at']),
            expires_at=float(row['expires_at']),
            reauthenticated_at=float(row['reauthenticated_at']) if row['reauthenticated_at'] is not None else None,
        )

    def issue(self, device_id: str, *, reauthenticated: bool = True) -> tuple[str, PwaSession]:
        now = time.time()
        token = secrets.token_urlsafe(32)
        session_id = str(uuid.uuid4())
        reauth = now if reauthenticated else None
        expires = now + self.ttl_seconds
        with self._con() as con:
            con.execute(
                '''INSERT INTO pwa_sessions(
                    id,device_id,token_hash,created_at,last_seen_at,expires_at,reauthenticated_at,revoked_at
                ) VALUES(?,?,?,?,?,?,?,NULL)''',
                (session_id, str(device_id), self._hash(token), now, now, expires, reauth),
            )
        return token, PwaSession(session_id, str(device_id), now, now, expires, reauth)

    def authenticate(self, token: str | None, device_id: str | None, *, touch: bool = True) -> PwaSession | None:
        if not token or not device_id:
            return None
        now = time.time()
        token_hash = self._hash(token)
        with self._con() as con:
            row = con.execute(
                '''SELECT * FROM pwa_sessions
                   WHERE token_hash=? AND device_id=? AND revoked_at IS NULL AND expires_at>=?''',
                (token_hash, str(device_id), now),
            ).fetchone()
            if not row:
                return None
            if touch:
                con.execute('UPDATE pwa_sessions SET last_seen_at=? WHERE id=?', (now, row['id']))
                row = dict(row)
                row['last_seen_at'] = now
                return self._row(row)
        return self._row(row)

    def get(self, session_id: str) -> PwaSession | None:
        now = time.time()
        with self._con() as con:
            row = con.execute(
                'SELECT * FROM pwa_sessions WHERE id=? AND revoked_at IS NULL AND expires_at>=?',
                (str(session_id), now),
            ).fetchone()
        return self._row(row) if row else None

    def mark_reauthenticated(self, session_id: str, *, at: float | None = None) -> bool:
        stamp = time.time() if at is None else float(at)
        with self._con() as con:
            cur = con.execute(
                '''UPDATE pwa_sessions SET reauthenticated_at=?
                   WHERE id=? AND revoked_at IS NULL AND expires_at>=?''',
                (stamp, str(session_id), time.time()),
            )
        return cur.rowcount == 1

    def revoke(self, session_id: str) -> bool:
        with self._con() as con:
            cur = con.execute(
                'UPDATE pwa_sessions SET revoked_at=? WHERE id=? AND revoked_at IS NULL',
                (time.time(), str(session_id)),
            )
        return cur.rowcount == 1

    def revoke_token(self, token: str | None) -> bool:
        if not token:
            return False
        with self._con() as con:
            cur = con.execute(
                'UPDATE pwa_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL',
                (time.time(), self._hash(token)),
            )
        return cur.rowcount == 1

    def revoke_device(self, device_id: str) -> int:
        with self._con() as con:
            cur = con.execute(
                'UPDATE pwa_sessions SET revoked_at=? WHERE device_id=? AND revoked_at IS NULL',
                (time.time(), str(device_id)),
            )
        return int(cur.rowcount)

    def revoke_all(self) -> int:
        with self._con() as con:
            cur = con.execute(
                'UPDATE pwa_sessions SET revoked_at=? WHERE revoked_at IS NULL',
                (time.time(),),
            )
        return int(cur.rowcount)

    def active_for_device(self, device_id: str) -> list[PwaSession]:
        now = time.time()
        with self._con() as con:
            rows = con.execute(
                '''SELECT * FROM pwa_sessions
                   WHERE device_id=? AND revoked_at IS NULL AND expires_at>=?
                   ORDER BY created_at''',
                (str(device_id), now),
            ).fetchall()
        return [self._row(row) for row in rows]

    def purge_expired(self) -> int:
        with self._con() as con:
            cur = con.execute('DELETE FROM pwa_sessions WHERE expires_at<?', (time.time(),))
        return int(cur.rowcount)
