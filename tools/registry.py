from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import sqlite3
from typing import Any, Callable
from urllib.parse import urlparse

from core.permissions import PermissionDecision, PermissionEngine


class Risk(IntEnum):
    READ_ONLY = 0
    REVERSIBLE = 1
    EXTERNAL_SIDE_EFFECT = 2
    DESTRUCTIVE = 3
    CRITICAL = 4


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    reason: str
    evidence: dict[str, Any]


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], Any]
    risk: Risk = Risk.READ_ONLY
    verifier: Callable[[dict[str, Any], Any], Any] | None = None
    rollback: Callable[[dict[str, Any], Any], Any] | None = None
    rollback_description: str = ''
    allowed_destinations: tuple[str, ...] | None = None
    verification_required: bool = False
    requires_reauth: bool = False


class ToolRegistry:
    def __init__(self, settings):
        self.settings = settings
        self.permissions = PermissionEngine(settings.autonomy_mode)
        self._tools = {}
        self.emergency_stop = False
        self._control_path = None
        self._approval_path = None
        data_dir = getattr(settings, 'data_dir', None)
        if data_dir is not None:
            data_root = Path(data_dir)
            self._control_path = data_root / 'runtime-controls.sqlite3'
            self._approval_path = data_root / 'trusted-actions.sqlite3'
            self._control_path.parent.mkdir(parents=True, exist_ok=True)
            with self._control_con() as con:
                con.execute('CREATE TABLE IF NOT EXISTS runtime_controls (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
                row = con.execute("SELECT value FROM runtime_controls WHERE key='emergency_stop'").fetchone()
                self.emergency_stop = bool(row and row[0] == '1')

    def _control_con(self):
        return sqlite3.connect(self._control_path)

    def set_emergency_stop(self, enabled: bool):
        previous = self.emergency_stop
        self.emergency_stop = bool(enabled)
        if self._control_path is not None:
            with self._control_con() as con:
                con.execute(
                    "INSERT OR REPLACE INTO runtime_controls(key,value) VALUES('emergency_stop',?)",
                    ('1' if enabled else '0',),
                )
        if self.emergency_stop and not previous and self._approval_path is not None and self._approval_path.exists():
            from security.approvals import ApprovalManager
            ApprovalManager(path=self._approval_path).advance_security_epoch()
        return self.emergency_stop

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f'Duplicate tool {tool.name}')
        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools[name]

    def all(self):
        return list(self._tools.values())

    def schema_text(self):
        return '\n'.join(f'- {tool.name}: {tool.description}; risk={tool.risk.name}' for tool in self._tools.values())

    def set_autonomy_mode(self, mode: str):
        mode = str(mode).lower().strip()
        if mode not in {'observe', 'suggest', 'ask', 'act'}:
            raise ValueError('invalid autonomy mode')
        self.permissions.mode = mode
        return mode

    @property
    def autonomy_mode(self):
        return self.permissions.mode

    @staticmethod
    def destination(parameters: dict[str, Any] | None) -> str:
        params = parameters or {}
        for key in (
            'destination', 'recipient', 'recipients', 'to', 'email', 'emails',
            'url', 'domain', 'path', 'file_path', 'filename', 'channel', 'room',
            'calendar_id', 'spreadsheet_id', 'document_id', 'repository',
        ):
            value = params.get(key)
            if value in (None, '', [], {}):
                continue
            if isinstance(value, (list, tuple, set)):
                return ','.join(str(item) for item in value)[:1000]
            if isinstance(value, dict):
                return str(sorted(value.items()))[:1000]
            return str(value)[:1000]
        return ''

    @staticmethod
    def _destination_host(destination: str) -> str:
        value = str(destination or '').strip().lower()
        if not value:
            return ''
        if '@' in value and '://' not in value:
            return value.rsplit('@', 1)[-1]
        parsed = urlparse(value if '://' in value else f'https://{value}')
        return (parsed.hostname or value).lower()

    def validate_destination(self, tool: Tool, parameters: dict[str, Any] | None) -> None:
        if not tool.allowed_destinations:
            return
        destination = self.destination(parameters)
        host = self._destination_host(destination)
        allowed = tuple(str(item).strip().lower() for item in tool.allowed_destinations if str(item).strip())
        if not host or not any(host == item or host.endswith('.' + item) for item in allowed):
            raise PermissionError('destination is outside the configured allowlist')

    def effective_risk(
        self,
        tool: Tool,
        *,
        parameters: dict[str, Any] | None = None,
        data_classification: str = 'internal',
    ) -> Risk:
        risk = Risk(int(tool.risk))
        destination = self.destination(parameters)
        classification = str(data_classification or 'internal').strip().lower()
        if destination and classification == 'secret':
            risk = max(risk, Risk.CRITICAL)
        elif destination and classification in {'sensitive', 'restricted'}:
            risk = max(risk, Risk.DESTRUCTIVE)
        return Risk(int(risk))

    def automatic(self, tool: Tool):
        return self.authorize(tool, confirmed=False).allowed

    def authorize(
        self,
        tool: Tool,
        confirmed: bool = False,
        *,
        parameters: dict[str, Any] | None = None,
        data_classification: str = 'internal',
    ):
        if self.emergency_stop:
            return PermissionDecision(False, False, 'owner emergency stop is active')
        self.validate_destination(tool, parameters)
        risk = self.effective_risk(
            tool,
            parameters=parameters,
            data_classification=data_classification,
        )
        return self.permissions.decide(int(risk), confirmed=confirmed)

    def verify_result(self, tool: Tool, parameters: dict[str, Any], result: Any) -> VerificationResult:
        if tool.verifier is not None:
            verdict = tool.verifier(parameters, result)
            if isinstance(verdict, VerificationResult):
                verification = verdict
            elif isinstance(verdict, dict):
                verification = VerificationResult(
                    bool(verdict.get('verified')),
                    str(verdict.get('reason') or ('verified' if verdict.get('verified') else 'verification failed')),
                    dict(verdict.get('evidence') or {}),
                )
            else:
                verification = VerificationResult(bool(verdict), 'custom verification contract', {})
        elif isinstance(result, dict) and result.get('verified') is True:
            verification = VerificationResult(True, 'tool returned explicit verification evidence', dict(result))
        elif tool.risk == Risk.READ_ONLY:
            verification = VerificationResult(True, 'read-only handler returned observed data', {})
        else:
            verification = VerificationResult(False, 'no result verification contract is configured for this side-effecting tool', {})

        if tool.verification_required and not verification.verified:
            raise RuntimeError(f'tool result verification failed: {verification.reason}')
        return verification

    @staticmethod
    def rollback_metadata(tool: Tool) -> dict[str, Any]:
        return {
            'available': callable(tool.rollback),
            'description': str(tool.rollback_description or ''),
        }
