from __future__ import annotations

import base64
import json
import re
from copy import deepcopy


_SECRET_KEYS = re.compile(
    r'(api[_-]?key|authorization|cookie|session[_-]?(token|secret)|access[_-]?token|refresh[_-]?token|'
    r'approval[_-]?token|recovery[_-]?(credential|secret|token)|password|private[_-]?key|client[_-]?secret)',
    re.IGNORECASE,
)
_SENSITIVE_CONTEXT_KEYS = re.compile(
    r'(raw_(memory|knowledge|audio|camera|location|prompt|screen)|system_prompt|provider_config|headers)',
    re.IGNORECASE,
)


class ActivitiesProjection:
    """User-safe projection over the canonical audit ledger.

    Audit remains the evidence authority. This class never mutates or replaces
    audit data; it returns a recursively sanitized, bounded owner-facing view.
    Cursor identity is projection-only and is derived from immutable audit IDs.
    """

    CATEGORY_LABELS = {
        'agent': 'Personal AI', 'approval': 'Approval', 'tool': 'Tool',
        'memory': 'Memory', 'knowledge': 'Knowledge', 'automation': 'Automation',
        'workflow': 'Workflow', 'model': 'Model', 'continuity': 'Continuity',
        'owner-product': 'Owner action', 'recovery': 'Recovery',
        'verification': 'Verification',
    }
    MAX_PAGE = 200
    MAX_SCAN = 1000

    def __init__(self, audit_store):
        self.audit_store = audit_store

    @classmethod
    def _sanitize(cls, value, *, depth=0):
        if depth > 8:
            return '[bounded]'
        if isinstance(value, dict):
            clean = {}
            for key, item in list(value.items())[:100]:
                name = str(key)[:200]
                if _SECRET_KEYS.search(name) or _SENSITIVE_CONTEXT_KEYS.search(name):
                    clean[name] = '[redacted]'
                else:
                    clean[name] = cls._sanitize(item, depth=depth + 1)
            return clean
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(item, depth=depth + 1) for item in list(value)[:100]]
        if isinstance(value, str):
            return value[:1000]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)[:1000]

    @classmethod
    def project_entry(cls, entry: dict) -> dict:
        item = deepcopy(dict(entry))
        category = str(item.get('category') or 'system')[:100]
        action = str(item.get('action') or 'event')[:200]
        payload = cls._sanitize(item.get('payload') or {})
        audit_id = str(item.get('id') or '')[:200]
        return {
            'id': audit_id,
            'activity_id': audit_id,
            'kind': category,
            'label': cls.CATEGORY_LABELS.get(category, category.replace('_', ' ').title()),
            'action': action,
            'status': cls._status(category, action, payload),
            'created_at': item.get('created_at'),
            'details': payload,
        }

    @staticmethod
    def _status(category: str, action: str, payload: dict) -> str:
        text = f'{category}.{action}'.lower()
        if payload.get('ok') is False or any(word in text for word in ('failed', 'error')):
            return 'error'
        if payload.get('verified') is False or any(word in text for word in ('warning', 'unverified', 'recovery')):
            return 'warning'
        if any(word in text for word in ('required', 'pending', 'waiting')):
            return 'needs_approval' if 'approval' in text else 'pending'
        if any(word in text for word in ('approved', 'completed', 'success', 'execute', 'committed')):
            return 'completed'
        if any(word in text for word in ('started', 'running')):
            return 'running'
        return 'recorded'

    @staticmethod
    def _encode_cursor(audit_id: str) -> str:
        raw = json.dumps({'after': str(audit_id)}, separators=(',', ':')).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip('=')

    @staticmethod
    def _decode_cursor(cursor: str | None) -> str | None:
        if not cursor:
            return None
        if len(cursor) > 512:
            raise ValueError('invalid activity cursor')
        try:
            padded = cursor + '=' * (-len(cursor) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
            value = str(data.get('after') or '')
            if not value or len(value) > 200:
                raise ValueError
            return value
        except Exception as exc:
            raise ValueError('invalid activity cursor') from exc

    def _rows(self, *, category: str | None = None) -> list[dict]:
        return list(self.audit_store.audit_entries(category=category, limit=self.MAX_SCAN))

    def page(
        self, *, limit: int = 50, category: str | None = None,
        status: str | None = None, cursor: str | None = None,
    ) -> dict:
        bounded = max(1, min(int(limit), self.MAX_PAGE))
        after = self._decode_cursor(cursor)
        projected = [self.project_entry(row) for row in self._rows(category=category)]
        if status:
            projected = [row for row in projected if row['status'] == str(status)]
        if after:
            positions = [i for i, row in enumerate(projected) if row['id'] == after]
            if not positions:
                raise ValueError('stale or invalid activity cursor')
            projected = projected[positions[0] + 1:]
        items = projected[:bounded]
        has_more = len(projected) > bounded
        return {
            'activities': items,
            'next_cursor': self._encode_cursor(items[-1]['id']) if has_more and items else None,
            'has_more': has_more,
        }

    def list(self, *, limit: int = 100, category: str | None = None) -> list[dict]:
        return self.page(limit=limit, category=category)['activities']

    def detail(self, activity_id: str) -> dict | None:
        wanted = str(activity_id or '').strip()
        if not wanted or len(wanted) > 200:
            return None
        rows = self._rows()
        match = next((row for row in rows if str(row.get('id') or '') == wanted), None)
        if match is None:
            return None
        projected = self.project_entry(match)
        payload = projected['details'] if isinstance(projected['details'], dict) else {}
        correlation_keys = ('request_id', 'turn_id', 'workflow_id', 'execution_id', 'operation_id', 'approval_id')
        correlations = {key: str(payload[key]) for key in correlation_keys if payload.get(key) is not None}
        timeline = []
        for row in rows:
            event = self.project_entry(row)
            details = event['details'] if isinstance(event['details'], dict) else {}
            if event['id'] == wanted or any(str(details.get(key)) == value for key, value in correlations.items()):
                timeline.append(event)
        timeline.sort(key=lambda row: (str(row.get('created_at') or ''), str(row.get('id') or '')))
        return {**projected, 'correlations': correlations, 'timeline': timeline[:self.MAX_PAGE]}
