from __future__ import annotations

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
    """

    CATEGORY_LABELS = {
        'agent': 'Personal AI',
        'approval': 'Approval',
        'tool': 'Tool',
        'memory': 'Memory',
        'knowledge': 'Knowledge',
        'automation': 'Automation',
        'workflow': 'Workflow',
        'model': 'Model',
        'continuity': 'Continuity',
        'owner-product': 'Owner action',
        'recovery': 'Recovery',
        'verification': 'Verification',
    }

    def __init__(self, audit_store):
        self.audit_store = audit_store

    @classmethod
    def _sanitize(cls, value, *, depth=0):
        if depth > 8:
            return '[bounded]'
        if isinstance(value, dict):
            clean = {}
            for key, item in value.items():
                name = str(key)
                if _SECRET_KEYS.search(name) or _SENSITIVE_CONTEXT_KEYS.search(name):
                    clean[name] = '[redacted]'
                else:
                    clean[name] = cls._sanitize(item, depth=depth + 1)
            return clean
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(item, depth=depth + 1) for item in list(value)[:100]]
        if isinstance(value, str):
            # Bound arbitrary external/audit strings so Activities cannot become
            # an unrestricted prompt/document exfiltration surface.
            return value[:1000]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)[:1000]

    @classmethod
    def project_entry(cls, entry: dict) -> dict:
        item = deepcopy(dict(entry))
        category = str(item.get('category') or 'system')
        action = str(item.get('action') or 'event')
        payload = cls._sanitize(item.get('payload') or {})
        # Parameter hashes and evidence identifiers are safe useful references;
        # raw parameters, prompts and credentials are never needed here.
        return {
            'id': str(item.get('id') or ''),
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

    def list(self, *, limit: int = 100, category: str | None = None) -> list[dict]:
        bounded = max(1, min(int(limit), 500))
        rows = self.audit_store.audit_entries(category=category, limit=bounded)
        return [self.project_entry(row) for row in rows]
