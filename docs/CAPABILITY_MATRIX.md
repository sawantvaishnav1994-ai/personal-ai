# Personal AI — Capability Matrix

Baseline date: 2026-09-15

Statuses distinguish automated software evidence from real-world Windows, physical-device, live-provider and production evidence.

| Capability | Status | Automated evidence | Remaining boundary | Exact SHA / next |
| --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | frozen design |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth; reused by W7.1-W7.6 | live operational proof partial | preserve authority |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit, cancellation, recovery, Emergency Stop | physical qualification pending | frozen |
| W7.2 Observation / Sensitive Evidence | AUTOMATED VALIDATED | 85 focused; 557 full | physical desktop/browser proof pending | `2a05e1da...` docs |
| W7.3 Allowlists / Data-Safety Policies | AUTOMATED VALIDATED | 45 focused; 602 full; implementation + docs 6/6 | physical policy qualification pending | `72408596...` docs |
| W7.4 Safe Browser Operator | AUTOMATED VALIDATED | 52 focused; 654 full; implementation + docs 6/6 | real-site/physical-browser proof pending | `745952cb...` docs |
| W7.5 Safe Desktop and File Operator | AUTOMATED VALIDATED | 55 focused; 709 full; implementation + docs 6/6 | real-world Windows/physical/production qualification pending | `acbbefea...` docs |
| W7.6 Verification and Recovery | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED | frozen W7 baseline contains completed recovery implementation/evidence | physical/production qualification separate | preserve frozen W7 |
| W8 Model Health / Failover / Observability | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE | implementation and documentation exact-head workflows 6/6 PASS | live-provider/local-model/physical/production qualification separate | implementation `42616b2e8faca9b16a5695ac319ea78200e7af74`; docs `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce` |
| P4 Everyday Personal Intelligence | IMPLEMENTED FOUNDATION / INTEGRATED / AUTOMATED VALIDATED FOR CURRENT TRANCHE | daily briefing now returns authoritative Second Brain context; full repo 972 PASS | live adapters, real reminder delivery, daily-use acceptance, proactive precision/recall | implementation `fc8f1aeb...` |
| P5 Second Brain / Life Graph | IMPLEMENTED FOUNDATION / INTEGRATED / AUTOMATED VALIDATED FOR CURRENT TRANCHE | read-through Second Brain→Life Graph linking, privacy filtering, relationships/supersession/deletion behavior tested | graph retrieval/media/long-term corpus quality; physical P3.5 | implementation `fc8f1aeb...` |
| P6 Autonomous Operations | IMPLEMENTED FOUNDATION / PARTIAL INTEGRATION | durable plans, P3 gate, consequential approval, restart persistence | direct governed delegation/qualification; real P3.4 production-like evidence | next unblocked integration candidate |
| P7 Multimodal Understanding | IMPLEMENTED FOUNDATION | normalized persistent source-attributed observation ledger | real sensors/device evidence; broader qualification | deterministic tests + physical later |
| P8 Personal AI Everywhere | IMPLEMENTED FOUNDATION / PARTIAL SURFACES | shared surface registry + continuity foundation | physical cross-device proof; watch/earbuds/car/home/AR are not complete surfaces | P3.6 physical later |
| P9 Hybrid Intelligence | AUTOMATED FOUNDATION; W8 RESILIENCE AUTOMATED VALIDATED | privacy/offline routing foundation plus W8 health/failover/observability | live provider and real local runtime unverified | owner/live qualification later |
| P10 Advanced Autonomous Intelligence | IMPLEMENTED FOUNDATION / FAIL-CLOSED ACTIVATION | persistent agents, allowlists, budgets, Emergency Stop, outcomes/self-evaluation | activation and deeper governed execution depend on P3 prerequisites | validate without bypassing P3 |
| Computer operator overall | AUTOMATED SCOPE CANDIDATE COMPLETE | W7.1-W7.6 automated authorities integrated | physical/production qualification remain | preserve frozen W7 |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 software gates green | real Google account qualification owner-deferred with paid isolated infrastructure | preserve blocker |
| Production durable storage | BLOCKED | fail-closed hosted guard exists | approved production volume absent | future production gate |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | physical protocol |
| W10 Signed Distribution | BLOCKED / QUALIFICATION | unsigned/dev package and simulator/instrumentation evidence exists | physical-device and signing credentials missing | readiness only until owner gates |
| W12 Release Readiness | PARTIAL | strong repository/automated evidence | live OAuth/provider/storage, physical devices, signing and production gates | no production promotion |

## Post-W8 P4/P5 implementation evidence

Branch: `p5/second-brain-life-graph-qualification-20260915`. Draft PR: #25. Base: frozen W8 documentation head `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`. Implementation: `fc8f1aeb5a8121f0faf911b6840b7ec15d48b609`.

The P4 repair replaces a swallowed call to nonexistent `SecondBrain.search()` with the authoritative `SecondBrain.context()` retrieval path, so daily briefing can actually include ranked owner memory. The P5 bridge is read-through rather than a second memory database: the existing Second Brain remains authoritative for storage, deletion, retention, supersession, sensitivity and evidence. Owner Life Graph inspection projects live memory nodes/relations/supersession and uses existing device scopes; secret/sensitive content fails closed unless authorized.

Full repository pytest at the implementation head: **972 passed, 0 failed, 8 warnings in 26.17s**. `pip check`, compileall, `pip-audit`, isolated encrypted backup/restore and 45-second soak passed. Exact implementation-head applicable workflows: CI #1060 / `34980195417`; Reliability and Security #245 / `34980195624`; Android Instrumentation #244 / `34980195358`; Package Validation #244 / `34980195728`; iOS Companion #226 / `34980195661` — **5/5 applicable workflows PASS**. P3 iPhone PWA is path-filtered N/A because no P3/PWA path changed; it is not counted as a pass. iOS remains simulator evidence only.

## W7.6 recovery contract

W7.6 composes W7.1 transaction authority, W7.2 evidence/observation discipline, W7.3 default-deny policy/temporary permits, W7.4 browser verification/no-blind-retry behavior, W7.5 desktop/file operator behavior, Trusted Action Core and Emergency Stop. It adds a shared durable verification/recovery layer rather than another execution authority.

Durable dispatch attempts are journaled with transaction/action/idempotency bindings, worker leases and fencing tokens. Verification records bind transaction, action, dispatch and idempotency identity and retain verifier identity/version, precondition, expected postcondition, observed postcondition, checksummed evidence references, timestamp/freshness, result and explanation. Unknown or stale evidence cannot become implicit success.

Consequential operations and application input are never blindly retried. Retry is fail-closed unless objective fresh evidence proves no effect and the operation class is eligible for fresh governance. Compensation is a separate action, cannot reuse the original action, must satisfy current W7.3 policy and one-use permit rules, enforces approval/reauthentication where required, and receives independent verification. Manual-recovery-only and irreversible compensation classes cannot be automated.

Recovery decisions are bound to transaction, owner, device, session, current security epoch and nonce; replay/stale-session decisions fail closed. Emergency Stop blocks new dispatch and compensation authorization. Recovery reporting redacts sensitive fields and uses digested evidence references where raw paths/names are unnecessary. Owner review is exposed under Settings → Activities rather than redesigning Home/AI Core.

## W8 model resilience contract

W8 extends the existing `ModelRouter` through `GovernedModelRouter`; it does not introduce a second provider stack or side-effect authority. Provider/model eligibility is decided by existing capability, sensitivity, local/external and owner-policy rules before health can influence routing. A local-only/sensitive request therefore cannot become externally eligible merely because a local provider is unhealthy.

Provider health is explicit (`UNKNOWN`, `HEALTHY`, `DEGRADED`, `UNHEALTHY`, `UNAVAILABLE`, `DISABLED`) with separate configuration, transport and capability dimensions. Circuit breakers implement `CLOSED → OPEN → HALF_OPEN → CLOSED` and `HALF_OPEN → OPEN`, with locked single-flight half-open admission to prevent recovery thundering herds. Retry and failover have separate bounded budgets; non-retryable authentication/configuration/policy/capability/invalid/malformed classes do not enter uncontrolled retry loops. Attempted targets are unique per candidate sequence, preventing recursive `A → B → A → B` fallback.

Observability retains only bounded safe metadata: generation identity, safe provider/model/capability/sensitivity/routing/result/error identifiers, timestamps/latency, retry/failover counts and attempted/terminal targets. Prompt/response bodies, passwords, API keys, bearer tokens, cookies, authorization headers, environment secrets, clipboard data and memory contents are not retained in generation records. Ordinary status does not probe providers; an owner-requested health probe is explicit, bounded and uses the existing read-only provider request path.

Implementation exact-head workflows at `42616b2e8faca9b16a5695ac319ea78200e7af74`: CI #1047 / `34967707625`; Reliability and Security #239 / `34967707659`; P3 iPhone PWA #199 / `34967707692`; Android Instrumentation #238 / `34967707628`; Package Validation #238 / `34967707632`; iOS Companion #220 / `34967707682` — **6/6 PASS**. Documentation exact-head workflows at `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`: CI #1055 / `34968483715`; Reliability and Security #243 / `34968483919`; P3 iPhone PWA #203 / `34968483669`; Android Instrumentation #242 / `34968483729`; Package Validation #242 / `34968483720`; iOS Companion #224 / `34968483967` — **6/6 PASS**. Schema remains **73**.

## Boundaries

Automated evidence is not live-provider verification, real-world local-model verification, physical-device verification, signed distribution or production verification. No production/Railway deployment, OAuth change, provider credential change, signing credential change or Home V1 redesign was performed by W8 or the post-W8 P4/P5 tranche.
