# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses are limited to: COMPLETE, QUALIFICATION, PARTIAL, STUB, PLANNED, BLOCKED.

| Capability | Implementation location | Status | Automated/integration evidence | Deployment/physical evidence | Exact SHA | Known limitation / next action |
| --- | --- | --- | --- | --- | --- | --- |
| Home / AI Core owner surface | `pwa/`, `server/iphone_pwa.py`, deployed UI branch | QUALIFICATION | UI/PWA workflows green | `/iphone/` returned 200 on latest Railway runtime; no full physical UX qualification recorded | `e63f02b...` deployed | preserve frozen visual architecture; complete physical voice/state validation |
| Owner authentication bootstrap | `server/iphone_pwa.py`, `security/owner_access.py` | PARTIAL | P3/owner-access tests exist | live deployment includes owner auth variables | PR21 `a8a6d61...`; deployed branch differs | full recovery/re-auth/security-epoch design not yet complete |
| Google owner sign-in | deployed UI branch + owner auth code | QUALIFICATION | exact-head UI CI green | deployment commit history records validated Google owner sign-in | `e63f02b...` | connected API redacts variable values; owner/device real-world tests still required |
| Trusted-device registry | `devices/registry.py` | PARTIAL | device tests and P3 workflow green | qualification service deployed | `a8a6d61...` | no security epoch/session binding; lost-device/global session semantics require hardening |
| Per-device scopes | `devices/registry.py`, `server/owner_product.py` | PARTIAL | owner product tests | not independently physical-qualified | `a8a6d61...` | scopes exist; complete session and critical-action binding |
| Conversation message persistence | `memory/store.py`, `devices/continuity.py` | PARTIAL | grounded conversation/owner product tests | main runtime has no durable volume | `a8a6d61...` | code persists to SQLite but production data can be lost on redeploy |
| Conversation reopen / continuation | `devices/continuity.py`, owner UI | PARTIAL | owner product and workflow tests | no physical refresh/browser-close/server-restart evidence | `a8a6d61...` | perform persistence/restart/cross-device qualification |
| Memory store | `memory/store.py`, `memory/second_brain.py` | PARTIAL | memory/grounding tests present | no durable main-runtime volume | `a8a6d61...` | add NEVER_STORE/retention policy hardening and production persistence evidence |
| Memory Graph | `memory/store.py`, `server/owner_product.py` | PARTIAL | API tests included in owner product suite | owner UI exists | `a8a6d61...` | production durability and physical UX verification pending |
| Memory Tree | `memory/store.py`, `server/owner_product.py` | PARTIAL | API tests | owner UI exists | `a8a6d61...` | production durability pending |
| Memory Detail/correction/deletion/export | `memory/store.py`, `memory/second_brain.py`, `server/owner_product.py` | PARTIAL | owner product/memory tests | no restart/redeploy evidence | `a8a6d61...` | verify deletion/export/retention on durable production storage |
| Memory contradiction handling | `memory/store.py`, `memory/second_brain.py` | PARTIAL | conflict/supersede code exists | no operational qualification | `a8a6d61...` | strengthen provenance, verification and owner-correction flows |
| Knowledge ingestion | `knowledge/store.py` | PARTIAL | `tests/test_knowledge.py` | no durable main-runtime volume | `a8a6d61...` | text extraction supports PDF/DOCX/XLSX etc.; OCR/image ingestion not implemented here |
| Knowledge citations/provenance | `knowledge/store.py`, `agent/executor.py` | PARTIAL | grounded conversation tests | no production persistence evidence | `a8a6d61...` | verify citations end-to-end on durable deployment |
| Knowledge access controls | `knowledge/store.py`, `server/owner_product.py` | PARTIAL | owner product tests | no security review evidence for every surface | `a8a6d61...` | complete policy integration and session binding |
| Voice recognition/TTS | `voice/`, `server/iphone_pwa.py` | QUALIFICATION | P3 iPhone PWA workflow green | mandatory physical P3 evidence not complete | P3 `78c7e9d...` | do not claim natural/background full-duplex beyond platform limits |
| Interruption / cancellation | `agent/executor.py`, voice runtime | QUALIFICATION | automated cancellation tests/workflow green | physical interruption/cancellation still mandatory | P3/PR21 | capture P3 physical evidence |
| Activities/audit | `memory/store.py`, owner UI | PARTIAL | audit calls covered indirectly by tests | main runtime non-durable | `a8a6d61...` | add tamper evidence, stronger redaction, durable production proof |
| Emergency stop | `tools/registry.py` | PARTIAL | reliability/security suite green | state persists only if data root persists | `a8a6d61...` | add broader workflow/session/freeze semantics and durable deployment evidence |
| One-use tool approval | `security/approvals.py`, `agent/executor.py` | PARTIAL | current tests exercise approval flow | process-memory tickets/paused state | `a8a6d61...` | make approvals durable/atomic and bind owner/device/session/epoch/destination/classification |
| Permission engine | `core/permissions.py`, `tools/registry.py` | PARTIAL | reliability/security tests | no full dynamic-risk production proof | `a8a6d61...` | add destination/data classification/rate/spend rules |
| Workflows | `automation/engine.py` | PARTIAL | workflow recovery tests; CI green | DB is non-durable on main runtime | `a8a6d61...` | workflow approval resume depends on in-memory executor approval state; harden restart semantics |
| Workflow restart recovery | `automation/engine.py` | PARTIAL | `_recover_interrupted_runs` + tests | no production restart persistence test | `a8a6d61...` | validate restart/redeploy with durable storage and approval waits |
| Proactive intelligence | `proactive/`, runtime wiring | PARTIAL | existing tests/CI | no owner-controlled production qualification | `a8a6d61...` | verify quiet hours/frequency/why surfaced/notification destinations |
| Tool registry | `tools/registry.py`, `tools/builtins.py` | PARTIAL | tool/integration tests | live connectors not generally authenticated | `a8a6d61...` | route every consequential tool through hardened Trusted Action Core |
| File tools | `tools/files.py` | PARTIAL | file-scope tests | not production-qualified | `a8a6d61...` | verify sandbox/path scopes/rollback |
| Gmail / Calendar connectors | `tools/integrations.py`, integration runtime | PARTIAL | mocks/integration tests | OAuth/owner consent not verified live | `a8a6d61...` | read-only first; owner OAuth is external blocker |
| Google Drive / Sheets connectors | connector architecture present but current owner-product evidence incomplete | PARTIAL | connector/tool tests are not enough to claim live operations | no live OAuth evidence | `a8a6d61...` | implement/verify declared operations and scopes |
| GitHub connector | integration/tool architecture | PARTIAL | code-level tests only | no live owner-product connector qualification recorded | `a8a6d61...` | implement read-first then controlled write with approval |
| Computer operator | browser/computer modules + builtins | PARTIAL | tool tests | no full end-to-end safe desktop qualification | current branches | enforce API/DOM/accessibility preference, sandbox, verification/rollback |
| Provider abstraction | `models/router.py` | PARTIAL | model-router and dialogue evaluation tests | Gemini deployment evidence exists | `a8a6d61...` / deployed `e63f02b...` | complete owner preference, health/failover and private endpoint qualification |
| Sensitive-data routing | `models/router.py` | PARTIAL | router tests | no live private model | `a8a6d61...` | fail closed until self-hosted/approved private provider exists |
| Self-hosted vLLM package | `deploy/self-hosted-model/` | QUALIFICATION | package files/verify script exist | no GPU host purchased/deployed | `a8a6d61...` | owner-only GPU purchase then live security/latency/concurrency tests |
| Backup service | `recovery/backup.py` | PARTIAL | code exists | no isolated restore evidence recorded for current candidate | current branch | implement encrypted backup/checksum/restore qualification |
| Production durable storage | `core/config.py`, `app/main.py`, Railway | BLOCKED | local SQLite stores exist | main Railway runtime has no volume | deployed `e63f02b...` | W1: add fail-closed validation, attach durable storage, restart/redeploy/backup/restore tests |
| Windows package | packaging code/workflows | QUALIFICATION | package validation workflow green | signed installer/physical install not proven | PR21/UI heads | signing prerequisite + install/update/uninstall tests |
| Android package | `android-companion/` | QUALIFICATION | Android Companion + Instrumentation workflows green | physical installation/reconnect not yet recorded | PR21/UI heads | signed APK/AAB and physical qualification |
| Native iOS distribution | `ios-companion/` | BLOCKED | iOS workflow green | no Apple Developer/TestFlight signed distribution evidence | current branches | Apple Developer account/signing owner blocker |
| Physical P3 qualification | `qualification/`, PR #18 | BLOCKED | automated P3 workflow green | mandatory real-device evidence incomplete | `78c7e9d...` | owner must perform/permit required physical tests; do not fabricate evidence |
