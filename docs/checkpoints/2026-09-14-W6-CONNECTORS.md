# Personal AI — W6 Governed Connectors Checkpoint

Date: 2026-09-14

## W6.1 baseline

W6.1 established the shared governed Connector Contract Foundation.

- Previous W5 documentation head: `83f2230d3d6a705807bf7161a1b00b2d9a65dc4b`
- Direct W6.1 implementation SHA: `baaa7da38956e97231970c548626a71cde257176`
- Validated W6.1 integration SHA: `152ef13217b652121917a890de14e20edb139473`
- Validated W6.1 documentation head: `a828cca77bbb910306641fabcc0f8211e3e65e19`

W6.1 is IMPLEMENTED, INTEGRATED and AUTOMATED VALIDATED. It is not live-OAuth or production verified.

## W6.2 exact implementation

- Exact W6.2 baseline: `a828cca77bbb910306641fabcc0f8211e3e65e19`
- Direct W6.2 implementation SHA: `ecb5e2615d06816e869dd4adb398565bb5c524fa`
- Commit message: `W6.2 Drive and Sheets read connectors`
- Parent: exactly `a828cca77bbb910306641fabcc0f8211e3e65e19`
- Branch advanced by normal non-force fast-forward.

The implementation diff contains exactly 16 files:

1. `integrations/adapters.py`
2. `integrations/contracts.py`
3. `integrations/gateway.py`
4. `integrations/google_read.py`
5. `integrations/knowledge_bridge.py`
6. `integrations/registry.py`
7. `integrations/runtime.py`
8. `server/connector_api.py`
9. `server/connector_knowledge_api.py`
10. `server/connector_ui.py`
11. `tests/test_connector_knowledge_bridge.py`
12. `tests/test_connector_registry_tools_api.py`
13. `tests/test_drive_sheets_read.py`
14. `tests/test_w62_registry_tools.py`
15. `tools/builtins.py`
16. `tools/google_read.py`

No Railway, deployment, frozen Home V1, AI Core, or unrelated production configuration file is part of the W6.2 implementation diff.

## Drive read-first connector

W6.2 adds a first-class Google Drive manifest under the existing W6.1 contract using only:

`https://www.googleapis.com/auth/drive.readonly`

The manifest is explicitly read-only. It declares scope rationale, content limits, supported content types, retry/rate-limit/pagination behavior, health behavior and these operations:

- `drive.files.list`
- `drive.files.search`
- `drive.files.metadata`
- `drive.files.read`
- `drive.files.download`
- `drive.files.export`

No create, upload, update, move, delete, share, or permission-changing Drive operation is declared in W6.2.

Drive reads implement bounded pagination, query/search, metadata retrieval, safe download, Google Docs export, Sheets handoff, cancellation/deadline checks, MIME validation, result-size limits, malformed-response handling, and provenance including provider file ID, name, MIME type, source account/owners where supplied, created/modified time, size, checksum/version evidence when supplied, web/source reference and retrieval time.

Raw binary Drive data is not exposed directly to the model-facing tool path. Binary content must pass through explicit Knowledge ingestion. Textual previews are bounded.

## Sheets read-first connector

W6.2 adds a first-class Google Sheets manifest using only:

`https://www.googleapis.com/auth/spreadsheets.readonly`

Read-first operations:

- spreadsheet discovery through Drive
- `sheets.spreadsheets.metadata`
- `sheets.worksheets.list`
- `sheets.values.read`
- `sheets.values.batch_read`

No cell write, append, clear, formatting, worksheet create/delete, spreadsheet create/delete, sharing, or permission-changing operation is implemented.

Sheets reads require explicit spreadsheet/range identity and enforce bounded A1 validation, worksheet/range/row/column/cell/response-byte limits, cancellation/deadline checks, malformed/empty response handling and provider quota/rate-limit behavior. Formatted values, unformatted values and formulas remain distinct. Formulas are data only and are never executed. CSV/export rendering neutralizes formula-injection prefixes.

Sheets provenance retains spreadsheet ID/title, worksheet ID/title when available, exact range and bounds, retrieval time, version/modified evidence when supplied, source connector/account and value-render mode.

## Knowledge integration

Drive files and Sheets ranges enter Knowledge only after explicit owner approval. There is no automatic bulk Drive ingestion path.

Connector Knowledge provenance retains:

- connector/provider
- source account identity where available
- Drive file ID or Sheets spreadsheet ID
- source URL/reference
- version/modified time
- checksum where supplied
- worksheet/range and row/column bounds for Sheets
- ingestion/retrieval time
- access classification
- authorizing owner/device/session

Knowledge remains separate from Memory. Existing Knowledge source/version semantics are reused so later source changes create lineage rather than silently overwriting historical content. Deleting a local Knowledge copy does not delete the provider source. `NEVER_STORE` rejects connector ingestion. Sensitive/private connector content is blocked from external model routing unless policy explicitly allows that route.

## Provider-specific behavior

The W6.1 gateway is extended for Drive/Sheets operational semantics while preserving existing Gmail/Calendar compatibility:

- 401 -> authentication required
- 403 -> insufficient scope or explicit permission failure
- quota/rate-limit provider responses -> bounded retryable safe errors
- 404 -> provider resource not found
- 429 -> `Retry-After` respected within configured maximum
- transient 5xx -> bounded retry
- timeout/network failure -> safe connector error
- malformed response -> safe invalid-response state
- unsupported type/content too large/range too large -> bounded safe rejection
- cancellation and deadlines remain authoritative

Document/cell content, tokens, authorization codes and provider secret payloads are excluded from normal audit metadata.

## Apps & Tools owner surface

Apps & Tools now exposes Drive and Sheets under the existing connector-management surface, including safe health/status, connected state, granted/missing scopes, scope rationale, read-only state, capabilities, last health/error state, reconnect and revoke controls. The UI explicitly indicates that write/delete/share capabilities are not enabled. Frozen Home V1 and AI Core were not changed.

## Focused validation

Combined recovered W6.1 + W6.2 focused suite: **110 PASS**.

Pre-branch checks:

- Python compileall: PASS
- Apps & Tools JavaScript `node --check`: PASS
- changed-file secret-pattern scan: PASS
- legacy Gmail/Calendar behavior regression coverage: PASS

During development, two focused-test issues were caught before Git integration: generic W6.1 403 compatibility was preserved while Drive/Sheets permission/quota distinctions were added, and a Sheets test was corrected to use the keyword-only value-render mode. A later combined review caught a missing `hashlib` import after modularization; it was restored and the complete 110-test focused suite passed again before branch movement.

## Exact-head automated evidence

All six required workflows passed on exact W6.2 implementation SHA `ecb5e2615d06816e869dd4adb398565bb5c524fa`:

| Workflow | Run number | Run ID | Conclusion |
| --- | ---: | ---: | --- |
| CI | #579 | `34836268100` | PASS |
| Reliability and Security | #155 | `34836268108` | PASS |
| P3 iPhone PWA | #123 | `34836268173` | PASS |
| Android Instrumentation | #154 | `34836268200` | PASS |
| Package Validation | #154 | `34836268171` | PASS |
| iOS Companion | #136 | `34836268106` | PASS |

CI passed dependency installation, `pip check`, repository `compileall` and full `pytest -q`. Reliability/Security passed dependency audit, full pytest, compileall, encrypted backup/restore qualification and the 45-second soak. Package Validation passed macOS, Ubuntu and Windows package jobs.

## W6.3 read-only audit

W6.3 should remain a separate controlled-write batch. Recommended operations are granular rather than one broad write capability:

Drive:

- create/upload
- metadata update/rename
- move
- explicit sharing/permission change
- delete/trash only as separate high-risk operations

Sheets:

- values update
- append
- clear
- bounded batch update
- worksheet create/rename/delete only as separate operations

Every write must declare exact OAuth scope, destination/data classification, risk, approval and re-auth requirement. Create/update operations need durable idempotency and provider-ID verification. Delete/share/permission operations should be high risk, require approval and recent re-auth, and must never be implicitly enabled by a generic connector-write permission. Unknown consequential outcomes must stop for recovery review rather than blind retry. Rollback must only be declared where provider state can actually be restored from safe retained prior state.

## Live Google OAuth qualification audit

Software-side OAuth foundations are ready for a real-account qualification package, but no live credential evidence is claimed. The qualification gate must verify exact granted scopes, account identity, owner/device/session binding, refresh-token behavior, reconnect, provider revocation, local revoke, insufficient-scope negatives, real 401/403/429/quota behavior, read-only negative write tests, and audit redaction.

A provider-level Google token is currently shared across Google connectors. Real qualification must therefore explicitly verify multi-connector scope preservation/incremental consent before controlled writes are enabled. If the provider does not preserve previously granted connector scopes safely, token/account storage must be hardened before live multi-connector qualification is accepted.

## W7 read-only audit

The repository already has an Observe -> Understand -> Act -> Verify desktop operator, a bounded action set, per-step visual verification, cancellation checks and a transaction manager that attempts rollback. Browser tools also provide navigation, text extraction and click-by-visible-text primitives.

W7 still needs a unified operator contract that routes every consequential browser/desktop/file/application action through Trusted Action Core with explicit owner/device/session/security epoch, destination, data classification, approval/re-auth and Emergency Stop semantics. It also needs application/window identity, domain/app/path allowlists, accessibility/DOM-first behavior before coordinate control, clipboard/secret policy, file-operation sandboxing, before/after evidence, truthful rollback metadata, unknown-outcome recovery review, browser session persistence rules and platform-specific physical qualification.

## Classification

W6.2 is:

- **IMPLEMENTED**
- **INTEGRATED**
- **AUTOMATED VALIDATED**

W6.2 is deliberately not:

- **LIVE OAUTH VERIFIED**
- **PRODUCTION VERIFIED**
- **WRITE-CAPABLE DRIVE/SHEETS**
- **COMPLETE W6**

## Production boundary

No production deployment, Railway variable, Railway storage, Railway service, source-branch, or persistent-volume change was performed for W6.2. Main production still requires the later approved `/data` durable-volume qualification gate.

## Exact next continuation point

Freeze W6.2 unless a real regression is found. Next bounded engineering work is **W6.3 — controlled Drive and Sheets write operations with strict approval/reauth/idempotency/verification rules**. After W6.3 software validation, perform the real Google OAuth qualification gate. W7 Safe Computer Operator follows W6 completion.