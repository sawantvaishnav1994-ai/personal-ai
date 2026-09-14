# Personal AI — W7 Safe Computer Operator Checkpoint

Date: 2026-09-15

## Frozen prior baselines

- W7.1 Durable Operator Transaction Core: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED**.
- W7.2 Observation Safety / Sensitive Evidence: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at docs head `2a05e1da4777cdb2393759bd650b264735b1ec97`.
- W7.3 Allowlists and Data-Safety Policies: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at docs head `72408596db75b3e07b031ddc9a86502a0177902e`.
- W7.4 Safe Browser Operator: **IMPLEMENTED / INTEGRATED / AUTOMATED VALIDATED** at docs head `745952cbdc0ab25b93db6dbb3e5324b48fe7837b`.

None of W7.1-W7.4 is claimed physical-device, production or live-OAuth verified.

## W7.5 — Safe Desktop and File Operator

Baseline SHA: `745952cbdc0ab25b93db6dbb3e5324b48fe7837b`.

Validated implementation SHA: `f794373c68b07aae23d7c4cb258f02a765100bb5`.

### Exact implementation changed files

- `desktop/file_operator.py`
- `desktop/input_clipboard.py`
- `desktop/platform_adapter.py`
- `desktop/safe_desktop_operator.py`
- `tools/desktop_file.py`
- `tools/builtins.py`
- `tests/test_w75_file_operator.py`
- `tests/test_w75_release_gate.py`
- `tests/test_w75_safe_desktop_operator.py`
- `tests/test_w75_tool_integration.py`

No Home V1/AI Core file, production deployment file, Railway configuration or workflow definition was changed. W7.5 adds no database migration; policy schema remains **73**, and W7.1 transaction storage is reused.

### Authoritative flow

`owner request → W7.1 operator transaction → fresh W7.2-style observation → proposed bounded action → W7.3 default-deny policy → Trusted Action approval/recent reauthentication where required → temporary one-use permit(s) for the exact authorized policy bindings → immediate pre-dispatch verification → bounded execution → postcondition verification → redacted audit → completion or recovery_review_required`.

Composite file actions validate all required source/destination policies before dispatch. Policy checks are completed before permit consumption so policy-use counters cannot change the effective snapshot mid-check.

### Windows application / window controls

The platform layer is adapter-based and fails closed on unsupported systems. Windows application launch requires an absolute executable path and verified canonical executable SHA-256; policy may additionally bind publisher/version. Executable and arguments remain separate, shell interpolation is not used, `shell=True` is prohibited, and relative/PATH-style launch is rejected.

Window/control operations verify foreground/window identity before input. Type/select require a verified control identity. Coordinate fallback is restricted to click and requires an explicit verified visual target/digest supplied through the W7.2 evidence path. Hidden/disabled/changed targets fail closed. Emergency Stop is rechecked immediately before input; cancellation/failure releases held input state.

Unrestricted Command Prompt/PowerShell, arbitrary shell execution, elevation/UAC bypass, registry/service/driver/security modification, shutdown/restart, software installation and arbitrary process killing remain blocked.

### File operator

W7.5 implements governed metadata, bounded text read, create file/directory, copy, move, rename, list, checksum, trash and separately governed permanent delete.

The file adapter checks canonical approved roots and rejects path traversal, raw symlink components, Windows reparse/junction targets, unexpected mounts, unsafe network/UNC paths under default policy, NTFS ADS/reserved-name escapes and hard-link mutation risk. Copy/create use temporary confinement and atomic replacement where possible, enforce no blind overwrite, file-size/disk-space limits, MIME/signature checks and source/destination checksums.

Structured/binary documents such as PDF/Office/archive/executable/image files are not treated as direct model text by the file-read path; they must use the existing Knowledge ingestion route.

Trash reports `compensating_action_available` and retains recovery metadata. Permanent delete is `irreversible`, requires W7.3 destructive-delete policy, recent owner reauthentication and explicit approval, and verifies target absence. It never claims automatic rollback.

### Keyboard, mouse and clipboard

Input is foreground-target-bound; no global keyboard hooks, keylogging, credential capture or background input injection was added. Shortcuts are allowlisted and movement/scroll/click are bounded.

Clipboard read/write are separate owner-visible capabilities. Access is on-demand only with no clipboard monitor/history thread. Content is size-bounded, sequence/change checked and classified for secret/token/password/private-key patterns. Durable observation/audit stores digest/classification/size/sequence rather than raw clipboard secret content. External secret transfer is subject to exact W7.3 destination/classification policy and otherwise fails closed.

### Verification / recovery / rollback

Application launch verifies process/executable identity/window evidence. Focus verifies expected foreground window. File copy verifies destination checksum; move/rename verify destination existence/source absence/identity; trash verifies source absence and recovery metadata. Password/secret fields are never read back for verification.

Duplicate dispatch, process restart, dispatch exception or uncertain consequential postcondition is never blindly retried. The W7.1 transaction moves to `recovery_review_required` when outcome cannot be proven.

Rollback declarations are deliberately narrow: `reversible`, `compensating_action_available`, `manual_recovery_only`, or `irreversible`. An opposite operation is not automatically called rollback.

### Validation

Focused committed W7.5 tests: **55 PASS**.

Full repository exact implementation-head result: **709 passed, 8 warnings**.

`pip check`: PASS.

`compileall`: PASS.

Standalone JavaScript syntax: **N/A**, because W7.5 changed no standalone JS file.

Migration gate: **N/A for new storage**, because W7.5 adds no schema migration; existing schema 73 and restart/recovery regressions remain green.

Automated Windows result: Windows adapter/security contracts are exercised by focused tests; Package Validation successfully built and uploaded the `windows-latest` artifact. This is **not real-world Windows operator verification**.

### Security defects found and repaired during W7.5

1. Raw symlink identity could be lost if canonical resolution occurred before the adapter checked it; raw path components are now checked first.
2. A trash/delete regression initially expected execution without recent reauthentication; the stronger W7.3 delete rule was preserved and the test/contract corrected instead of weakening policy.
3. Composite source/destination policy evaluation initially interacted badly with one-use permit counters; all required policies are now re-evaluated before any permit consumption.
4. Hard-linked mutation targets are rejected for owner review.
5. Type/select cannot fall back to raw coordinates; click coordinate fallback requires verified visual identity.
6. Clipboard content is digest/classification/sequence bound and raw secret values are excluded from normal durable audit.
7. Restart, duplicate dispatch and uncertain consequential outcomes return recovery review with no blind retry.

### Exact implementation workflows

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #790 | `34889547472` | PASS |
| Reliability and Security | #214 | `34889547513` | PASS |
| P3 iPhone PWA | #182 | `34889547586` | PASS |
| Android Instrumentation | #213 | `34889547464` | PASS |
| Package Validation | #213 | `34889547577` | PASS |
| iOS Companion | #195 | `34889547565` | PASS |

Implementation gate: **6/6 PASS**.

## Current classification before documentation-head validation

W7.5 is:
- **IMPLEMENTED**
- **INTEGRATED**
- **IMPLEMENTATION-HEAD AUTOMATED VALIDATED**
- **DOCUMENTATION-HEAD VALIDATION PENDING**

Not claimed: **REAL-WORLD WINDOWS VERIFIED**, **PHYSICAL-DEVICE VERIFIED**, **PRODUCTION VERIFIED**, **LIVE OAUTH VERIFIED**, or **COMPLETE W7**.

## Production / infrastructure boundary

Production, Railway and the existing iPhone qualification service remain unchanged. W6 live Google OAuth/account qualification remains blocked/deferred because isolated paid qualification infrastructure is owner-deferred. No deployment, merge, paid-service purchase or secret request is part of W7.5.

## Exact W7.6 dependency

W7.6 Verification and Recovery may begin only from the final W7.5 documentation SHA after that documentation-only head independently passes the same six required workflows. W7.6 must preserve W7.1-W7.5 authorities and close cross-operator verification/recovery without reintroducing broad execution capabilities.
