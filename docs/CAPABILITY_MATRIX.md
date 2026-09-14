# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses describe implementation/qualification honestly; automated validation does not imply live-provider or production proof.

| Capability | Implementation location | Status | Evidence | Deployment/live evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| Home / AI Core | `pwa/`, `server/iphone_pwa.py` | QUALIFICATION | automated UI/PWA green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | `devices/`, security session code | PARTIAL | automated binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | `memory/`, `devices/continuity.py` | PARTIAL | automated tests | main runtime non-durable | current branch | durable production restart proof |
| Memory / Graph / Tree / Detail | `memory/` | PARTIAL | W4 automated validation | production durability pending | W4+ | durable/physical qualification |
| Knowledge/versioning/provenance | `knowledge/` | PARTIAL | W4 + W6.2 connector-ingestion tests | live source/provider pending | W6.2 | real provider + durable production |
| Voice / interruption | `voice/`, PWA | QUALIFICATION | P3 automation green | physical P3 incomplete | current branch | physical P3 |
| Trusted Action Core | `security/approvals.py`, `tools/registry.py` | PARTIAL | durable binding/replay/epoch tests | live operational proof partial | W5/W6 | live sessions/connectors |
| Workflow budgets/concurrency/idempotency | `automation/` | PARTIAL | W5 implemented/integrated/automated validated | production volume absent | W5 | production restart qualification |
| Connector manifest/runtime | `integrations/contracts.py`, `gateway.py`, `state.py` | PARTIAL | W6.1 automated validated | live provider not verified | W6.1 | live operational qualification |
| Durable OAuth transactions | `integrations/oauth.py`, `state.py`, vault | PARTIAL | replay/expiry/restart/binding tests | real account not connected | W6.1 | live Google qualification |
| Gmail | `integrations/adapters.py`, tools | PARTIAL | governed W6.1 tests | not live-OAuth verified | W6.1 | live read-first qualification |
| Google Calendar | adapters/tools | PARTIAL | governed W6.1 tests | not live-OAuth verified | W6.1 | live qualification |
| Google Drive read-first | `integrations/google_read.py`, `tools/google_read.py` | PARTIAL | **W6.2 implemented/integrated/automated validated**; list/search/metadata/read/download/export | not live Google verified | `ecb5e261...` | live read-only qualification then W6.3 writes |
| Google Sheets read-first | `integrations/google_read.py`, Knowledge bridge | PARTIAL | **W6.2 implemented/integrated/automated validated**; metadata/worksheets/range/batch reads | not live Google verified | `ecb5e261...` | live read-only qualification then W6.3 writes |
| Drive/Sheets Knowledge provenance | `integrations/knowledge_bridge.py`, `server/connector_knowledge_api.py` | PARTIAL | explicit approval, provenance, NEVER_STORE, routing and lineage tests | live source ingestion not qualified | `ecb5e261...` | live source qualification |
| Apps & Tools connector management | `server/connector_api.py`, `connector_ui.py` | PARTIAL | scopes/health/read-only/reconnect/revoke tests | live management UX not qualified | `ecb5e261...` | live account UX |
| Slack / Home Assistant | existing adapters + W6 contract | PARTIAL | common contract foundations | provider-specific qualification incomplete | W6.1 | later provider batch |
| GitHub connector | general integration foundation | PARTIAL | code foundations | no live owner-product qualification | current branch | read-first then controlled writes |
| Microsoft 365 connector | manifest architecture only | PLANNED | contract can represent provider | none | W6.1 | future connector batch |
| Computer operator | `vision/computer_intelligence.py`, `desktop/`, browser tools | PARTIAL | Observe->Understand->Act->Verify, cancellation and rollback foundations | full safe desktop/browser qualification absent | current branch | W7 hardening |
| Provider abstraction | `models/router.py` | PARTIAL | router/dialogue tests | Gemini temporary | current branch | W8 health/failover/observability |
| Backup/recovery | `recovery/backup.py` | PARTIAL | isolated encrypted restore workflow passes | production durable restore absent | current workflows | production volume gate |
| Production durable storage | Railway + storage guard | BLOCKED | code guards exist | main runtime has no persistent volume | deployed head | attach `/data` only at approved gate |
| Windows package | packaging | QUALIFICATION | Package Validation #154 green | signed physical install absent | W6.2 | signing/physical qualification |
| Android package | Android companion | QUALIFICATION | Android Instrumentation #154 green | physical install/reconnect absent | W6.2 | signed physical qualification |
| Native iOS distribution | iOS companion | BLOCKED | iOS Companion #136 green | Apple signing/TestFlight unavailable | W6.2 | owner signing prerequisite |
| Physical P3 | qualification/PWA | BLOCKED | P3 #123 green automated | real-device evidence incomplete | W6.2 automated | execute physical protocol |

## W6.2 exact evidence

- Baseline: `a828cca77bbb910306641fabcc0f8211e3e65e19`
- Implementation: `ecb5e2615d06816e869dd4adb398565bb5c524fa`
- Focused tests: **110 PASS**
- CI #579 / `34836268100`: PASS
- Reliability and Security #155 / `34836268108`: PASS
- P3 iPhone PWA #123 / `34836268173`: PASS
- Android Instrumentation #154 / `34836268200`: PASS
- Package Validation #154 / `34836268171`: PASS
- iOS Companion #136 / `34836268106`: PASS

W6.2 is **IMPLEMENTED**, **INTEGRATED**, and **AUTOMATED VALIDATED**. It is **not LIVE OAUTH VERIFIED**, **not PRODUCTION VERIFIED**, and does not enable Drive/Sheets writes.
