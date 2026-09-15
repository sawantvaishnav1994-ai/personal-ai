# Personal AI — Capability Matrix

Baseline date: 2026-09-15

Statuses distinguish automated software evidence from live service, real-world Windows, physical-device, signed-distribution and production evidence.

| Capability | Status | Automated evidence | Remaining boundary | Exact SHA / next |
| --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | frozen design |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth; reused by W7.1-W7.6 | live operational proof partial | preserve authority |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit, cancellation, recovery, Emergency Stop | physical qualification pending | frozen |
| W7.2 Observation / Sensitive Evidence | AUTOMATED VALIDATED | 85 focused; 557 full | physical desktop/browser proof pending | frozen evidence |
| W7.3 Allowlists / Data-Safety Policies | AUTOMATED VALIDATED | 45 focused; 602 full; implementation + docs 6/6 | physical policy qualification pending | frozen evidence |
| W7.4 Safe Browser Operator | AUTOMATED VALIDATED | 52 focused; 654 full; implementation + docs 6/6 | real-site/physical-browser proof pending | frozen evidence |
| W7.5 Safe Desktop / File Operator | AUTOMATED VALIDATED | 55 focused; 709 full; implementation + docs 6/6 | real-world Windows/physical/production qualification pending | frozen evidence |
| W7.6 Verification and Recovery | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED | frozen W7 baseline contains completed recovery implementation/evidence | physical/production qualification separate | preserve frozen W7 |
| W8 Model Health / Failover / Observability | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE | implementation and documentation exact-head workflows 6/6 PASS | live-provider/local-model/physical/production qualification separate | implementation `42616b2e8faca9b16a5695ac319ea78200e7af74`; docs `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce` |
| P4 Everyday Personal Intelligence | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED FOR RETRIEVAL-REMINDER TRANCHE | durable reminder/follow-up lifecycle, deterministic due/snooze/reschedule/terminal states, restart-safe surfacing, briefing integration and fixed precision/recall dataset; full repo 997 PASS | live delivery adapters, real push delivery, daily-use acceptance and physical-device proof | implementation `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b` |
| P5 Second Brain / Life Graph | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED FOR RETRIEVAL-REMINDER TRANCHE | 100/1,000/5,000 corpus retrieval, current/historical/superseded semantics, temporal queries, permission-safe relationship ranking, deletion/retention/context budget; Life Graph remains read-through | media extraction quality, larger/real long-term corpora and physical P3.5 | implementation `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b` |
| P6 Autonomous Operations | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED | governed delegation composes through existing AgentExecutor/AutomationEngine/W7; 44 focused PASS; 1041 full PASS; implementation workflows 6/6 PASS | documentation exact-head gate, then autonomous/live/physical/production qualification remain separate | implementation `e674ee80b66ba6c6dbe734ef1825df6a56c19d3f`; PR #27 |
| P7 Multimodal Understanding | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED | one hardened `WorldUnderstanding`; 8 modalities; 40 focused PASS; 1081 full PASS; security/performance/recovery/soak green; implementation workflows 6/6 PASS | this documentation head must pass exact-head gate; physical sensors/live service/production remain separate | implementation `821e04fe5214b793b8511877a9676cd78e9d86da`; PR #28 |
| P8 Personal AI Everywhere | IMPLEMENTED FOUNDATION / PARTIAL SURFACES | shared surface registry + continuity foundation | physical cross-device proof; watch/earbuds/car/home/AR are not complete surfaces | P3.6 physical later |
| P9 Hybrid Intelligence | AUTOMATED FOUNDATION; W8 RESILIENCE AUTOMATED VALIDATED | privacy/offline routing foundation plus W8 health/failover/observability | live provider and real local runtime unverified | owner/live qualification later |
| P10 Advanced Autonomous Intelligence | IMPLEMENTED FOUNDATION / FAIL-CLOSED ACTIVATION | persistent agents, allowlists, budgets, Emergency Stop, outcomes/self-evaluation | activation and deeper governed execution depend on P3 prerequisites | validate without bypassing P3 |
| Computer operator overall | AUTOMATED SCOPE CANDIDATE COMPLETE | W7.1-W7.6 automated authorities integrated | physical/production qualification remain | preserve frozen W7 |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 software gates green | real Google account qualification owner-deferred with paid isolated infrastructure | preserve blocker |
| Production durable storage | BLOCKED | fail-closed hosted guard exists | approved production volume absent | future production gate |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | physical protocol |
| W10 Signed Distribution | BLOCKED / QUALIFICATION | unsigned/dev package and simulator/instrumentation evidence exists | physical-device and signing credentials missing | readiness only until owner gates |
| W12 Release Readiness | PARTIAL | strong repository/automated evidence | live OAuth/provider/storage, physical devices, signing and production gates | no production promotion |

## P4/P5 retrieval intelligence + reminder lifecycle evidence

Starting evidence: `4985dd014ec8c29c9f90c2dba8f153ea8a5bb969`.
Branch: `p4-p5/retrieval-reminder-qualification-20260915`.
Draft PR: #26, stacked on PR #25.
Final implementation: `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b`.

Second Brain remains the sole authoritative memory persistence layer. Existing lexical retrieval, vector retrieval, salience, usage, source/evidence, conflicts, supersession, deletion and retention were extended rather than replaced. Retrieval now fails closed to normal sensitivity by default; sensitive/secret retrieval requires explicit existing authorization. Visible graph relationships can contribute to bounded context/ranking, but permission filtering happens before relationship expansion/counting so hidden nodes cannot become a metadata side-channel. Explanations expose actual ranking factors only. `current_truth()` excludes historical/superseded rows; `context_at()` supports evidence-preserving time-valid queries; retained history stays historical and deletion of the newest value does not resurrect older obsolete values. Context-character budgeting is bounded.

P4 `everyday_items` is the authoritative reminder/follow-up lifecycle. The lifecycle is additive and deterministic: `created`, `scheduled`, `due`, `surfaced`, `snoozed`, `completed`, `dismissed`, `cancelled`, `superseded`. Existing `open` behavior remains a compatibility view over active states. Due evaluation uses injected/frozen time and per-item timezone handling, including date-only values. Surfacing uses a persisted surface key/count to prevent repeated surfacing after restart. The existing reminder tool delegates to this lifecycle in the full runtime; the old `tasks` table remains only a compatibility fallback for minimal runtimes that do not construct P4. No third reminder authority was introduced.

Focused deterministic qualification: **25 collected, 25 passed, 0 failed, 0 warnings in 0.96s**. Large-corpus correctness was qualified at 100, 1,000 and 5,000 memories. Qualification-environment measurements were approximately **3.943 ms**, **18.603 ms**, and **90.067 ms** respectively; 5,000 future-reminder evaluation was approximately **24.772 ms**. The committed tests use <5 second bounds only as broad regression guards. These values are not production SLAs and no premature optimization was introduced. Existing vector search remains the current SQLite/full-scan foundation.

Fixed proactive/forgotten-item benchmark result: **precision 1.0, recall 1.0, 0 false positives, 0 false negatives** for the specified deterministic dataset of due/overdue/unscheduled explicit commitments versus future/completed/cancelled/superseded/irrelevant/duplicate items. This is deterministic state qualification, not an LLM-authority claim or real-world acceptance metric.

Full repository exact-head result: **997 passed, 0 failed, 8 warnings in 30.64s**. `pip check`, compileall and `pip-audit` PASS. Reliability/Security also passed isolated encrypted backup/restore and the 45-second soak.

Implementation exact-head workflows at `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b`:

- CI #1065 / `34984377146` — PASS
- Reliability and Security #247 / `34984377349` — PASS
- P3 iPhone PWA #204 / `34984377120` — PASS; legitimately triggered by the real `server/cloud_app.py` router mount
- Android Instrumentation #246 / `34984377166` — PASS
- Package Validation #246 / `34984377239` — PASS
- iOS Companion #228 / `34984377173` — PASS; simulator evidence only

Implementation gate: **6/6 PASS**.

Implementation diff from `4985dd014ec8c29c9f90c2dba8f153ea8a5bb969`: **1 commit, 10 files, +1,557 / -119**. No dependency file, production infrastructure, Railway, OAuth, provider credential, signing, W7, W8 or P6 change. Global W7/W8 schema remains **73**. P4 `everyday.sqlite3` is additively extended with lifecycle/audit fields and a local audit table; no global schema-version bump was introduced.

## P6 governed delegation implementation evidence

Starting evidence: `2a631346b0013adca810da32ed0e7519eca15240`.
Branch: `p6/governed-delegation-integration-20260915`.
Draft PR: #27.
Final implementation: `e674ee80b66ba6c6dbe734ef1825df6a56c19d3f`.

P6 remains an orchestration layer and composes `PersonalOperations -> AgentExecutor / AutomationEngine -> ToolRegistry / W7 -> verification -> W7.6 recovery -> outcome`. It introduces no competing executor, permission authority, ApprovalManager, transaction authority, retry authority, recovery authority or memory authority. P6 sets orchestration retries to zero and keeps owner override disabled.

Committed-tree security qualification verifies persisted security epoch and stale-epoch fail-closed behavior, owner/device/session binding, destination/resource-based consequential serialization, read-only parallelism, recursive nested secret-bearing parameter rejection, existing tool/destination/data policy enforcement, safe owner inspection, Emergency Stop composition, truthful cancellation/uncertainty semantics, idempotency/restart recovery, P4 reminder context handoff, P5 memory context filtering, Activities integration and Second Brain outcome recording through the existing authority.

Focused P6 result: **44 collected, 44 passed, 0 failed**. Full repository CI result: **1041 passed, 0 failed, 8 warnings in 41.03s**. Reliability independently ran **1041 passed, 8 warnings in 35.63s**, `pip-audit` with no known vulnerabilities, encrypted backup/restore plus 11 isolated recovery tests, and a 45-second soak with SQLite integrity `ok`.

Implementation exact-head workflows:

- CI #1071 / `34996184188` — PASS
- Reliability and Security #249 / `34996184334` — PASS
- P3 iPhone PWA #206 / `34996184148` — PASS
- Android Instrumentation #248 / `34996184426` — PASS
- Package Validation #248 / `34996184213` — PASS
- iOS Companion #230 / `34996184151` — PASS

Implementation gate: **6/6 PASS**. Implementation diff from the starting evidence is **1 commit, 20 files, +2,730 / -40**. Global W7 schema remains **73**; P6 owns only additive local operation-delegation persistence.

AUTONOMOUS ACTIVATION VERIFIED = NO. PHYSICAL P3 VERIFIED = NO. LIVE SERVICE VERIFIED = NO. PRODUCTION VERIFIED = NO.

## P7 multimodal world understanding implementation evidence

Starting evidence SHA: `0d2203aa78bfe7dc935ea42887c7ba9cf1e94427`.
Branch: `p7/multimodal-world-understanding-qualification-20260915`.
Draft PR: #28.
Final implementation SHA: `821e04fe5214b793b8511877a9676cd78e9d86da`.

P7 extends the existing `WorldUnderstanding` authority rather than creating a second multimodal framework. The normalized persistent observation contract covers all eight declared modalities, stable source-event identity, typed timestamps/confidence, privacy/payload classification, provenance/parents, RAW/EXTRACTED/INTERPRETED/DERIVED lineage, freshness, retention, deletion/expiration, simulation truth, safe summaries and device-trust state. Persistent reads are bounded indexed SQLite queries; startup does not load the observation history into a Python list.

Capability negotiation distinguishes supported/available/permission-required/denied/unavailable/offline/unsupported/simulation-only. Repository fixtures are explicitly simulation-only. Device-derived context composes with the existing DeviceRegistry and PWA trust/session path. P7 observation/context never grants action authority; P6/W7 still own permission, approval, execution, verification, recovery and Emergency Stop.

Focused P7 exact-head result: **40 passed, 0 failed, 9 warnings in 6.23s**. Full repository CI: **1081 passed, 0 failed, 15 warnings in 37.51s**. Reliability independently ran **1081 passed, 0 failed, 15 warnings in 37.75s**, `pip-audit` with no known vulnerabilities, **12 encrypted recovery tests in 0.33s**, explicit performance qualification and a P7-inclusive 45-second soak.

Performance qualification at 100/600/1,800 observations measured ingest at 0.107660/0.500055/1.950975 s, restart at 0.000575/0.000890/0.001644 s, bounded query at 0.003090/0.001303/0.001910 s, and retained **0 historical observations in Python memory at startup**. Database size grew from 229,376 to 3,129,344 bytes as data increased. These are qualification measurements, not production SLAs.

The 45-second soak completed **6,697 iterations**, main and P7 SQLite integrity `ok`, 0 pending device requests, 335 P7 simulated cycles, 469 persisted P7 observations, P7 database size 1,138,688 bytes, and 0 historical observations loaded into memory after restart. Overall process RSS growth was 81,022,976 bytes, below the existing 256 MiB guard.

Implementation exact-head workflows at `821e04fe5214b793b8511877a9676cd78e9d86da`:

- CI #1100 / `35008003160` — PASS
- Reliability and Security #263 / `35008003169` — PASS
- P3 iPhone PWA #216 / `35008003085` — PASS
- Android Instrumentation #262 / `35008003142` — PASS
- Package Validation #262 / `35008003101` — PASS
- iOS Companion #244 / `35008003281` — PASS; simulator evidence only

Implementation gate: **6/6 PASS**. Implementation diff: **13 commits, 9 files, +2,128 / -30**.

This automated evidence does not establish real camera, microphone, location, wearable, physical multimodal, live-service or production verification. Those evidence classes remain **NO / NOT VERIFIED** until genuine external evidence exists.

## Frozen authority boundaries

W7 remains the consequential-action/transaction/approval/recovery/Emergency Stop authority. W8 remains the model health/failover/observability authority. Second Brain remains the memory authority. Life Graph remains a read-through/context layer rather than a duplicate memory store. P4 reminders, P5 memory/context and P7 observations may provide context but do not authorize consequential actions. Deterministic persisted state—not an LLM—decides durable lifecycle/approval/authorization state.

Automated lifecycle, delegation and multimodal evidence is not live delivery or physical qualification. No physical iPhone push, physical sensor observation, live consequential action, production durability, signed distribution or physical P3 is claimed by these repository tranches.
