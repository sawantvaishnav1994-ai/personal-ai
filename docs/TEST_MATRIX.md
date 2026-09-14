# Personal AI — Test Matrix

Baseline date: 2026-09-14

## W6 validated history

| Batch | Exact code SHA | Focused tests | Required workflows |
| --- | --- | ---: | --- |
| W6.1 connector foundation | `152ef13217b652121917a890de14e20edb139473` validated integration | 60 | 6/6 PASS |
| W6.2 Drive/Sheets read-first | `ecb5e2615d06816e869dd4adb398565bb5c524fa` | 110 combined | 6/6 PASS |
| W6.3 controlled writes | `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254` | **131 combined** | **6/6 PASS** |

## W6.3 pre-commit validation

- exact baseline-parent candidate: PASS
- focused W6.1 + W6.2 + W6.3 suite: **131 PASS**
- Python compileall: PASS
- Apps & Tools JavaScript syntax: PASS
- additive migration/repeated-startup tests: PASS
- idempotency/concurrency/uncertain-outcome/restart recovery tests: PASS
- changed-file secret-pattern scan: PASS
- whitespace/syntax validation: PASS
- baseline-to-candidate diff: exactly 18 intended files

## W6.3 exact-head workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #585 | `34843634899` | PASS |
| Reliability and Security | #158 | `34843634900` | PASS |
| P3 iPhone PWA | #126 | `34843634890` | PASS |
| Android Instrumentation | #157 | `34843634957` | PASS |
| Package Validation | #157 | `34843634972` | PASS |
| iOS Companion | #139 | `34843634905` | PASS |

CI passed dependency install, `pip check`, repository compileall and full `pytest -q`. Reliability/Security passed dependency audit, compileall, full pytest, encrypted backup/restore qualification and soak. Package Validation passed macOS, Ubuntu and Windows jobs.

## W6.3 regression coverage

Authority/security: per-operation approval, recent reauthentication, Trusted Action bindings, Emergency Stop, data classification, destination/resource binding, changed-parameter invalidation and one-use/replay semantics through the existing core.

Scopes/OAuth: Drive `drive.file`, Sheets write scope, pre-dispatch missing-scope rejection, Google incremental-consent request, cumulative confirmed-scope preservation, reduced-scope detection and live-adapter token/scope refresh.

Drive writes: create/upload/rename/content update, filename/MIME/size limits, explicit parent verification, content checksum, expected provider version/ETag conflict, provider readback verification, duplicate submission/idempotency conflict, uncertain timeout recovery and no blind redispatch.

Sheets writes: spreadsheet creation, bounded A1 update/append, row/column/cell/request limits, RAW value input, formula-like literal strings, expected-current-value hash concurrency protection, returned-range/readback verification, duplicate request and uncertain append recovery.

Compatibility: W6.1 Gmail/Calendar, W6.2 Drive/Sheets reads, Knowledge provenance, workflows and Trusted Action approval paths remain in the combined focused/full repository validation.

## Mandatory evidence still outside automation

- real Google OAuth/account identity and exact-scope qualification;
- incremental-consent scope-union proof against Google;
- real token refresh/expiry/reconnect/revoke behavior;
- harmless live Drive/Sheets read/write verification and negative delete/share/trash/clear checks;
- main production restart/redeploy persistence and backup/restore on attached durable `/data`;
- physical P3 and multi-browser evidence;
- signed/physical distribution qualification;
- W7 Safe Computer Operator hardening/physical qualification.

Mocked provider tests remain software evidence only and never become live-provider evidence.
