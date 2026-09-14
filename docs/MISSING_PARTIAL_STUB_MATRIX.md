# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-14

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | main runtime still lacks persistent `/data` | attach only at approved production gate; restart/redeploy/backup/restore proof |
| P0 | W2 | Production durable approvals/actions | PARTIAL | software is durable but production filesystem is not | complete W1 production gate |
| P0 | W3 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute exact P3 protocol on validated candidate |
| P1 | W4 | Real OCR/provider qualification | PARTIAL | bounded OCR contract exists; real provider/docs not qualified | qualify approved OCR path |
| P1 | W5 | Workflow production durability | PARTIAL | W5 automated validated; Railway main volume absent | durable production operational proof |
| P1 | W6.1 | Shared connector contract/OAuth lifecycle | RESOLVED FOR AUTOMATED SCOPE | implemented/integrated/automated validated | freeze unless regression |
| P1 | W6.2 | Google Drive read-first | RESOLVED FOR AUTOMATED SCOPE | list/search/metadata/read/download/export + provenance exact-head validated | live Google account/provider qualification |
| P1 | W6.2 | Google Sheets read-first | RESOLVED FOR AUTOMATED SCOPE | metadata/worksheet/range/batch reads + limits/provenance exact-head validated | live Google account/provider qualification |
| P1 | W6 | Live Google OAuth | BLOCKED FOR LIVE EVIDENCE | real owner consent/account not yet connected by design | run exact read-only qualification package after software gate |
| P1 | W6 | Google multi-connector scope preservation | QUALIFICATION | provider-level Google token is shared; incremental/multi-scope behavior must be proven live | verify granted-scope preservation before accepting live qualification |
| P1 | W6.3 | Controlled Drive writes | PLANNED | intentionally excluded from W6.2 | granular create/upload/update/move/share/delete policies with approval/reauth/idempotency/verification |
| P1 | W6.3 | Controlled Sheets writes | PLANNED | intentionally excluded from W6.2 | update/append/clear/batch/worksheet operations with bounded governance |
| P1 | W6 | Provider-specific live quotas/revocation | PARTIAL | software contracts tested; real provider behavior not qualified | exercise real 401/403/429/quota/refresh/revoke behavior |
| P1 | W7 | Safe Computer Operator | PARTIAL | bounded operator exists but policy surface is incomplete | Trusted Action binding, app/domain/path allowlists, accessibility-first control, clipboard/file safety, verification/recovery |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | implement exact health/failover/correlation/cost telemetry |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no GPU host | later owner infrastructure prerequisite |
| P1 | W9 | Governed proactivity controls | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | perform when signing prerequisites are available |
| P1 | W11 | Complete observability taxonomy | PARTIAL | telemetry foundations exist | health endpoints, correlation, redaction, alert thresholds |
| P0 | W12 | Release readiness | PARTIAL | automated W6.2 is green; production/physical/signing gates remain | do not merge/promote until P0 evidence is complete |

## W6.2 evidence

Implementation SHA: `ecb5e2615d06816e869dd4adb398565bb5c524fa`

Focused suite: **110 PASS**.

Six exact-head workflows passed: CI #579, Reliability and Security #155, P3 iPhone PWA #123, Android Instrumentation #154, Package Validation #154 and iOS Companion #136.

W6.2 resolves the software-side read-only Drive/Sheets items only. It does not resolve live OAuth, controlled writes, production persistence or real-provider operational qualification.
