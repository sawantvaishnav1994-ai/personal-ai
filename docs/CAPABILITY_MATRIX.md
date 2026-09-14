# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses are limited to: COMPLETE, QUALIFICATION, PARTIAL, STUB, PLANNED, BLOCKED. Automated validation is stated explicitly in evidence rather than used to imply live/production qualification.

| Capability | Implementation location | Status | Automated/integration evidence | Deployment/physical evidence | Exact SHA | Known limitation / next action |
| --- | --- | --- | --- | --- | --- | --- |
| Home / AI Core owner surface | `pwa/`, `server/iphone_pwa.py`, deployed UI branch | QUALIFICATION | UI/PWA workflows green | `/iphone/` returned 200 on latest Railway runtime; no full physical UX qualification recorded | `e63f02b...` deployed | preserve frozen visual architecture; complete physical voice/state validation |
| Owner authentication bootstrap | `server/iphone_pwa.py`, `security/owner_access.py` | PARTIAL | owner-access/P3 tests | live deployment includes owner auth foundation | current branches | production/physical recovery and reauth qualification remains |
| Trusted-device registry | `devices/registry.py` | PARTIAL | device tests plus W6 revocation/OAuth invalidation integration | qualification service deployed | W6 `152ef132...` | production durable trust/session qualification remains |
| Per-device scopes | `devices/registry.py`, owner APIs | PARTIAL | owner product tests | not independently physical-qualified | current branch | physical multi-device qualification remains |
| Conversation message persistence | `memory/store.py`, `devices/continuity.py` | PARTIAL | grounded conversation/owner product tests | main runtime has no durable volume | current branch | production data can be lost on redeploy until durable volume gate |
| Conversation reopen / continuation | `devices/continuity.py`, owner UI | PARTIAL | owner product/workflow tests | no full physical restart evidence | current branch | perform persistence/restart/cross-device qualification |
| Memory / Graph / Tree / Detail | `memory/`, `server/owner_product.py`, W4 inspection | PARTIAL | W4 exact-head automated validation | main runtime non-durable | W4/W5 heads | production durability and physical UX verification pending |
| Knowledge ingestion/versioning/provenance | `knowledge/`, W4 APIs | PARTIAL | W4 exact-head automated validation | no production durable qualification | W4/W5 heads | real OCR/provider and durable production proof remain |
| Voice recognition/TTS | `voice/`, `server/iphone_pwa.py` | QUALIFICATION | P3 workflow green | mandatory physical P3 evidence incomplete | current branch | physical P3.2–P3.8 required |
| Activities / audit | memory audit + `security/action_audit.py` | PARTIAL | Trusted Action hash-chain and W6 lifecycle audit tests | production data root non-durable | W6 `152ef132...` | production persistence and broader operational qualification |
| Emergency Stop | `tools/registry.py`, workflow integration | PARTIAL | security/workflow exact-head tests green | durable only where data root persists | W5/W6 | production persistence qualification |
| Trusted Action one-use approval | `security/approvals.py`, `agent/executor.py` | PARTIAL | durable binding/replay tests + W5 exact-head CI | not production durable-qualified | W5 | live connector/session qualification |
| Workflow budgets/concurrency/idempotency | `automation/budget.py`, `automation/engine.py` | PARTIAL | W5 implemented/integrated/automated validated | main runtime has no persistent volume | W5 `8d4e5ea...` | production restart/durable-volume qualification |
| Connector manifest contract | `integrations/contracts.py`, `integrations/registry.py` | PARTIAL | **W6.1 implemented, integrated, automated validated**; manifest validation and stricter-policy tests | not live-provider verified | W6 implementation `baaa7da...`; validated head `152ef132...` | W6.2 + live provider qualification |
| Durable OAuth transaction lifecycle | `integrations/oauth.py`, `integrations/state.py`, vault | PARTIAL | restart, replay, expiry, owner/device/session/security-epoch, concurrent callback, redirect and redaction tests pass | no real OAuth account connected in W6.1 | `152ef132...` | live OAuth qualification when owner credentials are required |
| Connector health/error/retry/rate-limit/pagination | `integrations/gateway.py`, `integrations/state.py` | PARTIAL | 401/403/429/Retry-After/5xx/timeout/malformed response, bounded retry, deadline/cancel and cursor-cycle tests pass | no live provider quota/latency evidence | `152ef132...` | provider-specific operational qualification |
| Connector durable idempotency/recovery | `integrations/state.py`, `integrations/gateway.py` | PARTIAL | duplicate dispatch prevention, durable operation ID and outcome-unknown recovery behavior automated-tested | no live external side-effect recovery exercise | `152ef132...` | qualify real provider uncertain-outcome cases |
| Connector verification / rollback contract | connector manifests, gateway, tools | PARTIAL | W6 provider hooks and safe rollback-availability metadata tested | only implemented provider-specific subset | `152ef132...` | expand to Drive/Sheets/remaining providers; never claim rollback where impossible |
| Connector lifecycle audit | `integrations/lifecycle.py`, `security/action_audit.py` | PARTIAL | redacted tamper-evident lifecycle audit tests | production durability pending | `152ef132...` | live connect/refresh/revoke audit qualification |
| Gmail connector | `integrations/adapters.py`, `tools/integrations.py` | PARTIAL | existing reads preserved; read/search/draft/send/modify/delete-governance and verification hooks automated validated; legacy adapter compatibility repaired | **not live OAuth/provider verified** | W6 `152ef132...` | live Google account read-first qualification; delete remains prohibited by default |
| Google Calendar connector | `integrations/adapters.py`, `tools/integrations.py` | PARTIAL | read/search/create/update/delete governance, provider-ID verification and rollback metadata automated validated | **not live OAuth/provider verified** | W6 `152ef132...` | live read-first then controlled write qualification |
| Apps & Tools connector management | `server/connector_api.py`, `server/connector_ui.py` | PARTIAL | authenticated owner API, trust rejection, safe scopes/health/reconnect/revoke display tests pass; Home unchanged | no live OAuth management exercise | `152ef132...` | live connector owner UX qualification |
| Slack connector | existing adapter + W6 manifest foundation | PARTIAL | common contract/runtime foundations present | not W6.1 live-qualified | `152ef132...` | migrate/qualify provider-specific verification/idempotency as needed |
| Home Assistant connector | existing adapter + W6 manifest foundation | PARTIAL | common contract/runtime foundations present | not W6.1 live-qualified | `152ef132...` | provider-specific operational qualification |
| Google Drive connector | W6 contract foundation only | PLANNED | no W6.1 Drive implementation claim | none | W6.1 | W6.2 read/search/download, then controlled writes |
| Google Sheets connector | W6 contract foundation only | PLANNED | no W6.1 Sheets implementation claim | none | W6.1 | W6.2 read/search, then controlled writes |
| GitHub connector | general integration/tool architecture | PARTIAL | code-level foundations only | no live owner-product qualification recorded | current branches | implement/qualify read-first then controlled write |
| Microsoft 365 connector | connector contract can represent provider but adapter not implemented | PLANNED | manifest/runtime architecture supports future provider | none | W6.1 | future bounded connector batch |
| Computer operator | browser/computer modules + builtins | PARTIAL | tool tests | no full end-to-end safe desktop qualification | current branches | W7 safety/verification/rollback hardening |
| Provider abstraction | `models/router.py` | PARTIAL | model-router/dialogue tests | Gemini deployment evidence exists | current/deployed heads | W8 health/failover/observability hardening |
| Sensitive-data routing | `models/router.py` | PARTIAL | router tests | no live private model | current branch | fail closed until approved private endpoint exists |
| Self-hosted vLLM package | `deploy/self-hosted-model/` | QUALIFICATION | package/verify files exist | no GPU host deployed | current branch | later owner-only GPU prerequisite |
| Backup service | `recovery/backup.py` | PARTIAL | Reliability/Security automated isolated backup/restore passes | no main production durable restore proof | W5/W6 workflows | production durable qualification |
| Production durable storage | storage guard + Railway | BLOCKED | fail-closed/local code exists | main Railway runtime has no persistent volume | deployed `e63f02b...` | attach volume only at approved production gate, then restart/redeploy/backup/restore proof |
| Windows package | packaging workflows | QUALIFICATION | Package Validation #149 green including Windows build | signed physical install not proven | `152ef132...` | signing prerequisite + physical install/update/uninstall |
| Android package | Android companion/instrumentation | QUALIFICATION | Android Instrumentation #149 green | physical install/reconnect not recorded | `152ef132...` | signed release + physical qualification |
| Native iOS distribution | `ios-companion/` | BLOCKED | iOS Companion #131 green | no Apple Developer/TestFlight signed evidence | `152ef132...` | Apple Developer/signing owner blocker |
| Physical P3 qualification | `qualification/`, PR #18 | BLOCKED | P3 iPhone PWA #118 green | mandatory real-device evidence incomplete | `152ef132...` automated | owner must perform/permit physical tests; do not fabricate evidence |

## W6.1 exact evidence

- Direct baseline-parent implementation SHA: `baaa7da38956e97231970c548626a71cde257176`
- Exact validated branch integration SHA: `152ef13217b652121917a890de14e20edb139473`
- Focused W6 tests: **60 PASS**
- CI #569 / `34831726193`: PASS
- Reliability and Security #150 / `34831726152`: PASS
- P3 iPhone PWA #118 / `34831726271`: PASS
- Android Instrumentation #149 / `34831726189`: PASS
- Package Validation #149 / `34831726154`: PASS
- iOS Companion #131 / `34831726233`: PASS

W6.1 is therefore **IMPLEMENTED**, **INTEGRATED**, and **AUTOMATED VALIDATED**. It is deliberately **not LIVE OAUTH VERIFIED**, **not PRODUCTION VERIFIED**, and **not complete W6**, because Drive/Sheets and real-provider qualification remain.
