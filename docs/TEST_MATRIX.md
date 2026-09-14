# Personal AI — Test Matrix

Baseline date: 2026-09-14

Statuses distinguish automated software evidence from live-provider, physical-device and production evidence.

## W7 validated history

| Batch | Exact implementation SHA | Focused/full evidence | Required workflows |
| --- | --- | ---: | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` | 471 full PASS | 6/6 PASS |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f9e1587fe5a68d3923f15d0425ef81715` | **85 focused PASS; 557 full PASS, 8 warnings** | **6/6 PASS** |

## W7.2 implementation coverage

Observation authority/freshness:
- durable observation ID/digest and owner/device/session/security-epoch/transaction binding;
- observation and plan expiry;
- canonical plan digest tied to exact observation digest through existing Trusted Action approval scope;
- immediate fresh observation before dispatch;
- action-by-action observation renewal and bounded before/after evidence;
- changed app/process/window/browser session/tab/origin/URL/frame rejection;
- actionable-target removal/replacement/movement rejection;
- new sensitive-region detection;
- Emergency Stop/cancellation check immediately before input;
- uncertain outcome -> recovery review.

Browser privacy/evidence:
- bounded visible text, sanitized DOM and accessibility extraction;
- stable browser-context/tab/action-target identities;
- normalized URL strips user-info/query/fragment;
- password/hidden/OTP/payment/token/secret/PIN/CVV/CVC detection;
- browser-native in-memory masking across frames;
- no cookie/local-storage/session-storage/authorization-header capture;
- no unrestricted DOM persistence.

Coordinate-space version 2:
- browser viewport;
- browser document;
- browser window;
- physical monitor;
- virtual desktop;
- screenshot image.

Transformation and clipping regressions cover DPR 1/2/3, page zoom, document scrolling, browser chrome/content offset, resized browser windows, positive/negative monitor origins, multi-monitor layouts, partially off-screen and cross-monitor rectangles, malformed/out-of-bounds rectangles and missing/unsupported geometry.

Evidence boundary:
- desktop screenshot captured into memory;
- sanitize before persistence;
- incomplete/uncertain geometry -> full-frame fail-safe redaction / visual evidence unavailable;
- full-redacted image cannot prove target position or visual success;
- `SanitizedEvidenceGuard` rejects unsanitized/full-redacted, unknown-provenance, expired, binding-mismatched and checksum-invalid evidence;
- no model/vision call for unavailable or unsanitized visual evidence;
- unique concurrent evidence IDs;
- retention/deletion;
- path confinement and symlink resistance.

Migration/restart:
- fresh W7.2 database creation;
- additive W7.1-style upgrade;
- repeated/restart initialization;
- `PRAGMA user_version = 72`;
- durable `operator_observations` journal;
- operator action observation/target/plan bindings.

## Focused regression count

Final W7.2-focused coverage: **85 cases PASS**. This supersedes the earlier intermediate 33/33 prototype and the earlier 58-case implementation checkpoint.

## Full repository result

Exact implementation SHA `78ba7e7f9e1587fe5a68d3923f15d0425ef81715`:

- `pip check`: PASS;
- compileall: PASS;
- `pytest -q`: **557 passed, 8 warnings**.

No standalone JavaScript file changed in the final W7.2 delta; embedded browser scripts are exercised by the browser observation/masking regressions.

## Exact-head workflows — final W7.2 implementation

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #717 | `34873006958` | PASS |
| Reliability and Security | #202 | `34873006929` | PASS |
| P3 iPhone PWA | #170 | `34873006957` | PASS |
| Android Instrumentation | #201 | `34873006928` | PASS |
| Package Validation | #201 | `34873006956` | PASS |
| iOS Companion | #183 | `34873007037` | PASS |

Implementation gate: **6/6 PASS**.

## Repair history

1. Recovered WIP lacked complete immediate-dispatch binding and explicit plan/observation digest binding.
2. Browser tab/window and normalized URL identity were hardened.
3. Browser viewport sensitive rectangles were found unsafe to reuse as monitor coordinates.
4. Browser-native masking and explicit typed geometry were added.
5. Coordinate-space version 2 added all six requested coordinate systems and explicit DPR/zoom/scroll/window/chrome/monitor/crop inputs.
6. Screenshot consumer guard added; full-redacted or invalid evidence cannot reach vision/model as proof.
7. Legacy fixture compatibility was updated to the live provenance version without weakening production tests.

The superseded candidate `5d100d16501d98f32856a16789198707e01e7ddd` and workflow `34867451105` are not final evidence.

## Evidence outside automation

W7.2 is not physical-device or production verified. Remaining future qualification includes physical Windows/browser operation, W7.3-W7.6, live Google OAuth/account qualification when infrastructure is approved, production durable storage, physical P3 and signed distribution.
