# Personal AI — Test Matrix

Baseline date: 2026-09-15

## Frozen validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.5 Safe Desktop / File Operator | `f794373c...` | 55 focused; 709 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | 778 full PASS, 8 warnings | frozen W7 automated evidence |
| W8 Model Health / Failover / Observability | `42616b2e8faca9b16a5695ac319ea78200e7af74` | 965 full PASS, 8 warnings | implementation + docs 6/6 PASS; frozen |
| Post-W8 P4/P5 Life Graph integration | `fc8f1aeb5a8121f0faf911b6840b7ec15d48b609` | 972 full PASS, 8 warnings | 5/5 applicable implementation + docs PASS; frozen |

## P4/P5 Retrieval Intelligence + Reminder/Follow-up Lifecycle

Starting evidence SHA: `4985dd014ec8c29c9f90c2dba8f153ea8a5bb969`.
Branch: `p4-p5/retrieval-reminder-qualification-20260915`.
Draft PR: #26.
Final implementation SHA: `14f0d5dbe532d5edf7ec910270d0d9114f5f9d8b`.

### Focused qualification

Focused qualification covered:

- `tests/test_p5_retrieval_qualification.py`
- `tests/test_p4_reminder_lifecycle.py`
- `tests/test_p4_proactive_precision_recall.py`
- `tests/test_p4_reminder_tool_delegation.py`

Result: **25 collected, 25 passed, 0 failed, 0 warnings in 0.96s** in the isolated qualification harness.

P5 cases qualify deterministic 100 / 1,000 / 5,000 memory corpora, existing vector search behavior, lexical correctness, visible relationship expansion/ranking, hidden sensitive relationship side-channel protection, normal-only default sensitivity, A→B→C supersession, historical/current truth, deletion without obsolete resurrection, time-valid queries, exact duplicate suppression, retention removal and context-character budgeting.

P4 cases qualify exact-time due evaluation, date-only timezone handling, snooze/reschedule/completion/dismissal/cancellation/supersession, persisted restart/idempotency, reminder tool delegation to P4 authority, memory-linked follow-ups, normal/sensitive/secret filtering, deleted-memory exclusion, daily briefing due/overdue integration, evidence-based forgotten items, privacy-safe operational audit, trusted owner API authorization and 5,000-reminder evaluation.

### Deterministic precision / recall dataset

Expected positive set:

1. overdue explicit John follow-up;
2. due explicit proposal commitment;
3. explicit unscheduled promise.

Explicit negative set includes future follow-up, completed commitment, cancelled commitment, superseded commitment, irrelevant goal and a duplicate commitment.

Result: **precision 1.0; recall 1.0; false positives 0; false negatives 0**. This benchmark validates deterministic lifecycle selection only. It is not an LLM language-understanding benchmark and does not establish live daily-use precision.

### Performance evidence

Qualification-environment measurements:

| Corpus/load | Result | Measured latency |
| --- | --- | ---: |
| 100 memories | target ranked first | ~3.943 ms |
| 1,000 memories | target ranked first | ~18.603 ms |
| 5,000 memories | target ranked first | ~90.067 ms |
| 5,000 scheduled future reminders | 0 due, correct | ~24.772 ms |

The committed tests use <5 second bounds only as broad regression guards. These values are not production SLAs and no premature optimization was introduced. Existing vector search remains the current SQLite/full-scan foundation.

### Full repository gate

CI #1065 exact-head full repository result: **997 passed, 0 failed, 8 warnings in 30.64s**.

- `pip check` — PASS
- compileall — PASS
- `pip-audit -r requirements.txt` — PASS
- isolated encrypted backup/restore qualification — PASS
- `python tests/soak_runtime.py --seconds 45` — PASS

### Exact-head workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1065 | `34984377146` | PASS |
| Reliability and Security | #247 | `34984377349` | PASS |
| P3 iPhone PWA | #204 | `34984377120` | PASS |
| Android Instrumentation | #246 | `34984377166` | PASS |
| Package Validation | #246 | `34984377239` | PASS |
| iOS Companion | #228 | `34984377173` | PASS |

Implementation exact-head gate: **6/6 PASS**. P3 was legitimately triggered because `server/cloud_app.py` mounts the trusted P4 lifecycle router. iOS remains simulator evidence, not physical-device evidence.

## Evidence boundaries

Repository tests prove deterministic lifecycle/retrieval behavior, not live delivery. No physical iPhone push notification, live email/calendar follow-up, physical-device qualification, production database behavior, signed distribution, live provider or real local model is established here.
