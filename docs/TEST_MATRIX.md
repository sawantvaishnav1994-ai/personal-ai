# Personal AI — Test Matrix

Baseline date: 2026-09-14

## W6.1 exact evidence

- Direct implementation: `baaa7da38956e97231970c548626a71cde257176`
- Validated integration: `152ef13217b652121917a890de14e20edb139473`
- Validated documentation head: `a828cca77bbb910306641fabcc0f8211e3e65e19`
- Focused connector suite: **60 PASS**

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #569 | 34831726193 | PASS |
| Reliability and Security | #150 | 34831726152 | PASS |
| P3 iPhone PWA | #118 | 34831726271 | PASS |
| Android Instrumentation | #149 | 34831726189 | PASS |
| Package Validation | #149 | 34831726154 | PASS |
| iOS Companion | #131 | 34831726233 | PASS |

## W6.2 exact evidence

- Baseline: `a828cca77bbb910306641fabcc0f8211e3e65e19`
- Implementation: `ecb5e2615d06816e869dd4adb398565bb5c524fa`
- Focused W6.1 + W6.2 suite: **110 PASS**
- Compileall: PASS
- Apps & Tools JavaScript syntax: PASS
- changed-file secret-pattern scan: PASS
- full repository pytest through CI: PASS

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #579 | 34836268100 | PASS |
| Reliability and Security | #155 | 34836268108 | PASS |
| P3 iPhone PWA | #123 | 34836268173 | PASS |
| Android Instrumentation | #154 | 34836268200 | PASS |
| Package Validation | #154 | 34836268171 | PASS |
| iOS Companion | #136 | 34836268106 | PASS |

CI passed dependency installation, `pip check`, repository compileall and full `pytest -q`. Reliability/Security passed dependency audit, compileall, full pytest, encrypted backup/restore qualification and the 45-second soak. Package Validation passed macOS, Ubuntu and Windows jobs.

## Current coverage by workstream

| Workstream | Evidence | Status | Remaining qualification |
| --- | --- | --- | --- |
| W1 durable storage | hosted guard + recovery tests | PARTIAL | production `/data`, restart/redeploy/restore |
| W2 Trusted Action Core | durable binding/replay/epoch/security tests | PARTIAL | live sessions/connectors + production persistence |
| W3 conversation/voice/devices | automated P3 and owner-product tests | QUALIFICATION/PARTIAL | physical P3 and multi-browser evidence |
| W4 memory/knowledge | NEVER_STORE, retrieval, versioning, provenance, OCR-policy tests | PARTIAL | production durability + real OCR/provider docs |
| W5 workflows | budgets/concurrency/idempotency exact-head validated | AUTOMATED VALIDATED | production durable restart qualification |
| W6.1 connector foundation | 60 focused + six exact-head workflows | AUTOMATED VALIDATED | live provider qualification |
| W6.2 Drive/Sheets reads | 110 combined focused + full pytest + six exact-head workflows | AUTOMATED VALIDATED | live Google OAuth/account/provider qualification |
| W7 computer operator | bounded operator + verification/rollback foundations | PARTIAL | Trusted Action binding, allowlists, accessibility-first, clipboard/secret policy, physical qualification |
| W8 models | router/dialogue tests | PARTIAL | provider health/failover/observability + private route |
| W9 proactivity | runtime tests | PARTIAL | quiet hours/frequency/snooze/why/privacy |
| W10 clients | package/mobile workflows | QUALIFICATION | signing and physical install/update/reconnect |
| W11 observability | telemetry/logging foundations | PARTIAL | correlation, subsystem health, alerts, thresholds |
| W12 release | exact-head CI evidence | PARTIAL | durable production, physical P3, signing, release smoke |

## W6.2 regression coverage

Drive: manifest validation, least-privilege scope declaration, list/search/metadata, bounded pagination, cursor-cycle rejection, download/export, unsupported MIME, content-size rejection, 401/403/404/429/5xx, Retry-After, timeout/cancellation/deadline, malformed responses, provenance and redacted audit.

Sheets: manifest validation, read-only scope declaration, spreadsheet metadata, worksheet listing, A1 range validation, row/column/cell/range/response limits, batch reads, formatted/unformatted/formula separation, formula-injection-safe export/display, empty/malformed responses, quota/rate-limit/timeout/cancellation and provenance.

Knowledge: explicit owner-approved ingestion, no automatic bulk ingestion, Drive/Sheets provenance, version lineage through source semantics, local deletion independent from provider deletion, NEVER_STORE rejection, sensitive external-model routing guard and owner/device/session authorization.

Existing Gmail/Calendar W6.1 regression coverage remains required and passing.

## Mandatory evidence still outside automation

- live Google OAuth/account qualification;
- real provider quota/revocation behavior;
- W6.3 controlled writes;
- main production restart/redeploy persistence;
- physical P3.2-P3.8;
- two simultaneous trusted physical browsers;
- signed/physical distribution qualification;
- self-hosted GPU model qualification.

A capability is only counted at the evidence level actually demonstrated; mocked provider tests never become live-provider evidence.
