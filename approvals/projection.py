from __future__ import annotations

import time
from typing import Any


class ApprovalsProjection:
    """Read-only owner projection over the Stage-2 durable ApprovalManager.

    This class never creates, approves, rejects, dispatches or recovers work.  It
    only renders canonical approval records for an authenticated owner surface.
    """

    MAX_ITEMS = 100
    _SECRET_FRAGMENTS = (
        'password', 'secret', 'credential', 'api_key', 'apikey', 'access_token',
        'refresh_token', 'authorization', 'cookie', 'private_key', 'client_secret',
    )

    def __init__(self, manager):
        self.manager = manager

    @classmethod
    def _safe(cls, value: Any, *, depth: int = 0):
        if depth > 6:
            return '[bounded]'
        if isinstance(value, dict):
            out = {}
            for key, item in list(value.items())[:60]:
                normalized = str(key).lower().replace('-', '_').replace(' ', '_')
                if any(fragment in normalized for fragment in cls._SECRET_FRAGMENTS):
                    out[str(key)] = '[redacted]'
                else:
                    out[str(key)] = cls._safe(item, depth=depth + 1)
            return out
        if isinstance(value, (list, tuple)):
            return [cls._safe(item, depth=depth + 1) for item in list(value)[:60]]
        if isinstance(value, str):
            return value[:1000]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)[:1000]

    @staticmethod
    def _status(record: dict, ticket, now: float):
        status = str(record.get('status') or 'pending')
        if status == 'pending' and now >= float(ticket.expires_at):
            return 'expired'
        return status

    def project_record(self, record: dict, *, now: float | None = None):
        ticket = record['ticket']
        now = time.time() if now is None else float(now)
        status = self._status(record, ticket, now)
        outcome = self._safe(record.get('outcome')) if record.get('outcome') is not None else None
        return {
            'approval_id': ticket.id,
            'execution_id': ticket.execution_id,
            'tool_id': ticket.tool_name,
            'status': status,
            'created_at': ticket.created_at,
            'expires_at': ticket.expires_at,
            'destination': str(ticket.destination or '')[:1000],
            'data_classification': str(ticket.data_classification or 'internal')[:40],
            'security_epoch': int(ticket.security_epoch),
            'device_bound': ticket.device_id is not None,
            'session_bound': ticket.session_id is not None,
            'dispatch_started_at': record.get('dispatch_started_at'),
            'completed_at': record.get('completed_at'),
            'failure_code': str(record.get('failure_code') or '')[:160] or None,
            'outcome': outcome,
        }

    def detail(self, approval_id: str, *, owner_id='owner', device_id=None, session_id=None):
        record = self.manager.record(str(approval_id))
        if record is None:
            return None
        ticket = record['ticket']
        if ticket.owner_id != owner_id:
            return None
        if ticket.device_id not in (None, device_id):
            return None
        if ticket.session_id not in (None, session_id):
            return None
        return self.project_record(record)

    def list(self, *, owner_id='owner', device_id=None, session_id=None, status=None, limit=50):
        limit = max(1, min(int(limit), self.MAX_ITEMS))
        # Stage-2 remains the authority. list_records is deliberately a read-only
        # manager method; no projection-local pending state is created here.
        records = self.manager.list_records(owner_id=owner_id, device_id=device_id, session_id=session_id, limit=self.MAX_ITEMS)
        projected = [self.project_record(record) for record in records]
        if status:
            projected = [item for item in projected if item['status'] == status]
        return projected[:limit]
