# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-15

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | approved production volume absent | attach only at future approved production gate |
| P0 | W3/W12 | Physical P3 / multi-browser | BLOCKED/QUALIFICATION | real-device evidence required | execute physical protocol later |
| P1 | W6 | Isolated Google connector qualification service | BLOCKED — OWNER-APPROVED PAID INFRASTRUCTURE DEFERRED | owner postponed paid isolated infrastructure | preserve checkpoint |
| P1 | W6 | Live Google OAuth/account qualification | BLOCKED BY DEFERRED HOSTED INFRASTRUCTURE | real account/consent deliberately not connected | resume only after owner approval |
| P1 | W7.1 | Durable Operator Transaction Core | RESOLVED FOR AUTOMATED SCOPE | implementation/documentation gates complete | frozen |
| P1 | W7.2 | Observation/application context + sensitive evidence | RESOLVED FOR AUTOMATED SCOPE | automated gates complete | frozen; physical qualification separate |
| P1 | W7.3 | Allowlists and data-safety policies | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.4 | Safe Browser Operator | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6; final docs `745952cb...` | frozen |
| P1 | W7.4 | Physical/real-site browser qualification | QUALIFICATION PENDING | automated evidence is not real-site/physical proof | later physical qualification |
| P1 | W7.5 | Safe Desktop and File Operator | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | implementation `f794373c...`; 55 focused PASS; 709 full PASS, 8 warnings; implementation workflows 6/6 | complete docs-only 6/6, then freeze |
| P1 | W7.5 | Real-world Windows desktop/file qualification | QUALIFICATION PENDING | Windows adapter contracts and Windows packaging are automated evidence only | later real-device Windows qualification |
| P1 | W7.6 | Verification and recovery | PARTIAL / NEXT | W7.1-W7.5 provide durable foundations; final cross-operator recovery qualification remains | begin only after W7.5 docs 6/6 |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists | after W7 automated scope |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | future signing gate |
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, W7.6, production/physical/signing gates remain | no merge/promotion yet |

## W7.5 exact implementation evidence

- Baseline: `745952cbdc0ab25b93db6dbb3e5324b48fe7837b`.
- Implementation: `f794373c68b07aae23d7c4cb258f02a765100bb5`.
- Exact changed files: `desktop/file_operator.py`, `desktop/input_clipboard.py`, `desktop/platform_adapter.py`, `desktop/safe_desktop_operator.py`, `tools/desktop_file.py`, `tools/builtins.py`, `tests/test_w75_file_operator.py`, `tests/test_w75_release_gate.py`, `tests/test_w75_safe_desktop_operator.py`, `tests/test_w75_tool_integration.py`.
- No W7.5 schema migration; policy schema remains **73** and W7.1 transaction storage is reused.
- Focused W7.5: **55 PASS**.
- Full repository: **709 passed, 8 warnings**; `pip check` PASS; compileall PASS; JS N/A.
- Automated Windows evidence: adapter/security contracts covered in focused tests; `windows-latest` Package Validation installer build PASS. **Not real-world Windows verified**.
- Implementation workflows: CI #790 / `34889547472`, Reliability/Security #214 / `34889547513`, P3 #182 / `34889547586`, Android #213 / `34889547464`, Package #213 / `34889547577`, iOS #195 / `34889547565` — **6/6 PASS**.

## W7.5 resolved automated-scope capabilities

- default-deny application/path/clipboard policy is mandatory;
- absolute/canonical executable identity and separate argument validation; no `shell=True`, unrestricted shell, elevation or PATH execution;
- verified foreground/window/control identity; visual coordinate fallback limited to verified click;
- bounded file roots and separate read/write/copy/move/rename/trash/delete operations;
- traversal/symlink/reparse/mount/UNC/ADS/reserved-name/hard-link defenses;
- checksum/MIME/size/disk-space/no-overwrite/temporary confinement checks;
- clipboard read/write separation, bounded content, sequence race detection and secret-safe audit;
- Emergency Stop/cancellation cleanup and restart/unknown-outcome recovery review;
- truthful rollback classes: reversible, compensating action, manual recovery, irreversible.

## Remaining boundaries

W7.5 does not qualify unrestricted shell, admin elevation, UAC bypass, registry/service/driver/security modification, shutdown/restart, software installation, arbitrary process killing, credential/cookie extraction, covert monitoring or unrestricted filesystem access. Those remain blocked.

Production, Railway and the existing iPhone qualification service are unchanged. W6 live OAuth remains blocked/deferred by the owner-approved paid-infrastructure decision.

Exact W7.6 dependency: final W7.5 documentation SHA must pass all six documentation workflows before W7.6 begins.
