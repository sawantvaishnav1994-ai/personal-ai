# Personal AI — Test Matrix

Baseline date: 2026-09-15

## W7 validated history

| Batch | Implementation SHA | Focused / full evidence | Required workflow gates |
| --- | --- | --- | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff...` | 471 full PASS | implementation + documentation complete |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f...` | 85 focused; 557 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9ef...` | 45 focused; 602 full, 8 warnings; scratch 81 non-release | implementation + documentation 6/6 PASS |
| W7.4 Safe Browser Operator | `839cc9d5...` | 52 focused; 654 full, 8 warnings | implementation + documentation 6/6 PASS |
| W7.5 Safe Desktop / File Operator | `f794373c68b07aae23d7c4cb258f02a765100bb5` | **55 focused PASS; 709 full PASS, 8 warnings** | implementation 6/6 PASS; documentation pending |

## W7.5 focused coverage

### Architecture / authority
- reuses W7.1 durable transaction, audit, cancellation and restart recovery;
- reuses W7.2 owner/device/session/security-epoch observation binding and TTL;
- reuses W7.3 default-deny application/path/clipboard policy and temporary permit store;
- reuses W7.4 verification/recovery/no-blind-retry conventions;
- side effects are exposed only through a trusted-context, external-side-effect tool requiring recent reauthentication and the existing Trusted Action approval path.

### Windows application / window safety
- unsupported platforms fail closed rather than fabricate success;
- absolute executable path required; canonical executable identity and SHA-256 verified;
- executable replacement/publisher-version mismatch policy behavior covered;
- arguments remain separate; shell execution/PATH resolution/elevation escape prohibited;
- launch/focus/window state verified; foreground window rechecked immediately before input;
- stale/hidden/disabled/changed controls rejected;
- unsaved-work close requires explicit approval;
- UIA/accessibility/control identity is preferred; verified visual coordinate fallback is restricted to click.

### Filesystem safety
- metadata, bounded text read, create file/dir, copy, move, rename, list, checksum, trash and permanent-delete contracts;
- canonical approved roots and source/destination checks;
- traversal, symlink swap, reparse/junction, unexpected mount, UNC/network default, ADS, reserved-name and hard-link mutation protections;
- destination collision/no-blind-overwrite;
- temporary-file confinement and atomic replacement where possible;
- file-size, disk-space, MIME/signature and checksum verification;
- structured/binary documents rejected from direct model-text interpretation;
- trash retains recovery metadata; permanent delete truthfully reports irreversible/no rollback.

### Input / clipboard safety
- verified foreground target required for keyboard/mouse input;
- no background injection, hooks or keylogging;
- bounded click/scroll and allowlisted shortcuts;
- Emergency Stop immediately before input and held-input cleanup on failure/cancellation;
- clipboard read/write are separate, on-demand capabilities;
- sequence/change detection, size bound, secret/private-key/token classification, exact destination binding and no raw clipboard content in normal audit;
- secret external transfer is blocked unless the exact W7.3 policy allows its classification/destination.

### Recovery / adversarial coverage
- process-name spoofing and executable replacement;
- malicious/unsafe launch arguments and shell capability absence;
- window/control replacement and coordinate-fallback rejection;
- file path attacks, hard links, collision, source/destination replacement and checksum failures;
- clipboard race/secret/oversize/unauthorized destination;
- owner/device/session/security-epoch and policy-change binding;
- observation expiry, Emergency Stop, cancellation, duplicate dispatch and restart recovery;
- unknown consequential outcomes become `recovery_review_required` and are not blindly retried;
- evidence/audit redaction and no background monitoring.

## Exact implementation validation

Implementation SHA: `f794373c68b07aae23d7c4cb258f02a765100bb5`.

- Focused W7.5 tests: **55 PASS**.
- `pytest -q`: **709 passed, 8 warnings**.
- `pip check`: PASS.
- `compileall`: PASS.
- standalone JavaScript syntax: N/A — no standalone JS changed.
- schema/migration: no W7.5 migration; schema remains **73**; W7.1 transaction and W7.3 policy stores are reused.
- automated Windows result: contract tests PASS and `windows-latest` Package Validation installer build PASS; not real-world Windows operator verification.

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #790 | `34889547472` | PASS |
| Reliability and Security | #214 | `34889547513` | PASS |
| P3 iPhone PWA | #182 | `34889547586` | PASS |
| Android Instrumentation | #213 | `34889547464` | PASS |
| Package Validation | #213 | `34889547577` | PASS |
| iOS Companion | #195 | `34889547565` | PASS |

Implementation gate: **6/6 PASS**.

## Security defects found and repaired

1. Symlink identity could be lost by canonical resolution before adapter checks; raw path components are now checked before resolution.
2. Trash/delete initially conflicted with a test expectation; the stronger W7.3 recent-reauth rule was preserved and the test/contract corrected.
3. Composite file operations initially interleaved policy evaluation and permit consumption, changing policy-use counters mid-check; all policy checks are completed before permit consumption.
4. Hard-linked mutation targets now fail closed for owner review.
5. Type/select require verified control identity; raw coordinate fallback is click-only and needs explicit verified visual evidence.
6. Clipboard observations persist hashes/classification/sequence, not raw secret content; sequence changes fail closed.
7. Interrupted/duplicate consequential actions enter recovery review instead of blind redispatch.

## Current classification / boundary

W7.5: **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

Not claimed: real-world Windows verified, physical-device verified, production verified, live OAuth verified, or complete W7. Production, Railway and the existing iPhone qualification service remain unchanged.

Exact W7.6 dependency: begin only from the final W7.5 documentation SHA after documentation-head 6/6 PASS.
