from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import sqlite3
import time
from typing import Any, Callable
from urllib.parse import urlparse
from core.permissions import PermissionDecision, PermissionEngine
from desktop.operator_context import current_operator_request

class Risk(IntEnum): READ_ONLY=0; REVERSIBLE=1; EXTERNAL_SIDE_EFFECT=2; DESTRUCTIVE=3; CRITICAL=4
@dataclass(frozen=True)
class VerificationResult:
    verified: bool; reason: str; evidence: dict[str,Any]
@dataclass
class Tool:
    name:str; description:str; handler:Callable[[dict[str,Any]],Any]; risk:Risk=Risk.READ_ONLY
    verifier:Callable[[dict[str,Any],Any],Any]|None=None; rollback:Callable[[dict[str,Any],Any],Any]|None=None; rollback_description:str=''
    allowed_destinations:tuple[str,...]|None=None; verification_required:bool=False; requires_reauth:bool=False
    connector_id:str|None=None; capability:str|None=None; minimum_risk:Risk|None=None; prohibited_data_classifications:tuple[str,...]=(); prohibited:bool=False
    prepare:Callable[[dict[str,Any]],dict[str,Any]]|None=None; on_reject:Callable[[dict[str,Any]],Any]|None=None; requires_trusted_context:bool=False
    policy_operation:str|None=None; policy_target_type:str|None=None
class ToolRegistry:
    def __init__(self,settings):
        self.settings=settings; self.permissions=PermissionEngine(settings.autonomy_mode); self._tools={}; self.emergency_stop=False; self._control_path=None; self._approval_path=None; self.policy_gateway=None
        data_dir=getattr(settings,'data_dir',None)
        if data_dir is not None:
            data_root=Path(data_dir); self._control_path=data_root/'runtime-controls.sqlite3'; self._approval_path=data_root/'trusted-actions.sqlite3'; self._control_path.parent.mkdir(parents=True,exist_ok=True)
            with self._control_con() as con:
                con.execute('CREATE TABLE IF NOT EXISTS runtime_controls (key TEXT PRIMARY KEY,value TEXT NOT NULL)'); row=con.execute("SELECT value FROM runtime_controls WHERE key='emergency_stop'").fetchone(); self.emergency_stop=bool(row and row[0]=='1')
            from security.approvals import ApprovalManager
            from security.policy_gateway import PolicyGateway
            self.policy_gateway=PolicyGateway(data_root/'operator-policies.sqlite3',emergency_stop=lambda:self.emergency_stop,security_epoch_provider=lambda:ApprovalManager(path=self._approval_path).current_security_epoch())
    def _control_con(self):return sqlite3.connect(self._control_path)
    def current_security_epoch(self):
        if self._approval_path is None:return 0
        from security.approvals import ApprovalManager
        return ApprovalManager(path=self._approval_path).current_security_epoch()
    def set_emergency_stop(self,enabled:bool):
        previous=self.emergency_stop; self.emergency_stop=bool(enabled)
        if self._control_path is not None:
            with self._control_con() as con:con.execute("INSERT OR REPLACE INTO runtime_controls(key,value) VALUES('emergency_stop',?)",('1' if enabled else '0',))
        if self.emergency_stop and not previous and self._approval_path is not None and self._approval_path.exists():
            from security.approvals import ApprovalManager; ApprovalManager(path=self._approval_path).advance_security_epoch()
        return self.emergency_stop
    def evaluate_policy(self,operation,**kwargs):
        if self.policy_gateway is None:raise PermissionError('policy gateway is unavailable; default deny')
        return self.policy_gateway.evaluate(operation,**kwargs)
    def policy_snapshot(self,owner_id='owner'):
        if self.policy_gateway is None:return {'policies':[],'recent_use':[],'safe_default':'deny','schema_version':None}
        return self.policy_gateway.owner_snapshot(owner_id)
    def register(self,tool:Tool):
        if tool.name in self._tools:raise ValueError(f'Duplicate tool {tool.name}')
        if tool.minimum_risk is not None and int(tool.risk)<int(tool.minimum_risk):tool.risk=Risk(int(tool.minimum_risk))
        self._tools[tool.name]=tool
    def get(self,name):return self._tools[name]
    def all(self):return list(self._tools.values())
    def schema_text(self):return '\n'.join(f'- {t.name}: {t.description}; risk={t.risk.name}' for t in self._tools.values() if not t.prohibited)
    def set_autonomy_mode(self,mode):
        mode=str(mode).lower().strip()
        if mode not in {'observe','suggest','ask','act'}:raise ValueError('invalid autonomy mode')
        self.permissions.mode=mode; return mode
    @property
    def autonomy_mode(self):return self.permissions.mode
    @staticmethod
    def destination(parameters):
        params=parameters or {}
        sid=params.get('spreadsheet_id'); rng=params.get('range')
        if sid not in (None,'') and rng not in (None,''):return f'{str(sid)[:500]}#{str(rng)[:500]}'
        fid=params.get('file_id'); parent=params.get('parent_id'); filename=params.get('filename')
        if fid not in (None,''):return f'file:{str(fid)[:800]}'
        if filename not in (None,'') and parent not in (None,''):return f'parent:{str(parent)[:500]}/name:{str(filename)[:400]}'
        event=params.get('event')
        if isinstance(event,dict) and event.get('attendees'):
            emails=[str(x.get('email','')) for x in event['attendees'] if isinstance(x,dict) and x.get('email')]
            if emails:return ','.join(emails)[:1000]
        for key in ('destination','recipient','recipients','to','email','emails','url','domain','path','file_path','filename','channel','room','calendar_id','spreadsheet_id','document_id','repository'):
            value=params.get(key)
            if value in (None,'',[],{}):continue
            if isinstance(value,(list,tuple,set)):return ','.join(str(x) for x in value)[:1000]
            if isinstance(value,dict):return str(sorted(value.items()))[:1000]
            return str(value)[:1000]
        return ''
    @staticmethod
    def _destination_host(destination):
        value=str(destination or '').strip().lower()
        if not value:return ''
        if '@' in value and '://' not in value:return value.rsplit('@',1)[-1]
        parsed=urlparse(value if '://' in value else f'https://{value}'); return (parsed.hostname or value).lower()
    def validate_destination(self,tool,parameters):
        if not tool.allowed_destinations:return
        host=self._destination_host(self.destination(parameters)); allowed=tuple(str(x).strip().lower() for x in tool.allowed_destinations if str(x).strip())
        if not host or not any(host==x or host.endswith('.'+x) for x in allowed):raise PermissionError('destination is outside the configured allowlist')
    def effective_risk(self,tool,*,parameters=None,data_classification='internal'):
        risk=Risk(int(tool.risk));
        if tool.minimum_risk is not None:risk=max(risk,Risk(int(tool.minimum_risk)))
        destination=self.destination(parameters); classification=str(data_classification or 'internal').strip().lower()
        if destination and classification=='secret':risk=max(risk,Risk.CRITICAL)
        elif destination and classification in {'sensitive','restricted'}:risk=max(risk,Risk.DESTRUCTIVE)
        return Risk(int(risk))
    @staticmethod
    def _strip_untrusted_internal(parameters:dict):
        reserved=('_trusted_','_personal_ai_','_operator_','_browser_','_policy_')
        for key in list(parameters):
            if str(key).startswith(reserved):parameters.pop(key,None)
    def _prepare_trusted(self,tool,parameters):
        if not tool.requires_trusted_context:return parameters
        if not isinstance(parameters,dict):raise PermissionError('trusted operator parameters are required')
        prepared=bool(parameters.get('_personal_ai_prepared'))
        if not prepared:self._strip_untrusted_internal(parameters)
        context=current_operator_request()
        if context is None:raise PermissionError('trusted browser/session context is required for computer control')
        if not prepared:
            parameters['_trusted_context']=context.safe_dict()
            parameters['_trusted_reauthenticated']=bool(context.reauthenticated_at is not None and 0 <= time.time()-float(context.reauthenticated_at) <= 300)
            if tool.prepare is not None:
                value=tool.prepare(parameters)
                if not isinstance(value,dict):raise RuntimeError('trusted tool preparation must return parameters')
                parameters.clear();parameters.update(value)
            parameters['_personal_ai_prepared']=True
        return parameters
    @staticmethod
    def _public_policy_parameters(parameters):return {str(k):v for k,v in dict(parameters or {}).items() if not str(k).startswith('_')}
    def _tool_policy_operation(self,tool,parameters,data_classification='internal',*,outcome_state='not_dispatched'):
        if not tool.policy_operation:return None
        from security.policy_gateway import PolicyOperation
        context=dict(parameters.get('_trusted_context') or {})
        if any(context.get(k) in (None,'') for k in ('owner_id','device_id','session_id','security_epoch')):raise PermissionError('trusted policy binding is required')
        destination=self.destination(parameters); target_type=str(tool.policy_target_type or 'destination')
        if target_type=='domain':target={'url':destination}
        elif target_type=='path':target={'path':destination,'approved_roots':list(parameters.get('approved_roots') or [])}
        else:target={'identity':destination}
        return PolicyOperation(operation=str(tool.policy_operation),owner_id=str(context['owner_id']),device_id=str(context['device_id']),session_id=str(context['session_id']),security_epoch=int(context['security_epoch']),target_type=target_type,target_identity=target,application=dict(parameters.get('_application') or {}) or None,destination=destination,parameters=self._public_policy_parameters(parameters),data_classification=str(data_classification or 'internal'),observation_id=str(parameters.get('_observation_id') or parameters.get('_operator_observation_id') or ''),observation_digest=str(parameters.get('_observation_digest') or parameters.get('_operator_observation_digest') or ''),outcome_state=outcome_state)
    def _policy_authorize(self,tool,parameters,data_classification,*,approved=False):
        if not tool.policy_operation:return None,None
        if self.policy_gateway is None:raise PermissionError('policy gateway is unavailable; default deny')
        classification=str(parameters.get('_policy_data_classification') or data_classification or 'internal')
        if not approved:parameters['_policy_data_classification']=classification
        operation=self._tool_policy_operation(tool,parameters,classification)
        decision=self.policy_gateway.evaluate(operation,approved=bool(approved),reauthenticated=bool(parameters.get('_trusted_reauthenticated')))
        return operation,decision
    def issue_tool_policy_permit(self,parameters,data_classification='internal'):
        tool_name=str(parameters.get('_policy_tool_name') or '')
        if not tool_name or tool_name not in self._tools:raise PermissionError('trusted policy tool binding is missing')
        tool=self._tools[tool_name];operation,decision=self._policy_authorize(tool,parameters,str(parameters.get('_policy_data_classification') or data_classification),approved=True)
        if operation is None or decision is None or not decision.allowed:raise PermissionError(getattr(decision,'reason_code','policy_not_allowed'))
        permit=self.policy_gateway.issue_temporary_permit(operation,decision,ttl_seconds=60)
        return {'permit_id':permit['permit_id'],'operation':operation,'decision':decision}
    def consume_tool_policy_permit(self,parameters,permit):
        if not permit or not self.policy_gateway:raise PermissionError('one-use policy permit is required')
        if not self.policy_gateway.consume_temporary_permit(permit['permit_id'],permit['operation'],permit['decision']):raise PermissionError('one-use policy permit is invalid, expired, changed, or already used')
        return True
    def automatic(self,tool):return self.authorize(tool,confirmed=False).allowed
    def authorize(self,tool,confirmed=False,*,parameters=None,data_classification='internal'):
        if self.emergency_stop:return PermissionDecision(False,False,'owner emergency stop is active')
        if tool.prohibited:return PermissionDecision(False,False,'this connector operation is prohibited by policy')
        parameters=self._prepare_trusted(tool,parameters)
        classification=str(data_classification or 'internal').strip().lower()
        if classification in set(tool.prohibited_data_classifications):return PermissionDecision(False,False,'this data classification is prohibited for the connector operation')
        self.validate_destination(tool,parameters)
        operation,policy=self._policy_authorize(tool,parameters,classification,approved=bool(confirmed))
        if policy is not None and not policy.allowed:
            requires=policy.decision.value in {'approval_required','reauthentication_required'}
            return PermissionDecision(False,requires,policy.reason_code)
        risk=self.effective_risk(tool,parameters=parameters,data_classification=classification); return self.permissions.decide(int(risk),confirmed=confirmed)
    def verify_result(self,tool,parameters,result):
        if tool.verifier is not None:
            verdict=tool.verifier(parameters,result)
            if isinstance(verdict,VerificationResult):verification=verdict
            elif isinstance(verdict,dict):verification=VerificationResult(bool(verdict.get('verified')),str(verdict.get('reason') or ('verified' if verdict.get('verified') else 'verification failed')),dict(verdict.get('evidence') or {}))
            else:verification=VerificationResult(bool(verdict),'custom verification contract',{})
        elif isinstance(result,dict) and result.get('verified') is True:verification=VerificationResult(True,'tool returned explicit verification evidence',dict(result.get('evidence') or {}))
        elif tool.risk==Risk.READ_ONLY:verification=VerificationResult(True,'read-only handler returned observed data',{})
        else:verification=VerificationResult(False,'no result verification contract is configured for this side-effecting tool',{})
        if tool.verification_required and not verification.verified:raise RuntimeError(f'tool result verification failed: {verification.reason}')
        return verification
    @staticmethod
    def rollback_metadata(tool):return {'available':callable(tool.rollback),'description':str(tool.rollback_description or '')}
