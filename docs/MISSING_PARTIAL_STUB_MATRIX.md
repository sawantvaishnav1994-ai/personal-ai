# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-14

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | main runtime still lacks approved persistent `/data` | attach only at approved production gate; restart/redeploy/backup/restore proof |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute exact physical protocol |
| P1 | W4 | Real OCR/provider qualification | PARTIAL | bounded OCR contract exists; real provider/docs not qualified | qualify approved OCR path |
| P1 | W5 | Workflow production durability | PARTIAL | automated validated; main production volume absent | durable production operational proof |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | owner postponed paid isolated infrastructure | preserve checkpoint and resume only after future owner approval |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected without isolated durable service | execute prepared package only after owner-approved service exists |
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | exact-head validation complete | frozen automated baseline |
| P1 | W7.2 | Observation/application context + sensitive evidence | RESOLVED FOR AUTOMATED SCOPE | implementation and documentation automated gates complete | frozen automated baseline; physical qualification remains separate |
| P1 | W7.3 | Allowlists and data-safety policies | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | implementation `893db9ef...`; 45 committed focused PASS; 602 full PASS, 8 warnings; implementation workflows 6/6 PASS | complete documentation-only exact-head 6/6, then freeze W7.3 |
| P1 | W7.3 | Physical application/domain/path/clipboard qualification | QUALIFICATION PENDING | automated policy evidence is not physical Windows/browser/filesystem proof | later physical qualification; do not misclassify automated evidence |
| P1 | W7.4 | Safe Browser Operator | BLOCKED ON W7.3 DOC GATE | must consume final frozen W7.3 policy authority; no W7.4 code may share the W7.3 docs commit | begin only from final W7.3 documentation SHA after docs 6/6 |
| P1 | W7.5 | Desktop and file operator | PARTIAL | bounded desktop actions exist; approved app/file execution surface incomplete | begin after W7.4 automated validation |
| P1 | W7.6 | Verification and recovery | PARTIAL | W7.1-W7.3 foundations validated at software level; complete end-to-end qualification remains | complete after W7.4-W7.5 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated work |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no approved GPU host | later infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, remaining W7, production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## W7.3 exact evidence

- Baseline: `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- Implementation: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.
- Changed files: `security/policy_gateway.py`, `security/policy_store.py`, `security/policy_targets.py`, `tests/test_w73_policy.py`, `tests/test_w73_binding_controls.py`, `tests/test_w73_adversarial_edges.py`, `tools/registry.py`, `ui/settings_panel.py`.
- Policy schema: **73**; fresh DB, additive 72→73 migration, restart and repeated initialization covered.
- Focused committed W7.3: **45 PASS**.
- Supplementary adversarial scratch: **81 PASS — non-release supplementary evidence**.
- Full repository CI: **602 passed, 8 warnings**.
- Exact implementation workflows: CI #742 / `34879964954`, Reliability/Security #207 / `34879964723`, P3 #175 / `34879964821`, Android #206 / `34879964875`, Package #206 / `34879964783`, iOS #188 / `34879964725` — **6/6 PASS**.

Security repairs include fail-closed default deny, permit SQL repair, approval replay/policy-change invalidation, application spoof/replacement resistance, domain/IDN/redirect/private-network hardening, canonical filesystem and mounted/reparse/UNC/ADS/MIME/size hardening, clipboard secret/race controls, audit redaction and strong approval/reauthentication for high-risk side effects.

Production, Railway and the existing iPhone qualification service remain unchanged. W6 live OAuth remains blocked/deferred under the owner-approved paid-infrastructure decision.

Still not: physical-device verified, production verified, live OAuth verified, or complete W7.

Exact W7.4 dependency: final W7.3 documentation-only SHA must independently pass all six required workflows before W7.4 begins.