# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-14

## Frozen prior baselines

W7.1 Durable Operator Transaction Core remains **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

W7.2 Observation Safety / Sensitive Evidence remains **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at final documentation head `2a05e1da4777cdb2393759bd650b264735b1ec97`.

## W7.3 — Allowlists and Data-Safety Policies

Baseline SHA: `2a05e1da4777cdb2393759bd650b264735b1ec97`.

Validated implementation SHA: `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`.

Exact implementation changed files:
- `security/policy_gateway.py`
- `security/policy_store.py`
- `security/policy_targets.py`
- `tests/test_w73_policy.py`
- `tests/test_w73_binding_controls.py`
- `tests/test_w73_adversarial_edges.py`
- `tools/registry.py`
- `ui/settings_panel.py`

### Policy model and authority

W7.3 adds one authoritative default-deny policy gateway above the existing Trusted Action Core. It does not create a competing approval system. Consequential operations are evaluated against durable owner policy before execution, and approvals remain bound to the existing trusted-action authority.

The gateway returns exactly: `allow`, `deny`, `approval_required`, `reauthentication_required`, or `recovery_review_required`, with stable owner-safe reason codes. Unknown applications, domains/origins, paths, destinations and operation classes fail closed.

Policies are durable and versioned with owner/device/session/security-epoch scope, target identity, allowed/denied operations, sensitivity restrictions, approval/reauthentication rules, validity, priority, version, actor and active/revoked state. Explicit deny takes precedence. Owner controls in Settings allow inspect/add/enable/disable/revoke/reset without redesigning Home V1 or the AI Core.

Temporary/one-action permits are bound to current policy digest, owner, device, session, security epoch, exact operation/parameters, application/destination, data classification, observation identity/digest, expiry and maximum uses. Policy changes, security-epoch changes, Emergency Stop or binding mismatch invalidate authorization.

### SQLite migration

W7.3 policy schema version is **73**. The migration is additive and restart-safe from W7.2 schema 72. Fresh creation, 72→73 upgrade, repeated initialization, restart persistence and concurrent policy-update behavior are covered. Policy tables include durable policy state, temporary permits and redacted audit evidence.

### Application policy

Application identity does not rely on process/display name alone. It uses canonical executable path plus executable SHA-256 and optional publisher/signature identity and version. Unknown/unverifiable executables are rejected; executable replacement, path mismatch and application-name spoofing are detected.

### Domain/navigation policy

Origins normalize scheme, IDNA hostname and port. HTTP and HTTPS are distinct. Exact-host and explicit-subdomain matching avoids suffix/wildcard confusion. Credential-bearing URLs are rejected. IP literals and localhost/private/link-local/reserved destinations require explicit owner policy. Redirects are checked against final origin; cross-origin or scheme-changing redirects require explicit final-origin permission.

### Filesystem and clipboard policy

File paths use canonical/root-aware checks rather than string-prefix authorization. Coverage includes traversal, symlinks, Windows case behavior, UNC/network paths, junction/reparse indications, mounted-drive policy, NTFS alternate streams, reserved device names, MIME/extension/signature checks, size limits and temporary-root confinement. Destructive delete is separately reauthentication/approval gated.

Clipboard read/write are separate policy operations. Access is bounded and owner-visible. Secret/token/password/private-key patterns are classified; secret transfer is blocked; destination and content digest are bound so changed clipboard content invalidates authorization. Raw clipboard contents are excluded from normal policy audit and are not made durable Memory evidence by this layer.

### Data/side-effect policy

Classifications are normalized to public, personal, sensitive, secret and NEVER_STORE. NEVER_STORE cannot enter durable memory/evidence. Secret data cannot leave approved private boundaries. Sensitive external transfer requires explicit approval. High-risk actions require recent reauthentication. Purchase, financial transfer, public publishing, permission/security changes, legal acceptance and destructive delete require strong explicit approval. Prohibited operations remain blocked even if model-generated.

### Recovery

If a consequential outcome is unknown/uncertain, the gateway returns `recovery_review_required`; it does not authorize automatic blind retry. Redacted evidence is retained for owner review.

### Validation

Focused committed W7.3 tests: **45 PASS**.

Supplementary adversarial scratch qualification: **81 PASS**. This is explicitly **non-release supplementary evidence only** and is not used as a substitute for committed tests or CI.

Full repository exact implementation-head CI: **602 passed, 8 warnings**.

`pip check`: PASS.

`compileall`: PASS.

Standalone JavaScript syntax check: not applicable because the W7.3 implementation changed no standalone `.js` file.

### Security findings repaired

1. Temporary-permit SQLite insert mismatch found by focused tests and repaired.
2. Missing policy now explicitly means deny.
3. Approval replay and policy-change reuse are invalidated by snapshot/digest and one-use binding.
4. Application-name spoofing/executable replacement are rejected using canonical path/hash identity.
5. Domain wildcard/suffix, IDN, credential URL, scheme, redirect and private-network confusion were hardened.
6. Filesystem prefix confusion, traversal, symlink, junction/reparse, mounted path, UNC, ADS, reserved-name, MIME/signature and oversized-file cases were hardened.
7. Clipboard secret detection and changed-after-approval races were hardened; audits redact sensitive content.
8. Destructive delete and other consequential side effects now require appropriate reauthentication/approval.

### Exact implementation-head workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #742 | `34879964954` | PASS |
| Reliability and Security | #207 | `34879964723` | PASS |
| P3 iPhone PWA | #175 | `34879964821` | PASS |
| Android Instrumentation | #206 | `34879964875` | PASS |
| Package Validation | #206 | `34879964783` | PASS |
| iOS Companion | #188 | `34879964725` | PASS |

Implementation gate: **6/6 PASS**.

## Current classification before documentation-head validation

W7.3 is:
- **IMPLEMENTED**
- **INTEGRATED**
- **IMPLEMENTATION-HEAD AUTOMATED VALIDATED**
- **DOCUMENTATION-HEAD VALIDATION PENDING**

Do not classify W7.3 yet as physical-device verified, production verified, live OAuth verified or complete W7.

Production, Railway and the existing iPhone qualification service were not changed. W6 live Google OAuth remains blocked/deferred because the isolated paid qualification infrastructure is owner-deferred. No service purchase, production deployment or secret request is part of W7.3.

## Documentation-only gate

This checkpoint plus `CAPABILITY_MATRIX.md`, `TEST_MATRIX.md` and `MISSING_PARTIAL_STUB_MATRIX.md` form the documentation-only evidence commit. Its parent must be exactly `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`, its diff must contain only those four documentation files, and the same six workflows must independently pass on the exact documentation SHA.

Only after documentation-head **6/6 PASS** may W7.3 be frozen and classified **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.

## Exact W7.4 dependency

W7.4 — Safe Browser Operator — may begin only from the final validated W7.3 documentation SHA. W7.4 must consume W7.1 transaction authority, W7.2 observation/evidence safety and the W7.3 policy gateway rather than duplicating them. Production/Railway remain out of scope.