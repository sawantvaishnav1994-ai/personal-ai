# Personal AI — Test Matrix

Baseline date: 2026-09-14

## W7 validated history

| Batch | Exact implementation SHA | Focused/full evidence | Required workflows |
| --- | --- | ---: | --- |
| W7.1 Durable Operator Transaction Core | `fe52b6ff960ebb57f89ca29120f2a57ebe3be3cc` | 471 full PASS | 6/6 PASS |
| W7.2 Observation Safety / Sensitive Evidence | `78ba7e7f9e1587fe5a68d3923f15d0425ef81715` | 85 focused PASS; 557 full PASS, 8 warnings | 6/6 PASS |
| W7.3 Allowlists / Data-Safety Policies | `893db9efd3a0c3838c31d13eda0f9b04f3710ee6` | **45 committed focused PASS; 602 full PASS, 8 warnings** | **implementation 6/6 PASS; documentation pending** |

## W7.3 implementation coverage

Policy authority:
- one authoritative default-deny evaluation path;
- durable versioned SQLite policy storage at schema **73**;
- owner/device/session/security-epoch scope;
- policy priority, explicit deny precedence, active/revoked state, expiry, temporary and one-action permissions;
- policy snapshot/digest and Trusted Action binding;
- stable results: allow, deny, approval_required, reauthentication_required, recovery_review_required;
- owner-safe explanations and redacted decision audit;
- Emergency Stop/security-epoch invalidation;
- unknown consequential outcome -> recovery_review_required with no blind retry.

Application/domain policy:
- canonical executable path plus hash; optional publisher/version; executable replacement and name-spoof rejection;
- scheme/hostname/port normalization and IDN/punycode handling;
- exact hosts and explicit subdomains; no unsafe wildcard matching;
- redirect final-origin checks; HTTP/HTTPS distinction; credential-bearing URL rejection;
- IP-literal/private/localhost restrictions; origin/suffix confusion resistance;
- cross-origin redirect requires explicit final-origin policy.

Filesystem/clipboard policy:
- canonical roots without string-prefix authorization;
- traversal/symlink/UNC/case/reparse/junction/mounted-drive/NTFS ADS/reserved-name controls;
- MIME/extension/signature and size checks; temporary-root confinement;
- read/write/create/rename/move/delete/destructive-delete separable at policy operation level;
- clipboard read/write separable; bounded access; secret detection; destination binding; clipboard-change race detection;
- clipboard secret contents are not persisted in normal policy audit.

Data/side-effect policy:
- public/personal/sensitive/secret/NEVER_STORE classification normalization;
- NEVER_STORE durable-write blocking;
- secret external transfer blocked;
- sensitive external transfer approval;
- recent reauthentication for high-risk actions;
- strong explicit approval for purchase, financial transfer, public publish, permission/security modification, legal acceptance and destructive delete;
- approval binding includes owner/device/session/security epoch/application/destination/exact parameter digest/data class/policy digest/observation/expiry/max uses.

Migration/restart:
- fresh schema 73 database;
- additive 72→73 upgrade;
- repeated initialization and restart persistence;
- concurrent policy update coverage.

## Counts and release evidence

Focused committed W7.3 test count: **45 PASS**.

Supplementary adversarial scratch qualification: **81 PASS**. This is explicitly **non-release supplementary evidence** and does not replace committed tests or exact-head CI.

Exact implementation SHA `893db9efd3a0c3838c31d13eda0f9b04f3710ee6`:
- `pip check`: PASS;
- compileall: PASS;
- `pytest -q`: **602 passed, 8 warnings**;
- standalone JavaScript syntax gate: N/A because no standalone `.js` file changed in W7.3.

## Exact-head workflows — W7.3 implementation

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #742 | `34879964954` | PASS |
| Reliability and Security | #207 | `34879964723` | PASS |
| P3 iPhone PWA | #175 | `34879964821` | PASS |
| Android Instrumentation | #206 | `34879964875` | PASS |
| Package Validation | #206 | `34879964783` | PASS |
| iOS Companion | #188 | `34879964725` | PASS |

Implementation gate: **6/6 PASS**.

## Security findings repaired

1. A temporary-permit SQL insert mismatch was found during focused testing and repaired.
2. Policy absence was made explicit default-deny rather than implicit permission.
3. Approval replay/policy-change invalidation was bound to current snapshot/digest and one-use permits.
4. Application display/process-name spoofing was rejected in favor of canonical executable identity and hash.
5. Domain wildcard/suffix, IDN, redirect, embedded credential, private-network and scheme-confusion cases were hardened.
6. Filesystem path-prefix confusion, traversal, symlink, reparse/junction, mounted path, UNC, ADS, reserved-name, MIME/signature and oversized-file cases were hardened.
7. Clipboard secret/race handling and policy audit redaction were hardened.
8. Destructive delete and other high-risk side effects were made reauthentication/approval gated.

## Evidence boundaries

W7.3 is **IMPLEMENTED / INTEGRATED / IMPLEMENTATION-HEAD AUTOMATED VALIDATED / DOCUMENTATION-HEAD VALIDATION PENDING**.

It is not physical-device verified, production verified, live OAuth verified, or complete W7. Production, Railway and the existing iPhone qualification service were unchanged. W6 live OAuth remains blocked/deferred pending future owner approval for isolated paid infrastructure.

W7.4 Safe Browser Operator may begin only from the final validated W7.3 documentation SHA after the second 6/6 workflow gate.