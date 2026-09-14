# Personal AI — Capability Matrix

Baseline date: 2026-09-14

Statuses distinguish automated software evidence from live-provider, physical-device and production evidence.

| Capability | Status | Automated evidence | Live/production evidence | Exact SHA | Next action |
| --- | --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | deployed UI head | preserve frozen design; physical P3 |
| Trusted devices/sessions | PARTIAL | binding/revocation tests | physical multi-browser incomplete | current branch | physical trust qualification |
| Conversation continuity | PARTIAL | automated tests | main runtime non-durable | current branch | production restart proof |
| Memory / Knowledge | PARTIAL | W4 + W6 provenance tests | durable/live-source qualification pending | current branch | production/live qualification |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth tests; W7.1/W7.2 reuse it | live operational proof partial | W5/W7.2 | W7.3-W7.6 + physical qualification |
| Workflow budgets/concurrency/idempotency | PARTIAL | W5 automated validated | production volume absent | W5 | production durable qualification |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 connector/OAuth/Drive/Sheets/Gmail software gates green | real Google account qualification deferred | W6 | resume only when isolated paid infrastructure is approved |
| Isolated connector qualification environment | BLOCKED | deployment requirements/code guards prepared | owner-deferred paid infrastructure | current | OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable SQLite transaction/action/audit authority; binding, idempotency, recovery, cancellation/deadline/Emergency Stop | physical operator qualification not performed | `fe52b6ff...` | frozen automated baseline |
| W7.2 Observation/Application Context Safety | AUTOMATED VALIDATED | **85 focused PASS; 557 full PASS; 6/6 exact implementation workflows**; coordinate-space v2; browser-native masking; sanitized evidence guard; app/window/browser/tab/origin/target freshness binding | physical desktop/browser and production qualification not performed | `78ba7e7f...` | documentation-head 6/6, then W7.3 |
| W7.2 Sensitive Evidence Geometry | AUTOMATED VALIDATED | viewport/document/window/monitor/virtual-desktop/screenshot coordinate spaces; DPR 1/2/3, zoom, scroll, chrome offsets, multi-monitor clipping; fail-safe redaction | physical display-layout qualification pending | `78ba7e7f...` | preserve until physical qualification |
| Computer operator overall | PARTIAL | W7.1 durable core + W7.2 observation/evidence safety automated validated | W7.3-W7.6 and physical safe-operation evidence pending | `78ba7e7f...` | continue bounded W7 batches after docs gate |
| Provider abstraction | PARTIAL | router/dialogue tests | production failover qualification pending | current | W8 after W7 |
| Backup/recovery | PARTIAL | isolated encrypted restore workflow | production durable restore absent | current | production volume gate |
| Production durable storage | BLOCKED | fail-closed hosted storage guard exists | main runtime lacks approved durable volume | deployed head | attach only at approved production gate |
| Windows / Android / iOS distribution | QUALIFICATION/BLOCKED | package/mobile workflows green | signed/physical evidence incomplete | current | signing + physical qualification |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | current | execute physical protocol |

## W7.2 exact implementation evidence

- Validated W7.1 documentation baseline: `526b249c54f5726421ecd8e2b6773916b5eed1a0`.
- Recovered W7.2 WIP: `f41aba85cf236800e1fc7ead0665448d9246e20d`.
- Final W7.2 implementation: `78ba7e7f9e1587fe5a68d3923f15d0425ef81715`.
- Focused W7.2 coverage: **85 PASS**.
- Full repository: **557 passed, 8 warnings**.
- CI #717 / `34873006958`: PASS.
- Reliability and Security #202 / `34873006929`: PASS.
- P3 iPhone PWA #170 / `34873006957`: PASS.
- Android Instrumentation #201 / `34873006928`: PASS.
- Package Validation #201 / `34873006956`: PASS.
- iOS Companion #183 / `34873007037`: PASS.

W7.2 software is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at the implementation-head gate. It remains **not PHYSICAL-DEVICE VERIFIED**, **not PRODUCTION VERIFIED**, and W7 overall remains partial.

The documentation-only head must independently pass the same six workflows before W7.3 starts.

Production/Railway/iPhone qualification were unchanged by W7.2. W6 live OAuth remains deferred pending future owner approval for isolated paid infrastructure.
