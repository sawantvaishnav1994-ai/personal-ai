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
| P1 | W7.4 | Safe Browser Operator | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.4 | Physical/real-site browser qualification | QUALIFICATION PENDING | automated evidence is not real-site/physical proof | later physical qualification |
| P1 | W7.5 | Safe Desktop and File Operator | RESOLVED FOR AUTOMATED SCOPE | implementation + documentation 6/6 | frozen |
| P1 | W7.5 | Real-world Windows desktop/file qualification | QUALIFICATION PENDING | Windows contracts and packaging are automated evidence only | later real-device Windows qualification |
| P1 | W7.6 | Verification and recovery | IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING | implementation `38eeae2f...`; 778 full PASS, 8 warnings; shared implementation workflows 6/6 | complete docs-only 6/6, then W7 completion audit |
| P1 | W8 | Model health/failover/observability | PARTIAL | abstraction exists; automated W7 dependency is closing | next dependency-order implementation after W7 audit |
| P1 | W10 | Signed Windows/Android/iOS distribution | BLOCKED/QUALIFICATION | signing/physical evidence missing | future signing gate |
| P1 | W12 | Release readiness | PARTIAL | W6 live OAuth, production/physical/signing gates remain | no production promotion yet |

## W7.6 exact implementation evidence

- Baseline: `acbbefea2ad6d46406ee05f9d2a44676503b3b59`.
- Implementation: `38eeae2fc7f609ebc7d3e8681833885b8d35310d`.
- Net implementation diff: exactly 11 approved W7.6 files across `recovery/`, four W7.6 test files, `tools/builtins.py`, `tools/recovery.py`, `tools/registry.py`, and `ui/settings_panel.py`.
- Schema: additive recovery extension to **73**, using the existing W7.1 operator transaction database; no parallel transaction authority.
- Full repository: **778 passed, 8 warnings**; `pip check` PASS; compileall PASS.
- Implementation workflows: CI #828 / `34932656123`, Reliability/Security #226 / `34932656078`, P3 #186 / `34932656117`, Android #225 / `34932656134`, Package #225 / `34932656157`, iOS #207 / `34932656154` — **6/6 PASS**.

## W7.6 resolved automated-scope capabilities

- durable pre-side-effect dispatch journaling with idempotency, leases and fencing;
- shared verification outcomes with transaction/action/dispatch/idempotency binding;
- verifier identity/version, precondition, expected and observed postcondition, evidence checksum and freshness;
- fail-closed unknown/stale/mismatched verification and no implicit success;
- no blind automatic retry for consequential operations or application input;
- separate compensation actions governed by current W7.3 policy, one-use permits, approval/reauthentication and independent verification;
- manual/irreversible compensation cannot be automated;
- owner decisions bind transaction/owner/device/session/security epoch/nonce and reject replay;
- Emergency Stop blocks new dispatch/compensation authorization;
- redacted recovery reports and digested file/download evidence references;
- bounded cross-operator composition and Settings → Activities recovery review.

## Remaining boundaries

Automated W7.6 evidence is not real-world Windows verification, physical-device verification, production verification or live OAuth verification. Simulator and package-build success remain automated evidence only.

Production, Railway and the existing iPhone qualification service are unchanged. W6 live OAuth remains blocked/deferred by the owner-approved paid-infrastructure decision.

After the W7.6 documentation exact-head 6/6 gate, perform the authoritative W7 completion audit before marking W7 complete or starting the next roadmap milestone.
