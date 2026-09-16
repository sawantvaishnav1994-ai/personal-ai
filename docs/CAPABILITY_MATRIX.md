# Personal AI — Capability Matrix

Baseline date: 2026-09-16

Statuses distinguish automated repository evidence from live service, real local/external model, physical-device, signed-distribution and production evidence. Automated mocks, simulators and deterministic provider adapters are never classified as physical/live provider proof.

| Capability | Status | Automated evidence | Remaining boundary | Exact SHA / next |
| --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | frozen design |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth; reused by W7.1-W7.6 | live operational proof partial | preserve authority |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit, cancellation, recovery, Emergency Stop | physical qualification pending | frozen |
| W7.2 Observation / Sensitive Evidence | AUTOMATED VALIDATED | 85 focused; 557 full | physical desktop/browser proof pending | frozen evidence |
| W7.3 Allowlists / Data-Safety Policies | AUTOMATED VALIDATED | implementation + docs gates complete | physical policy qualification pending | frozen evidence |
| W7.4 Safe Browser Operator | AUTOMATED VALIDATED | implementation + docs gates complete | real-site/physical-browser proof pending | frozen evidence |
| W7.5 Safe Desktop / File Operator | AUTOMATED VALIDATED | implementation + docs gates complete | real-world Windows/physical/production qualification pending | frozen evidence |
| W7.6 Verification and Recovery | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED | frozen W7 baseline contains recovery implementation/evidence | physical/production qualification separate | preserve frozen W7 |
| W8 Model Health / Failover / Observability | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE | implementation and documentation exact-head workflows 6/6 PASS | live-provider/local-model/physical/production qualification separate | implementation `42616b2e8faca9b16a5695ac319ea78200e7af74`; evidence `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce` |
| P4 Everyday Personal Intelligence | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED FOR RETRIEVAL-REMINDER TRANCHE | durable lifecycle and deterministic retrieval/reminder qualification | live delivery/daily-use/physical proof separate | `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b` |
| P5 Second Brain / Life Graph | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED FOR RETRIEVAL-REMINDER TRANCHE | bounded retrieval, temporal/current truth, deletion/retention/context budget | larger real corpus/media/physical proof separate | `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b` |
| P6 Autonomous Operations | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED | governed delegation composes through existing AgentExecutor/AutomationEngine/W7 | autonomous/live/physical/production qualification separate | implementation `e674ee80b66ba6c6dbe734ef1825df6a56c19d3f`; PR #27 |
| P7 Multimodal Understanding | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE | implementation and evidence exact-head gates 6/6; hardened canonical WorldUnderstanding | real camera/mic/location/wearable/live/production separate | implementation `c0498146a0753b24da611e392181970b227a63d4`; evidence `5f13ff2a994e2d257ba1c8d4d4f6cdd6a32d481e`; PR #28 |
| P8 Personal AI Everywhere | IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE | governed cross-device continuity; implementation and evidence exact-head gates 6/6 | real iPhone/Android/desktop cross-device and live/production separate | implementation `041584c50e2e2df8e74aa67843eebd2c2e0e058c`; evidence `bd36011cc71d57110e60843019e52bc6b1963a61`; PR #30 |
| P9 Hybrid AI | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED | canonical W8 router + deterministic privacy/capability/owner policy; 53 P9 focused/adversarial/E2E/performance tests; 1184 full; implementation workflows 6/6 | documentation/evidence exact-head gate; real local/external provider/live/production remain separate | frozen implementation `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb`; PR #31 |
| P10 Advanced Autonomous Intelligence | NOT STARTED IN THIS CONTINUATION | no P10 changes in P9 diff | separate owner directive required | STOP after P9 closure |
| Computer operator overall | AUTOMATED SCOPE CANDIDATE COMPLETE | W7.1-W7.6 automated authorities integrated | physical/production qualification remain | preserve frozen W7 |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 software gates green | real Google account qualification owner-deferred | preserve blocker |
| Production durable storage | BLOCKED | fail-closed hosted guard exists | approved production volume absent | future production gate |
| Physical P3 | BLOCKED / DEFERRED | automated P3 green | mandatory real-device evidence incomplete | final pre-release physical protocol |
| W10 Signed Distribution | BLOCKED / QUALIFICATION | unsigned/dev package and simulator/instrumentation evidence exists | physical-device/signing credentials missing | readiness only until owner gates |
| W12 Release Readiness | PARTIAL | strong repository/automated evidence | live OAuth/providers/storage, physical devices, signing and production gates | no production promotion |

## P7 repository closure

P7 final implementation is `c0498146a0753b24da611e392181970b227a63d4`; final evidence lineage is `5f13ff2a994e2d257ba1c8d4d4f6cdd6a32d481e`. Both required six-workflow exact-head gates passed. P7 remains context-only: P6/W7 retain permission, approval, execution, verification, recovery and Emergency Stop authority. Physical camera, microphone, location, wearable, live-service and production evidence remain NO.

## P8 repository closure

P8 final implementation is `041584c50e2e2df8e74aa67843eebd2c2e0e058c`; P8 evidence is `bd36011cc71d57110e60843019e52bc6b1963a61`. Both required exact-head six-workflow gates passed. P8 composes trusted device/session continuity without transferring model/provider/action authority. Real iPhone, Android and desktop cross-device qualification, physical cross-device proof, live service and production remain NO.

## P9 Hybrid AI implementation evidence

P9 starts exactly from P8 evidence `bd36011cc71d57110e60843019e52bc6b1963a61` on branch `p9/hybrid-ai-qualification-20260916`, draft PR #31. Frozen implementation: `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb`.

P9 builds on the canonical `ModelRouter`, `GovernedModelRouter` and W8 `ModelObservability`/circuit-breaker authorities. It does not introduce ModelRouterV2, ModelHealthV2, FailoverV2, ObservabilityV2, ProviderRegistryV2, ModelMemory or another action/approval authority. `self_hosted` remains the first-class local/owner-controlled route; external OpenAI-compatible adapters remain optional intelligence resources.

Deterministic policy supports `LOCAL_ONLY`, `LOCAL_PREFERRED` and `EXTERNAL_ALLOWED`, owner allow/block lists, capability filtering, W8 health/circuit eligibility, bounded failover and safe failure. Sensitive/secret requests do not become externally eligible. External context projection excludes Memory and Knowledge contents and allows only explicitly bounded safe derived world context/references. P8 device/session trust is checked; model output has no authority; consequential Emergency Stop remains authoritative.

P9 focused/adversarial/E2E/performance qualification: **53 passed in 0.52 s**. Full repository: **1184 passed, 0 failed, 24 warnings in 66.97 s**. Encrypted isolated recovery: **14 passed in 0.74 s**. `pip-audit`: no known vulnerabilities. Compileall and CI `pip check` pass.

Qualification-environment P9 policy/router measurements: 5,000 policy selections **0.006051 s**; 1,000 health-aware selections **0.004593 s**; 500 governed routes **0.009515 s**; router restart **0.000074 s**; bounded generation history **200**. These are router/mock qualification measurements, not LLM inference speed or production SLA.

The final 45-second P9 Hybrid AI soak completed **1,079,693 iterations** with RSS start **33,099,776**, peak/end **35,106,816**, growth **2,007,040 bytes**; local success **179,949**, external-eligible failover success **179,949**, privacy-blocked failures **179,949**, timeout cases **179,949**, observed circuit-open states **179,229**, deterministic recoveries **178,508**, restarts **2,159**, bounded history **160**. No real provider/model was contacted.

Implementation exact-head workflows at `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb`:

- CI #1171 / `35072821803` — PASS
- Reliability and Security #279 / `35072821905` — PASS
- P3 iPhone PWA #231 / `35072821832` — PASS
- Android Instrumentation #278 / `35072821844` — PASS
- Package Validation #278 / `35072822017` — PASS
- iOS Companion #260 / `35072821977` — PASS; simulator evidence only

Implementation gate: **6/6 PASS**. Diff from exact P8 evidence: **19 commits, 10 files, +749 / -48**. No P10 implementation, production/Railway deployment, real credentials, OAuth activation, signing or physical qualification is present.

## Frozen authority boundaries

W7 remains consequential-action/transaction/approval/recovery/Emergency Stop authority. W8 remains model health/failover/observability authority. Second Brain remains memory authority. Knowledge remains distinct from Memory. P7 remains world-understanding context authority. P8 remains trusted continuity/device/session authority. P9 decides which eligible intelligence resource may compute a result; it never decides permissions or grants action authority.

REAL_LOCAL_MODEL_VERIFIED = NO
REAL_EXTERNAL_PROVIDER_VERIFIED = NO
PHYSICAL_DEVICE_VERIFICATION = NO
LIVE_HYBRID_ROUTING_VERIFIED = NO
LIVE_SERVICE_VERIFIED = NO
PRODUCTION_VERIFIED = NO

The P9 documentation/evidence exact-head six-workflow gate is required before P9 may be classified repository/automated evidence complete.
