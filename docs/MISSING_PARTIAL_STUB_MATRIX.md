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
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | W7.1 exact-head validation complete | frozen automated baseline |
| P1 | W7.2 | Observation/application context + sensitive evidence | RESOLVED FOR AUTOMATED SCOPE | implementation `78ba7e7f...`; **85 focused + 557 full PASS**; coordinate-space v2; exact implementation **6/6 PASS** | complete documentation-head 6/6, then freeze automated scope |
| P1 | W7.2 | Physical desktop/browser observation qualification | QUALIFICATION PENDING | automated evidence is not real physical-device proof | execute later physical Windows/browser protocol; do not misclassify automated proof |
| P1 | W7.3 | Allowlists and data-safety policies | NEXT AFTER W7.2 DOC GATE | app/domain/path/clipboard/secret/destination policy incomplete | begin only after W7.2 documentation head is 6/6 green |
| P1 | W7.4 | Browser operator | PENDING | unified allowlist/policy/verification operator incomplete | begin after W7.3 |
| P1 | W7.5 | Desktop and file operator | PARTIAL | bounded desktop actions exist; approved app/file sandbox surface incomplete | begin after W7.4 |
| P1 | W7.6 | Verification and recovery | PARTIAL | W7.1 durable transaction core + W7.2 observation safety are validated; complete end-to-end qualification remains | complete after W7.3-W7.5 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated work |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no approved GPU host | later infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6/W7.1/W7.2 software gates green; remaining W7/live Google/production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## Final W7.2 implementation evidence

- W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`.
- Recovered WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`.
- Final implementation: `78ba7e7f9e1587fe5a68d3923f15d0425ef81715`.
- Focused W7.2: **85 PASS**.
- Full repository CI: **557 passed, 8 warnings**.
- Exact implementation workflows: CI #717 / `34873006958`, Reliability/Security #202 / `34873006929`, P3 #170 / `34873006957`, Android #201 / `34873006928`, Package #201 / `34873006956`, iOS #183 / `34873007037` — **all PASS**.

W7.2 classification after implementation gate: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

Still not: **PHYSICAL-DEVICE VERIFIED**, **PRODUCTION VERIFIED**, or **COMPLETE W7**.

Production, Railway and existing iPhone qualification service remain unchanged. W6 live OAuth remains deferred under the owner-approved paid-infrastructure decision.

The next software continuation is W7.3 only after the W7.2 documentation-only head independently passes the same 6/6 workflow gate.
