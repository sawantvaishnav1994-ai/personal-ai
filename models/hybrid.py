from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from models.router import ModelUnavailable, Provider


class PrivacyMode(str, Enum):
    LOCAL_ONLY = 'local_only'
    LOCAL_PREFERRED = 'local_preferred'
    EXTERNAL_ALLOWED = 'external_allowed'


@dataclass(frozen=True)
class HybridRequest:
    capability: str = 'chat'
    sensitivity: str = 'internal'
    privacy: PrivacyMode = PrivacyMode.LOCAL_PREFERRED
    allowed_providers: tuple[str, ...] = ()
    blocked_providers: tuple[str, ...] = ()
    required_context_tokens: int = 0
    owner_id: str | None = None
    device_trusted: bool = True
    session_fresh: bool = True
    emergency_stop: bool = False
    consequential: bool = False


@dataclass(frozen=True)
class SafeContext:
    memory: tuple[str, ...] = ()
    knowledge: tuple[str, ...] = ()
    world: tuple[str, ...] = ()
    references: tuple[str, ...] = ()

    @classmethod
    def bounded(
        cls,
        *,
        memory: Iterable[str] = (),
        knowledge: Iterable[str] = (),
        world: Iterable[str] = (),
        references: Iterable[str] = (),
        per_source_limit: int = 8,
        item_limit: int = 2000,
    ) -> 'SafeContext':
        def clean(values: Iterable[str]) -> tuple[str, ...]:
            result = []
            for value in values:
                text = str(value).strip()
                if text:
                    result.append(text[:item_limit])
                if len(result) >= per_source_limit:
                    break
            return tuple(result)
        return cls(clean(memory), clean(knowledge), clean(world), clean(references))

    def external_projection(self) -> 'SafeContext':
        # External providers receive only explicit safe references/derived world context.
        return SafeContext(world=self.world, references=self.references)


class HybridPolicy:
    """P9 policy layer. It filters intelligence resources; it never grants action authority."""

    LOCAL_PROVIDER = 'self_hosted'

    @staticmethod
    def validate_request(request: HybridRequest) -> None:
        if not request.device_trusted:
            raise ModelUnavailable('AI access denied for untrusted/revoked device')
        if not request.session_fresh:
            raise ModelUnavailable('AI access denied for stale session')
        if request.consequential and request.emergency_stop:
            raise ModelUnavailable('Consequential AI request blocked by Emergency Stop')

    @classmethod
    def filter_candidates(cls, request: HybridRequest, providers: Iterable[Provider]) -> list[Provider]:
        cls.validate_request(request)
        allowed = set(request.allowed_providers)
        blocked = set(request.blocked_providers)
        result: list[Provider] = []
        for provider in providers:
            if provider.id in blocked:
                continue
            if allowed and provider.id not in allowed:
                continue
            if request.capability not in provider.capabilities:
                continue
            is_local = provider.id == cls.LOCAL_PROVIDER or provider.private
            if request.privacy == PrivacyMode.LOCAL_ONLY and not is_local:
                continue
            if request.sensitivity in {'sensitive', 'secret'} and not is_local:
                continue
            result.append(provider)
        if request.privacy == PrivacyMode.LOCAL_PREFERRED:
            result.sort(key=lambda provider: (not (provider.id == cls.LOCAL_PROVIDER or provider.private), provider.cost_rank, provider.latency_rank, provider.id))
        return result

    @staticmethod
    def context_for_provider(context: SafeContext, provider: Provider) -> SafeContext:
        return context if provider.private else context.external_projection()

    @staticmethod
    def model_output_has_authority(_: object) -> bool:
        # Deliberately immutable invariant: model output is untrusted computational output.
        return False
