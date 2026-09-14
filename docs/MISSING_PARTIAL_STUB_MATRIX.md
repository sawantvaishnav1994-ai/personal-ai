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
| P1 | W6 | Gmail Draft OAuth scope defect | RESOLVED FOR AUTOMATED SCOPE | runtime admits `gmail.compose` from non-prohibited operation requirements; full access excluded; 446 full-repo tests + 6/6 workflows | live harmless Draft qualification later |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | Railway Free plan rejects third service; owner explicitly postponed Hobby purchase | preserve checkpoint and resume only after future owner approval |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected without isolated durable service | execute prepared qualification package after isolated service exists |
| P1 | W6 | Multi-connector scope-union operational proof | QUALIFICATION | software union/reduction behavior automated validated; Google behavior must be proven live | incremental Gmail/Calendar/Drive/Sheets consent evidence later |
| P1 | W6 | Token refresh/revoke/quota operational proof | PARTIAL | software contracts tested only | live refresh/expiry/401/403/429/reconnect/revoke later |
| P1 | W6 | Destructive/share/structural Google operations | PROHIBITED/NOT IMPLEMENTED | deliberately outside approved scope | keep disabled unless separately designed/approved |
| P1 | W7 | Durable Safe Computer Operator | IN PROGRESS / NEXT | bounded operator exists but durable operator transaction/policy surface incomplete | implement W7.1 then W7.2-W7.6 in bounded exact-head batches |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | begin after W7 automated validation |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no GPU host | later owner infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls after W8 |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | harden unsigned artifacts; sign when owner prerequisites exist |
| P1 | W12 | Release readiness | PARTIAL | W6 software green; live Google/production/physical/signing gates remain | continue independent engineering; no merge/promotion yet |

## Current W6 software evidence

- W6.3 controlled-write implementation: `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254`.
- Hosted OAuth qualification preparation: `f79958103c50c0e1b25442ffbf6e58e5b4e65203`, all six required workflows PASS.
- Gmail Draft scope-repair implementation: `ae1b3c12ff82785b1f8cefe1bcbc6201e88b08bc`.
- Full repository CI on Gmail scope-repair head: **446 passed, 7 warnings**.
- Scope-repair workflows: CI #597, Reliability/Security #164, P3 #132, Android #163, Package #163, iOS #145 — all PASS.

Final W6 software classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**.
