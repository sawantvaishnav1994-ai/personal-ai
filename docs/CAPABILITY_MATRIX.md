# Personal AI — Capability Matrix

Baseline date: 2026-09-15

Statuses distinguish automated software evidence from live-provider, physical-device and production evidence.

| Capability | Status | Automated evidence | Live/production evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | PARTIAL | binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | PARTIAL | automated tests | main runtime non-durable | current branch | production restart proof |
| Memory / Knowledge | PARTIAL | W4 + W6 provenance tests | durable/live-source qualification pending | current branch | production/live qualification |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth tests; W7.1-W7.4 reuse it | live operational proof partial | W5/W7.4 | W7.5-W7.6 + physical qualification |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 connector/OAuth/Drive/Sheets/Gmail software gates green | real Google account qualification deferred | W6 | resume only when isolated paid infrastructure is approved |
| Isolated connector qualification environment | BLOCKED | deployment requirements/code guards prepared | owner-deferred paid infrastructure | current | OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit authority; idempotency, recovery, cancellation, deadline, Emergency Stop | physical operator qualification not performed | `fe52b6ff...` | frozen automated baseline |
| W7.2 Observation/Application Context Safety | AUTOMATED VALIDATED | 85 focused PASS; 557 full PASS; implementation + documentation gates 6/6 | physical desktop/browser and production qualification not performed | `2a05e1da...` docs head | frozen automated baseline |
| W7.3 Allowlists and Data-Safety Policies | AUTOMATED VALIDATED | 45 focused PASS; 602 full PASS, 8 warnings; implementation + documentation gates 6/6; supplementary scratch 81 PASS non-release | not physical-device, production or live-OAuth verified | `72408596...` docs head | frozen automated baseline |
| W7.3 Policy Gateway | AUTOMATED VALIDATED | authoritative default-deny application/domain/path/clipboard/data gateway; stable reasons; policy digest; one-use permit; Emergency Stop/security epoch/recovery | live operation not qualified | `72408596...` | frozen policy authority for W7.4+ |
| W7.4 Safe Browser Operator | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | **52 focused PASS; 654 full PASS, 8 warnings; implementation workflows 6/6 PASS** | browser physical/production qualification not performed | `839cc9d5...` | documentation-head 6/6, then freeze W7.4 |
| W7.4 DOM/Accessibility/Visual Browser Safety | IMPLEMENTATION-HEAD AUTOMATED VALIDATED | DOM first; accessibility second; verified click-only coordinate fallback; stable target/context binding; redirect/tab/frame/challenge protections; bounded upload/download verification; recovery review/no blind retry | real-site/physical-browser qualification pending | `839cc9d5...` | preserve for W7.5; complete docs gate |
| Computer operator overall | PARTIAL | W7.1 transactions + W7.2 observation + W7.3 policy + W7.4 browser execution automated evidence | W7.5-W7.6 and physical safe-operation evidence pending | `839cc9d5...` | W7.5 only after W7.4 docs 6/6 |
| Provider abstraction | PARTIAL | router/dialogue tests | production failover qualification pending | current branch | W8 after W7 |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current branch | production volume gate |
| Production durable storage | BLOCKED | fail-closed hosted storage guard exists | main runtime lacks approved durable volume | deployed head | attach only at approved production gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current branch | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current branch | execute physical protocol |

## W7.3 frozen evidence

- Baseline: `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- Implementation: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.
- Final documentation: `72408596db75b3e07b031ddc9a86502a0177902e`.
- Schema: **73**, additive/restart-safe from 72.
- Focused: **45 PASS**; supplementary scratch **81 PASS, non-release only**; full: **602 passed, 8 warnings**.
- Implementation and documentation workflow gates: **6/6 PASS each**.
- Final W7.3 classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

## W7.4 implementation evidence

- Baseline: `72408596db75b3e07b031ddc9a86502a0177902e`.
- Implementation: `839cc9d55f73d0a88f8869a64cf11809ba7e9e3d`.
- Exact changed files: `browser/safe_operator.py`, `tests/test_w74_browser_security_edges.py`, `tests/test_w74_release_gate.py`, `tests/test_w74_safe_browser_operator.py`, `tests/test_w74_target_fallbacks.py`.
- No schema migration; W7.3 policy schema remains **73**.
- Focused committed W7.4 tests: **52 PASS**.
- Full repository: **654 passed, 8 warnings**; `pip check` PASS; compileall PASS; standalone JS gate N/A.
- Implementation exact-head workflows: CI #780 / `34884812596`; Reliability and Security #212 / `34884812653`; P3 #180 / `34884812640`; Android #211 / `34884812752`; Package #211 / `34884812643`; iOS #193 / `34884812616` — **6/6 PASS**.

W7.4 uses one authoritative browser execution path composed from W7.1 transaction authority, W7.2 observation/evidence safety and W7.3 default-deny policy. Web content is untrusted. Sensitive/challenge fields are owner-only, strong side effects require explicit operation class + policy + reauthentication + approval, and unknown consequential outcomes require recovery review without blind retry.

W7.4 currently classifies as **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

Not claimed: physical-device verified, production verified, live OAuth verified, or complete W7. Production, Railway and the existing iPhone qualification service are unchanged. W6 live OAuth remains blocked/deferred pending future owner approval for isolated paid infrastructure.

W7.5 may begin only from the final W7.4 documentation SHA after its independent six-workflow gate passes.
