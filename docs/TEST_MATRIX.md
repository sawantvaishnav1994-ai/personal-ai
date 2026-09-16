# Personal AI — Test Matrix

Baseline date: 2026-09-16

## Frozen validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.5 Safe Desktop / File Operator | `f794373c...` | 55 focused; 709 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | 778 full PASS, 8 warnings | frozen W7 automated evidence |
| W8 Model Health / Failover / Observability | `42616b2e8faca9b16a5695ac319ea78200e7af74` | 965 full PASS, 8 warnings | implementation + docs 6/6 PASS; frozen |
| Post-W8 P4/P5 Life Graph integration | `fc8f1aeb5a8121f0faf911b6840b7ec15d48b609` | 972 full PASS, 8 warnings | 5/5 applicable implementation + docs PASS; frozen |

## P4/P5 Retrieval Intelligence + Reminder/Follow-up Lifecycle

Starting evidence SHA: `4985dd014ec8c29c9f90c2dba8f153ea8a5bb969`.
Branch: `p4-p5/retrieval-reminder-qualification-20260915`.
Draft PR: #26.
Final implementation SHA: `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b`.

Focused qualification covered `tests/test_p5_retrieval_qualification.py`, `tests/test_p4_reminder_lifecycle.py`, `tests/test_p4_proactive_precision_recall.py`, and `tests/test_p4_reminder_tool_delegation.py`.

Result: **25 collected, 25 passed, 0 failed, 0 warnings in 0.96s**. The fixed proactive/forgotten-item benchmark achieved **precision 1.0; recall 1.0; false positives 0; false negatives 0**. Corpus qualification covered 100/1,000/5,000 memories and 5,000 scheduled reminders. Qualification latencies were approximately 3.943/18.603/90.067 ms for memory retrieval and 24.772 ms for 5,000-reminder evaluation. These are deterministic qualification measurements, not production SLAs.

CI exact-head full repository result: **997 passed, 0 failed, 8 warnings in 30.64s**. `pip check`, compileall, `pip-audit`, isolated encrypted backup/restore and 45-second soak passed.

Implementation exact-head workflows: CI #1065 / `34984377146`; Reliability and Security #247 / `34984377349`; P3 iPhone PWA #204 / `34984377120`; Android Instrumentation #246 / `34984377166`; Package Validation #246 / `34984377239`; iOS Companion #228 / `34984377173` — **6/6 PASS**.

## P6 Governed Delegation Integration

Starting evidence SHA: `2a631346b0013adca810da32ed0e7519eca15240`.
Branch: `p6/governed-delegation-integration-20260915`.
Draft PR: #27.
Final implementation SHA: `e674ee80b66ba6c6dbe734ef1825df6a56c19d3f`.

Focused qualification: **44 collected, 44 passed, 0 failed**. Full repository CI: **1041 passed, 0 failed, 8 warnings in 41.03s**. Reliability independently ran **1041 passed, 8 warnings in 35.63s**, `pip-audit` with no known vulnerabilities, encrypted backup/restore plus 11 isolated recovery tests, and a 45-second soak with SQLite integrity `ok`.

P6 qualification verifies security-epoch binding, owner/device/session binding, existing approval/replay/Emergency Stop composition, truthful cancellation/uncertainty semantics, zero orchestration retries, restart recovery/idempotency, consequential serialization, nested-secret rejection, allowlists/policies/budgets, P4/P5 context handoff without authorization transfer, safe owner inspection and deterministic success/denial/recovery flows.

Implementation exact-head workflows: CI #1071 / `34996184188`; Reliability and Security #249 / `34996184334`; P3 iPhone PWA #206 / `34996184148`; Android Instrumentation #248 / `34996184426`; Package Validation #248 / `34996184213`; iOS Companion #230 / `34996184151` — **6/6 PASS**.

## P7 Multimodal World Understanding — Final Implementation Qualification

P7 start base: `0d2203aa78bfe7dc935ea42887c7ba9cf1e94427`.
Branch: `p7/multimodal-world-understanding-qualification-20260915`.
Draft PR: #28.
Final implementation SHA: `c0498146a0753b24da611e392181970b227a63d4`.

### Defect closure regression qualification

The final focused suite covers the original four findings and the requested surrounding adversarial cases:

- sensor rejection classification: positive Infinity, negative Infinity, NaN, malformed sensor value, invalid unit and out-of-contract value all fail closed and audit as `invalid_sensor_value` without raw rejected payload;
- recursive secret rejection: normalized `credential`, `credentials`, password/passwd/secret/token/access-token/refresh-token/API-key/authorization/cookie/private-key equivalents, nested maps/lists and case variants reject before persistence; tested marker is absent from exception text, database bytes, Activities/event payload, audit payload and bounded governed context;
- lineage/retention: RAW→DERIVED and RAW→EXTRACTED→INTERPRETED→DERIVED, siblings, multiple levels, multi-parent descendants, parent/ancestor expiration and deletion, restart, duplicate expiry/deletion, bounded query, owner inspection and governed action context all fail closed for lineage-invalid descendants while tombstoned provenance/audit state remains retained;
- P7→P6 boundary: legitimate governed context reaches P6 orchestration, but authorization remains false, approval/execution/verification/recovery/Emergency Stop remain P6/W7-controlled, and public projections do not expose `approval_id` or other internal consequential identifiers.

Focused exact-head result: **44 passed, 0 failed, 9 warnings in 7.21s**.

### Security and adversarial coverage

Qualification includes nested secrets, unsafe references, NaN/±Infinity, malformed sensor values, abusive timestamps, privacy-before-persistence, provenance/lineage spoofing controls, trusted owner API authorization, P3 trusted/untrusted device behavior, P7→P6 authority-boundary behavior and Emergency Stop preservation. No security test was weakened to obtain a pass.

`pip-audit -r requirements.txt` — **PASS: No known vulnerabilities found**.
Compileall — **PASS**.
`pip check` — **PASS: No broken requirements found**.

### Deterministic E2E coverage

A. simulated observation → validation/privacy → persistence → bounded retrieval → owner inspection — PASS.

B. RAW → EXTRACTED → INTERPRETED → DERIVED — PASS.

C. duplicate → restart → duplicate → one logical observation — PASS.

D. concurrent duplicate delivery → deterministic result — PASS.

E. secret-bearing payload → reject → categorical payload-free audit — PASS.

F. fresh → stale → expired → correct context behavior — PASS.

G. source expiration/deletion → descendants unusable as fresh governed context — PASS.

H. P3 trusted/untrusted device behavior — PASS.

I. P7 context → P6 → existing authorization still required — PASS.

J. Emergency Stop → consequential action remains blocked despite P7 context — PASS.

### Performance qualification

At 100 / 600 / 1,800 observations:

| Volume | Ingest | Restart | Bounded query | Duplicate | DB bytes | Python history loaded |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.117669 s | 0.000501 s | 0.000601 s | 0.000383 s | 229,376 | 0 |
| 600 | 0.535670 s | 0.000751 s | 0.001261 s | 0.000376 s | 1,085,440 | 0 |
| 1,800 | 1.585818 s | 0.001379 s | 0.001638 s | 0.000391 s | 3,129,344 | 0 |

Extended measurements: provenance lookup **0.001021 s**; concurrent ingestion of 64 unique observations **0.072918 s**; descendant delete cascade **0.001240 s**; expiration of 40 source/descendant observations **0.003209 s**; measured startup state `loaded_observations_in_memory = 0`.

The measurements verify that P7 did not restore the old whole-ledger Python startup materialization. They are qualification measurements, not production SLAs.

### Backup / restore

Encrypted backup/restore plus isolated recovery qualification: **12 passed in 0.38s**. Representative P7 state preserves observation/source-event IDs, idempotency, provenance, lineage, privacy, retention, deletion and expiration semantics. The final case explicitly restores an expired RAW source plus a longer-retained child and verifies neither reactivates and lineage-invalid context remains unavailable.

### Final candidate soak

45-second P7-inclusive soak:

- iterations: **6,610**
- SQLite integrity: **ok**
- P7 SQLite integrity: **ok**
- pending device requests: **0**
- P7 events: **331**
- P7 observations: **465**
- P7 database bytes: **1,130,496**
- P7 historical observations loaded in Python: **0**
- RSS start: **46,886,912**
- RSS peak: **128,077,824**
- RSS end: **128,110,592**
- RSS growth: **81,223,680 bytes**

The process-wide RSS increase remains an observation, not proof of either a leak or harmless allocator/cache retention. P7-specific bounded-state evidence establishes that historical observations are not materialized as an unbounded Python ledger.

### Full repository gate

Exact-head direct CI full repository: **1085 passed, 0 failed, 15 warnings in 38.77s**.
Reliability/Security independent full repository: **1085 passed, 0 failed, 15 warnings in 40.46s**.

### Implementation exact-head workflows

| Workflow | Run | Run ID | Head SHA | Result |
| --- | ---: | ---: | --- | --- |
| CI | #1140 | `35042584877` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |
| Reliability and Security | #273 | `35042584893` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |
| P3 iPhone PWA | #225 | `35042584920` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |
| Android Instrumentation | #272 | `35042584924` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |
| Package Validation | #272 | `35042584939` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |
| iOS Companion | #254 | `35042584896` | `c0498146a0753b24da611e392181970b227a63d4` | PASS |

Implementation gate: **6/6 PASS**. PR workflows validate GitHub's PR merge ref against the unchanged P7 base while their workflow-run head SHA is the frozen implementation SHA; direct push CI independently checked out the implementation SHA itself.

Cumulative implementation/test diff from P7 start base: **18 commits, 9 files, +2,387 / -30**. No P6 runtime files changed and no P8/P9/P10 implementation, deployment, OAuth, production credential, signing or new authority was introduced.

### Evidence boundary

REAL_CAMERA_VERIFIED = NO
REAL_MICROPHONE_VERIFIED = NO
REAL_LOCATION_VERIFIED = NO
REAL_WEARABLE_VERIFIED = NO
PHYSICAL_MULTIMODAL_VERIFIED = NO
LIVE_SERVICE_VERIFIED = NO
PRODUCTION_VERIFIED = NO

The documentation/evidence exact-head workflow gate remains required before P7 may be classified repository-automated evidence complete.
