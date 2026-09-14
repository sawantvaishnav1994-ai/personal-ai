# Personal AI — Test Matrix

Baseline date: 2026-09-14

## Exact-head workflow evidence

### PR #21 head

SHA: `a8a6d61be84747076a04360bf6f46defbeb7a664`

| Workflow | Run ID | Result |
| --- | ---: | --- |
| CI | 34780031010 | PASS |
| P3 iPhone PWA | 34780031079 | PASS |
| Android Companion | 34780031024 | PASS |
| Android Instrumentation | 34780031027 | PASS |
| iOS Companion | 34780030989 | PASS |
| Package Validation | 34780031048 | PASS |
| Reliability and Security | 34780031057 | PASS |

The CI job runs dependency installation, `pip check`, `compileall`, and `pytest -q` successfully on this exact SHA.

### Deployed UI head

SHA: `e63f02b653dd821ebe41cb7100dadd1b99f0af53`

| Workflow | Run ID | Result |
| --- | ---: | --- |
| CI | 34780326974 | PASS |
| P3 iPhone PWA | 34780327116 | PASS |
| Android Companion | 34780327048 | PASS |
| Android Instrumentation | 34780327086 | PASS |
| iOS Companion | 34780327029 | PASS |
| Package Validation | 34780327092 | PASS |
| Reliability and Security | 34780327042 | PASS |

### P3 exact candidate

SHA: `78c7e9d6d848f0dcc93ee4f1f281fad4eff970f5`

Observed successful workflow families include CI, P3 iPhone PWA, Android Instrumentation, iOS Companion, Package Validation, and Reliability and Security. Automated evidence does not replace physical P3 qualification.

## Current test coverage by workstream

| Workstream | Existing evidence | Status | Required additions |
| --- | --- | --- | --- |
| W1 durable storage | SQLite-backed stores have unit/integration coverage | PARTIAL | hosted-runtime fail-closed test; durable data-root diagnostics; restart persistence; redeploy persistence; corruption detection; export/delete; encrypted backup + isolated restore/checksum |
| W2 Trusted Action Core | approval/permission/tool security tests exist | PARTIAL | durable approval restart test; atomic consume race; wrong owner/device/session/security epoch; changed destination/data class; duplicate/idempotency; false-success verification; timeout/partial failure; audit redaction |
| W3 conversation | grounded conversation + owner-product tests | PARTIAL | refresh/browser-close/server-restart/cross-device continuation; rename/search/archive/delete/export full lifecycle |
| W3 voice | P3 PWA automation tests | QUALIFICATION | physical endpoint detection, barge-in, stop speaking, auto-return, mic errors, reconnect, cancellation while thinking, timeout/invalid response |
| W3 devices | registry/owner-product tests | PARTIAL | simultaneous trusted browsers; lost-device controls; global session revoke; re-auth critical path; per-device audit |
| W4 memory | memory/grounding tests | PARTIAL | NEVER_STORE, retention boundaries, duplicate/contradiction owner correction, explainable retrieval path, export/delete restart persistence |
| W4 knowledge | `tests/test_knowledge.py` + grounded conversation | PARTIAL | OCR/image policy, versioning/re-ingest, access-control negatives, delete object integrity, durable restart/redeploy |
| W5 workflows | `tests/test_workflow_recovery.py` + CI | PARTIAL | durable approval wait across restart; concurrency limits; budget limits; owner override; partial completion; idempotent resume |
| W6 connectors | integration/tool tests using mocks/config checks | PARTIAL | provider-contract tests, scope declarations, health/revocation, read-only live qualification, controlled write approval tests |
| W7 computer operator | tool tests | PARTIAL | sandbox/app/domain/path allowlist, clipboard/secret protection, before/after verification, rollback/recovery, accessibility-vs-coordinate policy |
| W8 models | `tests/test_model_router.py`, dialogue evaluation | PARTIAL | private-route negative tests, provider health/failover matrix, explicit fallback audit, concurrency/latency on self-hosted endpoint |
| W9 proactivity | runtime code/tests exist | PARTIAL | quiet hours, rate/frequency, snooze/dismiss, why-surfaced, destination/privacy controls |
| W10 clients | Android/iOS/package workflows green | QUALIFICATION | signed package tests and physical installation/update/uninstall/reconnect |
| W11 observability | telemetry/logging exists | PARTIAL | correlation IDs, subsystem health endpoints, redaction tests, alerting, performance thresholds and user-facing error taxonomy |
| W12 release | exact-head workflows green | PARTIAL | persistence/restart/backup/restore; package signing; physical P3; exact release candidate smoke and secret scan evidence |

## Mandatory release evidence not satisfied yet

The following cannot be marked passed based only on the current automated suite:

- Main production restart persistence.
- Main production redeploy persistence.
- Encrypted backup and isolated restore verification.
- Physical P3.2–P3.8 evidence on the required candidate/environment.
- Two simultaneous trusted physical browsers.
- Physical voice interruption and cancellation while thinking.
- Physical network disconnect/reconnect.
- Physical session-expiry behaviour.
- Windows installation/update/uninstall on a real Windows host.
- Android installation/reconnect on a physical Android device.
- Self-hosted GPU model loading, streaming, latency, concurrency and failover.

## Rule

A test is counted only when the exact SHA, environment and evidence source are recorded. Simulator/browser automation may supplement but must not replace a physical test where the qualification protocol explicitly requires a physical device.
