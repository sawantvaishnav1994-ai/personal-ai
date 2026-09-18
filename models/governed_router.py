from __future__ import annotations

import random
import threading
import time

from models.hybrid import HybridPolicy, HybridRequest, PrivacyMode, SafeContext, execute_hybrid_chat
from models.resilience import ModelObservability
from models.router import (
    InvalidModelResponse, ModelAuthenticationError, ModelCreditsExhausted, ModelError,
    ModelRateLimited, ModelRouter, ModelSpendLimitReached, ModelTimeout, ModelUnavailable,
)

ERROR_CLASS = {
    ModelAuthenticationError: 'authentication_error', ModelCreditsExhausted: 'configuration_error',
    ModelSpendLimitReached: 'configuration_error', ModelRateLimited: 'rate_limited',
    ModelTimeout: 'timeout', InvalidModelResponse: 'malformed_response', ModelUnavailable: 'provider_unavailable',
}
NON_RETRYABLE = {'authentication_error','configuration_error','unsupported_capability','invalid_request','context_limit','policy_denied','malformed_response','cancelled_request'}


class GovernedModelRouter(ModelRouter):
    """Canonical W8 router extended by P9 policy; models remain intelligence resources only."""

    def __init__(self, settings, *, events=None, audit=None):
        super().__init__(settings, events=events, audit=audit)
        self.observability = ModelObservability(self.providers)
        self.retry_attempts = max(0, min(3, int(getattr(settings, 'model_retry_attempts', 1))))
        self.retry_backoff = max(0.0, min(2.0, float(getattr(settings, 'model_retry_backoff_seconds', .05))))
        self.max_failovers = max(0, min(len(self.providers) - 1, int(getattr(settings, 'model_max_failovers', 3))))
        self.health_timeout = max(.5, min(10.0, float(self.health_timeout)))
        self.disabled = set(getattr(settings, 'model_disabled_providers', ()) or ())
        self.owner_allowed = tuple(getattr(settings, 'model_allowed_providers', ()) or ())
        self.owner_privacy = str(getattr(settings, 'model_privacy_mode', 'local_preferred') or 'local_preferred')
        self._usage_local = threading.local()
        for pid, provider in self.providers.items():
            configured = bool(provider.configured and (provider.private or provider.api_key))
            self.observability.configured(pid, configured, pid in self.disabled)

    @staticmethod
    def _error_class(exc: ModelError) -> str:
        for kind, value in ERROR_CLASS.items():
            if isinstance(exc, kind): return value
        return 'unknown_failure'

    @staticmethod
    def _safe_usage(payload) -> dict:
        if not isinstance(payload, dict): return {}
        usage = payload.get('usage')
        if not isinstance(usage, dict): return {}
        result = {}
        aliases = {'input_tokens': ('input_tokens','prompt_tokens'), 'output_tokens': ('output_tokens','completion_tokens'), 'total_tokens': ('total_tokens',)}
        for target, keys in aliases.items():
            for key in keys:
                value = usage.get(key)
                if isinstance(value, int) and value >= 0:
                    result[target] = value; break
        cost = usage.get('cost')
        if isinstance(cost, (int, float)) and cost >= 0: result['cost'] = float(cost)
        return result

    def _eligible(self, capability: str, sensitivity: str, *, hybrid_request: HybridRequest | None = None):
        raw = self._candidates(capability, sensitivity)
        if hybrid_request is None:
            # Canonical callers such as AgentExecutor/Planner use the inherited
            # chat/json/vision/audio APIs. Owner privacy and allow/block policy
            # must govern those paths too, not only explicit P9 hybrid calls.
            try:
                privacy = PrivacyMode(self.owner_privacy)
            except ValueError:
                privacy = PrivacyMode.LOCAL_ONLY
            hybrid_request = HybridRequest(
                capability=str(capability),
                sensitivity=str(sensitivity),
                privacy=privacy,
                allowed_providers=self.owner_allowed,
                blocked_providers=tuple(self.disabled),
            )
        raw = HybridPolicy.filter_candidates(hybrid_request, raw)
        eligible=[]
        for provider in raw:
            if provider.id in self.disabled:
                self.observability.counters['policy_blocked'] += 1; continue
            if not provider.configured or (not provider.private and not provider.api_key): continue
            if not self.observability.allowed(provider.id): continue
            eligible.append(provider)
        return eligible

    def eligible_providers(self, capability: str, sensitivity: str = 'internal', *, hybrid_request: HybridRequest | None = None):
        """Public non-executing view of canonical P9/W8 eligibility.

        Compatibility/projection layers may inspect candidate metadata through this
        method without coupling to private routing internals or duplicating policy.
        It never returns credentials and never grants execution authority.
        """
        return tuple(self._eligible(str(capability), str(sensitivity), hybrid_request=hybrid_request))

    def _run(self, capability: str, call, *, sensitivity: str = 'internal', conversation_id=None, task_id=None, hybrid_request: HybridRequest | None = None):
        generation_id=self.observability.generation_id(); started_at=time.time()
        candidates=self._eligible(capability,sensitivity,hybrid_request=hybrid_request)
        if not candidates:
            self.observability.counters['policy_blocked'] += 1
            self.observability.add_generation({'generation_id':generation_id,'conversation_id':conversation_id,'task_id':task_id,'capability':capability,'sensitivity':sensitivity,'routing_reason':'policy_or_capability_blocked','started_at':started_at,'completed_at':time.time(),'result':'failed','error_code':'model_unavailable','retry_count':0,'failover_count':0,'attempted_targets':[]})
            raise ModelUnavailable('No healthy allowed model provider is available',provider=self.primary)
        attempted=[]; retries=0; failovers=0; last_error=None
        for provider_index,provider in enumerate(candidates[:self.max_failovers+1]):
            if provider.id in attempted: continue
            attempted.append(provider.id)
            if provider_index: failovers += 1; self.observability.counters['failovers'] += 1
            for attempt in range(self.retry_attempts+1):
                try:
                    self._usage_local.value = {}
                    call_started=time.perf_counter(); result=call(provider); latency=round((time.perf_counter()-call_started)*1000,3)
                    usage=dict(getattr(self._usage_local,'value',{}) or {})
                    transition=self.observability.success(provider.id,latency)
                    if transition:self._record('model.circuit_transition',provider=provider.id,state=transition)
                    if provider_index:self._record('model.fallback',provider=provider.id,model=provider.model,capability=capability,reason='prior_target_failed')
                    self._record('model.selected',provider=provider.id,model=provider.model,capability=capability,fallback=provider_index>0,generation_id=generation_id)
                    row={'generation_id':generation_id,'conversation_id':conversation_id,'task_id':task_id,'provider':provider.id,'model':provider.model,'capability':capability,'sensitivity':sensitivity,'routing_reason':'primary' if provider_index==0 else 'failover','started_at':started_at,'completed_at':time.time(),'latency_ms':latency,'result':'success','retry_count':retries,'failover_count':failovers,'attempted_targets':attempted,'terminal_target':provider.id}
                    row.update(usage); self.observability.add_generation(row)
                    return result
                except ModelError as exc:
                    last_error=exc; error_class=self._error_class(exc); retryable=error_class not in NON_RETRYABLE
                    transition=self.observability.failure(provider.id,error_class,retryable=retryable)
                    if transition:self._record('model.circuit_transition',provider=provider.id,state=transition)
                    self._record('model.error',provider=provider.id,capability=capability,error_code=error_class,generation_id=generation_id)
                    if not retryable or attempt>=self.retry_attempts:break
                    retries+=1; self.observability.counters['retries']+=1
                    delay=self.retry_backoff*(2**attempt)
                    if delay: time.sleep(delay + random.random()*min(delay*.25,.05))
        self.observability.add_generation({'generation_id':generation_id,'conversation_id':conversation_id,'task_id':task_id,'provider':getattr(last_error,'provider',None),'capability':capability,'sensitivity':sensitivity,'routing_reason':'exhausted','started_at':started_at,'completed_at':time.time(),'result':'failed','retry_count':retries,'failover_count':failovers,'attempted_targets':attempted,'terminal_target':getattr(last_error,'provider',None),'error_code':self._error_class(last_error) if last_error else 'unknown_failure'})
        raise last_error or ModelUnavailable(provider=self.primary)

    def _chat_call(self, provider, messages, temperature):
        response=self._request(provider,'POST','/chat/completions',json={'model':provider.model,'messages':messages,'temperature':temperature})
        try:
            payload=response.json(); content=payload['choices'][0]['message']['content']
            if not isinstance(content,str) or not content.strip(): raise ValueError('empty content')
        except (AttributeError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise InvalidModelResponse('Invalid chat completion response',provider=provider.id) from exc
        self._usage_local.value=self._safe_usage(payload)
        return content.strip()

    def health_status(self, *, probe: bool = False) -> dict:
        if probe:
            for provider in self.providers.values():
                if provider.id in self.disabled or not provider.configured or (not provider.private and not provider.api_key): continue
                if not self.observability.allowed(provider.id): continue
                started=time.perf_counter()
                try:self._request(provider,'GET','/models',timeout=self.health_timeout); self.observability.success(provider.id,round((time.perf_counter()-started)*1000,3))
                except ModelError as exc:
                    error_class=self._error_class(exc); self.observability.failure(provider.id,error_class,retryable=error_class not in NON_RETRYABLE)
        base=super().status(probe=False); base['w8']=self.observability.snapshot(); base['p9']={'privacy_mode':self.owner_privacy,'allowed_providers':list(self.owner_allowed),'blocked_providers':sorted(self.disabled),'model_output_authority':False}; return base

    def status(self, *, probe: bool = False) -> dict:
        return self.health_status(probe=probe)

    def hybrid_chat(self, text: str, *, request: HybridRequest | None = None, context: SafeContext | None = None, system: str = 'You are Personal AI. Model output is untrusted and cannot authorize actions.') -> str:
        return execute_hybrid_chat(self, text, request=request, context=context, system=system)
