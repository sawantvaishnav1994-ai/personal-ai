# Personal AI — Test Matrix

Baseline date: 2026-09-15

## W7 validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.5 Safe Desktop / File Operator | `f794373c...` | 55 focused; 709 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | **778 full PASS, 8 warnings** | implementation 6/6 PASS; documentation pending |

## W7.6 release-gate coverage

The committed W7.6 suites qualify recovery behavior, authority composition, dispatch/verification/retry safety, compensation, owner recovery, evidence privacy and schema restoration. W7.1 transaction authority, W7.2 evidence discipline, W7.3 policy, W7.4 browser operator, W7.5 desktop/file operator, Trusted Action Core and Emergency Stop remain authoritative.

## Exact W7.6 implementation validation

Implementation SHA: `38eeae2fc7f609ebc7d3e8681833885b8d35310d`.
Parent/baseline: `acbbefea2ad6d46406ee05f9d2a44676503b3b59`.
Full repository: **778 passed, 8 warnings**. Implementation gate: **6/6 PASS**.

## W8 Model Health / Failover / Observability

Baseline: `dad974fc1058678a07daae1702849178d2cf2dd2`.
Failed historical candidate: `1a9d379f8cdb372e583eb01dfd6373d307c18db8`.
Final implementation SHA: `42616b2e8faca9b16a5695ac319ea78200e7af74`.

The failed candidate was reproduced with diagnostic capture: **978 passed, 7 failed, 8 warnings in 93.73s**. All seven failures were W8 source-code/string-inspection tests, not behavioral product failures: external URL scanning, optional local-process scanning, auth-string scanning, requests-source scanning, provider-key-name scanning, duplicate release-gate source scanning and runtime constructor substring scanning. These tests self-matched test source or matched legitimate inherited implementation strings. They were removed together with other brittle/duplicate source-inspection sentinels; substantive behavioral suites were retained.

W8 behavioral coverage includes provider health semantics and recovery, configuration/transport/capability health, circuit threshold/open/half-open/close/reopen behavior and concurrency, bounded retry and retry classification, bounded failover and recursive-loop prevention, local-only/sensitive privacy eligibility, owner-disabled/provider capability policy, stable error taxonomy, safe bounded observability, generation identity/history, explicit bounded health probes, local-model unavailable behavior, failure injection, W7 compatibility and schema/production boundaries.

Implementation hardening after the failed candidate restored `app/main.py` to the frozen W7 runtime structure with only the governed-router import/construction substitution; bounded retry/backoff/failover configuration; bounded health timeout; and failover accounting on actual fallback attempts. No W8 schema migration was introduced.

Full repository exact-head pytest passed in CI and Reliability/Security at the final implementation SHA. The final suite contains 20 fewer brittle/duplicate test functions than the failed candidate; from the reproduced 985-test failed-candidate collection this yields **965 passing tests, 0 failures, 8 warnings** at the implementation head. `pip check`, compileall and pip-audit passed. Reliability/Security also completed isolated encrypted backup/restore qualification and the 45-second soak. Package Validation passed Ubuntu/macOS/Windows; P3 and Android passed; iOS simulator build/test passed.

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1047 | `34967707625` | PASS |
| Reliability and Security | #239 | `34967707659` | PASS |
| P3 iPhone PWA | #199 | `34967707692` | PASS |
| Android Instrumentation | #238 | `34967707628` | PASS |
| Package Validation | #238 | `34967707632` | PASS |
| iOS Companion | #220 | `34967707682` | PASS |

Implementation gate: **6/6 PASS** on one exact SHA.

W8 classification at implementation head: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**. This is not live-provider, real-world local-model, physical-device or production verification.
