# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-14

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | main runtime still lacks persistent `/data` | attach only at approved production gate; restart/redeploy/backup/restore proof |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute exact physical protocol |
| P1 | W4 | Real OCR/provider qualification | PARTIAL | bounded OCR contract exists; real provider/docs not qualified | qualify approved OCR path |
| P1 | W5 | Workflow production durability | PARTIAL | automated validated; Railway main volume absent | durable production operational proof |
| P1 | W6.1 | Shared connector contract/OAuth lifecycle | RESOLVED FOR AUTOMATED SCOPE | exact-head automated validated | freeze unless regression |
| P1 | W6.2 | Drive/Sheets read-first + Knowledge provenance | RESOLVED FOR AUTOMATED SCOPE | exact-head automated validated | real Google/source qualification |
| P1 | W6.3 | Controlled Drive/Sheets writes | RESOLVED FOR AUTOMATED SCOPE | exact-head automated validated | harmless live Google qualification |
| P1 | W6 | Hosted OAuth callback/evidence preparation | RESOLVED FOR AUTOMATED SCOPE | exact head `f7995810...`, 6/6 workflows | retain; deploy only in isolated qualification service |
| P1 | W6 | Gmail Draft OAuth scope defect | RESOLVED FOR AUTOMATED SCOPE | `gmail.compose` request path fixed; full access excluded; 446 full-repo tests + 6/6 workflows | live harmless Draft qualification later |
| P1 | W6 | Qualification deployment/preflight artifacts | RESOLVED FOR AUTOMATED SCOPE | fail-closed callback/secret/storage/startup/runbook prep on `0092051e...`, 6/6 workflows | use only when isolated paid service is approved |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | Railway Free plan rejects third service; owner explicitly postponed Hobby purchase | preserve checkpoint and resume only after future owner approval |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected without isolated durable service | execute prepared qualification package after isolated service exists |
| P1 | W6 | Multi-connector scope-union operational proof | QUALIFICATION | software union/reduction behavior automated validated; Google behavior must be proven live | incremental Gmail/Calendar/Drive/Sheets consent evidence later |
| P1 | W6 | Token refresh/revoke/quota operational proof | PARTIAL | software contracts tested only | live refresh/expiry/401/403/429/reconnect/revoke later |
| P1 | W6 | Destructive/share/structural Google operations | PROHIBITED/NOT IMPLEMENTED | deliberately outside approved scope | keep disabled unless separately designed/approved |
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | implementation `fe52b6ff...`; durable Trusted Action binding/recovery/idempotency; 471 full-repo tests; 6/6 workflows | frozen automated baseline |
| P1 | W7.2 | Observation and application context | RESOLVED FOR AUTOMATED SCOPE | implementation `3d9f5a4f...`; 58 focused + 530 full tests; typed coordinate/redaction evidence safety; 6/6 implementation workflows | complete documentation-head 6/6 gate; then freeze automated scope |
| P1 | W7.2 | Physical desktop/browser observation qualification | QUALIFICATION PENDING | automated identity/redaction/context-change evidence is not physical-device proof | execute later physical Windows/browser protocol; do not block W7.3 software work after docs gate |
| P1 | W7.3 | Allowlists and data-safety policies | NEXT AFTER W7.2 DOC GATE | app/domain/path/clipboard/secret/destination policy incomplete | begin only after W7.2 documentation-only head is 6/6 green |
| P1 | W7.4 | Browser operator | PENDING | browser primitives exist but unified policy/verification operator incomplete | begin after W7.3 |
| P1 | W7.5 | Desktop and file operator | PARTIAL | bounded desktop actions exist; approved app/file sandbox surface incomplete | begin after W7.4 |
| P1 | W7.6 | Verification and recovery | PARTIAL | W7.1 establishes durable transaction/recovery core and W7.2 observation safety; end-to-end operator qualification incomplete | complete after W7.3-W7.5 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated validation |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no GPU host | later owner infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when owner prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6 + W7.1 + W7.2 software gates green; remaining W7/live Google/production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## W7.1 current evidence

- Final implementation: `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`.
- Full repository CI: **471 passed, 7 warnings**.
- Required workflows: 6/6 PASS.

## W7.2 implementation evidence

- Validated W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`.
- Recovered WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`.
- Final implementation: `3d9f5a4f21cf59307758f261d6291a4b7a36003b`.
- Focused W7.2: **58 PASS**.
- Full repository CI: **530 passed, 7 warnings**.
- Exact implementation workflows: CI #700 / `34869967548`, Reliability/Security #197 / `34869967279`, P3 #165 / `34869967422`, Android #196 / `34869967534`, Package #196 / `34869967417`, iOS #178 / `34869967290` — all PASS.

W7.2 implementation classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**. It remains **not PHYSICAL-DEVICE VERIFIED** and **not PRODUCTION VERIFIED**. W7 overall remains partial.

Final W6 software classification remains **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**.
