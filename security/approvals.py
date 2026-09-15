from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from typing import Any


def parameter_hash(parameters: dict[str, Any]) -> str:
    raw = json.dumps(
        parameters or {},
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        default=str,
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ApprovalTicket:
    id: str
    execution_id: str
    tool_name: str
    parameter_hash: str
    created_at: float
    expires_at: float
    owner_id: str = 'owner'
    device_id: str | None = None
    session_id: str | None = None
    security_epoch: int = 0
    destination: str = ''
    data_classification: str = 'internal'
    max_uses: int = 1


class ApprovalManager:
    """Durable, one-use approvals bound to the exact proposed action.

    The legacy in-memory mode is retained only for small isolated tests that do
    not supply ``path``. Production AgentExecutor instances provide a path under
    the Personal AI durable data root so pending approvals and continuation
    checkpoints survive process restarts.
    """

    def __init__(self, ttl_seconds: int = 300, *, path: Path | None = None):
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.path = Path(path) if path is not None else None
        self._lock = threading.RLock()
        self._tickets: dict[str, tuple[ApprovalTicket, str]] = {}
        self._contexts: dict[str, dict] = {}
        self._epoch = 0
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    def _con(self):
        if self.path is None:
            raise RuntimeError('durable approval database is not configured')
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        with self._con() as con:
            con.executescript(
                '''
                CREATE TABLE IF NOT EXISTS approval_tickets(
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    parameter_hash TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    device_id TEXT,
                    session_id TEXT,
                    security_epoch INTEGER NOT NULL,
                    destination TEXT NOT NULL DEFAULT '',
                    data_classification TEXT NOT NULL DEFAULT 'internal',
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    max_uses INTEGER NOT NULL DEFAULT 1,
                    used_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    consumed_at REAL,
                    rejected_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_approval_status_expiry
                    ON approval_tickets(status,expires_at);
                CREATE TABLE IF NOT EXISTS approval_continuations(
                    approval_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(approval_id) REFERENCES approval_tickets(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS approval_security_state(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                INSERT OR IGNORE INTO approval_security_state(key,value,updated_at)
                    VALUES('security_epoch','0',0);
                '''
            )

    @staticmethod
    def _from_row(row) -> ApprovalTicket:
        return ApprovalTicket(
            id=row['id'],
            execution_id=row['execution_id'],
            tool_name=row['tool_name'],
            parameter_hash=row['parameter_hash'],
            created_at=float(row['created_at']),
            expires_at=float(row['expires_at']),
            owner_id=row['owner_id'],
            device_id=row['device_id'],
            session_id=row['session_id'],
            security_epoch=int(row['security_epoch']),
            destination=row['destination'] or '',
            data_classification=row['data_classification'] or 'internal',
            max_uses=int(row['max_uses']),
        )

    def current_security_epoch(self) -> int:
        if self.path is None:
            with self._lock:
                return self._epoch
        with self._con() as con:
            row = con.execute(
                "SELECT value FROM approval_security_state WHERE key='security_epoch'"
            ).fetchone()
        return int(row['value']) if row else 0

    def advance_security_epoch(self) -> int:
        """Invalidate every outstanding permit/approval after a trust reset."""
        if self.path is None:
            with self._lock:
                self._epoch += 1
                self._tickets = {
                    key: (ticket, 'invalidated' if status == 'pending' else status)
                    for key, (ticket, status) in self._tickets.items()
                }
                self._contexts.clear()
                return self._epoch
        now = time.time()
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute(
                "SELECT value FROM approval_security_state WHERE key='security_epoch'"
            ).fetchone()
            epoch = (int(row['value']) if row else 0) + 1
            con.execute(
                "INSERT INTO approval_security_state(key,value,updated_at) VALUES('security_epoch',?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                (str(epoch), now),
            )
            con.execute(
                "UPDATE approval_tickets SET status='invalidated' WHERE status='pending'"
            )
            con.execute('DELETE FROM approval_continuations')
            con.commit()
        return epoch

    def create(
        self,
        execution_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        *,
        owner_id: str = 'owner',
        device_id: str | None = None,
        session_id: str | None = None,
        security_epoch: int | None = None,
        destination: str = '',
        data_classification: str = 'internal',
    ) -> ApprovalTicket:
        now = time.time()
        epoch = self.current_security_epoch() if security_epoch is None else int(security_epoch)
        ticket = ApprovalTicket(
            secrets.token_urlsafe(24),
            str(execution_id),
            str(tool_name),
            parameter_hash(parameters),
            now,
            now + self.ttl_seconds,
            str(owner_id or 'owner'),
            str(device_id) if device_id else None,
            str(session_id) if session_id else None,
            epoch,
            str(destination or '')[:1000],
            str(data_classification or 'internal')[:40],
            1,
        )
        if self.path is None:
            with self._lock:
                self._tickets[ticket.id] = (ticket, 'pending')
            return ticket
        with self._lock, self._con() as con:
            con.execute(
                '''INSERT INTO approval_tickets(
                    id,execution_id,tool_name,parameter_hash,owner_id,device_id,session_id,
                    security_epoch,destination,data_classification,created_at,expires_at,max_uses,
                    used_count,status,consumed_at,rejected_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,0,'pending',NULL,NULL)''',
                (
                    ticket.id,
                    ticket.execution_id,
                    ticket.tool_name,
                    ticket.parameter_hash,
                    ticket.owner_id,
                    ticket.device_id,
                    ticket.session_id,
                    ticket.security_epoch,
                    ticket.destination,
                    ticket.data_classification,
                    ticket.created_at,
                    ticket.expires_at,
                ),
            )
        return ticket

    @staticmethod
    def _validate_scope(
        ticket: ApprovalTicket,
        *,
        execution_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        owner_id: str | None,
        device_id: str | None,
        session_id: str | None,
        security_epoch: int,
        destination: str | None,
        data_classification: str | None,
    ) -> None:
        if ticket.execution_id != execution_id or ticket.tool_name != tool_name:
            raise PermissionError('approval scope mismatch')
        if ticket.parameter_hash != parameter_hash(parameters):
            raise PermissionError('approval scope mismatch')
        if ticket.owner_id and owner_id is not None and ticket.owner_id != owner_id:
            raise PermissionError('approval owner mismatch')
        if ticket.device_id is not None and ticket.device_id != device_id:
            raise PermissionError('approval device mismatch')
        if ticket.session_id is not None and ticket.session_id != session_id:
            raise PermissionError('approval session mismatch')
        if ticket.security_epoch != int(security_epoch):
            raise PermissionError('approval security epoch mismatch')
        if destination is not None and ticket.destination != str(destination or '')[:1000]:
            raise PermissionError('approval destination mismatch')
        if data_classification is not None and ticket.data_classification != str(data_classification or 'internal')[:40]:
            raise PermissionError('approval data classification mismatch')

    def consume(
        self,
        ticket_id: str,
        execution_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        *,
        now: float | None = None,
        owner_id: str | None = None,
        device_id: str | None = None,
        session_id: str | None = None,
        security_epoch: int | None = None,
        destination: str | None = None,
        data_classification: str | None = None,
    ) -> ApprovalTicket:
        now = time.time() if now is None else float(now)
        epoch = self.current_security_epoch() if security_epoch is None else int(security_epoch)
        if self.path is None:
            with self._lock:
                item = self._tickets.get(ticket_id)
                if not item or item[1] != 'pending':
                    raise PermissionError('approval is missing, expired, rejected, or already used')
                ticket = item[0]
                if now > ticket.expires_at:
                    self._tickets[ticket_id] = (ticket, 'expired')
                    self._contexts.pop(ticket_id, None)
                    raise PermissionError('approval expired')
                self._validate_scope(
                    ticket,
                    execution_id=execution_id,
                    tool_name=tool_name,
                    parameters=parameters,
                    owner_id=owner_id,
                    device_id=device_id,
                    session_id=session_id,
                    security_epoch=epoch,
                    destination=destination,
                    data_classification=data_classification,
                )
                self._tickets[ticket_id] = (ticket, 'consumed')
                self._contexts.pop(ticket_id, None)
                return ticket

        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute(
                "SELECT * FROM approval_tickets WHERE id=? AND status='pending'",
                (ticket_id,),
            ).fetchone()
            if not row:
                con.rollback()
                raise PermissionError('approval is missing, expired, rejected, or already used')
            ticket = self._from_row(row)
            if now > ticket.expires_at:
                con.execute(
                    "UPDATE approval_tickets SET status='expired' WHERE id=? AND status='pending'",
                    (ticket_id,),
                )
                con.execute('DELETE FROM approval_continuations WHERE approval_id=?', (ticket_id,))
                con.commit()
                raise PermissionError('approval expired')
            try:
                self._validate_scope(
                    ticket,
                    execution_id=execution_id,
                    tool_name=tool_name,
                    parameters=parameters,
                    owner_id=owner_id,
                    device_id=device_id,
                    session_id=session_id,
                    security_epoch=epoch,
                    destination=destination,
                    data_classification=data_classification,
                )
            except Exception:
                con.rollback()
                raise
            cur = con.execute(
                "UPDATE approval_tickets SET status='consumed',used_count=used_count+1,consumed_at=? "
                "WHERE id=? AND status='pending' AND used_count < max_uses",
                (now, ticket_id),
            )
            if cur.rowcount != 1:
                con.rollback()
                raise PermissionError('approval is missing, expired, rejected, or already used')
            con.execute('DELETE FROM approval_continuations WHERE approval_id=?', (ticket_id,))
            con.commit()
            return ticket

    def reject(
        self,
        ticket_id: str,
        *,
        device_id: str | None = None,
        session_id: str | None = None,
        now: float | None = None,
    ) -> bool:
        now = time.time() if now is None else float(now)
        if self.path is None:
            with self._lock:
                item = self._tickets.get(ticket_id)
                if not item or item[1] != 'pending':
                    return False
                ticket = item[0]
                if ticket.device_id is not None and ticket.device_id != device_id:
                    raise PermissionError('approval device mismatch')
                if ticket.session_id is not None and ticket.session_id != session_id:
                    raise PermissionError('approval session mismatch')
                self._tickets[ticket_id] = (ticket, 'rejected')
                self._contexts.pop(ticket_id, None)
                return True
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute(
                "SELECT * FROM approval_tickets WHERE id=? AND status='pending'",
                (ticket_id,),
            ).fetchone()
            if not row:
                con.rollback()
                return False
            ticket = self._from_row(row)
            if ticket.device_id is not None and ticket.device_id != device_id:
                con.rollback()
                raise PermissionError('approval device mismatch')
            if ticket.session_id is not None and ticket.session_id != session_id:
                con.rollback()
                raise PermissionError('approval session mismatch')
            con.execute(
                "UPDATE approval_tickets SET status='rejected',rejected_at=? WHERE id=? AND status='pending'",
                (now, ticket_id),
            )
            con.execute('DELETE FROM approval_continuations WHERE approval_id=?', (ticket_id,))
            con.commit()
            return True

    def save_context(self, ticket_id: str, payload: dict) -> None:
        safe = json.dumps(payload, ensure_ascii=False, default=str, separators=(',', ':'))
        if self.path is None:
            with self._lock:
                self._contexts[ticket_id] = json.loads(safe)
            return
        with self._lock, self._con() as con:
            pending = con.execute(
                "SELECT 1 FROM approval_tickets WHERE id=? AND status='pending'",
                (ticket_id,),
            ).fetchone()
            if not pending:
                raise PermissionError('approval is not pending')
            con.execute(
                '''INSERT INTO approval_continuations(approval_id,payload_json,created_at)
                   VALUES(?,?,?) ON CONFLICT(approval_id) DO UPDATE SET
                   payload_json=excluded.payload_json,created_at=excluded.created_at''',
                (ticket_id, safe, time.time()),
            )

    def context(self, ticket_id: str) -> dict | None:
        if self.path is None:
            with self._lock:
                value = self._contexts.get(ticket_id)
                return dict(value) if value is not None else None
        with self._con() as con:
            row = con.execute(
                '''SELECT c.payload_json FROM approval_continuations c
                   JOIN approval_tickets t ON t.id=c.approval_id
                   WHERE c.approval_id=? AND t.status='pending' AND t.expires_at>=?''',
                (ticket_id, time.time()),
            ).fetchone()
        return json.loads(row['payload_json']) if row else None

    def ticket(self, ticket_id: str) -> ApprovalTicket | None:
        if self.path is None:
            with self._lock:
                item = self._tickets.get(ticket_id)
                return item[0] if item and item[1] == 'pending' else None
        with self._con() as con:
            row = con.execute(
                "SELECT * FROM approval_tickets WHERE id=? AND status='pending' AND expires_at>=?",
                (ticket_id, time.time()),
            ).fetchone()
        return self._from_row(row) if row else None

    def purge_expired(self, *, now: float | None = None) -> int:
        now = time.time() if now is None else float(now)
        if self.path is None:
            with self._lock:
                stale = [
                    key for key, (ticket, status) in self._tickets.items()
                    if status == 'pending' and now > ticket.expires_at
                ]
                for key in stale:
                    ticket = self._tickets[key][0]
                    self._tickets[key] = (ticket, 'expired')
                    self._contexts.pop(key, None)
                return len(stale)
        with self._lock, self._con() as con:
            rows = con.execute(
                "SELECT id FROM approval_tickets WHERE status='pending' AND expires_at<?",
                (now,),
            ).fetchall()
            ids = [row['id'] for row in rows]
            if ids:
                placeholders = ','.join('?' for _ in ids)
                con.execute(
                    f"UPDATE approval_tickets SET status='expired' WHERE id IN ({placeholders})",
                    ids,
                )
                con.execute(
                    f"DELETE FROM approval_continuations WHERE approval_id IN ({placeholders})",
                    ids,
                )
            return len(ids)
