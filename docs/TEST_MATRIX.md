# Personal AI — Test Matrix

Baseline date: 2026-09-15

## W7 validated history

| Batch | Exact implementation SHA | Focused/full evidence | Required workflows |
| --- | --- | ---: | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` | 471 full PASS | implementation + documentation gates complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f9e1587fe5a68d3923f15d0425ef81715` | 85 focused PASS; 557 full PASS, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9efd3a0c3838c31d13eda0f9b04f3710ee6` | 45 focused PASS; 602 full PASS, 8 warnings; scratch 81 PASS non-release | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d55f73d0a88f8869a64cf11809ba7e9e3d` | **52 focused PASS; 654 full PASS, 8 warnings** | **implementation 6/6 PASS; documentation pending** |

## W7.3 final evidence

Final documentation SHA: `72408596db75b3e07b031ddc9a86502a0177902e`.

Documentation workflows: CI #744 / `34881398264`, Reliability and Security #208 / `34881398407`, P3 #176 / `34881398376`, Android #207 / `34881398344`, Package #207 / `34881398448`, iOS #189 / `34881398242` — **6/6 PASS**.

W7.3 final classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

## W7.4 focused coverage

### Authority and policy composition

- reuses W7.1 durable transaction/recovery authority;
- reuses W7.2 bounded browser observation, stable target identity and sanitized evidence contract;
- reuses W7.3 default-deny policy gateway and one-use permit storage;
- policy is re-evaluated against the exact fresh pre-dispatch observation and expected policy digest;
- one-use permit is issued/consumed only after fresh-observation binding;
- owner/device/session/security-epoch mismatch remains fail-closed.

### DOM/accessibility/visual targeting

- exact DOM locator is first priority;
- accessibility role/name target is second priority;
- coordinate fallback is third priority, click-only, and requires explicit verified visual target identity;
- detached, hidden, covered, disabled, sensitive and materially moved targets are rejected;
- same-label/changed-target and stale target identity cases are covered.

### Navigation security

- approved URL navigation, back/forward/refresh and bounded tab operations;
- origin verification before/after navigation;
- HTTPS downgrade rejection;
- cross-origin redirect rejection unless W7.3 policy explicitly permits final destination;
- credential-bearing URL rejection;
- localhost/private-IP default deny through W7.3;
- browser-context/tab substitution detection;
- iframe-origin digest change detection;
- stale-page/context rejection.

### Prompt-injection and challenge resistance

- visible webpage text is explicitly labelled `untrusted_web_content`;
- malicious text cannot modify policy/approval state;
- prompt-injection indicators are surfaced as metadata only;
- CAPTCHA, MFA, authenticator and security-challenge states pause with `owner_intervention_required` rather than bypassing controls.

### Form/secret/upload/download safety

- password/OTP/payment/secret-like fields are rejected for automation;
- form submission is separately classified as consequential;
- email/message send, purchase, financial transfer, public publish, share, deletion, account/security/permission changes and legal acceptance require explicit operation class + applicable policy + recent reauthentication + owner approval or remain blocked;
- upload path/domain permission plus MIME/signature/size checks occur before dispatch;
- unsafe download traversal/absolute/Windows-drive/backslash/colon/reserved filenames are rejected;
- duplicate download names do not overwrite existing files;
- final download is confined to canonical owner-approved root and is MIME/signature/size validated;
- download checksum and size are retained as bounded evidence.

### Verification/recovery

- fresh policy-evaluation observation;
- fresh pre-dispatch observation;
- exact context/target comparison before input;
- Emergency Stop immediately before dispatch;
- postcondition observation/readback after action;
- navigation, tab, upload, download and DOM/accessibility postconditions checked;
- duplicate dispatch and uncertain consequential outcomes become `recovery_review_required`;
- process/browser restart recovery returns safe recovery review and does not blind-retry;
- cancellation and bounded wait/timeout paths are covered.

### Privacy / no background monitoring

- no cookie collection;
- no local/session storage collection;
- no credential/token extraction;
- no background monitoring thread or timer;
- observations remain on-demand and use W7.2 sanitized evidence.

## Counts and release evidence

Focused committed W7.4 test count: **52 PASS**.

Exact implementation SHA `839cc9d55f73d0a88f8869a64cf11809ba7e9e3d`:
- `pip check`: PASS;
- compileall: PASS;
- `pytest -q`: **654 passed, 8 warnings**;
- standalone JavaScript syntax: N/A because no standalone `.js` file changed;
- migration/schema: no W7.4 storage migration; W7.3 schema **73** retained; restart recovery regression PASS.

## Exact-head workflows — W7.4 implementation

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #780 | `34884812596` | PASS |
| Reliability and Security | #212 | `34884812653` | PASS |
| P3 iPhone PWA | #180 | `34884812640` | PASS |
| Android Instrumentation | #211 | `34884812752` | PASS |
| Package Validation | #211 | `34884812643` | PASS |
| iOS Companion | #193 | `34884812616` | PASS |

Implementation gate: **6/6 PASS**.

## Security defects found and repaired during W7.4

1. One-use permit initially preceded fresh pre-dispatch observation; fixed so permit binding is exact and fresh.
2. Typed W7.3 `NormalizedOrigin` was initially handled as a mapping in browser verification; corrected at the typed contract.
3. Download filename sanitization initially missed Windows drive syntax under non-Windows CI; fixed with explicit cross-platform rejection.
4. Recovered browser transactions initially reached a raw invalid-state error; now they return `recovery_review_required` immediately with no redispatch.
5. Prompt injection, overlay/clickjacking, detached/replaced target, tab/frame substitution, HTTPS downgrade, credential/private-network destination, challenge, upload/download confinement and visual fallback are covered by explicit regressions.

## Evidence boundaries

W7.4 is currently **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

It is not physical-device verified, production verified, live OAuth verified, or complete W7. Production, Railway and the existing iPhone qualification service were unchanged. W6 live OAuth remains blocked/deferred pending future owner approval for isolated paid infrastructure.

W7.5 Desktop and File Operator may begin only from the final validated W7.4 documentation SHA after the second 6/6 workflow gate.
