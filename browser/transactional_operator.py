from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from browser.safe_operator import BrowserRecoveryRequired, BrowserSafetyError, SafeBrowserOperator
from desktop.operator_transactions import OperatorBinding, OperatorTransactionStore, new_transaction_id
from security.approvals import parameter_hash


def _digest(value) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class TransactionalBrowserOperator:
    """Durable W7.1 transaction shell around the W7.4 browser operator."""
    def __init__(self, safe: SafeBrowserOperator, data_dir: Path, *, emergency_stop=None):
        self.safe=safe
        self.store=OperatorTransactionStore(Path(data_dir)/'operator-transactions.sqlite3')
        self.emergency_stop=emergency_stop or (lambda:False)

    @staticmethod
    def _binding(context:dict)->OperatorBinding:
        required=('owner_id','device_id','session_id','security_epoch')
        if not isinstance(context,dict) or any(context.get(key) in (None,'') for key in required):
            raise PermissionError('trusted browser transaction binding is required')
        return OperatorBinding(owner_id=str(context['owner_id']),device_id=str(context['device_id']),session_id=str(context['session_id']),security_epoch=int(context['security_epoch']),conversation_id=str(context.get('conversation_id') or ''),workflow_id=str(context.get('workflow_id') or ''))

    def prepare(self,action:str,parameters:dict,*,requires_approval:bool)->dict:
        incoming=dict(parameters or {})
        context=dict(incoming.get('_trusted_context') or {})
        reauthenticated=bool(incoming.get('_trusted_reauthenticated'))
        binding=self._binding(context)
        prepared=self.safe.prepare(action,incoming)
        # Only authenticated runtime context is restored. Model-supplied internal
        # fields were already stripped by ToolRegistry before this call.
        prepared['_trusted_context']=context
        prepared['_trusted_reauthenticated']=reauthenticated
        txid=new_transaction_id()
        public={str(k):v for k,v in prepared.items() if not str(k).startswith('_')}
        plan={
            'kind':'safe_browser',
            'steps':[{
                'kind':str(action),
                'parameter_hash':parameter_hash(public),
                'destination':str(prepared.get('destination') or ''),
                'target_id':str(prepared.get('target_id') or ''),
                'observation_digest':str(prepared.get('_observation_digest') or ''),
                'expected_postcondition':'fresh browser postcondition must be verified and recorded',
            }],
        }
        plan['canonical_plan_digest']=_digest(plan)
        deadline=time.time()+max(5,min(int(public.get('timeout_ms') or 10000)//1000+30,120))
        record,created=self.store.propose(txid,binding,goal=f'browser:{action}',action_plan=plan,deadline_at=deadline)
        if not created:
            raise RuntimeError('new browser transaction ID unexpectedly collided')
        self.store.transition(txid,'policy_check')
        self.store.transition(txid,'approval_required' if requires_approval else 'permitted')
        prepared['_browser_transaction_id']=txid
        prepared['_browser_plan_digest']=plan['canonical_plan_digest']
        prepared['_browser_requires_approval']=bool(requires_approval)
        return prepared

    def cancel(self,parameters:dict)->bool:
        txid=str((parameters or {}).get('_browser_transaction_id') or '')
        if not txid:return False
        tx=self.store.transaction(txid)
        if not tx:return False
        if tx['state'] not in {'completed','failed','cancelled','recovery_review_required'}:
            self.store.request_cancel(txid)
            self.store.transition(txid,'cancelled',error_code='cancelled')
        return True

    def execute(self,action:str,parameters:dict)->dict:
        params=dict(parameters or {})
        context=dict(params.get('_trusted_context') or {})
        binding=self._binding(context)
        txid=str(params.get('_browser_transaction_id') or '')
        if not txid or not params.get('_personal_ai_prepared'):
            raise PermissionError('browser execution requires a prepared trusted transaction')
        tx=self.store.assert_binding(txid,binding)
        if tx['state']=='completed':
            return {'verified':True,'reason':'deduplicated completed browser transaction','transaction_id':txid,'deduplicated':True,'evidence':{}}
        if tx['state']=='recovery_review_required':
            raise BrowserRecoveryRequired('Browser transaction requires owner recovery review before any redispatch.')
        if tx.get('cancel_requested'):
            if tx['state'] not in {'cancelled','completed','failed'}:self.store.transition(txid,'cancelled',error_code='cancelled')
            raise RuntimeError('browser execution cancelled by owner')
        if self.emergency_stop():
            if tx['state'] not in {'cancelled','completed','failed','recovery_review_required'}:self.store.transition(txid,'cancelled',error_code='emergency_stop')
            raise BrowserSafetyError('emergency_stop_active')
        if tx.get('deadline_at') is not None and time.time()>=float(tx['deadline_at']):
            if tx['state'] not in {'completed','failed','cancelled','recovery_review_required'}:self.store.transition(txid,'failed',error_code='observation_expired')
            raise BrowserSafetyError('observation_expired')
        plan=tx.get('plan') or {}
        if str(plan.get('canonical_plan_digest') or '') != str(params.get('_browser_plan_digest') or ''):
            raise PermissionError('browser plan digest changed after preparation')
        if tx['state']=='approval_required':
            # Reaching a side-effecting handler means the existing Trusted Action
            # Core consumed the exact one-use approval ticket first.
            self.store.transition(txid,'permitted')
        self.store.assert_dispatchable(txid,binding)
        self.store.transition(txid,'executing')
        public={str(k):v for k,v in params.items() if not str(k).startswith('_')}
        action_row,created=self.store.start_action(txid,1,kind=f'browser:{action}',parameter_hash=parameter_hash(public),expected_postcondition='fresh browser postcondition verified',before_observation_id=str(params.get('_observation_id') or ''),target_identity=str(params.get('target_id') or ''),plan_digest=str(params.get('_browser_plan_digest') or ''),observation_digest=str(params.get('_observation_digest') or ''))
        if not created:
            if action_row.get('state')=='verified':
                self.store.transition(txid,'verifying');self.store.transition(txid,'completed')
                return {'verified':True,'reason':'deduplicated verified browser action','transaction_id':txid,'deduplicated':True,'evidence':dict(action_row.get('evidence') or {})}
            self.store.transition(txid,'recovery_review_required',recovery_reason='duplicate_dispatch_uncertain')
            raise BrowserRecoveryRequired('Duplicate browser dispatch requires recovery review.')
        try:
            result=self.safe.execute(action,params)
        except BrowserRecoveryRequired as exc:
            self.store.finish_action(action_row['action_id'],verified=False,evidence={'redacted':True},error_code='recovery_review_required')
            self.store.transition(txid,'recovery_review_required',error_code='recovery_review_required',recovery_reason=str(exc)[:500])
            raise
        except Exception as exc:
            self.store.finish_action(action_row['action_id'],verified=False,evidence={'redacted':True},error_code=type(exc).__name__)
            if tx.get('state') not in {'recovery_review_required'}:
                self.store.transition(txid,'failed',error_code=type(exc).__name__)
            raise
        evidence=dict(result.get('evidence') or {})
        redacted={'before':evidence.get('before'),'after':evidence.get('after'),'reason':result.get('reason'),'verified':bool(result.get('verified'))}
        self.store.finish_action(action_row['action_id'],verified=bool(result.get('verified')),evidence=redacted,error_code='' if result.get('verified') else 'postcondition_unverified')
        if not result.get('verified'):
            self.store.transition(txid,'recovery_review_required',error_code='postcondition_unverified',recovery_reason='browser postcondition could not be verified')
            raise BrowserRecoveryRequired('Browser postcondition is uncertain; owner recovery review is required.')
        self.store.transition(txid,'verifying');self.store.transition(txid,'completed')
        result['transaction_id']=txid
        return result
