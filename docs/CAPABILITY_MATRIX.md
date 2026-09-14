# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses describe implementation/qualification honestly; automated validation does not imply live-provider or production proof.

| Capability | Status | Automated evidence | Live/production evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | PARTIAL | binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | PARTIAL | automated tests | main runtime non-durable | current branch | production restart proof |
| Memory / Knowledge | PARTIAL | W4 + W6 provenance tests | durable/live-source qualification pending | current branch | production/live qualification |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth tests | live operational proof partial | W5/W6 | live connectors/sessions |
| Workflow budgets/concurrency/idempotency | PARTIAL | W5 automated validated | production volume absent | W5 | production durable qualification |
| Connector manifest/runtime/OAuth | PARTIAL | W6.1 automated validated | real accounts not yet qualified | W6.1+ | live provider qualification |
| Gmail / Google Calendar | PARTIAL | governed W6.1 tests | not live OAuth/provider verified | W6.1 | real Google qualification |
| Google Drive read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Google Sheets read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Drive controlled writes | PARTIAL | **W6.3 implemented/integrated/automated validated**: create/upload/rename/content-update, scope/precondition/idempotency/verification/recovery tests | not live Google verified | `95d33a66...` | harmless live qualification |
| Sheets controlled writes | PARTIAL | **W6.3 implemented/integrated/automated validated**: spreadsheet create, bounded RAW update/append, concurrency/readback tests | not live Google verified | `95d33a66...` | harmless live qualification |
| Google scope-union/incremental consent | PARTIAL | W6.3 confirmed-union + reduced-scope regression tests | provider behavior not yet proven live | `95d33a66...` | real incremental-consent proof |
| Drive/Sheets Knowledge provenance | PARTIAL | W6.2 provenance/NEVER_STORE/version tests | live source ingestion pending | `ecb5e261...` | live source qualification |
| Apps & Tools connector management | PARTIAL | scope/health/read-write/approval/reauth/recovery UI tests | live owner UX pending | W6.3 | live account UX |
| Slack / Home Assistant | PARTIAL | common contract foundations | provider-specific qualification incomplete | W6.1 | later provider batch |
| GitHub / Microsoft 365 connectors | PARTIAL/PLANNED | architecture supports providers | live/adapter scope incomplete | current | future bounded connector batches |
| Computer operator | PARTIAL | Observe->Understand->Act->Verify + verification/rollback foundations | safe physical qualification absent | current | W7 hardening after W6 live gate |
| Provider abstraction | PARTIAL | router/dialogue tests | Gemini temporary | current | W8 health/failover/observability |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current workflows | production volume gate |
| Production durable storage | BLOCKED | code guards exist | main Railway runtime has no volume | deployed head | attach `/data` only at approved gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current | execute physical protocol |

## W6.3 exact evidence

- Baseline: `6310709f65534dba79d89cccd8ea94c6a4c9d765`
- Final tree: `e879cee54f019ca2f98c8b90564fd2681bf5cab6`
- Implementation: `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254`
- Focused W6 suite: **131 PASS**
- CI #585 / `34843634899`: PASS
- Reliability and Security #158 / `34843634900`: PASS
- P3 iPhone PWA #126 / `34843634890`: PASS
- Android Instrumentation #157 / `34843634957`: PASS
- Package Validation #157 / `34843634972`: PASS
- iOS Companion #139 / `34843634905`: PASS

W6.3 is **IMPLEMENTED**, **INTEGRATED**, and **AUTOMATED VALIDATED**. It is **not LIVE OAUTH VERIFIED**, **not PRODUCTION VERIFIED**, and W6 is not operationally complete until real Google qualification is recorded.
