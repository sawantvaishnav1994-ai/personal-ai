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
| W7.6 Verification / Recovery | `38eeae2fc7f609ebc7d3e8681833885b8d35310d` | **778 full PASS, 8 warnings** | implementation 6/6 PASS; documentation pending |

## W7.6 release-gate coverage

The committed W7.6 suites (`test_w76_recovery.py`, `test_w76_adversarial.py`, `test_w76_hardening.py`, `test_w76_release_gate.py`) qualify normal and adversarial recovery behavior including verified success/no-effect/partial/failure, unknown outcome, blocked/cancelled pre-dispatch states, recovery review, duplicate/idempotent dispatch, journal-before-side-effect uncertainty, crash/restart recovery, stale/mismatched/unsafe evidence, forged verification binding, fencing/lease behavior, competing workers, owner-decision replay, wrong device/session, security-epoch change, Emergency Stop, fail-closed consequential retry, policy-governed compensation, approval/reauthentication, one-use permit replay rejection, irreversible/manual recovery, compensation verification mismatch/uncertainty, redaction, schema restoration and W7.4/W7.5 composition.

### Architecture / authority
- W7.1 transaction/action authority remains authoritative; W7.6 only adds recovery tables to the same database.
- Schema upgrade is additive to **73** and older runtime state is restored without downgrade assumptions.
- W7.2-style evidence safety, W7.3 policy authority/temporary permits, W7.4 browser operator and W7.5 desktop/file operator remain composed rather than replaced.
- Trusted Action Core remains approval/reauthentication authority; Emergency Stop remains authoritative.

### Dispatch / verification / retry
- durable dispatch journal, idempotency key, worker lease and fencing token are persisted;
- duplicate dispatch is not treated as a new side effect;
- stale worker/fencing state fails closed;
- verification binds transaction/action/dispatch/idempotency and records precondition, expected/observed postcondition, verifier identity/version, evidence checksum, timestamp/freshness and outcome;
- stale or mismatched evidence cannot authorize retry;
- unknown outcome never becomes implicit success;
- consequential operations (`form_submission`, email/message send, external upload, share/public publish, delete/destructive delete, permission/security changes, purchase/financial transfer, legal acceptance) and `application_input` have no blind automatic retry path.

### Compensation / owner recovery
- compensation is distinct from the original side effect and cannot reuse the original action;
- current W7.3 policy is evaluated and a temporary permit is consumed once; replay fails;
- approval and recent reauthentication are enforced where required;
- manual-recovery-only and irreversible categories are not automatable;
- compensation receives separate verification; uncertain compensation returns to recovery review;
- owner recovery decisions bind transaction, owner, device, session, current security epoch and nonce.

### Evidence / privacy
- recovery redaction removes secret/token/password/cookie/authorization/clipboard raw content/DOM/screenshot-byte fields;
- unsafe traversal in evidence references is rejected;
- file/download evidence uses SHA-256 references where raw path/name is unnecessary;
- no background monitoring or hidden execution bypass is introduced.

## Exact W7.6 implementation validation

Implementation SHA: `38eeae2fc7f609ebc7d3e8681833885b8d35310d`.
Parent/baseline: `acbbefea2ad6d46406ee05f9d2a44676503b3b59`.
Net delta: 17 commits, exactly 11 implementation files.

- `pytest -q`: **778 passed, 8 warnings**.
- `pip check`: PASS.
- `compileall`: PASS.
- Reliability/Security dependency audit: PASS; no known dependency vulnerability reported by the gate.
- Reliability/Security soak: PASS.
- isolated encrypted backup/restore qualification: PASS.
- Package Validation: Ubuntu/macOS/Windows PASS.
- P3 iPhone PWA integration/security gate: PASS.
- iOS companion simulator build/test: PASS; not physical iPhone verification.

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #828 | `34932656123` | PASS |
| Reliability and Security | #226 | `34932656078` | PASS |
| P3 iPhone PWA | #186 | `34932656117` | PASS |
| Android Instrumentation | #225 | `34932656134` | PASS |
| Package Validation | #225 | `34932656157` | PASS |
| iOS Companion | #207 | `34932656154` | PASS |

Implementation gate: **6/6 PASS**.

## Current classification / boundary

W7.6: **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

Not claimed: real-world Windows verified, physical-device verified, production verified or live OAuth verified. Production, Railway and the existing iPhone qualification service remain unchanged.
