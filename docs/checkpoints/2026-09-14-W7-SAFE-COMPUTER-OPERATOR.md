# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-14

## W7.1 — Durable Operator Transaction Core

Validated baseline: `0092051edff451476a032da3934f72d459a75ae1`

Final W7.1 implementation head: `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`

W7.1 changes exactly these nine implementation/test paths relative to the validated baseline:

1. `desktop/operator_context.py`
2. `desktop/operator_transactions.py`
3. `desktop/transactions.py`
4. `server/session_bound_executor.py`
5. `tests/test_w71_operator_transactions.py`
6. `tests/test_w71_trusted_operator.py`
7. `tools/computer.py`
8. `tools/registry.py`
9. `vision/computer_intelligence.py`

No Home V1, AI Core, Railway, production deployment, connector live-OAuth, or PR-merge changes are part of W7.1.

## Durable transaction authority

The existing Trusted Action Core remains authoritative. W7.1 does not introduce a second approval system.

The authenticated browser/session boundary creates an `OperatorRequestContext` containing owner, device, session, security epoch, initiating conversation/workflow and recent reauthentication evidence. ToolRegistry strips any user-supplied trusted context and injects the authenticated context only after normal tool authorization preparation.

`computer_execute` is a consequential external-side-effect tool, requires recent reauthentication, requires trusted context, requires result verification, and uses the prepared bounded plan rather than accepting a user-supplied prepared transaction.

## Durable operator state

The operator transaction store is SQLite-backed under the Personal AI data root and persists transaction/action/audit state, trusted binding, goal/plan hashes, checkpoints, verification evidence, cancellation/deadline/recovery state, and redacted audit history.

Supported states are:

`proposed -> policy_check -> approval_required -> permitted -> executing -> verifying -> completed`

with bounded terminal/error paths `failed`, `cancelled`, and `recovery_review_required`. Invalid transitions fail closed.

## W7.1 exact-head workflow evidence

All six required workflows passed on `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`:

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #645 | `34861953280` | PASS |
| Reliability and Security | #188 | `34861953222` | PASS |
| P3 iPhone PWA | #156 | `34861953080` | PASS |
| Android Instrumentation | #187 | `34861953260` | PASS |
| Package Validation | #187 | `34861953264` | PASS |
| iOS Companion | #169 | `34861953258` | PASS |

W7.1 is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

---

## W7.2 — Observation Safety and Exact-Head Validation

Validated W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`

Recovered W7.2 WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`

Final W7.2 implementation head: `3d9f5a4f21cf59307758f261d6291a4b7a36003b`

The superseded intermediate candidate `5d100d16501d98f32856a16789198707e01e7ddd` and workflow `34867451105` are not validation evidence.

### Final implementation scope

The W7.2 implementation delta from recovered WIP is confined to these 20 runtime/test paths:

1. `browser/observation.py`
2. `browser/session.py`
3. `desktop/application_context.py`
4. `desktop/evidence_geometry.py`
5. `desktop/observation_policy.py`
6. `desktop/observation_policy_bridge.py`
7. `desktop/observation_policy_v72.py`
8. `desktop/operator_transactions.py`
9. `tests/test_w71_trusted_operator.py`
10. `tests/test_w72_browser_masking.py`
11. `tests/test_w72_capture_privacy.py`
12. `tests/test_w72_changed_source_scan.py`
13. `tests/test_w72_evidence_guard.py`
14. `tests/test_w72_evidence_persistence.py`
15. `tests/test_w72_geometry.py`
16. `tests/test_w72_observation_safety.py`
17. `tools/advanced_control.py`
18. `tools/computer.py`
19. `vision/computer_intelligence.py`
20. `vision/screen_understanding.py`

No Home V1/AI Core redesign, production, Railway, deployment, iPhone qualification-service, or unrelated product change is included.

### Observation and plan binding

W7.2 adds durable observation identity and binds execution to owner/device/session/security epoch, transaction, application/process/window, browser context/tab/origin/normalized URL, observation timestamp/expiry, redacted evidence reference/checksum, screen fingerprint, sanitized DOM/accessibility/actionable-element digests, capture reason/initiator, and sensitivity metadata.

Prepared operator plans carry the exact observation ID/digest, expected context, exact target identity and geometry, pre/postconditions, plan timestamps/expiry and canonical plan digest. The existing Trusted Action Core remains authoritative: approval hashing includes the prepared plan and observation digests, so consequential parameter changes invalidate the approval scope.

Immediately before every dispatch the runtime captures a fresh bounded observation, validates transaction/binding/deadline/Emergency Stop state, checks application/process/window and browser session/tab/origin/URL/frame identity, confirms the actionable target still exists, rejects coordinate-target movement, and fails closed on newly appearing sensitive regions or uncertain identity. After every action it captures a new observation, verifies the postcondition, stores bounded before/after references and binds the next step to the new observation. Unknown dispatch outcomes enter recovery review.

### Sensitive evidence hardening

Browser-supported observations use browser-native screenshot masking before screenshot bytes leave the browser capture boundary. Sensitive selectors cover password/hidden/OTP/payment and secret-bearing fields and are evaluated across frames. Browser observations do not read cookies, local/session storage or authorization headers and persist only sanitized/bounded DOM/accessibility metadata and digests.

Desktop screenshots are captured into memory. Redaction uses a versioned typed coordinate-space model covering browser viewport/document/window, physical monitor, virtual desktop and screenshot-image coordinates. The model records available DPR, page zoom, viewport/window geometry, scroll offsets, browser-content offsets, monitor/virtual origins/scaling, screenshot dimensions/origin and capture source. Rectangles from different spaces are never treated as interchangeable.

If mapping inputs are missing/inconsistent, W7.2 does not guess. The frame is full-redacted before persistence and marked `visual_evidence_unavailable` / `full_frame_redacted`; it is not accepted as coordinate or visual-success proof. No raw sensitive screenshot is written as an intermediate file.

`SanitizedEvidenceGuard` is the single model/vision screenshot-consumer boundary. It rejects unsanitized/full-redacted evidence, unknown coordinate provenance, expired evidence, owner/device/session mismatch, missing sanitized bytes and invalid checksums. Model/vision calls receive only evidence that passes this guard.

Evidence destinations use unique IDs, exclusive writes, confinement checks, symlink resistance, checksums, retention expiry and deletion controls. Durable observation metadata retains evidence ID/checksum/redaction status/method/coordinate-space version/capture source/retention metadata through restart.

### Migration and restart safety

The operator SQLite migration remains additive and restart-safe with schema version 72. It creates the durable `operator_observations` journal and observation/target/plan bindings for operator actions while retaining the validated W7.1 tables. Exact-head regressions cover fresh database creation, upgrade from the W7.1-style schema, repeated initialization/restart and evidence metadata restart persistence.

### Tests

Final focused W7.2 coverage: **58 cases PASS** as part of the exact-head repository run.

Full repository exact-head result: **530 passed, 7 warnings**.

Coverage includes Windows foreground identity, unsupported-platform/no-fabricated identity, browser tab/origin/URL/frame identity, bounded DOM/accessibility capture, password/payment masking, DPR 1/2/3, zoom/scroll/chrome offset, negative/positive monitor origins, multi-monitor/off-screen clipping, malformed/unsupported geometry, fail-safe full-frame redaction, sanitized consumer binding/checksum/expiry, no model call for unavailable visual evidence, concurrent captures, retention/deletion, symlink/path resistance, observation/approval expiry, changed application/window/tab/origin/actionable target, target movement, before/after evidence, cancellation, Emergency Stop, restart recovery, concurrent dispatch and prohibition of background monitoring primitives.

A separate JavaScript-file syntax gate was not applicable because W7.2 changes no standalone `.js` file; embedded browser scripts are exercised through the browser observation/masking regression suite.

### Security repair history

The recovered WIP did not yet provide immediate pre-dispatch observation renewal, explicit cryptographic plan/observation binding, sufficiently durable browser-tab/window identity, safe query-free URL identity, or complete evidence-coordinate provenance. These were repaired without replacing W7.1's Trusted Action Core.

Adversarial review also identified the risk of applying browser viewport rectangles directly to monitor screenshots. W7.2 now uses browser-native masking where supported and typed coordinate transformations only when complete provenance exists; otherwise it fails to full-frame redaction. A later review found new evidence integrity metadata was not all restart-persistent, so it was added to the durable sensitivity metadata envelope. Final CI exposed one safe-state ordering defect (`application_unavailable` being reported as generic verification failure); that classification ordering was repaired without relaxing validation.

### Exact implementation-head workflows

All six required workflows passed on `3d9f5a4f21cf59307758f261d6291a4b7a36003b`:

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #700 | `34869967548` | PASS |
| Reliability and Security | #197 | `34869967279` | PASS |
| P3 iPhone PWA | #165 | `34869967422` | PASS |
| Android Instrumentation | #196 | `34869967534` | PASS |
| Package Validation | #196 | `34869967417` | PASS |
| iOS Companion | #178 | `34869967290` | PASS |

The unrelated Vercel Team VS build-rate-limit status is not a W7.2 required workflow and no paid capacity or Vercel change was made.

## W7.2 classification

W7.2 is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at the software/exact-head level after the implementation gate above and remains subject to the documentation-head evidence gate recorded after this update.

W7.2 is **not PHYSICAL-DEVICE VERIFIED**, **not PRODUCTION VERIFIED**, and does not make W7 overall complete.

W6 remains **LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**, with isolated paid infrastructure still deferred by owner decision.

## Next bounded batch after documentation-head validation

W7.3 — Allowlists and Data-Safety Policies: approved applications/domains/paths/destinations, clipboard/secret handling, side-effect policy and bounded recovery rules. Do not begin W7.3 before the W7.2 documentation-only head passes the same six exact-head workflows.
