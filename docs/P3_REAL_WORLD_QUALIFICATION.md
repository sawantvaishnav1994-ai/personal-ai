# P3 — Real-World Intelligence, Reliability & Superiority Qualification

Status: ACTIVE QUALIFICATION PROGRAM

Frozen baseline: `e35f154af400af1f13b6f301be0848b13145c2f7`

P2.1–P2.7 and Home V1 are frozen. P3 does not reopen or redesign them unless qualification exposes a verified defect.

## Principle

Feature presence is not qualification. P3 promotes capabilities only from measurable evidence collected on real devices, real providers, realistic environments and sustained runs.

Evidence classes:

- structural: code/CI proves a capability exists
- simulated: deterministic harness/emulator proves behavior
- real_device: physical microphone, speaker, desktop, phone or other device evidence
- production_like: sustained real-world use under representative conditions
- competitive: same task executed against an external benchmark/reference under a recorded protocol

No capability may be labelled Reliable, Production or Superior from structural evidence alone.

## Roadmap

### P3.1 — Real Voice Qualification
Measure end-to-end conversational voice on real audio hardware.

Required evidence:
- wake/listening readiness
- speech endpoint accuracy
- transcript latency
- first-response latency
- first-audio latency where available
- true barge-in detection
- interruption-to-stop latency
- cancelled-turn correctness
- noisy-room trials
- continuous multi-turn sessions
- microphone/speaker switching
- provider/fallback attribution

Initial qualification gates:
- >= 30 completed real-device turns across >= 3 sessions
- >= 10 intentional barge-in trials
- barge-in success >= 95%
- p95 interruption-to-listening <= 750 ms
- p95 transcript-to-reply <= 5000 ms for provider-backed trials, recorded rather than hidden when exceeded
- zero stale approvals/actions after interrupted turns
- no unclassified voice errors

Passing P3.1 proves qualification evidence collection and measured voice behavior; it does not automatically prove superiority over another assistant.

### P3.2 — Screen Perception & Governed Computer Qualification
Measure Observe → Understand → Permission → Act → Verify on real Windows applications.

Gates include task success, wrong-target rate, verification accuracy, permission correctness, reversible-action rollback and recovery from UI changes.

### P3.3 — Permission, Identity & Safety Qualification
Exercise approvals, trusted-device identity, revoked devices, stale approvals, interruption races, destructive-action denial and audit evidence.

### P3.4 — Workflow Recovery & Long-Running Automation Qualification
Run event/scheduled workflows for sustained periods with retries, timeouts, process restarts, network/provider failures, pause/resume, approval waiting and rollback evidence.

### P3.5 — Second Brain Quality Qualification
Measure recall precision, temporal correctness, preference supersession, conflict handling, source/evidence traceability, salience, decay and long-horizon retrieval quality.

### P3.6 — Real Cross-Device Continuity Qualification
Validate physical phone ↔ desktop ↔ browser/PWA handoff, offline/reconnect behavior, trusted-device attribution, context continuity and duplicate/conflict handling.

### P3.7 — Latency, Reliability & Soak Qualification
Measure sustained runtime behavior, memory/resource growth, crash-free duration, provider degradation, recovery, automation throughput and percentile latencies.

### P3.8 — Competitive Superiority Qualification
Run recorded, repeatable task protocols against Brahma-style everyday assistant capabilities. A `Superior` result requires materially better measured outcomes on the defined task set without weaker memory, identity, security or permission behavior.

## Qualification states

`UNQUALIFIED → INSTRUMENTED → SIMULATED_PASS → REAL_DEVICE_PASS → RELIABLE → PRODUCTION → SUPERIOR`

Promotion must include evidence IDs, environment metadata, sample counts, thresholds and timestamps. Failed trials remain retained.

## P3 rule

Never change Home V1 or rebuild a P2 capability merely to obtain a qualification result. Fix only verified defects uncovered by evidence, and preserve the failed evidence that justified the change.
