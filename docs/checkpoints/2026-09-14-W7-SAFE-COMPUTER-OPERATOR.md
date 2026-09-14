# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-14

## W7.1 — frozen automated baseline

Validated W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`.

W7.1 Durable Operator Transaction Core remains **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**. Its Trusted Action Core, durable transaction authority, restart recovery, cancellation/deadline/Emergency Stop handling and approval binding are preserved; W7.2 extends rather than replaces them.

## W7.2 — Observation Safety and Sensitive Evidence Hardening

Recovered W7.2 WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`.

Superseded intermediate candidate: `5d100d16501d98f32856a16789198707e01e7ddd`; workflow `34867451105` is not final evidence.

Final W7.2 implementation SHA: `78ba7e7f9e1587fe5a68d3923f15d0425ef81715`.

### Observation and plan binding

W7.2 provides durable observation identity and expiry; owner/device/session/security-epoch/transaction binding; application/process/window identity; browser context/tab/origin/normalized URL/frame identity; sanitized DOM/accessibility/actionable-element digests; exact plan/observation digest binding through the existing Trusted Action Core; fresh observation immediately before dispatch; target removal/replacement/movement rejection; action-by-action observation renewal; before/after evidence; cancellation/Emergency Stop checks and recovery-review handling.

Consequential parameter changes change the prepared approval scope. Unknown or materially changed context fails closed before input dispatch.

### Sensitive evidence guarantees

Browser-supported observations use browser-native in-memory masking before screenshot bytes leave the browser capture boundary. Sensitive selectors cover password, hidden, OTP, payment, token/secret/pass/PIN/CVV/CVC fields and are evaluated across frames. Browser observation does not read cookies, local/session storage or authorization headers and stores bounded sanitized metadata/digests rather than unrestricted DOM values.

Desktop capture is memory-first. No raw sensitive screenshot is written as an intermediate file. Redaction uses coordinate-space model version **2** with explicit typed spaces for:

- browser viewport;
- browser document;
- browser window;
- physical monitor;
- virtual desktop;
- screenshot image.

The transformation model explicitly accounts for available devicePixelRatio, page zoom, document scroll, viewport/window geometry, browser content/chrome offsets, monitor scale/origin, virtual-desktop origin, screenshot crop origin and screenshot dimensions. Rectangles from different spaces are never treated as interchangeable.

Missing, malformed, inconsistent or out-of-bounds mapping fails closed. The runtime either uses browser-native masking, valid typed transformation, or full-frame redaction/visual-evidence-unavailable. Full-frame-redacted evidence is never accepted as proof of target position or visual success.

`SanitizedEvidenceGuard` rejects unsanitized/full-redacted visual evidence, unknown coordinate provenance, expired evidence, owner/device/session mismatch, missing sanitized bytes and invalid checksums before model/vision consumption.

Evidence uses unique IDs, exclusive writes, checksum verification, path confinement, symlink resistance and retention/deletion controls.

### Migration and restart safety

W7.2 keeps the additive restart-safe operator SQLite migration at schema version **72**. It creates the durable `operator_observations` journal and adds observation/target/plan bindings to operator actions while preserving W7.1 state. Fresh-database, W7.1-upgrade and repeated/restart migration regressions remain green.

### Final tests

Focused W7.2 coverage: **85 PASS**.

Full repository exact implementation-head CI: **557 passed, 8 warnings**.

`pip check`: PASS.

`compileall`: PASS.

Standalone JavaScript syntax gate: not applicable to this W7.2 delta; no standalone `.js` file changed. Embedded browser scripts are exercised through browser observation/masking tests.

Coverage includes DPR 1/2/3, zoom, scrolling, browser chrome/content offsets, resized windows, positive/negative monitor origins, multi-monitor layouts, partially off-screen/cross-monitor clipping, malformed/out-of-bounds rectangles, iframe sensitive fields, missing/unsupported geometry, full-frame fail-safe redaction, browser-native masking, no raw screenshot persistence, no unredacted model/vision call, concurrent captures, retention/deletion and symlink/path confinement, plus all prior observation/approval/context/target/Emergency Stop/recovery tests.

### Security findings repaired

1. Recovered WIP lacked complete fresh-dispatch binding and explicit plan/observation digest binding.
2. Browser tab/window identity and normalized URL identity were insufficiently durable/safe.
3. Browser viewport rectangles could not safely be reused as monitor screenshot rectangles.
4. Coordinate provenance did not fully model DPR, zoom, scroll, browser-window/chrome offsets and multi-monitor origins.
5. Screenshot consumers needed a single fail-closed sanitized-evidence boundary.
6. Legacy test fixtures were updated to the live coordinate-space version without weakening production validation.

### Exact implementation-head workflows

All six required workflows passed on `78ba7e7f9e1587fe5a68d3923f15d0425ef81715`:

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #717 | `34873006958` | PASS |
| Reliability and Security | #202 | `34873006929` | PASS |
| P3 iPhone PWA | #170 | `34873006957` | PASS |
| Android Instrumentation | #201 | `34873006928` | PASS |
| Package Validation | #201 | `34873006956` | PASS |
| iOS Companion | #183 | `34873007037` | PASS |

Implementation gate: **6/6 PASS**.

## Classification

W7.2 is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at the implementation-head gate.

It remains **not PHYSICAL-DEVICE VERIFIED**, **not PRODUCTION VERIFIED**, and does **not** make W7 complete.

Production, Railway and the existing iPhone qualification service were not changed. W6 live OAuth remains blocked/deferred under the owner-approved paid-infrastructure decision.

## Documentation-only gate

This checkpoint/matrix update must itself pass the same six exact-head workflows before W7.3 begins. The resulting documentation SHA and workflow IDs are the final W7.2 evidence head.

## Exact continuation point after documentation 6/6

W7.3 — **Allowlists and Data-Safety Policies**: approved applications/domains/paths/destinations, clipboard/secret handling, side-effect policy and bounded recovery rules. Do not begin W7.3 before the documentation-only W7.2 head is 6/6 green.
