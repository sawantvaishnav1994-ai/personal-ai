from __future__ import annotations

import random
import time

from models.resilience import ModelObservability
from models.router import (
    InvalidModelResponse, ModelAuthenticationError, ModelCreditsExhausted, ModelError,
    ModelRateLimited, ModelRouter, ModelSpendLimitReached, ModelTimeout, ModelUnavailable,
)


ERROR_CLASS = {
    ModelAuthenticationError: 'authentication_error',
    ModelCreditsExhausted: 'configuration_error',
    ModelSpendLimitReached: 'configuration_error',
    ModelRateLimited: 'rate_limited',
    ModelTimeout: 'timeout',
    InvalidModelResponse: 'malformed_response',
    ModelUnavailable: 'provider_unavailable',
}
NON_RETRYABLE = {'authentication_error','configuration_error','unsupported_capability','invalid_request','context_limit','policy_denied','malformed_response','cancelled_request'}


class GovernedModelRouter(ModelRouter):
    """W8 extension of the existing router: health-aware, bounded and privacy governed."""

    def __init__(self, settings, *, events=None, audit=None):
        super().__init__(settings, events=events, audit=audit)
        self.observability = ModelObservability(self.providers)
        self.retry_attempts = max(0, min(3, int(getattr(settings, 'model_retry_attempts', 1))))
        self.retry_backoff = max(0.0, min(2.0, float(getattr(settings, 'model_retry_backoff_seconds', .05))))
        self.max_failovers = max(0, min(len(self.providers) - 1, int(getattr(settings, 'model_max_failovers', 3))))
        self.health_timeout = max(.5, min(10.0, float(self.health_timeout)))
        self.disabled = set(getattr(settings, 'model_disabled_providers', ()) or ())
        for pid, provider in self.providers.items():
            configured = bool(provider.configured and (provider.private or provider.api_key))
            self.observability.configured(pid, configured, pid in self.disabled)

    @staticmethod
    def _error_class(exc: ModelError) -> str:
        for kind, value in ERROR_CLASS.items():
            if isinstance(exc, kind): return value
        return 'unknown_failure'

    def _eligible(self, capability: str, sensitivity: str):
        raw = self._candidates(capability, sensitivity)
        eligible=[]
        for provider in raw:
            if provider.id in self.disabled:
                self.observability.counters['policy_blocked'] += 1
                continue
            if not provider.configured or (not provider.private and not provider.api_key):
                continue
            if not self.observability.allowed(provider.id):
                continue
            eligible.append(provider)
        return eligible

    def _run(self, capability: str, call, *, sensitivity: str = 'internal', conversation_id=None, task_id=None):
        generation_id=self.observability.generation_id(); started_at=time.time()
        candidates=self._eligible(capability,sensitivity)
        if not candidates:
            if self._candidates(capability,sensitivity):
                reason='eligible_provider_unavailable'
            else:
                reason='policy_or_capability_blocked'
                self.observability.counters['policy_blocked'] += 1
            self.observability.add_generation({'generation_id':generation_id,'conversation_id':conversation_id,'task_id':task_id,'capability':capability,'sensitivity':sensitivity,'routing_reason':reason,'started_at':started_at,'completed_at':time.time(),'result':'failed','error_code':'model_unavailable','retry_count':0,'failover_count':0,'attempted_targets':[]})
            raise ModelUnavailable('No healthy allowed model provider is available',provider=self.primary)
        attempted=[]; retries=0; failovers=0; last_error=None
        for provider_index,provider in enumerate(candidates[:self.max_failovers+1]):
            attempted.append(provider.id)
            if provider_index:
                failovers += 1
                self.observability.counters['failovers'] += 1
            for attempt in range(self.retry_attempts+1):
                try:
                    call_started=time.perf_counter(); result=call(provider); latency=round((time.perf_counter()-call_started)*1000,3)
                    transition=self.observability.success(provider.id,latency)
                    if transition:self._record('model.circuit_transition',provider=provider.id,state=transition)
                    if provider_index:
                        self._record('model.fallback',provider=provider.id,model=provider.model,capability=capability,reason='prior_target_failed')
                    self._record('model.selected',provider=provider.id,model=provider.model,capability=capability,fallback=provider_index>0,generation_id=generation_id)
                    self.observability.add_generation({'generation_id':generation_id,'conversation_id':conversation_id,'task_id':task_id,'provider':provider.id,'model':provider.model,'capability':capability,'sensitivity':sensitivity,'routing_reason':'primary' if provider_index==0 else 'failover','started_at':started_at,'completed_at':time.time(),'latency_ms':latency,'result':'success','retry_count':retries,'failover_count':failovers,'attempted_targets':attempted,'terminal_target':provider.id})
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

    def health_status(self, *, probe: bool = False) -> dict:
        if probe:
            for provider in self.providers.values():
                if provider.id in self.disabled or not provider.configured or (not provider.private and not provider.api_key): continue
                if not self.observability.allowed(provider.id): continue
                started=time.perf_counter()
                try:
                    self._request(provider,'GET','/models',timeout=self.health_timeout)
                    self.observability.success(provider.id,round((time.perf_counter()-started)*1000,3))
                except ModelError as exc:
                    error_class=self._error_class(exc)
                    self.observability.failure(provider.id,error_class,retryable=error_class not in NON_RETRYABLE)
        base=super().status(probe=False)
        base['w8']=self.observability.snapshot()
        return base

    def status(self, *, probe: bool = False) -> dict:
        return self.health_status(probe=probe)
