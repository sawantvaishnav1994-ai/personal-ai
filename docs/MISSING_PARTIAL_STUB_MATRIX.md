# Personal AI — Missing / Partial / Stub Matrix

Baseline date: 2026-09-14

This matrix intentionally excludes capabilities that have sufficient implementation + integration + operational evidence. Items remain here until their status can be raised with evidence.

| Priority | Workstream | Item | Current status | Why not complete | Next bounded action |
| --- | --- | --- | --- | --- | --- |
| P0 | W1 | Main Railway durable storage | BLOCKED/PARTIAL | production runtime has no attached volume; data root defaults to container home | add hosted-storage guard + diagnostics, then attach durable storage and run restart/redeploy proof |
| P0 | W1 | Backup/restore qualification | PARTIAL | automated isolated qualification exists, but production-like durable restore is not complete | attach durable production storage and perform restart/redeploy/restore proof |
| P0 | W2 | Durable pending approvals | PARTIAL | implementation and restart tests pass; production durability is blocked by missing Railway volume | attach durable production storage and execute restart/redeploy proof |
| P0 | W2 | Full permit binding | PARTIAL | owner/device/session/epoch/destination/classification binding is implemented and automated-tested | qualify concrete connectors and production sessions |
| P0 | W2 | Atomic replay prevention | PARTIAL | durable one-use transaction/race tests pass | complete production persistence and distributed deployment proof |
| P0 | W2 | Verification contracts | PARTIAL | generic verification/rollback infrastructure exists and W6 adds provider hooks for Gmail/Calendar | extend provider-specific verification/rollback contracts to remaining connectors and live-qualify them |
| P0 | W2 | Security epoch / global revocation | PARTIAL | durable approval epoch exists and W6 pending OAuth is bound to security epoch/device/session | production persistence and broader real-session qualification remain |
| P0 | W3 | Production conversation durability | PARTIAL | SQLite implementation exists but main Railway service is ephemeral | complete W1 and physical restart/redeploy tests |
| P0 | W3 | Multi-browser physical qualification | QUALIFICATION | software supports multiple devices but required real-world evidence is missing | run two trusted browsers simultaneously on exact candidate |
| P0 | W3 | Physical voice P3 | QUALIFICATION | automated P3 is green but required physical evidence missing | execute P3 protocol without fabricating evidence |
| P1 | W3 | Conversation lifecycle completeness | PARTIAL | persistence/continuity exists; title/search/archive/export lifecycle needs evidence | inspect APIs/UI, add missing operations and tests |
| P1 | W3 | Re-authentication for critical actions | PARTIAL | critical trusted actions and W6 high-risk connector actions can require recent re-auth | extend/qualify every critical surface and physical session |
| P1 | W4 | NEVER_STORE policy | PARTIAL | extraction/write/retrieval enforcement and exact-head automation exist | production persistence evidence remains |
| P1 | W4 | Explainable retrieval path | PARTIAL | W4 retrieval explanation implemented and automated validated | production/physical owner UX qualification remains |
| P1 | W4 | Knowledge OCR/images | PARTIAL | bounded image/OCR contract exists, but real OCR provider/doc qualification remains | qualify approved OCR provider and real documents with provenance |
| P1 | W4 | Knowledge versioning | PARTIAL | version lineage/current/superseded/per-version behavior implemented | production durability and owner UX qualification remain |
| P1 | W5 | Approval wait/session binding | PARTIAL | durable initiating authority and approval binding are automated validated | qualify deployed durable restart and cross-session rejection |
| P1 | W5 | Workflow budgets/concurrency | PARTIAL | persisted budgets, atomic concurrency, provider/tool dispatch accounting and recovery are automated validated | durable Railway operational qualification remains |
| P1 | W6 | Stable connector declaration contract | RESOLVED FOR W6.1 AUTOMATED SCOPE | versioned manifest/runtime contract, health, retry/rate-limit/pagination/idempotency/verification/rollback metadata and lifecycle audit are implemented and exact-head validated | freeze W6.1 unless regression; proceed to W6.2 |
| P1 | W6 | Durable OAuth transaction/replay state | RESOLVED FOR W6.1 AUTOMATED SCOPE | durable owner/device/session/security-epoch-bound PKCE transaction state passes restart/replay/expiry/concurrency tests | live provider OAuth qualification remains |
| P1 | W6 | Gmail / Calendar governed migration | RESOLVED FOR W6.1 AUTOMATED SCOPE | existing adapters are migrated under shared governance with compatibility repair, provider IDs/verification and safe action policy | live Google account/provider qualification remains |
| P1 | W6 | Google Drive / Sheets | PLANNED W6.2 | not included in W6.1 candidate | implement read/search/download for Drive and read/search for Sheets, then controlled writes |
| P1 | W6 | Live Google/Gmail/Calendar/Drive/Sheets OAuth | BLOCKED | owner consent/credentials required and were intentionally not requested during software-side W6.1 | request owner only when live qualification gate is reached |
| P1 | W6 | Provider-specific live quotas/revocation/webhooks | PARTIAL | common contracts exist but real provider behavior is not operationally qualified | qualify provider-specific rate limits, revocation, health and events with real accounts |
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
| P0 | W12 | Release readiness | PARTIAL | W6.1 exact-head automated workflows are green; storage/security/physical/package-signing gates remain | do not merge/promote until all P0 gates are evidence-complete |

## W6.1 evidence update

Direct implementation SHA: `baaa7da38956e97231970c548626a71cde257176`  
Validated branch integration SHA: `152ef13217b652121917a890de14e20edb139473`

Six required exact-head workflows passed: CI #569, Reliability and Security #150, P3 iPhone PWA #118, Android Instrumentation #149, Package Validation #149 and iOS Companion #131. This resolves the software-side W6.1 contract foundation items only; it does not resolve live OAuth, W6.2 Drive/Sheets, production persistence, or real-provider operational qualification.
