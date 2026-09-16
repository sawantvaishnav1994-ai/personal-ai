# Personal AI — Test Matrix

Baseline date: 2026-09-16

## Frozen validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full | implementation + documentation complete |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full | implementation + documentation complete |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full | implementation + documentation complete |
| W7.5 Safe Desktop / File Operator | `f794373c...` | 55 focused; 709 full | implementation + documentation complete |
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | 778 full PASS | frozen W7 automated evidence |
| W8 Model Health / Failover / Observability | `42616b2e8faca9b16a5695ac319ea78200e7af74` | 965 full PASS | implementation + docs 6/6 PASS; frozen |
| P7 Multimodal Understanding | `c0498146a0753b24da611e392181970b227a63d4` | 44 focused; 1085 full | implementation + evidence 6/6 PASS; repository scope closed |
| P8 Cross-device Continuity | `041584c50e2e2df8e74aa67843eebd2c2e0e058c` | 46 focused; 1127 full prior qualification | implementation + evidence 6/6 PASS; repository scope closed |
| P9 Hybrid AI | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | 53 P9 focused/adversarial/E2E/perf; 1184 full | implementation 6/6 PASS; evidence gate pending |

## P7 repository closure

P7 implementation `c0498146a0753b24da611e392181970b227a63d4` and final evidence lineage `5f13ff2a994e2d257ba1c8d4d4f6cdd6a32d481e` both passed the canonical six exact-head workflows. Physical camera, microphone, location, wearable, live-service and production verification remain separate.

## P8 repository closure

P8 implementation `041584c50e2e2df8e74aa67843eebd2c2e0e058c` and P8 evidence `bd36011cc71d57110e60843019e52bc6b1963a61` both passed the canonical six exact-head workflows. Automated continuity qualification is not physical cross-device verification.

## P9 Hybrid AI — Frozen implementation qualification

Start base: exact P8 evidence `bd36011cc71d57110e60843019e52bc6b1963a61`.
Branch: `p9/hybrid-ai-qualification-20260916`.
Draft PR: #31, OPEN / DRAFT / UNMERGED.
Frozen implementation SHA: `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb`.

### Authority and architecture qualification

P9 reuses `ModelRouter`, `GovernedModelRouter` and W8 `ModelObservability`/`CircuitBreaker`. Tests verify that privacy/capability/owner policy filters resources before execution, W8 health/circuit state may remove but never create eligibility, bounded retry/failover terminates, and attempted provider targets are unique. `self_hosted` is the first-class local route; external provider adapters remain optional and require eligibility/configuration.

Memory, Knowledge, P7 and P8 remain external canonical authorities. `SafeContext` is bounded; external projection excludes Memory and Knowledge contents and includes only bounded safe derived world context/references. Device/session trust fails closed. Model output is always untrusted and has no approval/action authority. Consequential Emergency Stop remains authoritative.

### Focused / adversarial / deterministic E2E

Committed P9 qualification files:

- `tests/test_p9_hybrid_ai.py`
- `tests/test_p9_adversarial.py`
- `tests/test_p9_e2e.py`
- `tests/test_p9_performance_recovery.py`

Combined exact-head Reliability result: **53 passed in 0.52 s**.

Mandatory adversarial coverage includes forged/malformed provider result, timeout, all unavailable, privacy-forbidden fallback, capability mismatch, unavailable/open circuit, failover-loop attempt, prompt injection, fake owner approval, fake security state, tool escalation, Memory exfiltration, P7 raw-context leakage contract, secret-exfiltration attempt, owner-policy bypass, revoked device, stale session, concurrent routing isolation and Emergency Stop bypass.

Deterministic E2E A–L all pass:

A — healthy local route — PASS
B — local failure + external allowed — PASS
C — local failure + external forbidden — PASS
D — capability-based selection — PASS
E — timeout + legitimate failover — PASS
F — all eligible providers unavailable — PASS
G — bounded authorized Memory/Knowledge context — PASS
H — safe P7-derived context only for external route — PASS
I — P8 trusted-device/fresh-session AI use — PASS
J — malicious model cannot authorize P6 action — PASS
K — restart/concurrent routing remains isolated — PASS
L — Emergency Stop blocks consequential action — PASS

### Full repository and security

Reliability/Security exact-head full repository result: **1184 passed, 0 failed, 24 warnings in 66.97 s**.

- `pip-audit -r requirements.txt` — **PASS: No known vulnerabilities found**
- compileall — **PASS**
- CI `pip check` — **PASS**
- isolated encrypted backup/restore/recovery — **14 passed in 0.74 s**

No security test was removed or weakened to obtain P9 qualification. Earlier P9 candidate failures were fixed by respecting frozen W8 source/health boundaries and by correcting the P9 soak model; W8 runtime security semantics were preserved.

### Performance and boundedness

Qualification-environment router/policy measurements:

| Measurement | Result |
| --- | ---: |
| 5,000 privacy/policy selections | 0.006051 s |
| 1,000 health-aware eligible selections | 0.004593 s |
| 500 governed mock routes | 0.009515 s |
| router restart | 0.000074 s |
| bounded generation history after test | 200 |

These measure router/policy overhead using deterministic mock calls. They are **not** real local-model or external-LLM inference latency and are not production SLAs.

Context qualification bounds each source to 8 entries and each item to 2,000 characters in the test contract. W8 generation history remains bounded at 200; owner-visible snapshots remain bounded. Concurrent tests use independent request policy and context and verify no cross-request policy leakage or deadlock.

### Encrypted backup / restore

P9 recovery qualification verifies encrypted isolated backup/restore of safe owner/provider policy metadata and confirms plaintext test credentials/Authorization material are absent from the archive. Runtime circuit state does not restore stale authority; restart rebuilds bounded runtime state. Real provider credentials are not part of P9 repository evidence.

### P9 mixed soak

45-second exact-head P9 soak:

- iterations: **1,079,693**
- RSS start: **33,099,776**
- RSS peak: **35,106,816**
- RSS end: **35,106,816**
- RSS growth: **2,007,040 bytes**
- healthy local routes: **179,949**
- external-eligible failover successes: **179,949**
- privacy-blocked local-only failures: **179,949**
- timeout/failover cases: **179,949**
- observed circuit-open states: **179,229**
- deterministic circuit recoveries: **178,508**
- router restarts: **2,159**
- final bounded generation history: **160**

The same Reliability workflow also ran the existing 45-second repository soak: **6,634 iterations**, SQLite integrity `ok`, pending device requests 0, P7/P8 SQLite integrity `ok`. No real AI provider or physical GPU/model was used.

### Implementation exact-head workflow gate

| Workflow | Run | Run ID | Head SHA | Result |
| --- | ---: | ---: | --- | --- |
| CI | #1171 | `35072821803` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |
| Reliability and Security | #279 | `35072821905` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |
| P3 iPhone PWA | #231 | `35072821832` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |
| Android Instrumentation | #278 | `35072821844` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |
| Package Validation | #278 | `35072822017` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |
| iOS Companion | #260 | `35072821977` | `bfb9b574e2dfbd2e0026ab1affbe74ba9a17e7eb` | PASS |

Implementation exact-head gate: **6/6 PASS**.

Implementation diff from exact P8 evidence: **19 commits, 10 files, +749 / -48**. No P10 implementation, production/Railway deployment, production OAuth/provider credentials, signing or physical-device qualification is included.

### Evidence boundary

REAL_LOCAL_MODEL_VERIFIED = NO
REAL_EXTERNAL_PROVIDER_VERIFIED = NO
PHYSICAL_DEVICE_VERIFICATION = NO
LIVE_HYBRID_ROUTING_VERIFIED = NO
LIVE_SERVICE_VERIFIED = NO
PRODUCTION_VERIFIED = NO

The documentation/evidence exact-head six-workflow gate remains required before P9 repository/automated scope closure. P10 is NOT STARTED.
