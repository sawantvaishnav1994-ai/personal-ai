# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-14

## W7.1 — Durable Operator Transaction Core

Validated baseline: `0092051edff451476a032da3934f72d459a75ae1`

Final W7.1 implementation head: `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`

W7.1 changes exactly these nine implementation/test paths relative to the validated baseline:

1. `desktop/operator_context.py`
2. `desktop/operator_transactions.py`
3. `desktop/transactions.py`
4. `server/session_bound_executor.py`
5. `tests/test_w71_operator_transactions.py`
6. `tests/test_w71_trusted_operator.py`
7. `tools/computer.py`
8. `tools/registry.py`
9. `vision/computer_intelligence.py`

No Home V1, AI Core, Railway, production deployment, connector live-OAuth, or PR-merge changes are part of W7.1.

## Durable transaction authority

The existing Trusted Action Core remains authoritative. W7.1 does not introduce a second approval system.

The authenticated browser/session boundary creates an `OperatorRequestContext` containing owner, device, session, security epoch, initiating conversation/workflow and recent reauthentication evidence. ToolRegistry strips any user-supplied trusted context and injects the authenticated context only after normal tool authorization preparation.

`computer_execute` is a consequential external-side-effect tool, requires recent reauthentication, requires trusted context, requires result verification, and uses the prepared bounded plan rather than accepting a user-supplied prepared transaction.

## Durable operator state

The operator transaction store is SQLite-backed under the Personal AI data root and persists:

- transaction ID;
- action ID / sequence;
- owner/device/session/security epoch;
- initiating conversation/workflow;
- requested goal hash;
- exact approved plan hash/JSON;
- state and checkpoints;
- action parameter hash;
- dispatch/verification state;
- safe verification evidence;
- cancellation/deadline/recovery state;
- redacted audit history.

Supported states are:

`proposed -> policy_check -> approval_required -> permitted -> executing -> verifying -> completed`

with bounded terminal/error paths:

- `failed`
- `cancelled`
- `recovery_review_required`

Invalid transitions fail closed.

## Idempotency, restart and uncertain outcomes

Transaction IDs are binding-sensitive. Reusing an existing transaction ID with a different owner/device/session/security epoch/goal/plan fails.

Action dispatch is bound to transaction + sequence + action type + parameter hash. A verified action is deduplicated. An existing unresolved action is not blindly dispatched again.

On process restart, transactions that were executing or verifying are moved to `recovery_review_required`, and in-flight actions are marked outcome-unknown. Restart recovery never automatically repeats uncertain external UI actions.

Cancellation, deadline expiration and Emergency Stop are checked before dispatch and between steps. Consequential execution is refused when trusted browser/session context is absent.

## Verification

Each bounded physical action captures pre/post state through the existing desktop controller and must pass screen-change verification. Declared semantic postconditions are then checked from a fresh observation. Provider/handler return alone is not treated as completion proof.

Completed replay returns durable prior completion instead of causing another dispatch. Failed semantic verification enters recovery review rather than being reported as success.

Audit/evidence records store hashes, IDs, action kinds, states and bounded metadata. Secret/token/password/content/text/clipboard fields are redacted from durable W7.1 audit payloads.

## Tests

Full repository exact-head result: **471 passed, 7 warnings**.

Focused W7.1 regression coverage includes:

- durable state machine and binding;
- owner/device/session/security-epoch mismatch rejection;
- transaction ID rebinding rejection;
- concurrent proposal idempotency;
- action parameter binding/deduplication;
- crash/restart recovery and no blind redispatch;
- cancellation and deadline handling;
- invalid state-transition rejection;
- audit redaction;
- prepared-plan/goal/conversation authority binding;
- completed replay deduplication;
- semantic verification failure -> recovery review;
- Emergency Stop before dispatch;
- unprepared/wrong binding rejection;
- ToolRegistry trusted-context preparation;
- refusal without trusted browser/session context.

## Repair history

Initial W7.1 head `57407ed2ed2174fb28b6fd3b5e2e540f58b0b9c5` failed an existing SessionBoundExecutor compatibility test because its minimal mock executor had no `approvals` attribute.

Repair head `4fbbfafc9d6e287253b5de1e483de021dcdc4076` made security-epoch lookup use the real durable ApprovalManager when available and a compatibility value only for non-production/mock executors. That head exposed a second compatibility assumption: the same minimal mock had no `approval_context()` method.

Final repair head `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` made approval metadata lookup optional for mock/non-production executors while retaining real Personal AI approval metadata when available. No W7 security test or policy was weakened.

## Exact-head workflow evidence

All six required workflows passed on `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc`:

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #645 | `34861953280` | PASS |
| Reliability and Security | #188 | `34861953222` | PASS |
| P3 iPhone PWA | #156 | `34861953080` | PASS |
| Android Instrumentation | #187 | `34861953260` | PASS |
| Package Validation | #187 | `34861953264` | PASS |
| iOS Companion | #169 | `34861953258` | PASS |

CI passed dependency checks, compileall and full `pytest -q` with 471 passed. Reliability/Security passed dependency audit, compileall, full pytest, encrypted backup/restore and soak. Package Validation passed Windows/macOS/Ubuntu.

## Classification

W7.1 is **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** after its exact implementation head passed all required workflows.

This does not qualify W7.2-W7.6, physical desktop/browser behavior, or production deployment.

W6 remains **LIVE OAUTH QUALIFICATION PENDING / PRODUCTION QUALIFICATION PENDING**. Hosted Google connector qualification remains **BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED**.

## Next bounded batch

W7.2 — Observation and Application Context:

- active application/window identity;
- browser/tab/domain/URL identity;
- accessibility-tree capture where supported;
- DOM capture for supported browsers;
- visible-text and UI-element extraction;
- screenshot sensitive-region redaction;
- before/after evidence;
- observation freshness/expiry and stale-screen rejection;
- no covert background screen monitoring.
