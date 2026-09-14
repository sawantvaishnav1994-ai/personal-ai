# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses distinguish automated software evidence from live-provider, physical-device and production evidence.

| Capability | Status | Automated evidence | Live/production evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | PARTIAL | binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | PARTIAL | automated tests | main runtime non-durable | current branch | production restart proof |
| Memory / Knowledge | PARTIAL | W4 + W6 provenance tests | durable/live-source qualification pending | current branch | production/live qualification |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth tests; W7.1-W7.3 reuse it | live operational proof partial | W5/W7.3 | W7.4-W7.6 + physical qualification |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 connector/OAuth/Drive/Sheets/Gmail software gates green | real Google account qualification deferred | W6 | resume only when isolated paid infrastructure is approved |
| Isolated connector qualification environment | BLOCKED | deployment requirements/code guards prepared | owner-deferred paid infrastructure | current | OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit authority; idempotency, recovery, cancellation, deadline, Emergency Stop | physical operator qualification not performed | `fe52b6ff...` | frozen automated baseline |
| W7.2 Observation/Application Context Safety | AUTOMATED VALIDATED | 85 focused PASS; 557 full PASS; exact implementation + documentation gates 6/6 | physical desktop/browser and production qualification not performed | `2a05e1da...` docs head | frozen automated baseline |
| W7.3 Allowlists and Data-Safety Policies | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | **45 committed focused PASS; 602 full PASS, 8 warnings; implementation workflows 6/6 PASS**; supplementary adversarial scratch **81 PASS (non-release evidence)** | not physical-device, production or live-OAuth verified | `893db9ef...` | documentation-head 6/6, then freeze W7.3 |
| W7.3 Policy Gateway | IMPLEMENTATION-HEAD AUTOMATED VALIDATED | single authoritative default-deny gateway; stable reason codes; policy snapshot/digest; one-use temporary permits; Emergency Stop/security-epoch invalidation; recovery-review handling | live operation not qualified | `893db9ef...` | preserve for W7.4 execution path |
| W7.3 Application/Domain/File/Clipboard/Data Policy | IMPLEMENTATION-HEAD AUTOMATED VALIDATED | executable path/hash/publisher/version identity; scheme/host/port/IDN/redirect/private-network rules; canonical path/UNC/reparse/mount/ADS/MIME/size rules; clipboard secret/race controls; NEVER_STORE/sensitive/secret side-effect policy | physical Windows/browser/filesystem qualification pending | `893db9ef...` | W7.4 must consume this gateway, not duplicate it |
| Computer operator overall | PARTIAL | W7.1 core + W7.2 observation safety + W7.3 policy authority automated evidence | W7.4-W7.6 and physical safe-operation evidence pending | `893db9ef...` | W7.4 only after W7.3 docs 6/6 |
| Provider abstraction | PARTIAL | router/dialogue tests | production failover qualification pending | current branch | W8 after W7 |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current branch | production volume gate |
| Production durable storage | BLOCKED | fail-closed hosted storage guard exists | main runtime lacks approved durable volume | deployed head | attach only at approved production gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current branch | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current branch | execute physical protocol |

## W7.3 implementation evidence

- Baseline: `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- Implementation: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.
- Exact changed files: `security/policy_gateway.py`, `security/policy_store.py`, `security/policy_targets.py`, `tests/test_w73_policy.py`, `tests/test_w73_binding_controls.py`, `tests/test_w73_adversarial_edges.py`, `tools/registry.py`, `ui/settings_panel.py`.
- SQLite policy schema: **73**; fresh creation, 72→73 additive upgrade, repeated initialization and restart are covered.
- Focused committed W7.3 tests: **45 PASS**.
- Supplementary adversarial scratch qualification: **81 PASS — non-release supplementary evidence only**.
- Full repository: **602 passed, 8 warnings**; `pip check` PASS; compileall PASS; no changed standalone JavaScript file.
- Implementation exact-head workflows: CI #742 / `34879964954`; Reliability and Security #207 / `34879964723`; P3 iPhone PWA #175 / `34879964821`; Android Instrumentation #206 / `34879964875`; Package Validation #206 / `34879964783`; iOS Companion #188 / `34879964725` — **6/6 PASS**.

W7.3 currently classifies truthfully as **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

Not claimed: physical-device verified, production verified, live OAuth verified, or complete W7.

Production, Railway and the existing iPhone qualification service are unchanged. W6 live OAuth remains blocked/deferred pending future owner approval for isolated paid infrastructure.

W7.4 may begin only from the final W7.3 documentation SHA after that documentation head independently passes the same six workflows.