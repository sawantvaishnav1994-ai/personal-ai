# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-15

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | approved production volume absent | attach only at future approved production gate |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute physical protocol later |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | owner postponed paid isolated infrastructure | preserve checkpoint |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected | resume only after owner approval |
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | implementation/documentation gates complete | frozen |
| P1 | W7.2 | Observation/application context + sensitive evidence | RESOLVED FOR AUTOMATED SCOPE | automated gates complete | frozen; physical qualification separate |
| P1 | W7.3 | Allowlists and data-safety policies | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.4 | Safe Browser Operator | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.4 | Physical/real-site browser qualification | QUALIFICATION PENDING | automated evidence is not real-site/physical proof | later physical qualification |
| P1 | W7.5 | Safe Desktop and File Operator | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.5 | Real-world Windows desktop/file qualification | QUALIFICATION PENDING | Windows contracts and packaging are automated evidence only | later real-device Windows qualification |
| P1 | W7.6 | Verification and recovery | RESOLVED FOR AUTOMATED SCOPE | frozen W7 baseline includes completed recovery implementation/evidence | preserve frozen W7 |
| P1 | W8 | Model health/failover/observability | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | implementation `42616b2e...`; exact implementation workflows 6/6 | complete documentation exact-head 6/6; then inspect roadmap for next dependency-order milestone |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | future signing gate |
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, production/physical/signing gates remain | no production promotion yet |

## W8 resolved automated-scope capabilities

- first-class provider/model health with explicit `UNKNOWN`, `HEALTHY`, `DEGRADED`, `UNHEALTHY`, `UNAVAILABLE`, `DISABLED` states;
- separate configuration, transport and capability health dimensions;
- bounded privacy-safe explicit health probes using the existing provider request path;
- `GovernedModelRouter` extends the existing `ModelRouter`; no parallel provider stack or action authority;
- eligibility is determined before health-based selection, preserving local-only/sensitive fail-closed behavior;
- separate bounded retry and failover budgets, explicit retry taxonomy and unique attempted-target routing;
- circuit breaker `CLOSED/OPEN/HALF_OPEN` with locked half-open admission and recovery/reopen behavior;
- bounded safe generation metadata, provider health counters, latency percentiles, retry/failover/circuit/policy metrics;
- owner diagnostics under Settings without Home/AI Core redesign;
- schema remains **73**; no production/Railway/OAuth/iPhone infrastructure change.

## W8 exact implementation evidence

Baseline: `dad974fc1058678a07daae1702849178d2cf2dd2`.
Failed candidate: `1a9d379f8cdb372e583eb01dfd6373d307c18db8` — authoritative gate 4/6; reproduced pytest **978 passed, 7 failed, 8 warnings in 93.73s**. All seven failures were brittle source/string-inspection tests.
Final implementation: `42616b2e8faca9b16a5695ac319ea78200e7af74`.

Implementation workflows: CI #1047 / `34967707625`; Reliability/Security #239 / `34967707659`; P3 #199 / `34967707692`; Android #238 / `34967707628`; Package #238 / `34967707632`; iOS #220 / `34967707682` — **6/6 PASS**.

Reliability/Security passed dependency installation, pip-audit, compileall, full pytest, isolated encrypted backup/restore and 45-second soak. Package Validation passed Ubuntu/macOS/Windows. iOS evidence is simulator evidence only.

## Remaining W8 boundaries

Automated evidence is not live-provider verification, real-world local-model verification, physical-device verification or production verification. No paid-provider credential was introduced or exercised for qualification. Production/Railway remains unchanged.

Do not begin another milestone until the W8 documentation exact-head six-workflow gate is complete. After that gate, determine the next milestone from this matrix, the capability matrix and `docs/P4_P10_INTEGRATED_ROADMAP.md`; do not infer scope from a milestone number alone.
