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

| Batch | Exact implementation SHA | Focused/full evidence | Required workflows |
| --- | --- | ---: | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` | **471 PASS, 7 warnings** | **6/6 PASS** |
| W7.2 Observation Safety / Application Context | `3d9f5a4f21cf59307758f261d6291a4b7a36003b` | **58 focused PASS; 530 full PASS, 7 warnings** | **6/6 PASS** |

## W7.1 implementation coverage

Authority and binding, durable SQLite transaction/action/audit state, idempotency, restart recovery, cancellation/deadline/Emergency Stop, result verification and audit redaction are automated validated at the W7.1 exact head.

## W7.2 implementation coverage

Observation authority and freshness:
- durable observation ID/digest and owner/device/session/security-epoch/transaction binding;
- observation expiry and plan expiry;
- canonical plan digest tied to exact observation digest through the existing Trusted Action approval scope;
- immediate fresh observation before dispatch;
- action-by-action observation renewal and bounded before/after evidence;
- changed app/process/window/browser session/tab/origin/URL/frame rejection;
- actionable-target removal/replacement/movement rejection;
- new sensitive-region detection;
- Emergency Stop/cancellation checks immediately before dispatch;
- uncertain outcomes -> recovery review.

Browser privacy/evidence:
- bounded visible-text, DOM and accessibility extraction;
- stable browser-context/tab/element identities;
- URL identity strips user-info/query/fragment;
- password/secret/payment/OTP detection;
- browser-native in-memory element masking across frames;
- cookies, local/session storage and authorization headers are not captured;
- durable evidence stores hashes/metadata rather than unrestricted raw DOM values.

Screenshot geometry and evidence boundary:
- typed coordinate spaces for browser viewport/document/window, physical monitor, virtual desktop and screenshot image;
- DPR 1/2/3, page zoom, scroll, browser chrome/content offsets, positive/negative monitor origins and clipping covered;
- malformed/out-of-bounds/unsupported/missing geometry fails closed;
- desktop screenshots are memory-captured and sanitized before persistence;
- incomplete mapping -> full-frame fail-safe redaction / visual evidence unavailable;
- full-redacted evidence cannot prove target position or visual success;
- guarded vision/model boundary accepts only sanitized, checksum-valid, non-expired, provenance-known, owner/device/session-bound evidence;
- no model call for unavailable visual evidence;
- concurrent evidence IDs, retention/deletion and symlink/path confinement covered.

Migration/restart:
- fresh W7.2 database creation;
- additive upgrade from W7.1-style schema;
- repeated initialization/restart safety;
- `PRAGMA user_version = 72`;
- durable observation journal and action observation/target/plan bindings;
- evidence checksum/redaction/provenance/retention metadata survives restart in the durable sensitivity metadata envelope.

## W7.2 focused regression count

Final W7.2-focused suite: **58 cases**, all PASS as part of the exact implementation-head repository run. This count supersedes the earlier intermediate 33/33 prototype result.

## Exact-head workflows — W7.1

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #645 | `34861953280` | PASS |
| Reliability and Security | #188 | `34861953222` | PASS |
| P3 iPhone PWA | #156 | `34861953080` | PASS |
| Android Instrumentation | #187 | `34861953260` | PASS |
| Package Validation | #187 | `34861953264` | PASS |
| iOS Companion | #169 | `34861953258` | PASS |

## Exact-head workflows — W7.2 implementation

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #700 | `34869967548` | PASS |
| Reliability and Security | #197 | `34869967279` | PASS |
| P3 iPhone PWA | #165 | `34869967422` | PASS |
| Android Instrumentation | #196 | `34869967534` | PASS |
| Package Validation | #196 | `34869967417` | PASS |
| iOS Companion | #178 | `34869967290` | PASS |

CI passed dependency install, `pip check`, compileall and full `pytest -q`: **530 passed, 7 warnings**. Reliability/Security passed dependency audit, compileall, full pytest, isolated encrypted backup/restore and soak. Package Validation passed its OS packaging matrix. P3, Android and iOS companion workflows passed on the exact implementation SHA.

No standalone JavaScript file changed in W7.2; embedded browser scripts are exercised through Python browser observation and masking regressions.

## W7.2 repair history

1. Recovered WIP lacked complete fresh-dispatch binding, plan/observation digest binding, durable tab/window identity and safe URL identity.
2. Browser viewport sensitive rectangles were found unsafe to reuse directly as monitor screenshot coordinates; repaired with browser-native masking plus typed coordinate provenance and full-frame fail-safe behavior.
3. Evidence consumer boundary added so unsanitized/full-redacted/expired/mismatched/checksum-invalid evidence never reaches model/vision.
4. Evidence integrity metadata was made restart-persistent through the existing durable sensitivity metadata envelope.
5. CI compatibility failures in legacy fake screens were repaired at the adapter/test-fixture boundary without relaxing the production evidence contract.
6. Final safe-state ordering defect was repaired so unavailable foreground application returns `application_unavailable` instead of a generic verification failure.

The superseded candidate `5d100d16501d98f32856a16789198707e01e7ddd` and workflow `34867451105` are not final evidence. No W7 security test was weakened.

## Mandatory evidence still outside automation

- W7.3 allowlists/data-safety policy;
- W7.4 bounded browser operator;
- W7.5 desktop/file operator hardening;
- W7.6 complete verification/recovery qualification;
- physical Windows/browser/operator qualification;
- real Google OAuth/account identity and exact-scope qualification;
- isolated hosted connector persistence/backup/restore on a paid durable service;
- main production durable-storage qualification;
- physical P3 and signed distribution qualification.

Hosted connector qualification remains **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED**. Automated W7.2 evidence does not constitute physical-device or production verification.
