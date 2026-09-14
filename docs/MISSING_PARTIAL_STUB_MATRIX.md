# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-15

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | main runtime still lacks approved persistent `/data` | attach only at approved production gate; restart/redeploy/backup/restore proof |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute exact physical protocol |
| P1 | W4 | Real OCR/provider qualification | PARTIAL | bounded OCR contract exists; real provider/docs not qualified | qualify approved OCR path |
| P1 | W5 | Workflow production durability | PARTIAL | automated validated; main production volume absent | durable production operational proof |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | owner postponed paid isolated infrastructure | preserve checkpoint and resume only after future owner approval |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected without isolated durable service | execute prepared package only after owner-approved service exists |
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | implementation/documentation exact-head validation complete | frozen automated baseline |
| P1 | W7.2 | Observation/application context + sensitive evidence | RESOLVED FOR AUTOMATED SCOPE | implementation/documentation automated gates complete | frozen automated baseline; physical qualification remains separate |
| P1 | W7.3 | Allowlists and data-safety policies | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation exact-head 6/6; final docs `72408596...` | frozen automated policy baseline |
| P1 | W7.3 | Physical application/domain/path/clipboard qualification | QUALIFICATION PENDING | automated policy evidence is not physical Windows/browser/filesystem proof | later physical qualification; do not misclassify automated evidence |
| P1 | W7.4 | Safe Browser Operator | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | implementation `839cc9d5...`; 52 focused PASS; 654 full PASS, 8 warnings; implementation workflows 6/6 PASS | complete documentation-only exact-head 6/6, then freeze W7.4 |
| P1 | W7.4 | Physical/real-site browser operator qualification | QUALIFICATION PENDING | automated DOM/accessibility/visual fallback and policy evidence is not real-site/physical-browser proof | later physical qualification; preserve no-bypass boundaries |
| P1 | W7.5 | Desktop and File Operator | BLOCKED ON W7.4 DOC GATE | must start from final frozen W7.4 documentation SHA and reuse W7.1-W7.4 authorities | begin only after W7.4 documentation 6/6 |
| P1 | W7.6 | Verification and recovery | PARTIAL | W7.1-W7.4 foundations validated at software level; full end-to-end desktop/file recovery remains | complete after W7.5 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated work |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no approved GPU host | later infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, W7.5-W7.6, production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## W7.3 frozen evidence

- Baseline: `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- Implementation: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.
- Final documentation: `72408596db75b3e07b031ddc9a86502a0177902e`.
- Schema **73**; focused **45 PASS**; supplementary scratch **81 PASS non-release**; full **602 passed, 8 warnings**.
- Implementation workflows 6/6 and documentation workflows 6/6.
- Final W7.3 classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

## W7.4 exact implementation evidence

- Baseline: `72408596db75b3e07b031ddc9a86502a0177902e`.
- Implementation: `839cc9d55f73d0a88f8869a64cf11809ba7e9e3d`.
- Exact changed files: `browser/safe_operator.py`, `tests/test_w74_browser_security_edges.py`, `tests/test_w74_release_gate.py`, `tests/test_w74_safe_browser_operator.py`, `tests/test_w74_target_fallbacks.py`.
- No storage migration; schema remains **73**.
- Focused W7.4: **52 PASS**.
- Full repository CI: **654 passed, 8 warnings**; `pip check` PASS; compileall PASS; JS N/A.
- Exact implementation workflows: CI #780 / `34884812596`, Reliability/Security #212 / `34884812653`, P3 #180 / `34884812640`, Android #211 / `34884812752`, Package #211 / `34884812643`, iOS #193 / `34884812616` — **6/6 PASS**.

W7.4 security repairs include fresh-observation permit binding, typed origin verification, cross-platform unsafe download-name rejection, restart recovery/no-blind-retry handling, prompt-injection untrusted-content labeling, challenge owner-intervention handling, stable target/overlay/tab/frame checks, secret-field blocking, upload/download confinement, and restricted verified coordinate fallback.

Production, Railway and the existing iPhone qualification service remain unchanged. W6 live OAuth remains blocked/deferred under the owner-approved paid-infrastructure decision.

Still not: physical-device verified, production verified, live OAuth verified, or complete W7.

Exact W7.5 dependency: the W7.4 documentation-only SHA must independently pass all six required workflows before W7.5 begins.
