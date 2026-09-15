# Personal AI — Test Matrix

Baseline date: 2026-09-15

## W7 validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.5 Safe Desktop / File Operator | `f794373c...` | 55 focused; 709 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | **778 full PASS, 8 warnings** | frozen W7 automated evidence |

## W8 Model Health / Failover / Observability

Baseline: `dad974fc1058678a07daae1702849178d2cf2dd2`.
Failed historical candidate: `1a9d379f8cdb372e583eb01dfd6373d307c18db8`.
Final implementation SHA: `42616b2e8faca9b16a5695ac319ea78200e7af74`.
Final documentation/evidence head: `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`.

The failed candidate was reproduced with diagnostic capture: **978 passed, 7 failed, 8 warnings in 93.73s**. All seven failures were brittle source/string-inspection tests rather than behavioral product failures. The final implementation contains substantive behavioral coverage for provider health, configuration/transport/capability states, circuit transitions and concurrency, bounded retry/failover, privacy eligibility, error taxonomy, safe observability, explicit probes, local-model unavailability, failure injection, W7 compatibility and production/schema boundaries.

Final implementation full repository: **965 passed, 0 failed, 8 warnings**. `pip check`, compileall and `pip-audit` passed; Reliability/Security completed encrypted backup/restore and 45-second soak. Implementation exact-head workflows: CI #1047 / `34967707625`; Reliability #239 / `34967707659`; P3 #199 / `34967707692`; Android #238 / `34967707628`; Package #238 / `34967707632`; iOS #220 / `34967707682` — **6/6 PASS**.

Documentation exact-head workflows at `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`: CI #1055 / `34968483715`; Reliability #243 / `34968483919`; P3 #203 / `34968483669`; Android #242 / `34968483729`; Package #242 / `34968483720`; iOS #224 / `34968483967` — **6/6 PASS**.

W8 classification: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED / REPOSITORY-AUTOMATED SCOPE COMPLETE**. This is not live-provider, real-world local-model, physical-device or production verification.

## Post-W8 P4 Everyday Intelligence + P5 Second Brain/Life Graph tranche

Base: frozen W8 documentation/evidence head `bd8bdcfb25aee06ea078408e0a0da477fcfdfbce`.
Branch: `p5/second-brain-life-graph-qualification-20260915`.
Draft PR: #25.
Implementation SHA: `fc8f1aeb5a8121f0faf911b6840b7ec15d48b609`.

Behavior qualified in this tranche:

- P4 daily briefing retrieves real authoritative Second Brain context rather than swallowing a call to nonexistent `SecondBrain.search()`.
- P5 provides read-through Second Brain→Life Graph projection without creating a second memory persistence authority.
- normal-sensitivity memory is visible by default; sensitive/secret memory remains fail-closed unless existing device authorization permits it.
- Second Brain relationships are projected into the graph view.
- authoritative memory supersession is represented in graph relationships and historical state.
- deletion is reflected immediately because no memory copy is stored in Life Graph.
- owner Life Graph snapshot/timeline endpoints require trusted-device memory-read authority and preserve existing sensitive-memory scope behavior.
- existing Life Graph database remains independent for explicitly-created life nodes; linking does not rewrite Second Brain/Knowledge architecture.

Seven behavioral tests were added across the P4/P5/API suites. Full repository exact-head result: **972 passed, 0 failed, 8 warnings in 26.17s**. `pip check` PASS and compileall PASS.

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1060 | `34980195417` | PASS |
| Reliability and Security | #245 | `34980195624` | PASS |
| Android Instrumentation | #244 | `34980195358` | PASS |
| Package Validation | #244 | `34980195728` | PASS |
| iOS Companion | #226 | `34980195661` | PASS |
| P3 iPhone PWA | path-filtered N/A | — | N/A — no P3/PWA path changed |

Implementation applicable-workflow gate: **5/5 PASS**. P3 is explicitly N/A for this diff and is not counted as passing. Reliability/Security passed `pip-audit`, compileall, full pytest, isolated encrypted backup/restore and 45-second soak. Package Validation passed macOS, Windows and Ubuntu. iOS is simulator evidence only.

## Remaining qualification boundary

This post-W8 tranche does not establish live email/calendar/reminder delivery, physical P3.5 Second Brain quality, production durability, live provider qualification, a real local model, signed distribution or production readiness. Those remain separate evidence classes in the post-W8 checkpoint and capability/missing matrices.
