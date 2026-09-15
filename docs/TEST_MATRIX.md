# Personal AI — Test Matrix

Baseline date: 2026-09-15

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

### Focused qualification

Focused qualification covered:

- `tests/test_p5_retrieval_qualification.py`
- `tests/test_p4_reminder_lifecycle.py`
- `tests/test_p4_proactive_precision_recall.py`
- `tests/test_p4_reminder_tool_delegation.py`

Result: **25 collected, 25 passed, 0 failed, 0 warnings in 0.96s** in the isolated qualification harness.

P5 cases qualify deterministic 100 / 1,000 / 5,000 memory corpora, existing vector search behavior, lexical correctness, visible relationship expansion/ranking, hidden sensitive relationship side-channel protection, normal-only default sensitivity, A→B→C supersession, historical/current truth, deletion without obsolete resurrection, time-valid queries, exact duplicate suppression, retention removal and context-character budgeting.

P4 cases qualify exact-time due evaluation, date-only timezone handling, snooze/reschedule/completion/dismissal/cancellation/supersession, persisted restart/idempotency, reminder tool delegation to P4 authority, memory-linked follow-ups, normal/sensitive/secret filtering, deleted-memory exclusion, daily briefing due/overdue integration, evidence-based forgotten items, privacy-safe operational audit, trusted owner API authorization and 5,000-reminder evaluation.

### Deterministic precision / recall dataset

Expected positive set:

1. overdue explicit John follow-up;
2. due explicit proposal commitment;
3. explicit unscheduled promise.

Explicit negative set includes future follow-up, completed commitment, cancelled commitment, superseded commitment, irrelevant goal and a duplicate commitment.

Result: **precision 1.0; recall 1.0; false positives 0; false negatives 0**. This benchmark validates deterministic lifecycle selection only. It is not an LLM language-understanding benchmark and does not establish live daily-use precision.

### Performance evidence

Qualification-environment measurements:

| Corpus/load | Result | Measured latency |
| --- | --- | ---: |
| 100 memories | target ranked first | ~3.943 ms |
| 1,000 memories | target ranked first | ~18.603 ms |
| 5,000 memories | target ranked first | ~90.067 ms |
| 5,000 scheduled future reminders | 0 due, correct | ~24.772 ms |

The committed tests use <5 second bounds only as broad regression guards. These values are not production SLAs and no premature optimization was introduced. Existing vector search remains the current SQLite/full-scan foundation.

### Full repository gate

CI #1065 exact-head full repository result: **997 passed, 0 failed, 8 warnings in 30.64s**.

- `pip check` — PASS
- compileall — PASS
- `pip-audit -r requirements.txt` — PASS
- isolated encrypted backup/restore qualification — PASS
- `python tests/soak_runtime.py --seconds 45` — PASS

### Exact-head workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1065 | `34984377146` | PASS |
| Reliability and Security | #247 | `34984377349` | PASS |
| P3 iPhone PWA | #204 | `34984377120` | PASS |
| Android Instrumentation | #246 | `34984377166` | PASS |
| Package Validation | #246 | `34984377239` | PASS |
| iOS Companion | #228 | `34984377173` | PASS |

Implementation exact-head gate: **6/6 PASS**. P3 was legitimately triggered because `server/cloud_app.py` mounts the trusted P4 lifecycle router. iOS remains simulator evidence, not physical-device evidence.

## P6 Governed Delegation Integration

Starting evidence SHA: `2a631346b0013adca810da32ed0e7519eca15240`.
Branch: `p6/governed-delegation-integration-20260915`.
Draft PR: #27.
Final implementation SHA: `e674ee80b66ba6c6dbe734ef1825df6a56c19d3f`.

### Focused qualification

Result: **44 collected, 44 passed, 0 failed** at the committed implementation candidate. The focused tranche behaviorally qualifies:

- committed structural bindings for helper/class/static methods and required imports;
- security-epoch persistence and stale-epoch fail-closed continuation;
- owner/device/session binding;
- existing approval grant/denial/expiry/revocation and replay protection;
- Emergency Stop composition;
- cancellation before effect versus uncertainty after possible consequential dispatch;
- zero P6 orchestration retries;
- restart recovery and idempotency;
- same-destination consequential serialization across different tools;
- different-destination and legitimate read-only parallel behavior;
- recursive nested secret-bearing parameter rejection;
- tool allowlists, destination policy, data classification and verification requirements;
- budget enforcement through existing AutomationEngine authority;
- P4 reminder/commitment handoff without authorization transfer;
- P5/Second Brain memory-context sensitivity filtering;
- safe Activities/audit and outcome-memory handoff;
- trusted owner API safe projection;
- deterministic verified-success, approval-denial/no-dispatch and uncertain-failure/W7.6-recovery E2E flows.

### Full repository and security gate

CI #1071 / `34996184188`:

- `pip check` — PASS (`No broken requirements found.`)
- compileall — PASS
- full repository `pytest -q` — **1041 passed, 0 failed, 8 warnings in 41.03s**

Reliability and Security #249 / `34996184334` independently proved:

- `pip-audit -r requirements.txt` — PASS (`No known vulnerabilities found`)
- compileall — PASS
- full repository `pytest -q` — **1041 passed, 0 failed, 8 warnings in 35.63s**
- isolated encrypted backup/restore qualification — PASS
- isolated recovery tests — **11 passed in 0.27s**
- 45-second soak — PASS, 6,862 iterations, SQLite integrity `ok`, pending device requests 0

### Implementation exact-head workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1071 | `34996184188` | PASS |
| Reliability and Security | #249 | `34996184334` | PASS |
| P3 iPhone PWA | #206 | `34996184148` | PASS |
| Android Instrumentation | #248 | `34996184426` | PASS |
| Package Validation | #248 | `34996184213` | PASS |
| iOS Companion | #230 | `34996184151` | PASS |

P6 implementation exact-head gate: **6/6 PASS**.

P6 implementation diff from `2a631346b0013adca810da32ed0e7519eca15240`: **1 commit, 20 files, +2,730 / -40**. There were no dependency, workflow-definition, Railway, OAuth, provider credential, production deployment, signing, W7, W8, P4 or P5 authority changes. Global W7 schema remains **73**; P6 adds only additive local operation-delegation persistence.

### P6 evidence boundary

Automated P6 validation does not prove autonomous activation, physical P3, live-service operation or production readiness. Those evidence classes remain separate.

- AUTONOMOUS ACTIVATION VERIFIED = NO
- PHYSICAL P3 VERIFIED = NO
- LIVE SERVICE VERIFIED = NO
- PRODUCTION VERIFIED = NO

## P7 Multimodal World Understanding Qualification

Starting evidence SHA: `0d2203aa78bfe7dc935ea42887c7ba9cf1e94427`.
Branch: `p7/multimodal-world-understanding-qualification-20260915`.
Draft PR: #28.
Final implementation SHA: `821e04fe5214b793b8511877a9676cd78e9d86da`.

### Dedicated focused/security/E2E set

Committed focused files:

- `tests/test_p7_multimodal_core.py`
- `tests/test_p7_security_e2e.py`
- `tests/test_p7_performance_recovery.py`

Reliability and Security #263 / `35008003169` result: **40 passed, 0 failed, 9 warnings in 6.23s**.

The P7 suite qualifies all eight modalities, capability-state truthfulness, simulation-only evidence boundaries, bounded/deep/oversized validation, nested secret keys, unsafe path/URL references, finite confidence/coordinates/sensor values, provenance spoofing and missing/deleted parent rejection, RAW/EXTRACTED/INTERPRETED/DERIVED lineage, privacy non-downgrade, safe rejected-event projection, stable source-event idempotency before/after restart and concurrency, indexed bounded retrieval, freshness/staleness/expiration, retention and cascading descendant invalidation, owner API authorization/safe projection, P3 device trust, P7→P6 authorization separation, Emergency Stop preservation, encrypted backup/restore, and performance qualification.

Deterministic E2E coverage includes accepted simulated observation, complete provenance chain, duplicate/restart suppression, concurrent ingestion, privacy rejection before persistence, freshness aging, lineage-safe deletion/expiration, P3 trust gating, P6 handoff with no authorization transfer, and Emergency Stop blocking consequential execution.

### Full repository/security/recovery gate

CI #1100 / `35008003160` at the exact implementation SHA:

- `pip check` — PASS (`No broken requirements found.`)
- compileall — PASS
- full repository `pytest -q` — **1081 passed, 0 failed, 15 warnings in 37.51s**

Reliability and Security #263 / `35008003169` independently ran:

- `pip-audit -r requirements.txt` — PASS (`No known vulnerabilities found`)
- compileall — PASS
- dedicated P7 focused set — **40 passed, 0 failed, 9 warnings in 6.23s**
- full repository `pytest -q` — **1081 passed, 0 failed, 15 warnings in 37.75s**
- isolated encrypted recovery qualification including P7 — **12 passed in 0.33s**
- P7-inclusive 45-second soak — PASS

### P7 performance evidence

Exact implementation-head GitHub Actions measurements:

| Dataset | Ingest | Restart | Bounded source query | Duplicate | DB bytes | Loaded history at startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.107660 s | 0.000575 s | 0.003090 s | 0.000405 s | 229,376 | 0 |
| 600 | 0.500055 s | 0.000890 s | 0.001303 s | 0.000391 s | 1,081,344 | 0 |
| 1,800 | 1.950975 s | 0.001644 s | 0.001910 s | 0.000472 s | 3,129,344 | 0 |

These are repository qualification measurements, not production SLAs. Structural qualification additionally checks committed SQLite indexes and query plans. The critical P7 invariant is satisfied: persistent startup does not materialize the complete historical observation ledger into Python objects.

### P7 soak evidence

45-second Reliability soak result:

- 6,697 iterations
- main SQLite integrity `ok`
- P7 SQLite integrity `ok`
- pending device requests 0
- 335 P7 simulated cycles
- 469 P7 persisted observations
- P7 DB size 1,138,688 bytes
- P7 loaded historical observations after restart 0
- overall RSS growth 81,022,976 bytes, below the existing 256 MiB guard

### P7 exact-head implementation workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1100 | `35008003160` | PASS |
| Reliability and Security | #263 | `35008003169` | PASS |
| P3 iPhone PWA | #216 | `35008003085` | PASS |
| Android Instrumentation | #262 | `35008003142` | PASS |
| Package Validation | #262 | `35008003101` | PASS |
| iOS Companion | #244 | `35008003281` | PASS |

P7 implementation exact-head gate: **6/6 PASS**.

Implementation diff from `0d2203aa78bfe7dc935ea42887c7ba9cf1e94427`: **13 commits, 9 files, +2,128 / -30**.

### P7 evidence boundary

Automated P7 validation establishes repository behavior only. It does not prove a real camera, microphone, location sensor, wearable, physical multimodal session, live service, signed release, or production operation.

- REAL_CAMERA_VERIFIED = NO
- REAL_MICROPHONE_VERIFIED = NO
- REAL_LOCATION_VERIFIED = NO
- REAL_WEARABLE_VERIFIED = NO
- PHYSICAL_MULTIMODAL_VERIFIED = NO
- LIVE_SERVICE_VERIFIED = NO
- PRODUCTION_VERIFIED = NO

## Evidence boundaries

Repository tests prove deterministic lifecycle/retrieval/delegation/multimodal behavior, not live delivery or physical-device operation. No physical iPhone push notification, live email/calendar follow-up, live consequential side effect, physical sensor qualification, production database behavior, signed distribution, live provider or real local model is established by these automated tranches.
