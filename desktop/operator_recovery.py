from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
import time
import uuid
from typing import Any, Callable

from desktop.operator_transactions import OperatorBinding, OperatorTransactionStore
from desktop.verification import VerificationOutcome, VerificationRecord, canonical_json, sanitize_evidence

RECOVERY_STATES = {
    'active','waiting_for_approval','dispatching','dispatched','verifying','verified_success',
    'verified_no_effect','partially_completed','compensation_available','compensation_requires_approval',
    'recovery_review_required','cancelled','failed','completed','abandoned_by_owner',
}
TERMINAL_RECOVERY_STATES = {'cancelled','failed','completed','abandoned_by_owner'}
COMPENSATION_CATEGORIES = {'automatically_reversible','compensation_available','manual_recovery_only','irreversible'}
RETRY_BLOCKED_CLASSES = {
    'purchase','financial_transfer','email_send','message_send','public_publish','share','upload',
    'delete','destructive_delete','permission_change','security_setting_modify','legal_acceptance',
}
SAFE_OWNER_DECISIONS = {
    'verify_again','resume_safe_checkpoint','retry_after_no_effect','approve_compensation',
    'mark_externally_completed','abandon_transaction','cancel_remaining','export_recovery_report',
}
CONSEQUENTIAL_OWNER_DECISIONS = {
    'resume_safe_checkpoint','retry_after_no_effect','approve_compensation','mark_externally_completed',
}


def _hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class RecoveryLease:
    transaction_id: str
    worker_id: str
    fencing_token: int
    lease_expires_at: float


class OperatorRecoveryStore:
    """W7.6 durable verification/recovery extension keyed to W7.1 transaction/action IDs.

    W7.1 OperatorTransactionStore remains the transaction authority. This store never creates an
    operator transaction and never grants policy/approval authority.
    """
    SCHEMA_VERSION = 1

    def __init__(self, path: Path, transactions: OperatorTransactionStore, *, emergency_stop: Callable[[], bool] | None=None):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.transactions = transactions
        self._emergency_stop = emergency_stop or (lambda: False)
        self._lock = threading.RLock()
        self._init_db()
        self.recover_interrupted()

    def _con(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        return con

    def _init_db(self):
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            con.executescript('''
                CREATE TABLE IF NOT EXISTS recovery_transactions(
                    transaction_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL DEFAULT 'active', recovery_reason TEXT NOT NULL DEFAULT '',
                    owner_decision TEXT NOT NULL DEFAULT '', owner_decision_id TEXT NOT NULL DEFAULT '',
                    resume_position INTEGER NOT NULL DEFAULT -1, checkpoint_json TEXT NOT NULL DEFAULT '{}',
                    compensation_plan_json TEXT NOT NULL DEFAULT '{}', compensation_result_json TEXT NOT NULL DEFAULT '{}',
                    worker_id TEXT NOT NULL DEFAULT '', fencing_token INTEGER NOT NULL DEFAULT 0,
                    lease_expires_at REAL NOT NULL DEFAULT 0, deadline_at REAL,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_recovery_state ON recovery_transactions(state,updated_at);
                CREATE TABLE IF NOT EXISTS recovery_dispatches(
                    dispatch_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, action_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE, operation_class TEXT NOT NULL, target TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL, attempt_no INTEGER NOT NULL DEFAULT 1,
                    worker_id TEXT NOT NULL, fencing_token INTEGER NOT NULL,
                    parameter_digest TEXT NOT NULL DEFAULT '', dispatched_at REAL, completed_at REAL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_dispatch_tx ON recovery_dispatches(transaction_id,created_at);
                CREATE TABLE IF NOT EXISTS recovery_verifications(
                    verification_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, action_id TEXT NOT NULL,
                    dispatch_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, operation_class TEXT NOT NULL,
                    target TEXT NOT NULL DEFAULT '', precondition_json TEXT NOT NULL DEFAULT '{}',
                    expected_postcondition TEXT NOT NULL DEFAULT '', observed_postcondition_json TEXT NOT NULL DEFAULT '{}',
                    verifier_identity TEXT NOT NULL, verifier_version TEXT NOT NULL,
                    evidence_references_json TEXT NOT NULL DEFAULT '[]', evidence_checksum TEXT NOT NULL,
                    verification_timestamp REAL NOT NULL, verification_fresh_until REAL NOT NULL,
                    confidence REAL, result TEXT NOT NULL, explanation TEXT NOT NULL, attempt_no INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_verification_dispatch ON recovery_verifications(dispatch_id,verification_timestamp);
                CREATE TABLE IF NOT EXISTS recovery_compensations(
                    compensation_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, original_action_id TEXT NOT NULL,
                    compensation_action_id TEXT NOT NULL DEFAULT '', category TEXT NOT NULL, operation_class TEXT NOT NULL DEFAULT '',
                    plan_json TEXT NOT NULL DEFAULT '{}', result_json TEXT NOT NULL DEFAULT '{}',
                    requires_approval INTEGER NOT NULL DEFAULT 0, requires_reauth INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recovery_decisions(
                    decision_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL, session_id TEXT NOT NULL, security_epoch INTEGER NOT NULL,
                    decision TEXT NOT NULL, consequential INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recovery_audit(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT NOT NULL, event TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}', created_at REAL NOT NULL
                );
            ''')
            con.execute(f'PRAGMA user_version={self.SCHEMA_VERSION}')
            con.commit()

    def schema_version(self) -> int:
        with self._con() as con: return int(con.execute('PRAGMA user_version').fetchone()[0])

    def _audit(self, con, transaction_id: str, event: str, payload: dict[str,Any] | None=None):
        con.execute('INSERT INTO recovery_audit(transaction_id,event,payload_json,created_at) VALUES(?,?,?,?)',
                    (transaction_id, event, canonical_json(sanitize_evidence(payload)), time.time()))

    def ensure_transaction(self, transaction_id: str, binding: OperatorBinding, *, deadline_at: float | None=None):
        tx = self.transactions.assert_binding(transaction_id, binding)
        now = time.time()
        with self._lock, self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM recovery_transactions WHERE transaction_id=?',(transaction_id,)).fetchone()
            if not row:
                con.execute('''INSERT INTO recovery_transactions(transaction_id,state,deadline_at,created_at,updated_at)
                               VALUES(?,'active',?,?,?)''',(transaction_id, deadline_at, now, now))
                self._audit(con, transaction_id, 'recovery.created', {'source_state':tx['state']})
                con.commit()
            else:
                con.rollback()
        return self.snapshot(transaction_id)

    def snapshot(self, transaction_id: str):
        with self._con() as con:
            row=con.execute('SELECT * FROM recovery_transactions WHERE transaction_id=?',(transaction_id,)).fetchone()
        if not row:return None
        out=dict(row)
        for src,dst in (('checkpoint_json','checkpoint'),('compensation_plan_json','compensation_plan'),('compensation_result_json','compensation_result')):
            try:out[dst]=json.loads(out.pop(src))
            except Exception:out[dst]={}
        return out

    def transition(self, transaction_id: str, state: str, *, reason: str='', checkpoint: dict[str,Any] | None=None, resume_position: int | None=None):
        if state not in RECOVERY_STATES:raise ValueError('invalid recovery state')
        now=time.time()
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT state FROM recovery_transactions WHERE transaction_id=?',(transaction_id,)).fetchone()
            if not row:con.rollback();raise KeyError(transaction_id)
            values=[state,str(reason)[:500],canonical_json(sanitize_evidence(checkpoint)) if checkpoint is not None else None,resume_position,now,transaction_id]
            con.execute('''UPDATE recovery_transactions SET state=?,recovery_reason=?,
                           checkpoint_json=COALESCE(?,checkpoint_json),resume_position=COALESCE(?,resume_position),updated_at=?
                           WHERE transaction_id=?''',values)
            self._audit(con,transaction_id,'recovery.state',{'from_state':row['state'],'to_state':state,'reason':reason})
            con.commit()
        return self.snapshot(transaction_id)

    def acquire_lease(self, transaction_id: str, worker_id: str, *, ttl_seconds: int=30) -> RecoveryLease:
        if self._emergency_stop():raise PermissionError('emergency_stop_active')
        worker=str(worker_id or '').strip()
        if not worker:raise ValueError('worker identity required')
        now=time.time();expires=now+max(1,int(ttl_seconds))
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT worker_id,fencing_token,lease_expires_at,state FROM recovery_transactions WHERE transaction_id=?',(transaction_id,)).fetchone()
            if not row:con.rollback();raise KeyError(transaction_id)
            if row['state'] in TERMINAL_RECOVERY_STATES:con.rollback();raise RuntimeError('transaction is terminal')
            if row['worker_id'] and float(row['lease_expires_at'])>now and row['worker_id']!=worker:
                con.rollback();raise RuntimeError('recovery_lease_held')
            fence=int(row['fencing_token'])+1
            con.execute('UPDATE recovery_transactions SET worker_id=?,fencing_token=?,lease_expires_at=?,updated_at=? WHERE transaction_id=?',
                        (worker,fence,expires,now,transaction_id))
            self._audit(con,transaction_id,'lease.acquired',{'worker_id':worker,'fencing_token':fence,'lease_expires_at':expires})
            con.commit()
        return RecoveryLease(transaction_id,worker,fence,expires)

    def assert_fence(self, lease: RecoveryLease):
        with self._con() as con:row=con.execute('SELECT worker_id,fencing_token,lease_expires_at FROM recovery_transactions WHERE transaction_id=?',(lease.transaction_id,)).fetchone()
        if not row:raise KeyError(lease.transaction_id)
        if row['worker_id']!=lease.worker_id or int(row['fencing_token'])!=int(lease.fencing_token):raise PermissionError('fencing_token_mismatch')
        if float(row['lease_expires_at'])<=time.time():raise TimeoutError('recovery_lease_expired')
        return True

    def renew_lease(self, lease: RecoveryLease, *, ttl_seconds:int=30) -> RecoveryLease:
        self.assert_fence(lease);expires=time.time()+max(1,int(ttl_seconds))
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            cur=con.execute('UPDATE recovery_transactions SET lease_expires_at=?,updated_at=? WHERE transaction_id=? AND worker_id=? AND fencing_token=?',
                            (expires,time.time(),lease.transaction_id,lease.worker_id,lease.fencing_token))
            if cur.rowcount!=1:con.rollback();raise PermissionError('fencing_token_mismatch')
            con.commit()
        return RecoveryLease(lease.transaction_id,lease.worker_id,lease.fencing_token,expires)

    def release_lease(self, lease: RecoveryLease):
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            cur=con.execute('UPDATE recovery_transactions SET worker_id="",lease_expires_at=0,updated_at=? WHERE transaction_id=? AND worker_id=? AND fencing_token=?',
                            (time.time(),lease.transaction_id,lease.worker_id,lease.fencing_token))
            if cur.rowcount:self._audit(con,lease.transaction_id,'lease.released',{'fencing_token':lease.fencing_token})
            con.commit()
        return bool(cur.rowcount)

    def begin_dispatch(self, lease: RecoveryLease, *, action_id: str, idempotency_key: str, operation_class: str,
                       target: str='', parameter_digest: str=''):
        if self._emergency_stop():raise PermissionError('emergency_stop_active')
        self.assert_fence(lease)
        if not self.transactions.transaction(lease.transaction_id):raise KeyError(lease.transaction_id)
        key=str(idempotency_key or '').strip()
        if not key:raise ValueError('idempotency key required')
        now=time.time()
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            prior=con.execute('SELECT * FROM recovery_dispatches WHERE idempotency_key=?',(key,)).fetchone()
            if prior:
                if prior['transaction_id']!=lease.transaction_id or prior['action_id']!=action_id or prior['operation_class']!=operation_class:
                    con.rollback();raise PermissionError('idempotency_key_rebound')
                item=dict(prior);con.rollback();return item,False
            dispatch_id=str(uuid.uuid4())
            con.execute('''INSERT INTO recovery_dispatches(dispatch_id,transaction_id,action_id,idempotency_key,operation_class,target,state,attempt_no,worker_id,fencing_token,parameter_digest,created_at)
                           VALUES(?,?,?,?,?,?,'dispatching',1,?,?,?,?)''',
                        (dispatch_id,lease.transaction_id,action_id,key,str(operation_class),str(target)[:500],lease.worker_id,lease.fencing_token,str(parameter_digest),now))
            con.execute("UPDATE recovery_transactions SET state='dispatching',updated_at=? WHERE transaction_id=?",(now,lease.transaction_id))
            self._audit(con,lease.transaction_id,'dispatch.started',{'dispatch_id':dispatch_id,'action_id':action_id,'operation_class':operation_class})
            con.commit()
        return self.dispatch(dispatch_id),True

    def dispatch(self, dispatch_id: str):
        with self._con() as con:row=con.execute('SELECT * FROM recovery_dispatches WHERE dispatch_id=?',(dispatch_id,)).fetchone()
        return dict(row) if row else None

    def mark_dispatched(self, lease: RecoveryLease, dispatch_id: str):
        if self._emergency_stop():raise PermissionError('emergency_stop_active')
        self.assert_fence(lease);now=time.time()
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT transaction_id,state,fencing_token FROM recovery_dispatches WHERE dispatch_id=?',(dispatch_id,)).fetchone()
            if not row:con.rollback();raise KeyError(dispatch_id)
            if int(row['fencing_token'])!=lease.fencing_token:con.rollback();raise PermissionError('fencing_token_mismatch')
            if row['state']!='dispatching':con.rollback();raise RuntimeError('dispatch_not_waiting')
            con.execute("UPDATE recovery_dispatches SET state='dispatched',dispatched_at=? WHERE dispatch_id=?",(now,dispatch_id))
            con.execute("UPDATE recovery_transactions SET state='dispatched',updated_at=? WHERE transaction_id=?",(now,lease.transaction_id))
            self._audit(con,lease.transaction_id,'dispatch.committed',{'dispatch_id':dispatch_id})
            con.commit()
        return self.dispatch(dispatch_id)

    def mark_verifying(self, lease: RecoveryLease, dispatch_id: str):
        self.assert_fence(lease)
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT state FROM recovery_dispatches WHERE dispatch_id=?',(dispatch_id,)).fetchone()
            if not row:con.rollback();raise KeyError(dispatch_id)
            if row['state'] not in {'dispatched','verifying'}:con.rollback();raise RuntimeError('dispatch_not_verifiable')
            con.execute("UPDATE recovery_dispatches SET state='verifying' WHERE dispatch_id=?",(dispatch_id,))
            con.execute("UPDATE recovery_transactions SET state='verifying',updated_at=? WHERE transaction_id=?",(time.time(),lease.transaction_id))
            con.commit()

    def record_verification(self, lease: RecoveryLease, record: VerificationRecord):
        self.assert_fence(lease)
        if record.transaction_id!=lease.transaction_id:raise PermissionError('verification_transaction_mismatch')
        dispatch=self.dispatch(record.dispatch_id)
        if not dispatch or dispatch['action_id']!=record.action_id or dispatch['idempotency_key']!=record.idempotency_key:
            raise PermissionError('verification_dispatch_mismatch')
        expected_hash=hashlib.sha256(canonical_json({'references':list(record.evidence_references),'observed':sanitize_evidence(record.observed_postcondition)}).encode('utf-8')).hexdigest()
        if expected_hash!=record.evidence_checksum:raise PermissionError('evidence_checksum_mismatch')
        if record.verification_fresh_until < record.verification_timestamp:raise ValueError('invalid_verification_freshness')
        now=time.time();verification_id=str(uuid.uuid4())
        state_map={
            VerificationOutcome.VERIFIED_SUCCESS:'verified_success', VerificationOutcome.VERIFIED_NO_EFFECT:'verified_no_effect',
            VerificationOutcome.VERIFIED_PARTIAL:'partially_completed', VerificationOutcome.VERIFIED_FAILURE:'failed',
            VerificationOutcome.UNKNOWN_OUTCOME:'recovery_review_required', VerificationOutcome.RECOVERY_REVIEW_REQUIRED:'recovery_review_required',
            VerificationOutcome.CANCELLED_BEFORE_DISPATCH:'cancelled', VerificationOutcome.BLOCKED_BEFORE_DISPATCH:'failed',
        }
        next_state=state_map[record.result]
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            count=con.execute('SELECT COUNT(*) AS n FROM recovery_verifications WHERE dispatch_id=?',(record.dispatch_id,)).fetchone()['n']
            con.execute('''INSERT INTO recovery_verifications(verification_id,transaction_id,action_id,dispatch_id,idempotency_key,operation_class,target,precondition_json,expected_postcondition,observed_postcondition_json,verifier_identity,verifier_version,evidence_references_json,evidence_checksum,verification_timestamp,verification_fresh_until,confidence,result,explanation,attempt_no)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (verification_id,record.transaction_id,record.action_id,record.dispatch_id,record.idempotency_key,record.operation_class,record.target,
                         canonical_json(record.precondition),record.expected_postcondition,canonical_json(record.observed_postcondition),record.verifier_identity,record.verifier_version,
                         canonical_json(list(record.evidence_references)),record.evidence_checksum,record.verification_timestamp,record.verification_fresh_until,record.confidence,record.result.value,record.explanation,count+1))
            con.execute("UPDATE recovery_dispatches SET state='verified',completed_at=? WHERE dispatch_id=?",(now,record.dispatch_id))
            con.execute('UPDATE recovery_transactions SET state=?,recovery_reason=?,updated_at=? WHERE transaction_id=?',
                        (next_state,'verification_unknown' if next_state=='recovery_review_required' else '',now,record.transaction_id))
            self._audit(con,record.transaction_id,'verification.recorded',{'verification_id':verification_id,'dispatch_id':record.dispatch_id,'result':record.result.value,'evidence_checksum':record.evidence_checksum})
            con.commit()
        return {'verification_id':verification_id,'state':next_state,'result':record.result.value}

    def latest_verification(self, dispatch_id: str):
        with self._con() as con:row=con.execute('SELECT * FROM recovery_verifications WHERE dispatch_id=? ORDER BY verification_timestamp DESC LIMIT 1',(dispatch_id,)).fetchone()
        if not row:return None
        out=dict(row)
        for key in ('precondition_json','observed_postcondition_json','evidence_references_json'):
            try:out[key[:-5]]=json.loads(out.pop(key))
            except Exception:out[key[:-5]]={} if key!='evidence_references_json' else []
        return out

    def retry_decision(self, dispatch_id: str, *, idempotent: bool=False) -> dict[str,Any]:
        dispatch=self.dispatch(dispatch_id)
        if not dispatch:return {'allowed':False,'reason':'missing_dispatch'}
        if dispatch['state']=='dispatching' and dispatch.get('dispatched_at') is None:
            return {'allowed':True,'reason':'never_dispatched'}
        verification=self.latest_verification(dispatch_id)
        if not verification:return {'allowed':False,'reason':'retry_not_safe'}
        if dispatch['operation_class'] in RETRY_BLOCKED_CLASSES:return {'allowed':False,'reason':'retry_not_safe'}
        if verification['result']!='verified_no_effect':return {'allowed':False,'reason':'retry_not_safe'}
        if not idempotent:return {'allowed':False,'reason':'retry_not_safe'}
        return {'allowed':True,'reason':'verified_no_effect'}

    def plan_compensation(self, transaction_id: str, *, original_action_id: str, category: str,
                          operation_class: str='', plan: dict[str,Any] | None=None,
                          requires_approval: bool=False, requires_reauth: bool=False):
        if category not in COMPENSATION_CATEGORIES:raise ValueError('invalid compensation category')
        if category=='irreversible' and plan:raise ValueError('irreversible action cannot claim a rollback plan')
        if category=='automatically_reversible' and (requires_approval or requires_reauth):category='compensation_available'
        latest=self._latest_action_verification(transaction_id,original_action_id)
        if latest and latest['result'] in {'unknown_outcome','recovery_review_required'}:raise RuntimeError('unknown outcome must be verified before compensation')
        cid=str(uuid.uuid4());now=time.time();safe_plan=sanitize_evidence(plan)
        state='available' if category in {'automatically_reversible','compensation_available'} else category
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('''INSERT INTO recovery_compensations(compensation_id,transaction_id,original_action_id,category,operation_class,plan_json,result_json,requires_approval,requires_reauth,state,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,'{}',?,?,?,?,?)''',
                        (cid,transaction_id,original_action_id,category,str(operation_class),canonical_json(safe_plan),1 if requires_approval else 0,1 if requires_reauth else 0,state,now,now))
            tx_state='compensation_requires_approval' if requires_approval else ('compensation_available' if state=='available' else 'recovery_review_required')
            con.execute('UPDATE recovery_transactions SET state=?,compensation_plan_json=?,updated_at=? WHERE transaction_id=?',(tx_state,canonical_json({'compensation_id':cid,'category':category,**safe_plan}),now,transaction_id))
            self._audit(con,transaction_id,'compensation.planned',{'compensation_id':cid,'category':category,'requires_approval':requires_approval,'requires_reauth':requires_reauth})
            con.commit()
        return self.compensation(cid)

    def compensation(self, compensation_id: str):
        with self._con() as con:row=con.execute('SELECT * FROM recovery_compensations WHERE compensation_id=?',(compensation_id,)).fetchone()
        if not row:return None
        out=dict(row);out['requires_approval']=bool(out['requires_approval']);out['requires_reauth']=bool(out['requires_reauth'])
        for key in ('plan_json','result_json'):
            try:out[key[:-5]]=json.loads(out.pop(key))
            except Exception:out[key[:-5]]={}
        return out

    def record_compensation_result(self, lease: RecoveryLease, compensation_id: str, *, compensation_action_id: str,
                                   result: dict[str,Any], verified: bool):
        if self._emergency_stop():raise PermissionError('emergency_stop_active')
        self.assert_fence(lease);item=self.compensation(compensation_id)
        if not item or item['transaction_id']!=lease.transaction_id:raise KeyError(compensation_id)
        safe=sanitize_evidence(result);now=time.time();state='verified' if verified else 'compensation_failed'
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('UPDATE recovery_compensations SET compensation_action_id=?,result_json=?,state=?,updated_at=? WHERE compensation_id=?',
                        (str(compensation_action_id),canonical_json(safe),state,now,compensation_id))
            con.execute('UPDATE recovery_transactions SET compensation_result_json=?,state=?,updated_at=? WHERE transaction_id=?',
                        (canonical_json({'compensation_id':compensation_id,**safe}), 'active' if verified else 'recovery_review_required',now,lease.transaction_id))
            self._audit(con,lease.transaction_id,'compensation.finished',{'compensation_id':compensation_id,'verified':verified})
            con.commit()
        return self.compensation(compensation_id)

    def _latest_action_verification(self, transaction_id: str, action_id: str):
        with self._con() as con:row=con.execute('SELECT * FROM recovery_verifications WHERE transaction_id=? AND action_id=? ORDER BY verification_timestamp DESC LIMIT 1',(transaction_id,action_id)).fetchone()
        return dict(row) if row else None

    def owner_decision(self, transaction_id: str, binding: OperatorBinding, *, decision: str, decision_id: str,
                       reauthenticated: bool=False):
        self.transactions.assert_binding(transaction_id,binding)
        if decision not in SAFE_OWNER_DECISIONS:raise ValueError('invalid recovery decision')
        if decision in CONSEQUENTIAL_OWNER_DECISIONS and not reauthenticated:raise PermissionError('reauthentication_required')
        did=str(decision_id or '').strip()
        if not did:raise ValueError('decision id required')
        now=time.time()
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            prior=con.execute('SELECT * FROM recovery_decisions WHERE decision_id=?',(did,)).fetchone()
            if prior:
                if prior['transaction_id']!=transaction_id or prior['decision']!=decision:con.rollback();raise PermissionError('recovery_decision_replay')
                item=dict(prior);con.rollback();return item,False
            con.execute('''INSERT INTO recovery_decisions(decision_id,transaction_id,owner_id,device_id,session_id,security_epoch,decision,consequential,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?)''',(did,transaction_id,binding.owner_id,binding.device_id,binding.session_id,binding.security_epoch,decision,1 if decision in CONSEQUENTIAL_OWNER_DECISIONS else 0,now))
            next_state={'abandon_transaction':'abandoned_by_owner','cancel_remaining':'cancelled','mark_externally_completed':'completed'}.get(decision)
            con.execute('UPDATE recovery_transactions SET owner_decision=?,owner_decision_id=?,state=COALESCE(?,state),updated_at=? WHERE transaction_id=?',
                        (decision,did,next_state,now,transaction_id))
            self._audit(con,transaction_id,'owner.decision',{'decision':decision,'decision_id':did})
            con.commit()
        return {'decision_id':did,'transaction_id':transaction_id,'decision':decision},True

    def recover_interrupted(self):
        now=time.time();recovered=[]
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            rows=con.execute("SELECT transaction_id,state FROM recovery_transactions WHERE state IN ('dispatching','dispatched','verifying')").fetchall()
            for row in rows:
                txid=row['transaction_id'];recovered.append(txid)
                dispatched=con.execute("SELECT 1 FROM recovery_dispatches WHERE transaction_id=? AND dispatched_at IS NOT NULL LIMIT 1",(txid,)).fetchone()
                if dispatched:
                    con.execute("UPDATE recovery_transactions SET state='recovery_review_required',recovery_reason='restart_after_dispatch_outcome_requires_verification',worker_id='',lease_expires_at=0,updated_at=? WHERE transaction_id=?",(now,txid))
                else:
                    con.execute("UPDATE recovery_transactions SET state='active',recovery_reason='restart_before_dispatch_safe_to_replan',worker_id='',lease_expires_at=0,updated_at=? WHERE transaction_id=?",(now,txid))
                self._audit(con,txid,'recovery.restart',{'had_dispatch':bool(dispatched)})
            con.commit()
        return recovered

    def emergency_stop(self):
        now=time.time()
        with self._lock,self._con() as con:
            con.execute('BEGIN IMMEDIATE')
            rows=con.execute("SELECT transaction_id FROM recovery_transactions WHERE state NOT IN ('cancelled','failed','completed','abandoned_by_owner')").fetchall()
            for row in rows:
                con.execute("UPDATE recovery_transactions SET state='recovery_review_required',recovery_reason='emergency_stop_active',worker_id='',lease_expires_at=0,updated_at=? WHERE transaction_id=?",(now,row['transaction_id']))
                self._audit(con,row['transaction_id'],'emergency_stop',{})
            con.commit()
        return len(rows)

    def recovery_report(self, transaction_id: str) -> dict[str,Any]:
        tx=self.transactions.transaction(transaction_id)
        rec=self.snapshot(transaction_id)
        if not tx or not rec:raise KeyError(transaction_id)
        with self._con() as con:
            dispatches=[dict(r) for r in con.execute('SELECT * FROM recovery_dispatches WHERE transaction_id=? ORDER BY created_at',(transaction_id,)).fetchall()]
            verifications=[dict(r) for r in con.execute('SELECT verification_id,action_id,dispatch_id,operation_class,target,evidence_checksum,verification_timestamp,verification_fresh_until,result,explanation FROM recovery_verifications WHERE transaction_id=? ORDER BY verification_timestamp',(transaction_id,)).fetchall()]
            comps=[dict(r) for r in con.execute('SELECT compensation_id,original_action_id,compensation_action_id,category,state,requires_approval,requires_reauth,updated_at FROM recovery_compensations WHERE transaction_id=? ORDER BY created_at',(transaction_id,)).fetchall()]
        return {'transaction_id':transaction_id,'goal':tx['goal'],'state':rec['state'],'checkpoint_index':tx['checkpoint_index'],'resume_position':rec['resume_position'],
                'recovery_reason':rec['recovery_reason'],'owner_decision':rec['owner_decision'],'dispatches':dispatches,'verifications':verifications,'compensations':comps,
                'rollback_limitations':self._rollback_limitations(comps),'updated_at':rec['updated_at']}

    @staticmethod
    def _rollback_limitations(comps):
        if any(c['category']=='irreversible' for c in comps):return 'At least one action is irreversible; no automatic rollback is claimed.'
        if any(c['category']=='manual_recovery_only' for c in comps):return 'At least one action requires manual recovery.'
        if any(bool(c['requires_approval']) for c in comps):return 'Compensation exists but requires separate owner approval.'
        return 'Any compensation remains a separate governed and independently verified action.'

    def audit(self, transaction_id: str):
        with self._con() as con:rows=con.execute('SELECT event,payload_json,created_at FROM recovery_audit WHERE transaction_id=? ORDER BY id',(transaction_id,)).fetchall()
        return [dict(r) for r in rows]
