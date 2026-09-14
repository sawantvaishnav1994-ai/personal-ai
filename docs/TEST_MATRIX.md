# Personal AI — Test Matrix

Baseline date: 2026-09-14

Statuses distinguish automated software evidence from live-provider, physical-device, and production evidence.

## W6 validated history

| Batch | Exact code SHA | Focused/full evidence | Required workflows |
| --- | --- | ---: | --- |
| W6.1 connector foundation | `152ef13217b652121917a890de14e20edb139473` validated integration | 60 focused | 6/6 PASS |
| W6.2 Drive/Sheets read-first | `ecb5e2615d06816e869dd4adb398565bb5c524fa` | 110 combined focused | 6/6 PASS |
| W6.3 controlled writes | `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254` | 131 combined focused | 6/6 PASS |
| W6 hosted OAuth preparation | `f79958103c50c0e1b25442ffbf6e58e5b4e65203` | 137 recovered connector/preflight | 6/6 PASS |
| W6 Gmail Draft OAuth scope repair | `ae1b3c12ff82785b1f8cefe1bcbc6201e88b08bc` | full repository **446 PASS** | **6/6 PASS** |

## Final W6 software-scope repair

The Gmail Draft operation already required `https://www.googleapis.com/auth/gmail.compose`, but that operation-level scope was not requestable through the live connector OAuth manifest/catalog. The repair keeps operation-level least privilege authoritative:

- Gmail read/search remains `gmail.readonly`.
- Gmail Draft requires `gmail.compose`.
- Gmail Send remains independently governed by `gmail.send`.
- Gmail Modify remains independently governed by `gmail.modify`.
- Prohibited Gmail full-access `https://mail.google.com/` is not admitted into requestable runtime scopes.
- Calendar, Drive, and Sheets scopes remain in the shared Google provider catalog.
- Google incremental-consent union/reduced-scope detection remains unchanged.
- Gateway scope checks continue to fail closed before provider dispatch.

Regression coverage added for Draft allowed with compose, rejected without compose, unchanged read/search/send contracts, Calendar/Drive/Sheets scope-union preservation, reduced-scope detection, and redacted qualification evidence.

## Exact-head workflows — Gmail scope repair

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #597 | `34854396694` | PASS |
| Reliability and Security | #164 | `34854396635` | PASS |
| P3 iPhone PWA | #132 | `34854396766` | PASS |
| Android Instrumentation | #163 | `34854396887` | PASS |
| Package Validation | #163 | `34854396651` | PASS |
| iOS Companion | #145 | `34854396843` | PASS |

CI passed dependency install, `pip check`, repository compileall, and full `pytest -q`: **446 passed, 7 warnings**. Package Validation passed Windows, macOS, and Ubuntu jobs.

## Mandatory evidence still outside automation

- Real Google OAuth/account identity and exact-scope qualification.
- Real incremental-consent scope-union proof against Google.
- Real token refresh/expiry/reconnect/revoke behavior.
- Harmless live Gmail/Calendar/Drive/Sheets operation verification.
- Negative real-provider proof that prohibited destructive/share/clear operations remain unavailable.
- Isolated hosted restart/redeploy persistence and encrypted backup/restore on an attached `/data` volume.
- Main production durable-storage qualification.
- Physical P3 and multi-browser evidence.
- Signed/physical distribution qualification.

Hosted connector qualification is currently **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED** because Railway Free plan refused a third service and the owner chose not to upgrade now. Mocked/local provider tests remain software evidence only and are never classified as live-provider evidence.
