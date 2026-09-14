# Personal AI — Capability Matrix

Baseline date: 2026-09-15

Statuses distinguish automated software evidence from real-world Windows, physical-device, live-provider and production evidence.

| Capability | Status | Automated evidence | Remaining boundary | Exact SHA / next |
| --- | --- | --- | --- | --- |
| Home / AI Core | QUALIFICATION | UI/PWA workflows green | physical UX incomplete | frozen design |
| Trusted Action Core | PARTIAL | durable binding/replay/epoch/reauth; reused by W7.1-W7.5 | live operational proof partial | preserve authority |
| W7.1 Durable Operator Transaction Core | AUTOMATED VALIDATED | durable transaction/action/audit, cancellation, recovery, Emergency Stop | physical qualification pending | frozen |
| W7.2 Observation / Sensitive Evidence | AUTOMATED VALIDATED | 85 focused; 557 full | physical desktop/browser proof pending | `2a05e1da...` docs |
| W7.3 Allowlists / Data-Safety Policies | AUTOMATED VALIDATED | 45 focused; 602 full; implementation + docs 6/6 | physical policy qualification pending | `72408596...` docs |
| W7.4 Safe Browser Operator | AUTOMATED VALIDATED | 52 focused; 654 full; implementation + docs 6/6 | real-site/physical-browser proof pending | `745952cb...` docs |
| W7.5 Safe Desktop and File Operator | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | **55 focused PASS; 709 full PASS, 8 warnings; implementation workflows 6/6 PASS** | real-world Windows/physical/production qualification pending | implementation `f794373c...` |
| Computer operator overall | PARTIAL | W7.1-W7.5 automated authorities integrated | W7.6 + physical/production qualification remain | W7.6 after W7.5 docs gate |
| Google connector software scope | AUTOMATED VALIDATED / LIVE PENDING | W6 software gates green | real Google account qualification owner-deferred with paid isolated infrastructure | preserve blocker |
| Production durable storage | BLOCKED | fail-closed hosted guard exists | approved production volume absent | future production gate |
| Physical P3 | BLOCKED | automated P3 green | mandatory real-device evidence incomplete | physical protocol |

## W7.5 implementation evidence

- W7.4 baseline: `745952cbdc0ab25b93db6dbb3e5324b48fe7837b`.
- W7.5 implementation: `f794373c68b07aae23d7c4cb258f02a765100bb5`.
- Exact implementation files: `desktop/file_operator.py`, `desktop/input_clipboard.py`, `desktop/platform_adapter.py`, `desktop/safe_desktop_operator.py`, `tools/desktop_file.py`, `tools/builtins.py`, `tests/test_w75_file_operator.py`, `tests/test_w75_release_gate.py`, `tests/test_w75_safe_desktop_operator.py`, `tests/test_w75_tool_integration.py`.
- No W7.5 database migration; W7.3 policy schema remains **73** and W7.1 transaction storage is reused.
- Focused committed W7.5 tests: **55 PASS**.
- Full repository: **709 passed, 8 warnings**; `pip check` PASS; compileall PASS; no standalone JavaScript changed.
- Automated Windows evidence: Windows adapter/identity contracts are covered by focused tests and Package Validation built the `windows-latest` installer successfully. This is **not** real-world Windows operator verification.
- Implementation workflows: CI #790 / `34889547472`; Reliability and Security #214 / `34889547513`; P3 #182 / `34889547586`; Android #213 / `34889547464`; Package #213 / `34889547577`; iOS #195 / `34889547565` — **6/6 PASS**.

## W7.5 security contract

W7.5 composes W7.1 transaction/recovery authority, W7.2 fresh observation/evidence binding, W7.3 default-deny application/path/clipboard policy, W7.4 no-blind-retry verification conventions, and the Trusted Action Core. It does not expose a generic shell or unrestricted filesystem.

Application launch requires an absolute canonical executable and verified identity/hash; arguments remain separate and shell execution is prohibited. Desktop input requires a fresh verified foreground window/control; coordinate fallback is click-only and must be backed by verified W7.2-style visual identity. Clipboard is on-demand only, bounded, sequence-checked, classification-aware and raw secret content is excluded from durable audit.

File operations are separated into bounded capabilities. Paths are canonical-root checked and hardened against traversal, symlinks, reparse/junctions, unexpected mounts, UNC/network defaults, ADS/reserved names and hard-link mutation risk. Copy/create use temporary confinement/checksums/no-blind-overwrite; binary/structured documents are rejected from direct model-text reading. Trash is a compensating action; permanent deletion is irreversible and retains W7.3 high-risk reauthentication/approval requirements.

Security defects repaired during W7.5 include symlink identity loss before canonical resolution, preservation of W7.3 delete reauthentication, composite policy snapshot/permit ordering, hard-link mutation checks, strict control/visual-target identity, clipboard race/redaction handling and restart/duplicate-dispatch recovery.

## Boundaries

W7.5 does not enable unrestricted Command Prompt/PowerShell, arbitrary shell commands, elevation/UAC bypass, registry/service/driver modification, antivirus/firewall disabling, credential/cookie extraction, shutdown/restart, software installation, arbitrary process killing, covert monitoring or unrestricted filesystem access.

Production, Railway and the existing iPhone qualification service are unchanged. W6 live OAuth remains blocked/deferred by owner-approved paid-infrastructure deferral.

Current truthful W7.5 classification: **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

W7.6 may begin only from the final W7.5 documentation SHA after that exact documentation head independently passes all six required workflows.
