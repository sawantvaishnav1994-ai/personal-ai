# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses describe implementation/qualification honestly; automated validation does not imply live-provider, physical-device, or production proof.

| Capability | Status | Automated evidence | Live/production evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | PARTIAL | binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | PARTIAL | automated tests | main runtime non-durable | current branch | production restart proof |
| Memory / Knowledge | PARTIAL | W4 + W6 provenance tests | durable/live-source qualification pending | current branch | production/live qualification |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth tests; W7.1/W7.2 operator binding reuses it | live operational proof partial | W5/W7.2 | W7.3-W7.6 + physical qualification |
| Workflow budgets/concurrency/idempotency | PARTIAL | W5 automated validated | production volume absent | W5 | production durable qualification |
| Connector manifest/runtime/OAuth | PARTIAL | W6.1-W6.3 + hosted callback prep + Gmail scope repair automated validated | real Google account not yet qualified | `ae1b3c12...` | isolated live-provider qualification when paid infrastructure resumes |
| Gmail read/search | AUTOMATED VALIDATED / LIVE PENDING | `gmail.readonly` operation/gateway regressions + full CI | not live Google verified | `ae1b3c12...` | harmless live qualification |
| Gmail Draft | AUTOMATED VALIDATED / LIVE PENDING | Draft requestable only through `gmail.compose`; missing-scope fail-closed regression | not live Google verified | `ae1b3c12...` | harmless draft qualification |
| Gmail Send | AUTOMATED VALIDATED / LIVE PENDING | independent `gmail.send` scope retained; Trusted Action governance | not live Google verified | `ae1b3c12...` | approval-bound live qualification only |
| Google Calendar | PARTIAL | W6 governed read/write tests | not live Google verified | current W6 | harmless live qualification |
| Google Drive read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Google Sheets read-first | PARTIAL | W6.2 exact-head automated validated | not live Google verified | `ecb5e261...` | real Google qualification |
| Drive controlled writes | PARTIAL | W6.3 create/upload/rename/content-update exact-head validation | not live Google verified | `95d33a66...` | harmless live qualification |
| Sheets controlled writes | PARTIAL | W6.3 create/bounded RAW update/append exact-head validation | not live Google verified | `95d33a66...` | harmless live qualification |
| Google scope-union/incremental consent | AUTOMATED VALIDATED / LIVE PENDING | provider catalog includes Gmail/Calendar/Drive/Sheets; cumulative union + reduced-scope regression | provider behavior not yet proven live | `ae1b3c12...` | real incremental-consent proof |
| Hosted connector OAuth callback | AUTOMATED VALIDATED / LIVE PENDING | HTTPS redirect override, durable-state routing, no-store callback, redacted evidence harness | isolated Railway service deferred | `f7995810...` | resume after paid infra approval |
| Connector qualification preflight | AUTOMATED VALIDATED / LIVE PENDING | exact callback/routes, secret presence, `/data` mount proof and fail-closed startup artifacts; 6/6 workflows | paid isolated service not created | `0092051e...` | deploy only after future owner approval |
| Isolated connector qualification environment | BLOCKED | deployment requirements/code guards prepared | Railway Free plan prevents third service | current | **OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED** |
| Drive/Sheets Knowledge provenance | PARTIAL | W6.2 provenance/NEVER_STORE/version tests | live source ingestion pending | `ecb5e261...` | live source qualification |
| Apps & Tools connector management | PARTIAL | scope/health/read-write/approval/reauth/recovery UI tests | live owner UX pending | W6.3+ | live account UX |
| Slack / Home Assistant | PARTIAL | common contract foundations | provider-specific qualification incomplete | W6.1 | later provider batch |
| GitHub / Microsoft 365 connectors | PARTIAL/PLANNED | architecture supports providers | live/adapter scope incomplete | current | future bounded connector batches |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable SQLite operator transactions/actions/audit, trusted owner/device/session/epoch/conversation binding, idempotency, restart recovery, cancellation/deadline/Emergency Stop, redaction; full repo 471 PASS + 6/6 workflows | physical desktop/browser qualification not performed | `fe52b6ff...` | frozen automated baseline |
| W7.2 Observation/Application Context Safety | AUTOMATED VALIDATED | 58 focused W7.2 cases; full repo 530 PASS; exact-head 6/6 workflows; typed coordinate spaces; browser-native masking; sanitized evidence guard; app/window/browser/tab/origin/target freshness binding | physical desktop/browser and production qualification not performed | `3d9f5a4f...` | documentation-head 6/6, then W7.3 |
| Computer operator overall | PARTIAL | W7.1 durable core + W7.2 exact-head observation/evidence safety validated | W7.3-W7.6 and physical safe-operation evidence pending | `3d9f5a4f...` | continue bounded W7 batches after docs gate |
| Provider abstraction | PARTIAL | router/dialogue tests | Gemini temporary | current | W8 health/failover/observability after W7 |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current | production volume gate |
| Production durable storage | BLOCKED | fail-closed hosted storage guard exists | main Railway runtime has no volume | deployed head | attach `/data` only at approved production gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current | execute physical protocol |

## Final W6 software evidence

- Hosted OAuth-preparation head: `f79958103c50c0e1b25442ffbf6e58e5b4e65203` — 6/6 required workflows PASS.
- Gmail Draft scope-repair implementation head: `ae1b3c12ff82785b1f8cefe1bcbc6201e88b08bc` — full repository 446 PASS; 6/6 required workflows PASS.
- Qualification-preflight artifacts head: `0092051edff451476a032da3934f72d459a75ae1` — 6/6 required workflows PASS.

W6 software is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**. The isolated Railway qualification service is **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED**.

## W7.1 exact evidence

- Validated W7.1 baseline: `0092051edff451476a032da3934f72d459a75ae1`.
- Final W7.1 implementation: `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`.
- Full repository: **471 passed, 7 warnings**.
- Required implementation workflows: 6/6 PASS.

## W7.2 exact implementation evidence

- Validated W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`.
- Recovered W7.2 WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`.
- Final implementation: `3d9f5a4f21cf59307758f261d6291a4b7a36003b`.
- Focused W7.2 coverage: **58 PASS**.
- Full repository: **530 passed, 7 warnings**.
- CI #700 / `34869967548`: PASS.
- Reliability and Security #197 / `34869967279`: PASS.
- P3 iPhone PWA #165 / `34869967422`: PASS.
- Android Instrumentation #196 / `34869967534`: PASS.
- Package Validation #196 / `34869967417`: PASS.
- iOS Companion #178 / `34869967290`: PASS.

W7.2 software implementation is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at the implementation-head gate. It is not physical-device verified or production verified, and W7 overall remains partial. The documentation-only head must independently pass the same six workflows before W7.3 begins.
