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
| W7.6 Verification and Recovery | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | 778 full PASS, 8 warnings; shared implementation workflows 6/6 PASS | documentation exact-head 6/6; physical/production qualification separate | implementation `38eeae2f...` |
| W8 Model Health / Failover / Observability | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED | full repository exact-head PASS; implementation workflows 6/6 PASS | documentation exact-head 6/6; live-provider/local-model/production qualification separate | implementation `42616b2e8faca9b16a5695ac319ea78200e7af74` |
| Computer operator overall | AUTOMATED SCOPE CANDIDATE COMPLETE | W7.1-W7.6 automated authorities integrated | W7 completion audit + physical/production qualification remain | preserve frozen W7 |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 software gates green | real Google account qualification owner-deferred with paid isolated infrastructure | preserve blocker |
| Production durable storage | BLOCKED | fail-closed hosted guard exists | approved production volume absent | future production gate |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | physical protocol |

## W7.6 implementation evidence

- W7.5 documentation baseline: `acbbefea2ad6d46406ee05f9d2a44676503b3b59`.
- W7.6 implementation: `38eeae2fc7f609ebc7d3e8681833885b8d35310d`.
- Net implementation delta is exactly 11 files: `recovery/cross_operator.py`, `recovery/operator_recovery.py`, `recovery/recovery_authority.py`, `tests/test_w76_adversarial.py`, `tests/test_w76_hardening.py`, `tests/test_w76_recovery.py`, `tests/test_w76_release_gate.py`, `tools/builtins.py`, `tools/recovery.py`, `tools/registry.py`, `ui/settings_panel.py`.
- W7.6 extends the existing W7.1 operator transaction database additively to schema **73**. It does not create a parallel transaction authority and introduces no downgrade assumption.
- Full repository exact shared implementation-head result: **778 passed, 8 warnings**; `pip check` PASS; compileall PASS.
- Shared implementation workflows: CI #828 / `34932656123`; Reliability and Security #226 / `34932656078`; P3 iPhone PWA #186 / `34932656117`; Android #225 / `34932656134`; Package #225 / `34932656157`; iOS #207 / `34932656154` — **6/6 PASS**.
- Reliability/Security dependency audit, compile, full pytest, soak and isolated encrypted backup/restore qualification passed. Package Validation passed Ubuntu, macOS and Windows jobs. P3 passed integration and insecure-production-default fail-closed checks. iOS is simulator evidence, not physical-device evidence.

## W7.6 recovery contract

W7.6 composes W7.1 transaction authority, W7.2 evidence/observation discipline, W7.3 default-deny policy/temporary permits, W7.4 browser verification/no-blind-retry behavior, W7.5 desktop/file operator behavior, Trusted Action Core and Emergency Stop. It adds a shared durable verification/recovery layer rather than another execution authority.

Durable dispatch attempts are journaled with transaction/action/idempotency bindings, worker leases and fencing tokens. Verification records bind transaction, action, dispatch and idempotency identity and retain verifier identity/version, precondition, expected postcondition, observed postcondition, checksummed evidence references, timestamp/freshness, result and explanation. Unknown or stale evidence cannot become implicit success.

Consequential operations and application input are never blindly retried. Retry is fail-closed unless objective fresh evidence proves no effect and the operation class is eligible for fresh governance. Compensation is a separate action, cannot reuse the original action, must satisfy current W7.3 policy and one-use permit rules, enforces approval/reauthentication where required, and receives independent verification. Manual-recovery-only and irreversible compensation classes cannot be automated.

Recovery decisions are bound to transaction, owner, device, session, current security epoch and nonce; replay/stale-session decisions fail closed. Emergency Stop blocks new dispatch and compensation authorization. Recovery reporting redacts sensitive fields and uses digested evidence references where raw paths/names are unnecessary. Owner review is exposed under Settings → Activities rather than redesigning Home/AI Core.

## W8 model resilience contract

W8 extends the existing `ModelRouter` through `GovernedModelRouter`; it does not introduce a second provider stack or side-effect authority. Provider/model eligibility is decided by existing capability, sensitivity, local/external and owner-policy rules before health can influence routing. A local-only/sensitive request therefore cannot become externally eligible merely because a local provider is unhealthy.

Provider health is explicit (`UNKNOWN`, `HEALTHY`, `DEGRADED`, `UNHEALTHY`, `UNAVAILABLE`, `DISABLED`) with separate configuration, transport and capability dimensions. Circuit breakers implement `CLOSED → OPEN → HALF_OPEN → CLOSED` and `HALF_OPEN → OPEN`, with locked single-flight half-open admission to prevent recovery thundering herds. Retry and failover have separate bounded budgets; non-retryable authentication/configuration/policy/capability/invalid/malformed classes do not enter uncontrolled retry loops. Attempted targets are unique per candidate sequence, preventing recursive `A → B → A → B` fallback.

Observability retains only bounded safe metadata: generation identity, safe provider/model/capability/sensitivity/routing/result/error identifiers, timestamps/latency, retry/failover counts and attempted/terminal targets. Prompt/response bodies, passwords, API keys, bearer tokens, cookies, authorization headers, environment secrets, clipboard data and memory contents are not retained in generation records. Ordinary status does not probe providers; an owner-requested health probe is explicit, bounded and uses the existing read-only provider request path.

Implementation exact-head workflows at `42616b2e8faca9b16a5695ac319ea78200e7af74`: CI #1047 / `34967707625`; Reliability and Security #239 / `34967707659`; P3 iPhone PWA #199 / `34967707692`; Android Instrumentation #238 / `34967707628`; Package Validation #238 / `34967707632`; iOS Companion #220 / `34967707682` — **6/6 PASS**. Reliability completed dependency audit, compile, full pytest, encrypted backup/restore and 45-second soak. Schema remains **73**.

## Boundaries

W8 is repository/CI qualification. It does not establish live-provider verification, real-world local-model verification, physical-device verification or production verification. No production/Railway deployment, OAuth change, iPhone infrastructure change, provider credential change or Home V1 redesign was performed.
