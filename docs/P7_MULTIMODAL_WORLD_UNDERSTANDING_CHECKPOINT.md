# Personal AI — P7 Multimodal World Understanding Qualification Checkpoint

Evidence date: 2026-09-15

## Scope and frozen boundary

P7 start/base SHA: `0d2203aa78bfe7dc935ea42887c7ba9cf1e94427`.
Branch: `p7/multimodal-world-understanding-qualification-20260915`.
Draft PR: #28 — OPEN / DRAFT / UNMERGED.
Final implementation SHA: `821e04fe5214b793b8511877a9676cd78e9d86da`.

P7 hardens the existing canonical `future_intelligence.multimodal.WorldUnderstanding` authority. It does not introduce a second sensor engine, device authority, permission authority, action executor, approval authority, recovery authority, memory system, or Emergency Stop. P7 owns observation normalization, provenance, privacy-safe persistence and governed context. P3/device/session authorities remain responsible for device trust. P6/W7 remain responsible for authorization, approval, execution, verification, recovery, and Emergency Stop.

## Implementation diff

Implementation diff from the P6 evidence base to the frozen implementation head: **13 commits, 9 files, +2,128 / -30**.

Changed implementation/qualification files:

- `.github/workflows/reliability.yml`
- `future_intelligence/multimodal.py`
- `future_intelligence/program.py`
- `server/cloud_app.py`
- `server/multimodal_world_api.py`
- `tests/soak_runtime.py`
- `tests/test_p7_multimodal_core.py`
- `tests/test_p7_performance_recovery.py`
- `tests/test_p7_security_e2e.py`

No P8/P9/P10 implementation, Railway deployment, production deployment, OAuth activation, provider credential, signing credential, dependency addition, or P6/W7 authority replacement is part of this diff.

## Observation contract and modalities

The normalized P7 contract covers observation identity, stable source-event identity, modality, source/source adapter, device identity where applicable, observed/received/processed timestamps, finite confidence, payload/privacy classification, payload hash, provenance, parent observation references, lineage stage, derivation type, freshness TTL, retention policy/state, deletion/expiration state, simulation status, schema version, safe summary, and device-trust state.

Qualified modalities:

- screen
- camera
- image
- document
- audio
- location
- device_sensor
- wearable

Lineage stages are explicit: `raw`, `extracted`, `interpreted`, and `derived`. Derived observations require active parents and a derivation type. RAW observations cannot claim parents. Privacy cannot be downgraded below a parent observation. Owner projections expose safe metadata rather than raw multimodal payloads.

## Capability and adapter truthfulness

The canonical adapter contract distinguishes `supported`, `available`, `permission_required`, `denied`, `unavailable`, `offline`, `unsupported`, and `simulation_only`. Deterministic repository fixtures use `SimulatedObservationAdapter`, which reports `simulation_only` and `device_trust_state=simulation`; this is not physical sensor evidence.

Real/device-derived observations compose with the existing device registry. Unknown/revoked/untrusted device sources fail closed. P7 does not independently enroll, trust, or authorize a device.

## Validation and privacy

Validation occurs before normalized persistence. Qualification covers bounded nesting, bounded strings/collections/maps, finite JSON numeric values, valid timezone-aware timestamps with future-skew limits, finite 0..1 confidence, valid coordinates, finite typed sensor values, unsafe local/file/HTTP references, secret-bearing nested fields, and unsupported payload types.

Prohibited secret-bearing names include password/passwd/passphrase, secret/client_secret, api_key/apikey, token/access_token/refresh_token/bearer_token/session_token, authorization, cookie/set_cookie, credential/credentials, private_key, and matching sensitive suffixes.

Rejected adapter observations produce only categorical metadata such as reason and modality. Tests verify rejection audit/events do not contain raw payloads, credentials, tokens, document/audio/image contents, sensitive exact location, unsafe paths/URLs, session tokens, authorization headers, or other submitted secret values.

## Idempotency, storage, concurrency, and restart

Stable `(source, source_event_id)` identity prevents repeated logical observations. An identical duplicate returns the existing observation; a conflicting event with the same identity fails closed. Duplicate behavior is preserved after restart and under concurrent delivery.

Persistent P7 state uses the repository's existing SQLite approach with additive schema/indexes. Normal retrieval is bounded by database queries and indexes for time, modality, source, device, retention, parent relationship, and source-event identity. `storage_status()` proves persistent startup does not materialize historical observations into a Python ledger (`loaded_observations_in_memory=0`). SQLite transactional writes, `BEGIN IMMEDIATE`, WAL, busy timeout, foreign keys, and recursive lineage queries are reused for deterministic restart/concurrency behavior.

## Freshness, retention, deletion, and lineage safety

Freshness is explicit: fresh, stale, expired, or unknown. Modality defaults differ: dynamic sensor/location/screen/audio/image observations have bounded freshness windows while static document freshness may remain unknown unless explicitly configured. Governed context selects fresh observations only.

Retention policies are `ephemeral`, `standard`, `long`, and `owner_hold`. Owner deletion tombstones the source and descendants, clears payload/provenance, and prevents later context/inspection use. A qualification defect was found and fixed so source expiration now also transactionally tombstones active descendants. Tests cover direct and multi-level descendants, duplicate delete, restart, concurrent read/delete postconditions, owner inspection after delete, and context projection after deletion/expiration.

## Owner inspection and Activities/audit

`server/multimodal_world_api.py` is a trusted owner inspection/control surface mounted through the existing PWA session middleware. It exposes safe observation summaries, detail, lineage, capabilities, governed context, and governed deletion. It does not add a public multimodal ingestion endpoint or action endpoint.

Tests cover missing/invalid authentication, stale/revoked sessions, untrusted/revoked devices, restricted observations, invalid/deleted observations, and safe projection. Existing event/audit infrastructure receives payload-free lifecycle summaries for accepted/rejected observations, capability checks, deletion, and expiration.

## P7 → P6/W7 authority boundary

P7 context contains evidence references only. `action_context()` explicitly reports `authorization_granted=False`. Deterministic tests pass P7 context into P6 plans and verify consequential work still waits for the existing approval authority and produces no side effect before approval. With existing Emergency Stop active, the consequential operation remains blocked and P7 cannot mutate or bypass the stop state.

P7 cannot grant tool permission, create approval, bypass reauthentication, bypass ToolRegistry/destination/data restrictions, increase retry authority, bypass W7 verification/recovery, or execute a consequential action independently.

## Focused, adversarial, and deterministic E2E qualification

Reliability and Security #263 / run `35008003169` at the exact implementation SHA ran the dedicated P7 focused set:

`pytest -q tests/test_p7_multimodal_core.py tests/test_p7_security_e2e.py tests/test_p7_performance_recovery.py`

Result: **40 passed, 0 failed, 9 warnings in 6.23s**.

The suite covers all eight modalities plus capability truthfulness, strict validation, payload/metadata attacks, nested secret attacks, provenance spoofing, RAW→EXTRACTED→INTERPRETED→DERIVED lineage, source deletion/expiration cascading, idempotency before/after restart, concurrent unique and duplicate delivery, P3 trust, owner API authorization, safe Activities/rejection projections, P7→P6 authority separation, Emergency Stop preservation, bounded storage/indexes, encrypted backup/restore, and performance qualification.

Representative deterministic E2E behavior is therefore automated-qualified for: accepted simulated observation, provenance chain, duplicate delivery/restart, concurrent delivery, privacy rejection, freshness/expiration, lineage-safe deletion, P3 trust gating, P6 context handoff, and Emergency Stop preservation.

## Full repository/security qualification

CI #1100 / run `35008003160` at `821e04fe5214b793b8511877a9676cd78e9d86da`:

- `pip check` — PASS (`No broken requirements found.`)
- compileall — PASS
- full `pytest -q` — **1081 passed, 0 failed, 15 warnings in 37.51s**

Reliability and Security #263 / run `35008003169` independently ran:

- `pip-audit -r requirements.txt` — PASS (`No known vulnerabilities found`)
- compileall — PASS
- dedicated P7 focused qualification — **40 passed, 0 failed, 9 warnings in 6.23s**
- full repository `pytest -q` — **1081 passed, 0 failed, 15 warnings in 37.75s**
- isolated encrypted recovery qualification including P7 — **12 passed in 0.33s**
- P7-inclusive 45-second soak — PASS

## Performance qualification

The exact implementation head produced these deterministic GitHub Actions measurements. They are qualification observations, not production SLAs:

| Dataset | Ingest | Restart | Bounded source query | Duplicate lookup | DB bytes | Historical rows loaded into Python at startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 observations | 0.107660 s | 0.000575 s | 0.003090 s | 0.000405 s | 229,376 | 0 |
| 600 observations | 0.500055 s | 0.000890 s | 0.001303 s | 0.000391 s | 1,081,344 | 0 |
| 1,800 observations | 1.950975 s | 0.001644 s | 0.001910 s | 0.000472 s | 3,129,344 | 0 |

The important architectural result is that database size grows with history while persistent startup remains bounded and `loaded_observations_in_memory=0`; recent/source/modality lookups use the committed indexes and bounded SQL queries.

## Encrypted backup/restore qualification

The repository's existing encrypted `BackupService` was reused; P7 does not add a second backup system. The P7 recovery test created observations, source-event identities, lineage, capability records, privacy/retention metadata, and deleted descendants; created an encrypted archive; restored it into an isolated directory; verified SQLite integrity; re-opened `WorldUnderstanding`; verified identity/provenance/capability/deletion state; and verified source-event idempotency after restore.

Result inside Reliability #263: **12 recovery tests passed in 0.33s**.

## Soak qualification

The existing reliability soak was extended with P7 ingestion, duplicate ingestion, bounded reads, capability checks, lineage creation, cascading deletion, secret rejection, restart, and SQLite integrity checks.

Exact 45-second result at the implementation head:

- iterations: **6,697**
- overall RSS start: **46,903,296 bytes**
- overall RSS peak: **127,893,504 bytes**
- overall RSS end: **127,926,272 bytes**
- RSS growth: **81,022,976 bytes**, below the existing 256 MiB guard
- main SQLite integrity: `ok`
- pending device requests: **0**
- P7 simulated observation cycles: **335**
- P7 SQLite integrity: `ok`
- P7 persisted observations: **469**
- P7 database bytes: **1,138,688**
- P7 historical observations loaded into memory after restart: **0**

No soak error, deadlock, uncontrolled duplicate, corrupted lineage, stuck device request, or P7 whole-ledger RAM materialization was observed by this automated qualification.

## Implementation exact-head workflow gate

All required workflows passed at exactly `821e04fe5214b793b8511877a9676cd78e9d86da`:

| Workflow | Run | Run ID | Result |
| --- | ---: | ---: | --- |
| CI | #1100 | `35008003160` | PASS |
| Reliability and Security | #263 | `35008003169` | PASS |
| P3 iPhone PWA | #216 | `35008003085` | PASS |
| Android Instrumentation | #262 | `35008003142` | PASS |
| Package Validation | #262 | `35008003101` | PASS |
| iOS Companion | #244 | `35008003281` | PASS |

Implementation exact-head gate: **6/6 PASS**.

## Evidence boundaries

This checkpoint establishes repository/automated implementation evidence only. It does not convert simulator, fixture, PWA, instrumentation, or package evidence into physical/live/production evidence.

- REAL_CAMERA_VERIFIED = NO
- REAL_MICROPHONE_VERIFIED = NO
- REAL_LOCATION_VERIFIED = NO
- REAL_WEARABLE_VERIFIED = NO
- PHYSICAL_MULTIMODAL_VERIFIED = NO
- LIVE_SERVICE_VERIFIED = NO
- PRODUCTION_VERIFIED = NO

The documentation/evidence commit containing this checkpoint must itself pass the same six exact-head workflows before P7 is classified repository/automated evidence-closed.