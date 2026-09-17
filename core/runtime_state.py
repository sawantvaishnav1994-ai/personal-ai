from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock

class RuntimeState(StrEnum):
    IDLE='IDLE'; ACTIVE='ACTIVE'; LISTENING='LISTENING'; UNDERSTANDING='UNDERSTANDING'; THINKING='THINKING'
    MEMORY_RETRIEVAL='MEMORY_RETRIEVAL'; KNOWLEDGE_RETRIEVAL='KNOWLEDGE_RETRIEVAL'; TOOL_ACTION='TOOL_ACTION'
    RESPONDING='RESPONDING'; NEEDS_APPROVAL='NEEDS_APPROVAL'; BACKGROUND='BACKGROUND'; SUCCESS='SUCCESS'; WARNING='WARNING'; ERROR='ERROR'

LEGACY_STATE_ALIASES={
'idle':RuntimeState.IDLE,'ready':RuntimeState.ACTIVE,'active':RuntimeState.ACTIVE,'listening':RuntimeState.LISTENING,
'understanding':RuntimeState.UNDERSTANDING,'thinking':RuntimeState.THINKING,'memory':RuntimeState.MEMORY_RETRIEVAL,
'memory_retrieval':RuntimeState.MEMORY_RETRIEVAL,'retrieving_memory':RuntimeState.MEMORY_RETRIEVAL,
'knowledge':RuntimeState.KNOWLEDGE_RETRIEVAL,'knowledge_retrieval':RuntimeState.KNOWLEDGE_RETRIEVAL,
'retrieving_knowledge':RuntimeState.KNOWLEDGE_RETRIEVAL,'acting':RuntimeState.TOOL_ACTION,'action':RuntimeState.TOOL_ACTION,
'tool':RuntimeState.TOOL_ACTION,'tool_action':RuntimeState.TOOL_ACTION,'speaking':RuntimeState.RESPONDING,
'responding':RuntimeState.RESPONDING,'response':RuntimeState.RESPONDING,'approval':RuntimeState.NEEDS_APPROVAL,
'needs_approval':RuntimeState.NEEDS_APPROVAL,'waiting_approval':RuntimeState.NEEDS_APPROVAL,'background':RuntimeState.BACKGROUND,
'success':RuntimeState.SUCCESS,'warning':RuntimeState.WARNING,'error':RuntimeState.ERROR}

def normalize_runtime_state(value):
    if isinstance(value,RuntimeState): return value
    key=str(value or 'idle').strip().lower().replace('-','_').replace(' ','_')
    try:return RuntimeState[key.upper()]
    except KeyError:return LEGACY_STATE_ALIASES.get(key,RuntimeState.IDLE)

LEGAL_TRANSITIONS={
RuntimeState.IDLE:{RuntimeState.ACTIVE,RuntimeState.LISTENING,RuntimeState.BACKGROUND,RuntimeState.ERROR},
RuntimeState.ACTIVE:{RuntimeState.IDLE,RuntimeState.LISTENING,RuntimeState.UNDERSTANDING,RuntimeState.BACKGROUND,RuntimeState.ERROR},
RuntimeState.LISTENING:{RuntimeState.UNDERSTANDING,RuntimeState.ACTIVE,RuntimeState.IDLE,RuntimeState.ERROR},
RuntimeState.UNDERSTANDING:{RuntimeState.IDLE,RuntimeState.MEMORY_RETRIEVAL,RuntimeState.KNOWLEDGE_RETRIEVAL,RuntimeState.THINKING,RuntimeState.RESPONDING,RuntimeState.ERROR},
RuntimeState.MEMORY_RETRIEVAL:{RuntimeState.IDLE,RuntimeState.KNOWLEDGE_RETRIEVAL,RuntimeState.THINKING,RuntimeState.RESPONDING,RuntimeState.ERROR},
RuntimeState.KNOWLEDGE_RETRIEVAL:{RuntimeState.IDLE,RuntimeState.MEMORY_RETRIEVAL,RuntimeState.THINKING,RuntimeState.RESPONDING,RuntimeState.ERROR},
RuntimeState.THINKING:{RuntimeState.IDLE,RuntimeState.NEEDS_APPROVAL,RuntimeState.TOOL_ACTION,RuntimeState.RESPONDING,RuntimeState.BACKGROUND,RuntimeState.ERROR},
RuntimeState.NEEDS_APPROVAL:{RuntimeState.TOOL_ACTION,RuntimeState.ACTIVE,RuntimeState.IDLE,RuntimeState.ERROR},
RuntimeState.TOOL_ACTION:{RuntimeState.SUCCESS,RuntimeState.WARNING,RuntimeState.RESPONDING,RuntimeState.ERROR},
RuntimeState.SUCCESS:{RuntimeState.RESPONDING,RuntimeState.ACTIVE,RuntimeState.IDLE,RuntimeState.BACKGROUND},
RuntimeState.WARNING:{RuntimeState.TOOL_ACTION,RuntimeState.RESPONDING,RuntimeState.ACTIVE,RuntimeState.IDLE,RuntimeState.ERROR},
RuntimeState.RESPONDING:{RuntimeState.IDLE,RuntimeState.ACTIVE,RuntimeState.LISTENING,RuntimeState.ERROR},
RuntimeState.BACKGROUND:{RuntimeState.ACTIVE,RuntimeState.IDLE,RuntimeState.THINKING,RuntimeState.ERROR},
RuntimeState.ERROR:{RuntimeState.IDLE,RuntimeState.ACTIVE,RuntimeState.LISTENING}}

@dataclass(frozen=True)
class StateSnapshot:
    state:RuntimeState; sequence:int; reason:str; request_id:str|None=None

class RuntimeStateAuthority:
    """Canonical V1 user-facing state projection over factual runtime events."""
    def __init__(self,events,*,initial=RuntimeState.IDLE):
        self.events=events; self._state=initial; self._sequence=0; self._request_id=None; self._lock=RLock(); self._subscriptions=[]; self._bind_compatibility_events()
    @property
    def state(self):
        with self._lock:return self._state
    def snapshot(self):
        with self._lock:return StateSnapshot(self._state,self._sequence,'current',self._request_id)
    def transition(self,target,*,reason,force=False,request_id=None,activate_request=False,**context):
        normalized=normalize_runtime_state(target); scoped=str(request_id or '').strip() or None; stale=False
        with self._lock:
            current=self._state; previous_request=self._request_id
            if activate_request and scoped:self._request_id=scoped
            elif scoped and self._request_id and scoped!=self._request_id:
                stale=True; current_request=self._request_id; snapshot=StateSnapshot(current,self._sequence,'stale_request_ignored',current_request)
            else:
                if scoped and self._request_id is None:self._request_id=scoped
                changed_request=bool(activate_request and scoped and scoped!=previous_request)
                if normalized==current and not changed_request:return StateSnapshot(current,self._sequence,reason,self._request_id)
                if not force and normalized!=current and normalized not in LEGAL_TRANSITIONS[current]:
                    raise ValueError(f'illegal runtime state transition: {current.value} -> {normalized.value}')
                self._sequence+=1; self._state=normalized; snapshot=StateSnapshot(normalized,self._sequence,reason,self._request_id)
        if stale:
            self.events.emit('runtime.state.stale_ignored',request_id=scoped,current_request_id=current_request); return snapshot
        self.events.emit('runtime.state',state=normalized.value,previous_state=current.value,sequence=snapshot.sequence,reason=str(reason),request_id=snapshot.request_id,**context)
        return snapshot
    def _compat(self,event):
        try:self.transition(normalize_runtime_state(event.get('state')),reason=f"legacy:{event.get('event','state')}",request_id=event.get('request_id'))
        except ValueError:return
    def _safe_transition(self,target,reason,event,*,activate_request=False):
        try:self.transition(target,reason=reason,request_id=event.get('request_id'),activate_request=activate_request,force=activate_request)
        except ValueError:return
    def _bind_compatibility_events(self):
        self._subscriptions.append(self.events.subscribe('state',self._compat))
        mapping={
        'turn.started':(RuntimeState.UNDERSTANDING,'turn_started',True),
        'turn.needs_approval':(RuntimeState.NEEDS_APPROVAL,'approval_required',False),
        'turn.completed':(RuntimeState.RESPONDING,'turn_completed',False),
        'turn.cancelled':(RuntimeState.IDLE,'owner_cancelled',False),
        'turn.failed':(RuntimeState.ERROR,'turn_failed',False),
        'approval.required':(RuntimeState.NEEDS_APPROVAL,'approval_required',False),
        'approval.approved':(RuntimeState.TOOL_ACTION,'approval_approved',False),
        'tool.unverified':(RuntimeState.WARNING,'verification_warning',False),
        'automation.started':(RuntimeState.BACKGROUND,'background_started',False),
        'workflow.started':(RuntimeState.BACKGROUND,'background_started',False),
        'emergency_stop':(RuntimeState.ERROR,'emergency_stop',False),
        'p10.emergency_stop':(RuntimeState.ERROR,'emergency_stop',False)}
        for name,(target,reason,activate) in mapping.items():
            self._subscriptions.append(self.events.subscribe(name,lambda event,t=target,r=reason,a=activate:self._safe_transition(t,r,event,activate_request=a)))
    def close(self):
        for unsubscribe in self._subscriptions:unsubscribe()
        self._subscriptions.clear()
