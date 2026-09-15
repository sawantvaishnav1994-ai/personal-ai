# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-15

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | approved production volume absent | attach only at future approved production gate |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute physical protocol later |
| P0 | P4 | Daily briefing ↔ Second Brain context | RESOLVED FOR AUTOMATED SCOPE | authoritative current-memory context and permission filtering regression-tested | preserve; daily-use qualification later |
| P0 | P4 | Reminder/follow-up deterministic lifecycle | RESOLVED FOR CURRENT AUTOMATED SCOPE | durable lifecycle, due engine, restart/idempotency, owner inspection, forgotten-item benchmark validated | live delivery and daily-use proof remain separate |
| P0 | P5 | Second Brain ↔ Life Graph linking | RESOLVED FOR AUTOMATED SCOPE | read-through integration and owner inspection validated; no duplicate authority | preserve |
| P0 | P5 | Retrieval/corpus/temporal/supersession qualification | RESOLVED FOR CURRENT AUTOMATED SCOPE | 100/1,000/5,000 corpus, ranking explanations, temporal/current truth, privacy, deletion/retention and context budget validated | expand only when real long-term corpus evidence warrants it |
| P1 | P4 | Live reminder/push/email/calendar delivery | QUALIFICATION PENDING | deterministic scheduling is not physical/live delivery | owner/live adapter + physical protocol later |
| P1 | P4 | Natural-language commitment extraction daily-use precision | PARTIAL | fixed deterministic state benchmark is not a real-world language/acceptance corpus | build representative acceptance corpus without making LLM authoritative |
| P1 | P5 | Media extraction quality | PARTIAL | document/media pipeline quality needs broader fixture evidence | add deterministic extraction-quality qualification when prioritized |
| P1 | P6 | PersonalOperations governed delegation | PARTIAL INTEGRATION | plan facade persists/gates plans but non-consequential execution still reports delegated false | next recommended tranche: compose through existing AgentExecutor/AutomationEngine/W7 authority |
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
| P1 | W8 | Model health/failover/observability | RESOLVED FOR REPOSITORY/AUTOMATED SCOPE | implementation and documentation exact-head gates both 6/6 PASS | live-provider/local-model qualification remains separate |
| P1 | P7 | Real sensor/device multimodal qualification | QUALIFICATION PENDING | normalized software observations do not prove camera/location/wearable availability | deterministic tests now; physical sensors later |
| P1 | P8 | Real cross-device/surface qualification | PARTIAL / QUALIFICATION PENDING | registry/continuity foundation does not make every listed surface a complete runtime | qualify implemented surfaces and physical handoff later |
| P1 | P9 | Live provider / real local model | QUALIFICATION PENDING | W8 automated routing/resilience is not real provider/local runtime evidence | owner-approved bounded live/local protocol later |
| P1 | P10 | Advanced autonomy activation | BLOCKED/FAIL-CLOSED BY PREREQUISITES | persistent agents exist but P3 permissions/automation/memory/continuity/reliability must qualify first | continue repository validation without activation bypass |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | readiness work only until owner signing/device gates |
| P1 | W12 | Release readiness | PARTIAL | live OAuth/providers, production storage/service, physical and signing gates remain | no production promotion yet |

## P4/P5 retrieval/reminder automated-scope closure

Starting evidence: `4985dd014ec8c29c9f90c2dba8f153ea8a5bb969`.
Final implementation: `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b`.
Draft PR: #26.

Focused qualification: **25 passed, 0 failed in 0.96s**. Full repository: **997 passed, 0 failed, 8 warnings in 30.64s**. `pip check`, compileall, `pip-audit`, encrypted backup/restore and 45-second soak passed.

Implementation exact-head workflows: CI #1065 / `34984377146`; Reliability/Security #247 / `34984377349`; P3 #204 / `34984377120`; Android #246 / `34984377166`; Package #246 / `34984377239`; iOS #228 / `34984377173` — **6/6 PASS**.

Large deterministic retrieval corpora 100/1,000/5,000 returned the target correctly; measured qualification latencies were ~3.943/~18.603/~90.067 ms. 5,000-reminder evaluation measured ~24.772 ms. Fixed forgotten-item dataset achieved precision 1.0 / recall 1.0 / 0 FP / 0 FN. These are automated deterministic measurements, not daily-use/live-delivery evidence.

Global schema remains **73**; P4 storage has additive lifecycle/audit columns/table only. No dependency, Railway, production, OAuth, provider credential, signing, W7, W8 or P6 implementation change occurred.

## Remaining evidence classes

Automated repository evidence must remain distinct from live service, physical-device, signed-distribution and production evidence. Live reminder delivery remains **NOT VERIFIED**. Physical P3 remains incomplete. Live OAuth/providers, real local model, production durable storage, real Windows/iPhone/Android qualification and signing credentials remain external gates.
