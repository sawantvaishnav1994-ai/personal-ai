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
| P1 | W6.3 | Controlled Drive create/upload/rename/content update | RESOLVED FOR AUTOMATED SCOPE | 131 focused + exact-head six-workflow validation | harmless live Google qualification |
| P1 | W6.3 | Controlled Sheets create/update/append | RESOLVED FOR AUTOMATED SCOPE | RAW/concurrency/verification/recovery exact-head validated | harmless live Google qualification |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED FOR LIVE EVIDENCE | owner consent/account intentionally not connected during software work | run prepared real-account qualification package |
| P1 | W6 | Multi-connector scope-union operational proof | QUALIFICATION | software preserves/detects scope sets; Google behavior must be proven live | incremental Gmail/Calendar/Drive/Sheets consent evidence |
| P1 | W6 | Token refresh/revoke/quota operational proof | PARTIAL | software contracts tested only | exercise live refresh/expiry/401/403/429/reconnect/revoke |
| P1 | W6 | Destructive/share/structural Google operations | PROHIBITED/NOT IMPLEMENTED | deliberately outside W6.3 | keep disabled; design separately only if later approved |
| P1 | W7 | Safe Computer Operator | PARTIAL | bounded operator exists but unified safety surface incomplete | Trusted Action binding, app/window identity, allowlists, accessibility-first, clipboard/file safety, verification/recovery |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | implement health/failover/correlation/cost telemetry |
| P1 | W8 | Self-hosted private endpoint | BLOCKED | no GPU host | later owner infrastructure prerequisite |
| P1 | W9 | Governed proactivity | PARTIAL | engine exists | quiet hours/frequency/why/suggestion-vs-action controls |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | perform when signing prerequisites are available |
| P1 | W11 | Complete observability taxonomy | PARTIAL | telemetry foundations exist | subsystem health/correlation/redaction/alerts |
| P0 | W12 | Release readiness | PARTIAL | W6.3 software automated green; live Google/production/physical/signing gates remain | do not merge/promote until evidence-complete |

## W6.3 evidence

- Baseline: `6310709f65534dba79d89cccd8ea94c6a4c9d765`
- Implementation: `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254`
- Final tree: `e879cee54f019ca2f98c8b90564fd2681bf5cab6`
- Focused suite: **131 PASS**
- Six exact-head workflows: CI #585, Reliability and Security #158, P3 iPhone PWA #126, Android Instrumentation #157, Package Validation #157, iOS Companion #139 — all PASS.

W6.3 resolves only the software-side controlled-write batch. W6 remains operationally incomplete until real Google OAuth/account/provider evidence is recorded. Production persistence and physical qualification remain separate release gates.
