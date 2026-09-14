from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
import time
import uuid

STATES = {
    'proposed', 'policy_check', 'approval_required', 'permitted', 'executing',
    'verifying', 'completed', 'failed', 'cancelled', 'recovery_review_required',
}
TERMINAL_STATES = {'completed', 'failed', 'cancelled'}
TRANSITIONS = {
    'proposed': {'policy_check', 'failed', 'cancelled'},
    'policy_check': {'approval_required', 'permitted', 'failed', 'cancelled'},
    'approval_required': {'permitted', 'failed', 'cancelled'},
    'permitted': {'executing', 'failed', 'cancelled'},
    'executing': {'verifying', 'failed', 'cancelled', 'recovery_review_required'},
    'verifying': {'completed', 'failed', 'cancelled', 'recovery_review_required'},
    'recovery_review_required': {'failed', 'cancelled'},
    'completed': set(), 'failed': set(), 'cancelled': set(),
}


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def _hash(value) -> str:
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class OperatorBinding:
    owner_id: str
    device_id: str
    session_id: str
    security_epoch: int
    conversation_id: str = ''
    workflow_id: str = ''


class OperatorTransactionStore:
    """Durable, fail-closed transaction journal for consequential computer actions."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()
        self.recover_interrupted()

    def _con(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        with self._con() as con:
            con.executescript('''
                CREATE TABLE IF NOT EXISTS operator_transactions(
                    transaction_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    security_epoch INTEGER NOT NULL,
                    conversation_id TEXT NOT NULL DEFAULT '',
                    workflow_id TEXT NOT NULL DEFAULT '',
                    goal TEXT NOT NULL,
                    goal_hash TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    plan_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    checkpoint_index INTEGER NOT NULL DEFAULT -1,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    deadline_at REAL,
                    error_code TEXT NOT NULL DEFAULT '',
                    recovery_reason TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    completed_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_operator_state ON operator_transactions(state,updated_at);
                CREATE TABLE IF NOT EXISTS operator_actions(
                    action_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    parameter_hash TEXT NOT NULL,
                    expected_postcondition TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 0,
                    evidence_json TEXT NOT NULL DEFAULT '{}',
                    error_code TEXT NOT NULL DEFAULT '',
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    UNIQUE(transaction_id,sequence),
                    FOREIGN KEY(transaction_id) REFERENCES operator_transactions(transaction_id)
                );
                CREATE TABLE IF NOT EXISTS operator_audit(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    action_id TEXT,
                    event TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
            ''')

    @staticmethod
    def _row(row):
        if not row:
            return None
        out = dict(row)
        out['cancel_requested'] = bool(out.get('cancel_requested'))
        try: out['plan'] = json.loads(out.pop('plan_json'))
        except Exception: out['plan'] = {}
        return out

    def _audit(self, con, transaction_id: str, event: str, *, action_id=None, payload=None):
        safe = {}
        for key, value in dict(payload or {}).items():
            low = str(key).lower()
            if any(word in low for word in ('token', 'password', 'secret', 'content', 'text', 'clipboard')):
                continue
            safe[str(key)] = value
        con.execute(
            'INSERT INTO operator_audit(transaction_id,action_id,event,payload_json,created_at) VALUES(?,?,?,?,?)',
            (transaction_id, action_id, event, _json(safe), time.time()),
        )

    def propose(self, transaction_id: str, binding: OperatorBinding, *, goal: str, action_plan: dict, deadline_at=None):
        txid = str(transaction_id or '').strip()
        if not txid:
            raise ValueError('operator transaction ID is required')
        if not binding.owner_id or not binding.device_id or not binding.session_id:
            raise PermissionError('operator transaction requires owner, device and session binding')
        plan = dict(action_plan or {})
        steps = list(plan.get('steps') or [])
        if not steps:
            raise ValueError('operator transaction requires a non-empty approved action plan')
        now = time.time(); goal = str(goal or '').strip()
        if not goal:
            raise ValueError('operator transaction goal is required')
        record = (
            txid, binding.owner_id, binding.device_id, binding.session_id, int(binding.security_epoch),
            str(binding.conversation_id or ''), str(binding.workflow_id or ''), goal, _hash(goal),
            _json(plan), _hash(plan), 'proposed', -1, 0,
            float(deadline_at) if deadline_at is not None else None, '', '', now, now, None,
        )
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            existing = con.execute('SELECT * FROM operator_transactions WHERE transaction_id=?', (txid,)).fetchone()
            if existing:
                current = self._row(existing)
                expected = {
                    'owner_id': binding.owner_id, 'device_id': binding.device_id, 'session_id': binding.session_id,
                    'security_epoch': int(binding.security_epoch), 'conversation_id': str(binding.conversation_id or ''),
                    'workflow_id': str(binding.workflow_id or ''), 'goal_hash': _hash(goal), 'plan_hash': _hash(plan),
                }
                if any(current.get(key) != value for key, value in expected.items()):
                    con.rollback(); raise PermissionError('operator transaction ID is already bound to different authority or plan')
                con.rollback(); return current, False
            con.execute('''INSERT INTO operator_transactions(
                transaction_id,owner_id,device_id,session_id,security_epoch,conversation_id,workflow_id,
                goal,goal_hash,plan_json,plan_hash,state,checkpoint_index,cancel_requested,deadline_at,
                error_code,recovery_reason,created_at,updated_at,completed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', record)
            self._audit(con, txid, 'transaction.proposed', payload={'plan_hash': _hash(plan), 'step_count': len(steps)})
            con.commit()
        return self.transaction(txid), True

    def transaction(self, transaction_id: str):
        with self._con() as con:
            return self._row(con.execute('SELECT * FROM operator_transactions WHERE transaction_id=?', (transaction_id,)).fetchone())

    def actions(self, transaction_id: str):
        with self._con() as con:
            rows = con.execute('SELECT * FROM operator_actions WHERE transaction_id=? ORDER BY sequence', (transaction_id,)).fetchall()
        out = []
        for row in rows:
            item = dict(row); item['verified'] = bool(item['verified'])
            try: item['evidence'] = json.loads(item.pop('evidence_json'))
            except Exception: item['evidence'] = {}
            out.append(item)
        return out

    def assert_binding(self, transaction_id: str, binding: OperatorBinding):
        tx = self.transaction(transaction_id)
        if not tx:
            raise KeyError(transaction_id)
        checks = (
            ('owner', tx['owner_id'], binding.owner_id), ('device', tx['device_id'], binding.device_id),
            ('session', tx['session_id'], binding.session_id), ('security epoch', int(tx['security_epoch']), int(binding.security_epoch)),
        )
        mismatch = next((name for name, old, new in checks if old != new), None)
        if mismatch:
            raise PermissionError(f'operator {mismatch} binding mismatch')
        return tx

    def transition(self, transaction_id: str, new_state: str, *, error_code='', recovery_reason=''):
        if new_state not in STATES:
            raise ValueError('invalid operator transaction state')
        now = time.time()
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT state FROM operator_transactions WHERE transaction_id=?', (transaction_id,)).fetchone()
            if not row:
                con.rollback(); raise KeyError(transaction_id)
            old = row['state']
            if new_state == old:
                con.rollback(); return self.transaction(transaction_id)
            if new_state not in TRANSITIONS.get(old, set()):
                con.rollback(); raise RuntimeError(f'invalid operator transition: {old} -> {new_state}')
            completed = now if new_state in TERMINAL_STATES else None
            con.execute('''UPDATE operator_transactions SET state=?,error_code=?,recovery_reason=?,updated_at=?,completed_at=COALESCE(?,completed_at)
                           WHERE transaction_id=?''', (new_state, str(error_code or '')[:120], str(recovery_reason or '')[:500], now, completed, transaction_id))
            self._audit(con, transaction_id, 'transaction.state', payload={'from_state': old, 'to_state': new_state, 'error_code': str(error_code or '')[:120]})
            con.commit()
        return self.transaction(transaction_id)

    def request_cancel(self, transaction_id: str):
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            cur = con.execute('UPDATE operator_transactions SET cancel_requested=1,updated_at=? WHERE transaction_id=? AND state NOT IN (\'completed\',\'failed\',\'cancelled\')', (time.time(), transaction_id))
            if cur.rowcount:
                self._audit(con, transaction_id, 'transaction.cancel_requested')
            con.commit()
        return bool(cur.rowcount)

    def assert_dispatchable(self, transaction_id: str, binding: OperatorBinding):
        tx = self.assert_binding(transaction_id, binding)
        if tx['cancel_requested']:
            raise RuntimeError('operator transaction was cancelled')
        if tx.get('deadline_at') is not None and time.time() >= float(tx['deadline_at']):
            raise TimeoutError('operator transaction deadline exceeded')
        if tx['state'] != 'permitted':
            if tx['state'] in {'executing', 'verifying', 'recovery_review_required'}:
                raise RuntimeError('operator transaction requires recovery review before redispatch')
            raise RuntimeError(f'operator transaction is not dispatchable from state {tx["state"]}')
        return tx

    def start_action(self, transaction_id: str, sequence: int, *, kind: str, parameter_hash: str, expected_postcondition: str):
        action_id = f'{transaction_id}:{int(sequence)}'
        now = time.time()
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            prior = con.execute('SELECT * FROM operator_actions WHERE action_id=?', (action_id,)).fetchone()
            if prior:
                if prior['parameter_hash'] != parameter_hash or prior['kind'] != kind:
                    con.rollback(); raise PermissionError('operator action ID is already bound to different parameters')
                item = dict(prior); con.rollback(); return item, False
            con.execute('''INSERT INTO operator_actions(action_id,transaction_id,sequence,kind,parameter_hash,expected_postcondition,state,verified,evidence_json,error_code,started_at,completed_at)
                           VALUES(?,?,?,?,?,?,'executing',0,'{}','',?,NULL)''',
                        (action_id, transaction_id, int(sequence), str(kind), str(parameter_hash), str(expected_postcondition or '')[:2000], now))
            con.execute('UPDATE operator_transactions SET checkpoint_index=?,updated_at=? WHERE transaction_id=?', (int(sequence)-1, now, transaction_id))
            self._audit(con, transaction_id, 'action.started', action_id=action_id, payload={'sequence': int(sequence), 'kind': str(kind), 'parameter_hash': str(parameter_hash)})
            con.commit()
        return {
            'action_id': action_id, 'transaction_id': transaction_id, 'sequence': int(sequence),
            'kind': str(kind), 'parameter_hash': str(parameter_hash), 'expected_postcondition': str(expected_postcondition or '')[:2000],
            'state': 'executing', 'verified': False, 'evidence': {}, 'error_code': '', 'started_at': now, 'completed_at': None,
        }, True

    def finish_action(self, action_id: str, *, verified: bool, evidence=None, error_code=''):
        now = time.time(); safe_evidence = dict(evidence or {})
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT transaction_id,sequence,state FROM operator_actions WHERE action_id=?', (action_id,)).fetchone()
            if not row:
                con.rollback(); raise KeyError(action_id)
            if row['state'] != 'executing':
                con.rollback(); raise RuntimeError('operator action is not awaiting verification')
            state = 'verified' if verified else 'verification_failed'
            con.execute('UPDATE operator_actions SET state=?,verified=?,evidence_json=?,error_code=?,completed_at=? WHERE action_id=?',
                        (state, 1 if verified else 0, _json(safe_evidence), str(error_code or '')[:120], now, action_id))
            con.execute('UPDATE operator_transactions SET checkpoint_index=?,updated_at=? WHERE transaction_id=?', (int(row['sequence']), now, row['transaction_id']))
            self._audit(con, row['transaction_id'], 'action.finished', action_id=action_id,
                        payload={'sequence': int(row['sequence']), 'verified': bool(verified), 'error_code': str(error_code or '')[:120]})
            con.commit()
        return {'action_id': action_id, 'verified': bool(verified), 'state': state}

    def recover_interrupted(self):
        now = time.time(); recovered = []
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            rows = con.execute("SELECT transaction_id,state FROM operator_transactions WHERE state IN ('executing','verifying')").fetchall()
            for row in rows:
                txid = row['transaction_id']; recovered.append(txid)
                con.execute("UPDATE operator_transactions SET state='recovery_review_required',recovery_reason='process_restart_outcome_unknown',updated_at=? WHERE transaction_id=?", (now, txid))
                con.execute("UPDATE operator_actions SET state='outcome_unknown',error_code='process_restart' WHERE transaction_id=? AND state='executing'", (txid,))
                self._audit(con, txid, 'recovery.review_required', payload={'reason': 'process_restart_outcome_unknown'})
            con.commit()
        return recovered

    def audit(self, transaction_id: str):
        with self._con() as con:
            rows = con.execute('SELECT action_id,event,payload_json,created_at FROM operator_audit WHERE transaction_id=? ORDER BY id', (transaction_id,)).fetchall()
        return [dict(row) for row in rows]


def new_transaction_id() -> str:
    return str(uuid.uuid4())
