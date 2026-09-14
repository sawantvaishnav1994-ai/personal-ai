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
| Connector manifest/runtime/OAuth | PARTIAL | W6.1-W6.3 + hosted callback prep + Gmail scope repair automated validated | real Google account not yet qualified | `ae1b3c12...` | isolated live-provider qualification when paid infrastructure resumes |
| Gmail read/search | AUTOMATED VALIDATED / LIVE PENDING | `gmail.readonly` operation/gateway regressions + full CI | not live Google verified | `ae1b3c12...` | harmless live qualification |
| Gmail Draft | AUTOMATED VALIDATED / LIVE PENDING | Draft now requestable only through `gmail.compose`; missing-scope fail-closed regression | not live Google verified | `ae1b3c12...` | harmless draft qualification |
| Gmail Send | AUTOMATED VALIDATED / LIVE PENDING | independent `gmail.send` scope retained; Trusted Action governance | not live Google verified | `ae1b3c12...` | approval-bound live qualification only |
| Google Calendar | PARTIAL | W6 governed read/write tests | not live Google verified | current W6 | harmless live qualification |
| Google Drive read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Google Sheets read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Drive controlled writes | PARTIAL | W6.3 create/upload/rename/content-update exact-head validation | not live Google verified | `95d33a66...` | harmless live qualification |
| Sheets controlled writes | PARTIAL | W6.3 create/bounded RAW update/append exact-head validation | not live Google verified | `95d33a66...` | harmless live qualification |
| Google scope-union/incremental consent | AUTOMATED VALIDATED / LIVE PENDING | provider catalog includes Gmail/Calendar/Drive/Sheets; cumulative union + reduced-scope regression | provider behavior not yet proven live | `ae1b3c12...` | real incremental-consent proof |
| Hosted connector OAuth callback | AUTOMATED VALIDATED / LIVE PENDING | HTTPS redirect override, durable-state routing, no-store callback, redacted evidence harness | isolated Railway service deferred | `f7995810...` | resume after paid infra approval |
| Isolated connector qualification environment | BLOCKED | deployment requirements/code guards prepared | Railway Free plan prevents third service | current | **OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED** |
| Drive/Sheets Knowledge provenance | PARTIAL | W6.2 provenance/NEVER_STORE/version tests | live source ingestion pending | `ecb5e261...` | live source qualification |
| Apps & Tools connector management | PARTIAL | scope/health/read-write/approval/reauth/recovery UI tests | live owner UX pending | W6.3+ | live account UX |
| Slack / Home Assistant | PARTIAL | common contract foundations | provider-specific qualification incomplete | W6.1 | later provider batch |
| GitHub / Microsoft 365 connectors | PARTIAL/PLANNED | architecture supports providers | live/adapter scope incomplete | current | future bounded connector batches |
| Computer operator | PARTIAL | Observe→Understand→Act→Verify + Trusted Action/verification foundations | durable safe operator hardening pending | current | W7.1-W7.6 |
| Provider abstraction | PARTIAL | router/dialogue tests | Gemini temporary | current | W8 health/failover/observability |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current | production volume gate |
| Production durable storage | BLOCKED | fail-closed hosted storage guard exists | main Railway runtime has no volume | deployed head | attach `/data` only at approved production gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current | execute physical protocol |

## Final W6 software evidence

- Hosted OAuth-preparation head: `f79958103c50c0e1b25442ffbf6e58e5b4e65203` — 6/6 required workflows PASS.
- Gmail Draft scope-repair implementation head: `ae1b3c12ff82785b1f8cefe1bcbc6201e88b08bc`.
- Full repository suite on scope-repair head: **446 PASS**.
- Exact-head workflows: CI #597, Reliability/Security #164, P3 #132, Android #163, Package #163, iOS #145 — **all PASS**.

W6 software is **IMPLEMENTED**, **INTEGRATED**, and **AUTOMATED VALIDATED** for the approved connector scope. It remains **LIVE OAUTH QUALIFICATION PENDING** and **PRODUCTION QUALIFICATION PENDING**. The isolated Railway qualification service is not failed; it is **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED**.
