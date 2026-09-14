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
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | implementation `fe52b6ff...`; durable Trusted Action binding/recovery/idempotency; 471 full-repo tests; 6/6 workflows | freeze after docs-head validation |
| P1 | W7.2 | Observation and application context | NEXT | active app/window/browser/domain/accessibility/DOM/freshness surface not complete | implement bounded W7.2 candidate |
| P1 | W7.3 | Allowlists and data-safety policies | PENDING | app/domain/path/clipboard/secret/destination policy incomplete | begin after W7.2 automated validation |
| P1 | W7.4 | Browser operator | PENDING | browser primitives exist but unified policy/verification operator incomplete | begin after W7.3 |
| P1 | W7.5 | Desktop and file operator | PARTIAL | bounded desktop actions exist; approved app/file sandbox surface incomplete | begin after W7.4 |
| P1 | W7.6 | Verification and recovery | PARTIAL | W7.1 establishes durable transaction/recovery core; end-to-end operator qualification incomplete | complete after W7.2-W7.5 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated validation |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no GPU host | later owner infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when owner prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6 software + W7.1 automated green; live Google/remaining W7/production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## W7.1 current evidence

- Validated baseline: `0092051edff451476a032da3934f72d459a75ae1`.
- Final implementation: `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`.
- Full repository CI: **471 passed, 7 warnings**.
- Required workflows: CI #645, Reliability/Security #188, P3 #156, Android #187, Package #187, iOS #169 — all PASS.

W7.1 classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**. W7 overall remains partial until W7.2-W7.6 and physical safe-operator qualification are complete.

Final W6 software classification remains: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**.
