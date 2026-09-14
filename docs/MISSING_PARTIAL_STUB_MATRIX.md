# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-14

This matrix intentionally excludes capabilities that have sufficient implementation + integration + operational evidence. Items remain here until their status can be raised with evidence.

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | production runtime has no attached volume; data root defaults to container home | add hosted-storage guard + diagnostics, then attach durable storage and run restart/redeploy proof |
| P0 | W1 | Backup/restore qualification | PARTIAL | service exists but no current isolated restore/checksum evidence | add automated backup/restore test and production-like isolated restore procedure |
| P0 | W2 | Durable pending approvals | PARTIAL | approval tickets + paused execution state live in process memory | persist approval intent/state atomically under data root |
| P0 | W2 | Full permit binding | PARTIAL | current approval binds execution/tool/parameter hash only | add owner, device, session, security epoch, destination, classification, issuance/expiry/max-use |
| P0 | W2 | Atomic replay prevention | PARTIAL | in-memory pop prevents local reuse but does not survive restart or distributed execution | use durable transaction/unique consumption record; add race/restart tests |
| P0 | W2 | Verification contracts | PARTIAL | executor treats successful handler return as successful action | tool contract must expose verifiable outcome and rollback metadata; reject model-only success |
| P0 | W2 | Security epoch / global revocation | PLANNED/PARTIAL | device revoke exists; security epoch binding is not present in current approval flow | add durable epoch and enforce it across sessions/permits |
| P0 | W3 | Production conversation durability | PARTIAL | SQLite implementation exists but main Railway service is ephemeral | complete W1 and physical restart/redeploy tests |
| P0 | W3 | Multi-browser physical qualification | QUALIFICATION | software supports multiple devices but required real-world evidence is missing | run two trusted browsers simultaneously on exact candidate |
| P0 | W3 | Physical voice P3 | QUALIFICATION | automated P3 is green but required physical evidence missing | execute P3 protocol without fabricating evidence |
| P1 | W3 | Conversation lifecycle completeness | PARTIAL | persistence/continuity exists; title/search/archive/export lifecycle needs evidence | inspect APIs/UI, add missing operations and tests |
| P1 | W3 | Re-authentication for critical actions | PARTIAL | owner password/passkey exist but critical action re-auth is not globally enforced | add Trusted Action Core re-auth requirement by risk |
| P1 | W4 | NEVER_STORE policy | PARTIAL/PLANNED | current memory model has sensitivity/retention but no authoritative NEVER_STORE enforcement seen | implement policy at extraction/write/retrieval boundaries |
| P1 | W4 | Explainable retrieval path | PARTIAL | retrieval usage/confidence exists; owner-facing complete explanation contract needs verification | standardize retrieval explanation payload + tests/UI |
| P1 | W4 | Knowledge OCR/images | STUB/PLANNED | current ingestion extracts TXT/MD/CSV/JSON/PDF/DOCX/XLSX text; image OCR is not implemented in `knowledge/store.py` | implement bounded OCR ingestion where supported with provenance |
| P1 | W4 | Knowledge versioning | PARTIAL | checksum dedupe/update metadata exist, but document-version lineage is not explicit | add version lineage/supersession with tests |
| P1 | W5 | Approval wait survives restart | PARTIAL | workflows persist `pending_approval_id`, executor approval ticket does not | fix after durable Trusted Action Core |
| P1 | W5 | Workflow budgets/concurrency | PARTIAL | retry/timeout/pools exist; explicit per-workflow cost/time/concurrency budget schema incomplete | add persisted budgets + enforcement/tests |
| P1 | W6 | Stable connector declaration contract | PARTIAL | integrations exist, but provider/auth/scopes/risk/classification/health/revocation declarations are not uniformly authoritative | introduce connector manifest contract and read-first tests |
| P1 | W6 | Live Google/Gmail/Calendar/Drive/Sheets OAuth | BLOCKED | owner consent/credentials required | continue mocks/adapters; request owner only when live qualification is reached |
| P1 | W7 | Safe computer operator end-to-end | PARTIAL | browser/computer tools exist but complete sandbox/verification/rollback policy not evidenced | inventory operators and route every consequential action through Trusted Action Core |
| P1 | W8 | Self-hosted model live endpoint | BLOCKED | deployment package exists; no purchased GPU host | keep Gemini temporary/restrict sensitive routing; deploy only after owner purchase |
| P1 | W8 | Provider health/fallback operational proof | PARTIAL | router has health/error/fallback logic; live matrix evidence incomplete | add deterministic provider failure tests and production status evidence |
| P1 | W9 | Proactivity controls | PARTIAL | proactive engine exists; full quiet-hour/topic/frequency/destination/why controls not all verified | inspect UI/API, add missing controls/tests |
| P1 | W10 | Permanent domain | BLOCKED | no owner-purchased permanent domain in current baseline | after purchase configure Railway DNS/SSL/OAuth/PWA/cookies migration |
| P1 | W10 | Signed Windows distribution | BLOCKED/QUALIFICATION | packaging pipeline exists; signing prerequisites + physical install verification missing | prepare unsigned/dev artifacts; owner supplies signing prerequisite when ready |
| P1 | W10 | Signed Android distribution | QUALIFICATION | workflows green; signed release + physical install evidence missing | produce signed build when signing material is available; test install/reconnect |
| P1 | W10 | Native iOS/TestFlight | BLOCKED | Apple Developer/signing prerequisite not available | preserve project; do not claim distribution complete |
| P1 | W11 | Health/observability taxonomy | PARTIAL | logs/telemetry/model errors exist; subsystem health/correlation/alerting not complete | add structured health status + correlation IDs + redaction tests |
| P1 | W11 | Performance qualification | PARTIAL | some telemetry and soak evidence exists but release thresholds are not authoritative | record cold start/TTFR/voice/memory/knowledge/model/tool/reconnect metrics on exact candidate |
| P0 | W12 | Physical P3 release gate | BLOCKED | owner/physical-device action required | execute and record exact SHA/device/OS/browser/results/logs/artifacts |
| P0 | W12 | Release readiness | PARTIAL | automated exact-head CI green; storage/security/physical/package gates remain | do not merge/promote until all P0 gates are evidence-complete |
