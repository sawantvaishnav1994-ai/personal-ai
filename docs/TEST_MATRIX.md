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

### PR #22 W2/W3 predecessor head

SHA: `5b6fc87572ca592d3d3f59bcfd3b44405f5222d7`

| Workflow | Run ID | Result |
| --- | ---: | --- |
| CI #553 | 34810145820 | PASS |
| Reliability and Security #142 | 34810145825 | PASS |
| P3 iPhone PWA #110 | 34810145848 | PASS |
| Android Instrumentation #141 | 34810145821 | PASS |
| Package Validation #141 | 34810145839 | PASS |
| iOS Companion #123 | 34810145830 | PASS |

### PR #22 W6.1 governed connector candidate

Direct W6 implementation SHA: `baaa7da38956e97231970c548626a71cde257176`

Exact validated branch integration SHA: `152ef13217b652121917a890de14e20edb139473`

| Workflow | Run number | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #569 | 34831726193 | PASS |
| Reliability and Security | #150 | 34831726152 | PASS |
| P3 iPhone PWA | #118 | 34831726271 | PASS |
| Android Instrumentation | #149 | 34831726189 | PASS |
| Package Validation | #149 | 34831726154 | PASS |
| iOS Companion | #131 | 34831726233 | PASS |

Focused W6 connector suite: **60 PASS**. Pre-branch compileall, injected Apps & Tools JavaScript syntax validation, and changed-file secret-pattern scanning also passed. The first W6 integration candidate failed one pre-existing legacy connector compatibility test; the root cause was repaired and the final exact head passed full repository `pytest -q` through CI and Reliability/Security.

## Current test coverage by workstream

| Workstream | Existing evidence | Status | Required additions |
| --- | --- | --- | --- |
| W1 durable storage | SQLite-backed stores have unit/integration coverage | PARTIAL | hosted-runtime fail-closed test; durable data-root diagnostics; restart persistence; redeploy persistence; corruption detection; export/delete; encrypted backup + isolated restore/checksum |
| W2 Trusted Action Core | approval/permission/tool security tests exist | PARTIAL | durable approval restart test; atomic consume race; wrong owner/device/session/security epoch; changed destination/data class; duplicate/idempotency; false-success verification; timeout/partial failure; audit redaction |
| W3 conversation | grounded conversation + owner-product tests | PARTIAL | refresh/browser-close/server-restart/cross-device continuation; rename/search/archive/delete/export full lifecycle |
| W3 voice | P3 PWA automation tests | QUALIFICATION | physical endpoint detection, barge-in, stop speaking, auto-return, mic errors, reconnect, cancellation while thinking, timeout/invalid response |
| W3 devices | registry/owner-product tests | PARTIAL | simultaneous trusted browsers; lost-device controls; global session revoke; re-auth critical path; per-device audit |
| W4 memory | memory/grounding/NEVER_STORE tests | PARTIAL | production persistence and physical UX evidence remain |
| W4 knowledge | knowledge/versioning/provenance/OCR-policy tests | PARTIAL | real OCR provider/document qualification and production durability remain |
| W5 workflows | durable budget/accounting/authority/idempotency tests + exact-head CI | AUTOMATED VALIDATED | production restart/durable-volume qualification remains |
| W6 connectors | 60 focused manifest/OAuth/runtime/idempotency/governance/UI tests plus full repository suite and six exact-head workflows | AUTOMATED VALIDATED | live provider OAuth, Drive/Sheets W6.2, provider-specific quota/revocation/operational qualification |
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
- Physical P3.2–P3.8 evidence on the required candidate/environment.
- Two simultaneous trusted physical browsers.
- Physical voice interruption and cancellation while thinking.
- Physical network disconnect/reconnect.
- Physical session-expiry behaviour.
- Windows installation/update/uninstall on a real Windows host.
- Android installation/reconnect on a physical Android device.
- Live OAuth/provider qualification for Gmail/Calendar and later Drive/Sheets.
- Self-hosted GPU model loading, streaming, latency, concurrency and failover.

## Rule

A test is counted only when the exact SHA, environment and evidence source are recorded. Simulator/browser automation may supplement but must not replace a physical test where the qualification protocol explicitly requires a physical device.
