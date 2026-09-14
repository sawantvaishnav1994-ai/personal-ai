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
| W6 Gmail Draft OAuth scope repair | `ae1b3c12ff82785b1f8cefe1bcbc6201e88b08bc` | full repository 446 PASS | 6/6 PASS |
| W6 qualification preflight artifacts | `0092051edff451476a032da3934f72d459a75ae1` | full repository/regression CI | 6/6 PASS |

## W7 validated history

| Batch | Exact implementation SHA | Full evidence | Required workflows |
| --- | --- | ---: | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` | **471 PASS, 7 warnings** | **6/6 PASS** |

## W7.1 implementation coverage

Authority and binding:
- trusted owner/device/session/security epoch;
- initiating conversation/workflow binding;
- requested goal and exact prepared-plan hashes;
- ToolRegistry removes user-supplied trusted context and injects authenticated context;
- `computer_execute` requires Trusted Action authority/recent reauthentication;
- wrong owner/device/session/security epoch fails closed.

Durability/idempotency:
- SQLite-backed operator transaction/action/audit state;
- transaction and action IDs;
- explicit state machine and invalid-transition rejection;
- `BEGIN IMMEDIATE` concurrency controls;
- transaction-ID rebinding rejection;
- action parameter-hash binding;
- verified-action replay deduplication;
- unresolved actions never blindly redispatch;
- restart of executing/verifying work -> `recovery_review_required`;
- action outcome marked unknown when process restarts after dispatch.

Safety:
- cancellation and deadline checks;
- Emergency Stop before/between dispatches;
- screen-change verification;
- semantic postcondition verification from a fresh observation;
- handler return is not sufficient proof;
- semantic verification failure enters recovery review;
- redacted operator audit excludes token/password/secret/content/text/clipboard payload fields.

Focused W7.1 regressions cover durable state/binding, concurrent proposal idempotency, action checkpoint idempotency, crash/restart recovery, cancellation/deadline, audit redaction, prepared-plan authority, completed replay, semantic verification failure, Emergency Stop, wrong-session/unprepared rejection and trusted-context preparation.

## W7.1 repair history

1. Initial candidate `57407ed2ed2174fb28b6fd3b5e2e540f58b0b9c5` failed an existing compatibility test because a minimal test executor did not expose `.approvals`.
2. Repair `4fbbfafc9d6e287253b5de1e483de021dcdc4076` made security-epoch lookup use the durable ApprovalManager when available and compatibility epoch 0 only for minimal non-production/mock executors.
3. That candidate exposed a second compatibility assumption: the minimal mock did not expose `.approval_context()`.
4. Final implementation `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` made approval metadata lookup optional for minimal mocks while retaining the real metadata path.

No W7 policy/security tests were weakened.

## Exact-head workflows — W7.1

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #645 | `34861953280` | PASS |
| Reliability and Security | #188 | `34861953222` | PASS |
| P3 iPhone PWA | #156 | `34861953080` | PASS |
| Android Instrumentation | #187 | `34861953260` | PASS |
| Package Validation | #187 | `34861953264` | PASS |
| iOS Companion | #169 | `34861953258` | PASS |

CI passed dependency install, `pip check`, repository compileall and full `pytest -q`: **471 passed, 7 warnings**. Reliability/Security passed dependency audit, compileall, full pytest, isolated encrypted backup/restore and soak. Package Validation passed Windows, macOS and Ubuntu jobs.

## Mandatory evidence still outside automation

- W7.2 active app/window/browser/tab/domain/accessibility/DOM observation and stale-observation controls;
- W7.3 allowlists/data-safety policy;
- W7.4 bounded browser operator;
- W7.5 desktop/file operator hardening;
- W7.6 complete verification/recovery qualification;
- physical Windows/browser/operator qualification;
- real Google OAuth/account identity and exact-scope qualification;
- isolated hosted connector persistence/backup/restore on a paid durable service;
- main production durable-storage qualification;
- physical P3 and signed distribution qualification.

Hosted connector qualification remains **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED**. Mocked/local provider tests remain software evidence only.
