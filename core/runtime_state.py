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
    'success':RuntimeState.SUCCESS,'warning':RuntimeState.WARNING,'error':RuntimeState.ERROR,
}


def normalize_runtime_state(value:RuntimeState|str|None)->RuntimeState:
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
    RuntimeState.ERROR:{RuntimeState.IDLE,RuntimeState.ACTIVE,RuntimeState.LISTENING},
}


@dataclass(frozen=True)
class StateSnapshot:
    state:RuntimeState; sequence:int; reason:str


class RuntimeStateAuthority:
    """Canonical V1 user-facing state projection over factual runtime events."""
    def __init__(self,events,*,initial:RuntimeState=RuntimeState.IDLE):
        self.events=events;self._state=initial;self._sequence=0;self._lock=RLock();self._subscriptions=[];self._bind_compatibility_events()
    @property
    def state(self):
        with self._lock:return self._state
    def snapshot(self):
        with self._lock:return StateSnapshot(self._state,self._sequence,'current')
    def transition(self,target:RuntimeState|str,*,reason:str,force:bool=False,**context):
        normalized=normalize_runtime_state(target)
        with self._lock:
            current=self._state
            if normalized==current:return StateSnapshot(current,self._sequence,reason)
            if not force and normalized not in LEGAL_TRANSITIONS[current]:raise ValueError(f'illegal runtime state transition: {current.value} -> {normalized.value}')
            self._sequence+=1;self._state=normalized;sequence=self._sequence
        self.events.emit('runtime.state',state=normalized.value,previous_state=current.value,sequence=sequence,reason=str(reason),**context)
        return StateSnapshot(normalized,sequence,reason)
    def _compat(self,event):
        try:self.transition(normalize_runtime_state(event.get('state')),reason=f"legacy:{event.get('event','state')}")
        except ValueError:return
    def _safe_transition(self,target,reason,event):
        try:self.transition(target,reason=reason,request_id=event.get('request_id'))
        except ValueError:return
    def _bind_compatibility_events(self):
        self._subscriptions.append(self.events.subscribe('state',self._compat))
        mapping={
            'turn.started':(RuntimeState.UNDERSTANDING,'turn_started'),'turn.needs_approval':(RuntimeState.NEEDS_APPROVAL,'approval_required'),
            'turn.completed':(RuntimeState.RESPONDING,'turn_completed'),'turn.cancelled':(RuntimeState.IDLE,'owner_cancelled'),
            'turn.failed':(RuntimeState.ERROR,'turn_failed'),'approval.required':(RuntimeState.NEEDS_APPROVAL,'approval_required'),
            'approval.approved':(RuntimeState.TOOL_ACTION,'approval_approved'),'tool.unverified':(RuntimeState.WARNING,'verification_warning'),
            'automation.started':(RuntimeState.BACKGROUND,'background_started'),'workflow.started':(RuntimeState.BACKGROUND,'background_started'),
            'emergency_stop':(RuntimeState.ERROR,'emergency_stop'),'p10.emergency_stop':(RuntimeState.ERROR,'emergency_stop'),
        }
        for name,(target,reason) in mapping.items():self._subscriptions.append(self.events.subscribe(name,lambda event,t=target,r=reason:self._safe_transition(t,r,event)))
    def close(self):
        for unsubscribe in self._subscriptions:unsubscribe()
        self._subscriptions.clear()
