# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-15

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | approved production volume absent | attach only at future approved production gate |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute physical protocol later |
| P0 | P4 | Daily briefing ↔ Second Brain context | RESOLVED FOR CURRENT AUTOMATED SCOPE | verified integration defect repaired and regression-tested | preserve; qualify daily use later |
| P0 | P5 | Second Brain ↔ Life Graph linking | RESOLVED FOR CURRENT AUTOMATED SCOPE | read-through integration and owner inspection now implemented/validated | continue graph/corpus quality qualification |
| P1 | P5 | Graph retrieval / long-term corpus quality | PARTIAL QUALIFICATION | foundation exists but representative corpus metrics are not authoritative yet | build deterministic corpus/relevance/temporal/conflict suite |
| P1 | P5 | Media extraction quality | PARTIAL | document/media pipeline quality needs broader fixture evidence | add deterministic extraction-quality qualification |
| P1 | P4 | Reminder/follow-up execution and proactive precision | PARTIAL | software foundation exists; delivery lifecycle and precision/recall need deeper evidence | automate local lifecycle/quality tests before live accounts |
| P1 | P6 | PersonalOperations governed delegation | PARTIAL INTEGRATION | P6 plan facade persists/gates plans but reports non-consequential execution as delegated false | integrate only through existing W7-governed executor/automation path and test fail-closed |
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
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, production storage/service, physical and signing gates remain | no production promotion yet |

## Post-W8 implementation evidence

Frozen W8 implementation: `42616b2e8faca9b16a5695ac319ea78200e7af74`. Frozen W8 documentation/evidence head: `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`. W8 implementation and documentation exact-head gates are both 6/6 PASS. The historical failed candidate `1a9d379f8cdb372e583eb01dfd6373d307c18db8` remains failure/remediation evidence only.

Post-W8 branch: `p5/second-brain-life-graph-qualification-20260915`. Implementation SHA: `fc8f1aeb5a8121f0faf911b6840b7ec15d48b609`. Draft PR: #25.

The tranche repaired P4 daily briefing memory integration and added non-duplicating P5 Second Brain↔Life Graph linking with privacy-filtered owner inspection. Full repository: **972 passed, 0 failed, 8 warnings in 26.17s**. CI #1060 / `34980195417`, Reliability/Security #245 / `34980195624`, Android #244 / `34980195358`, Package #244 / `34980195728`, and iOS #226 / `34980195661` all PASS. P3 iPhone PWA is path-filtered N/A because no P3/PWA path changed; it is not counted as a pass. Reliability/Security passed `pip-audit`, compileall, full pytest, encrypted backup/restore and 45-second soak.

## Remaining evidence classes

Automated repository evidence must remain distinct from live service, physical-device, signed-distribution and production evidence. Physical P3, live OAuth/providers, real local model, production durable storage, real Windows/iPhone/Android qualification and signing credentials remain unresolved external gates. W10 must not displace higher-value unblocked P4/P5/P6 repository work merely because it is the next numbered workstream.
