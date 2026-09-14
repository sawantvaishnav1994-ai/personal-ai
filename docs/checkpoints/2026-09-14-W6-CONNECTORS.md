# Personal AI — W6 Governed Connectors Checkpoint

Date: 2026-09-14

## Validated history

- W6.1 governed connector foundation: implementation `baaa7da38956e97231970c548626a71cde257176`, validated integration `152ef13217b652121917a890de14e20edb139473`, documentation head `a828cca77bbb910306641fabcc0f8211e3e65e19`.
- W6.2 Drive/Sheets read-first: implementation `ecb5e2615d06816e869dd4adb398565bb5c524fa`, documentation head `6310709f65534dba79d89cccd8ea94c6a4c9d765`.
- W6.3 controlled writes baseline: `6310709f65534dba79d89cccd8ea94c6a4c9d765`.
- W6.3 implementation: `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254`.
- W6.3 final implementation tree: `e879cee54f019ca2f98c8b90564fd2681bf5cab6`.
- Commit: `W6.3: add verified Drive and Sheets write operations`.
- Parent is exactly the validated W6.2 documentation head; branch advanced by normal non-force fast-forward.

## W6.3 implementation scope

The implementation diff contains exactly 18 files:

1. `integrations/adapters.py`
2. `integrations/contracts.py`
3. `integrations/gateway.py`
4. `integrations/google_read.py`
5. `integrations/google_write.py`
6. `integrations/oauth.py`
7. `integrations/registry.py`
8. `integrations/runtime.py`
9. `integrations/state.py`
10. `server/connector_api.py`
11. `server/connector_ui.py`
12. `tests/test_connector_state_oauth.py`
13. `tests/test_drive_sheets_read.py`
14. `tests/test_w62_registry_tools.py`
15. `tests/test_w63_google_write.py`
16. `tools/builtins.py`
17. `tools/google_write.py`
18. `tools/registry.py`

No Railway/deployment, frozen Home V1, AI Core, or unrelated production configuration file is in the W6.3 implementation diff.

## Enabled write operations

Drive:

- `drive.files.create`
- `drive.files.upload`
- `drive.files.rename`
- `drive.files.update_content`

Sheets:

- `sheets.spreadsheets.create`
- `sheets.values.update`
- `sheets.values.append`

W6.3 deliberately does not enable Drive permanent delete, trash, sharing, permission changes, ownership transfer, arbitrary move, or unrestricted bulk modification. It does not enable Sheets clear, worksheet/spreadsheet deletion, structural `batchUpdate`, sharing changes, or background/autonomous writes.

## OAuth and scope behavior

- Drive reads retain `https://www.googleapis.com/auth/drive.readonly`.
- Drive writes use `https://www.googleapis.com/auth/drive.file`.
- Sheets reads retain `https://www.googleapis.com/auth/spreadsheets.readonly`.
- Sheets writes use `https://www.googleapis.com/auth/spreadsheets`.
- Google incremental authorization requests `include_granted_scopes=true`.
- The durable provider token record preserves the cumulative confirmed granted-scope set while separately tracking the currently returned scope set.
- Scope reduction is detected rather than silently replacing a larger previously confirmed set.
- Every operation checks its required scope before provider dispatch and fails closed on insufficient scope.
- OAuth completion refreshes already-live Google adapters with the returned token and current scope state.

No live Google account/credential qualification is claimed by this checkpoint.

## Trusted Action authority

Every W6.3 write is independently declared and requires owner approval plus recent reauthentication. Existing Trusted Action authority remains authoritative for owner, trusted device, browser/cloud session, security epoch, exact operation, normalized parameters, destination/resource, data classification, ticket expiry and one-use replay prevention. Content is represented in write bindings by checksum rather than exposed in audit metadata. Emergency Stop remains authoritative and blocks writes.

No generic `google.write`, `drive.write`, or `sheets.write` permission exists.

## Durable idempotency and recovery

The connector operation ledger is extended additively and restart-safely with provider-account, content-checksum and verification-evidence fields. Write records retain Personal AI operation identity, idempotency key, owner/device/session, connector/operation, destination, parameter hash, provider account, provider request/resource identifiers, dispatch time, state, verification state and rollback declaration.

Confirmed duplicate submissions return durable existing state rather than dispatching again. Reusing an idempotency key for different normalized parameters/destination fails with an idempotency conflict. Consequential writes are not blindly retried after dispatch. An uncertain timeout transitions to `recovery_review_required` / outcome-unknown state and restart recovery resumes review/verification rather than redispatch.

## Drive write safety and verification

Create/upload require explicit validated filename and MIME type, bounded content size, optional explicit parent, provider account and durable request identity. Upload content is checksummed. Post-write verification reads metadata back and checks resource identity plus applicable name, MIME, explicit parent, size/checksum and version evidence.

Rename requires explicit file ID, expected current name/version when supplied, validates the new name, uses provider version/ETag preconditions where available and verifies the resulting metadata. Content replacement requires explicit file ID, MIME/content checksum and expected provider version where available, and verifies the resulting provider metadata/checksum/size. Stale provider version or precondition conflict fails closed for owner review instead of overwriting newer external work.

## Sheets write safety and verification

Spreadsheet creation is bounded and verified by provider spreadsheet ID/title metadata. `sheets.values.update` requires explicit spreadsheet/range, validates the A1 bounds and dimensions/row/column/cell/request-byte limits, can require a hash of the previously observed values to reject concurrent/lost updates, uses `valueInputOption=RAW`, and verifies by RAW readback. `sheets.values.append` is bounded, uses RAW, retains the provider updated range and verifies that exact returned range by readback.

Formula-looking strings beginning with `=`, `+`, `-`, or `@` remain literal RAW values. No spreadsheet formula is executed or interpreted as code by Personal AI.

## Truthful rollback

W6.3 does not enable hidden delete/clear operations to manufacture rollback. Create/upload and append have no automatic rollback. Rename/content/update and Sheets update may only be compensated through a separately authorized action when sufficient prior state exists. A compensating action must itself pass Trusted Action approval/reauthentication/audit; rollback is never implied merely because provider HTTP returned success.

## Focused validation

Combined recovered W6.1 + W6.2 + W6.3 focused suite: **131 PASS**.

Pre-commit validation:

- Python compileall: PASS
- Apps & Tools JavaScript `node --check`: PASS
- migration/repeated-startup coverage: PASS
- concurrency/idempotency/uncertain-outcome coverage: PASS
- changed-file secret-pattern scan: PASS
- whitespace/syntax validation: PASS

## Exact-head automated evidence

All six required workflows passed on exact W6.3 implementation SHA `95d33a66dca6c9621e50dbbb8f7f3a5c35eb2254`:

| Workflow | Run | Run ID | Conclusion |
| --- | ---: | ---: | --- |
| CI | #585 | `34843634899` | PASS |
| Reliability and Security | #158 | `34843634900` | PASS |
| P3 iPhone PWA | #126 | `34843634890` | PASS |
| Android Instrumentation | #157 | `34843634957` | PASS |
| Package Validation | #157 | `34843634972` | PASS |
| iOS Companion | #139 | `34843634905` | PASS |

CI passed dependency checks, repository compileall and full pytest. Reliability/Security passed dependency audit, compileall, full pytest, encrypted backup/restore qualification and soak. Package Validation passed macOS, Ubuntu and Windows jobs.

## Real Google OAuth qualification package — prepared, not executed

Use one harmless owner test account/resource set and retain only redacted evidence:

1. Verify exact owner Google account identity and approved redirect URI.
2. Connect Gmail/Calendar first and record granted scopes without tokens.
3. Incrementally authorize Drive read then `drive.file`; prove prior Gmail/Calendar scopes remain in the confirmed union.
4. Incrementally authorize Sheets read then Sheets write; prove the complete scope union remains preserved.
5. Exercise token refresh, expiry, reconnect, local revoke, provider revoke, device/session revocation and reauthorization.
6. Exercise live 401/403/429/quota handling and safe owner-facing diagnostics.
7. Use one harmless Drive text file and one harmless spreadsheet/range to test read, create/upload, rename/content-update, spreadsheet creation, RAW bounded update and append.
8. Repeat identical request IDs to prove no duplicate side effects.
9. Force/observe an uncertain outcome where safely possible and verify recovery review rather than blind redispatch.
10. Prove Drive delete/trash/share/permission/ownership/move and Sheets clear/delete/structural/sharing capabilities are absent/prohibited.
11. Verify audit contains IDs/hashes/statuses but no token, auth code, PKCE verifier, file content or cell content.
12. Retain timestamps, provider resource IDs, exact scopes, operation IDs, verification evidence and negative-test outcomes in a redacted evidence record.

## W7 read-only audit

Existing foundations: Observe -> Understand -> Act -> Verify desktop operator, bounded action types, cooperative cancellation, visual/per-step verification, transaction rollback attempts, and browser navigation/text-extraction/visible-text click primitives.

Required W7 hardening before qualification: route every consequential browser/desktop/file/app operation through Trusted Action Core; bind owner/device/session/security epoch/destination/data classification; detect and bind application/window identity; enforce domain/app/path allowlists; prefer accessibility/DOM semantics before coordinates; protect clipboard/secrets; sandbox file operations; retain before/after evidence; declare rollback truthfully; stop uncertain outcomes in recovery review; and perform platform-specific physical qualification.

## Classification and production boundary

W6.3 is **IMPLEMENTED**, **INTEGRATED**, and **AUTOMATED VALIDATED** at software/CI level after the implementation exact-head gate. It remains **NOT LIVE OAUTH VERIFIED**, **NOT PRODUCTION VERIFIED**, and **NOT COMPLETE W6** until real Google-account operational evidence is completed.

No production deployment, Railway variable/storage/service/source-branch/volume change was performed. PR #22 remains draft and unmerged; PR #18 and PR #21 remain separate.

## Exact next continuation point

After this evidence-only documentation head itself passes all six workflows, freeze W6.3. The next phase is real Google OAuth and harmless-account operational qualification for Gmail, Calendar, Drive and Sheets. W7 Safe Computer Operator implementation begins only after that W6 operational qualification gate.
