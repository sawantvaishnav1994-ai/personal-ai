# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-15

## Frozen prior baselines

- W7.1 Durable Operator Transaction Core: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.
- W7.2 Observation Safety / Sensitive Evidence: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at final documentation head `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- W7.3 Allowlists and Data-Safety Policies: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at final documentation head `72408596db75b3e07b031ddc9a86502a0177902e`.

None of W7.1-W7.3 is claimed physical-device verified, production verified, live-OAuth verified, or complete W7.

## W7.3 closure evidence

W7.3 baseline: `2a05e1da4777cdb2393759bd650b264735b1ec97`.

Implementation SHA: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.

Final documentation SHA: `72408596db75b3e07b031ddc9a86502a0177902e`.

Schema version: **73**, additive/restart-safe from W7.2 schema 72.

Focused committed W7.3 tests: **45 PASS**. Supplementary adversarial scratch qualification: **81 PASS — non-release supplementary evidence only**. Full repository implementation result: **602 passed, 8 warnings**.

Implementation workflows: CI #742 / `34879964954`, Reliability and Security #207 / `34879964723`, P3 #175 / `34879964821`, Android #206 / `34879964875`, Package #206 / `34879964783`, iOS #188 / `34879964725` — **6/6 PASS**.

Documentation workflows: CI #744 / `34881398264`, Reliability and Security #208 / `34881398407`, P3 #176 / `34881398376`, Android #207 / `34881398344`, Package #207 / `34881398448`, iOS #189 / `34881398242` — **6/6 PASS**.

W7.3 remains the single default-deny policy authority for application/domain/path/clipboard/data access, reusing the existing Trusted Action Core for consequential approvals.

## W7.4 — Safe Browser Operator

Baseline SHA: `72408596db75b3e07b031ddc9a86502a0177902e`.

Validated implementation SHA: `839cc9d55f73d0a88f8869a64cf11809ba7e9e3d`.

### Exact implementation changed files

- `browser/safe_operator.py`
- `tests/test_w74_browser_security_edges.py`
- `tests/test_w74_release_gate.py`
- `tests/test_w74_safe_browser_operator.py`
- `tests/test_w74_target_fallbacks.py`

No Home V1/AI Core file, production deployment file, Railway configuration, workflow definition, or frozen W7.1-W7.3 source file was changed by W7.4. W7.4 adds no database migration; policy schema remains **73**.

### Authoritative execution flow

The W7.4 Safe Browser Operator composes, rather than duplicates, the frozen authorities:

`operator transaction → fresh W7.2 browser observation → W7.3 policy gateway → permission → approval/reauthentication where required → one-use permit bound to the fresh observation → fresh pre-dispatch verification → execution → postcondition verification → redacted durable audit/recovery state`.

Webpage text is always treated as **untrusted web content**. It cannot grant permissions, modify policy, expose secrets, override owner instructions, or satisfy authorization by itself.

### Browser/DOM/accessibility operation surface

Bounded operations cover approved URL navigation, back/forward/refresh, create/select/close tab, visible-element discovery, click, type, select, check/uncheck, bounded scroll, bounded wait, upload and download.

Stable `target_id` identity is required for element actions. Dispatch preference is:

1. exact DOM locator;
2. exact accessibility role/name locator;
3. restricted verified coordinate fallback for **click only**, requiring the explicit verified visual target identity.

Detached, hidden, covered, disabled, sensitive, replaced or materially moved targets fail closed.

### Navigation security

W7.4 binds browser context/tab/origin/normalized URL and frame-origin state across observations. It rejects credential-bearing URLs, private/localhost destinations unless W7.3 explicitly permits them, HTTPS downgrade, cross-origin redirect not explicitly permitted, tab substitution, browser-session changes, iframe-origin changes for consequential page actions and stale-page/target reuse.

New-page/tab operations remain policy-gated. Page content is never allowed to change the authorization channel.

### Form, upload and download safety

Password, OTP, payment and secret-like fields are not automated. CAPTCHA/MFA/security-challenge text causes `owner_intervention_required`; W7.4 does not bypass these challenges.

Uploads require W7.3 domain/path permission plus file-policy/MIME/signature/size validation before dispatch. Raw upload paths and typed values are represented in approval/audit binding by digests rather than normal logs.

Downloads are confined to an owner-approved root, sanitize untrusted filenames, reject traversal, absolute/drive syntax and Windows reserved names, handle duplicate names without overwrite, verify the final canonical path and validate MIME/signature/size, and record a download SHA-256/size as bounded evidence.

### Consequential side effects

Email/message sending, purchases, financial transfers, public publishing, file sharing, delete/destructive delete, account/security/permission modification and legal acceptance are never implicitly permitted. They require an explicit operation class, applicable W7.3 policy, recent reauthentication and strong owner approval, or remain blocked.

Form submission is classified separately and remains W7.3-policy/approval gated according to data classification and policy.

### Verification and recovery

W7.4 captures a new observation before dispatch and after execution. It checks expected navigation/DOM/accessibility/tab/frame/download/upload outcomes. Consequential actions are never blindly retried after an unknown result.

Duplicate dispatch, dispatch exceptions, unverified consequential postconditions and process/browser restart recovery use `recovery_review_required`. A transaction already recovered by W7.1 to `recovery_review_required` returns that owner-safe state immediately and performs no recapture or redispatch.

Emergency Stop and cancellation are checked before dispatch. One-use permits are issued only after the fresh pre-dispatch observation and are consumed against that exact observation/policy snapshot.

### Privacy boundary

W7.4 collects no cookies, local/session storage, tokens or background browser monitoring. Browser observations continue to use the W7.2 sanitized DOM/accessibility/evidence contract. This batch added no continuous observation thread or polling service.

### Validation

Focused committed W7.4 tests: **52 PASS**.

Full repository exact implementation-head CI: **654 passed, 8 warnings**.

`pip check`: PASS.

`compileall`: PASS.

Standalone JavaScript syntax gate: **N/A** because W7.4 changed no standalone JavaScript file.

Migration gate: **N/A for new storage** because W7.4 adds no schema/table migration and reuses W7.1-W7.3 durable stores at schema 73. Restart recovery behavior is explicitly regression-tested.

### Security defects found and repaired during W7.4

1. One-use browser permits were initially minted before the fresh pre-dispatch observation; they are now issued/consumed only after rebinding to that observation.
2. Post-navigation verification initially treated W7.3 `NormalizedOrigin` as a mapping rather than its typed object; verification was corrected without weakening redirect tests.
3. Cross-platform download filename validation initially allowed Windows drive syntax on non-Windows CI; explicit drive/root/backslash/colon rejection was added.
4. Browser/process restart recovery initially surfaced a raw invalid-state error; W7.4 now returns `recovery_review_required` and never blindly redispatches the recovered transaction.
5. Challenge/CAPTCHA/MFA handling, same-label/target replacement, overlay/clickjacking, tab/frame substitution, private-network/credential URL, secret field, upload/download confinement and coordinate fallback were hardened with focused regressions.

### Exact implementation-head workflows — W7.4

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #780 | `34884812596` | PASS |
| Reliability and Security | #212 | `34884812653` | PASS |
| P3 iPhone PWA | #180 | `34884812640` | PASS |
| Android Instrumentation | #211 | `34884812752` | PASS |
| Package Validation | #211 | `34884812643` | PASS |
| iOS Companion | #193 | `34884812616` | PASS |

Implementation gate: **6/6 PASS**.

## Current W7.4 classification before documentation-head validation

W7.4 is:
- **IMPLEMENTED**
- **INTEGRATED**
- **IMPLEMENTATION-HEAD AUTOMATED VALIDATED**
- **DOCUMENTATION-HEAD VALIDATION PENDING**

Do not yet classify W7.4 as fully automated validated until the documentation-only head independently passes all six workflows. Do not classify it as physical-device verified, production verified, live-OAuth verified, or complete W7.

## Production / infrastructure boundary

Production, Railway and the existing iPhone qualification service remain unchanged. W6 live Google OAuth/account qualification remains blocked/deferred because isolated paid qualification infrastructure is owner-deferred. No deployment, PR merge, paid-service purchase or secret request is part of W7.4.

## W7.5 dependency

W7.5 Desktop and File Operator may begin only from the final W7.4 documentation-only SHA after that exact documentation head independently passes the same six required workflows. W7.5 must reuse W7.1 transaction authority, W7.2 observation/evidence safety, W7.3 policy authority and W7.4 recovery conventions rather than duplicating them.
