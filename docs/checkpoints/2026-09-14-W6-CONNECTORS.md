# Personal AI — W6.1 Governed Connector Contract Checkpoint

Date: 2026-09-14

## Baseline and exact implementation

- Previous validated W5 documentation head: `83f2230d3d6a705807bf7161a1b00b2d9a65dc4b`
- Repaired direct W6.1 implementation SHA: `baaa7da38956e97231970c548626a71cde257176`
- Exact validated branch integration head: `152ef13217b652121917a890de14e20edb139473`
- W6 commit message: `W6: establish governed connector contract and OAuth lifecycle`

The direct W6 implementation commit is parented directly from `83f2230d3d6a705807bf7161a1b00b2d9a65dc4b`. The branch was advanced without force-push. An accidental placeholder staging file was created and immediately removed before W6 integration; those two no-op history commits leave zero tree diff from the W5 baseline. Because the branch could not then move backward non-force, the exact W6 tree was integrated through a non-force merge/integration head. The W6 implementation tree itself remains the one-commit direct-baseline candidate above.

## Scope implemented

W6.1 establishes the shared governed Connector Contract Foundation without rebuilding existing Personal AI architecture or frozen Home V1 / AI Core.

Implemented:

- versioned connector manifests with registration-time fail-closed validation;
- provider/authentication/scopes/capabilities/effects/risk/approval/reauth/data classification/destination metadata;
- standardized pagination, rate-limit, retry, idempotency, verification, rollback, webhook/revocation and health declarations;
- durable OAuth transaction state with owner/device/session/connector/provider/scope/PKCE/nonce/redirect/expiry/security-epoch/relink bindings;
- OAuth state digest persistence and PKCE verifier protection through the existing encrypted vault;
- atomic single-use callback consumption, replay rejection, expiry rejection and trust-binding rejection;
- explicit redirect allowlist with HTTPS requirement except local loopback development redirects;
- pending OAuth invalidation on device/session revocation;
- durable connector health and operation state;
- durable Personal AI connector operation IDs and idempotency keys;
- outcome-unknown / recovery-review behavior for uncertain consequential dispatches instead of blind replay;
- standardized safe handling for 401, 403, 429/Retry-After, transient 5xx, timeout, malformed response and permanent provider failures;
- bounded retry/backoff/jitter, cancellation/deadline awareness and bounded pagination with cursor-cycle protection;
- redacted connector lifecycle audit using the existing tamper-evident Trusted Action audit chain;
- Gmail and Google Calendar migration under the governed contract;
- Gmail read/search, draft, send, modify and default-prohibited delete governance;
- Calendar read/search/create/update/delete governance, verification and bounded rollback metadata where reversal is actually available;
- Apps & Tools owner UI/API for connector state, scopes, capabilities, risk, approval, health, reconnect and revocation status;
- existing Trusted Action Core remains authoritative; connector declarations cannot weaken stricter Personal AI risk, approval, Emergency Stop or sensitivity policy.

## Changed implementation files

1. `devices/registry.py`
2. `integrations/adapters.py`
3. `integrations/contracts.py`
4. `integrations/gateway.py`
5. `integrations/lifecycle.py`
6. `integrations/oauth.py`
7. `integrations/registry.py`
8. `integrations/runtime.py`
9. `integrations/state.py`
10. `security/pwa_sessions.py`
11. `server/cloud_app.py`
12. `server/connector_api.py`
13. `server/connector_ui.py`
14. `tests/test_connector_contracts.py`
15. `tests/test_connector_gateway.py`
16. `tests/test_connector_registry_tools_api.py`
17. `tests/test_connector_state_oauth.py`
18. `tools/integrations.py`
19. `tools/registry.py`

No Railway, deployment, Home V1, AI Core, model-routing or unrelated production configuration file is part of the W6 implementation diff.

## Persistence / migrations

W6 adds additive SQLite persistence for connector OAuth transactions, health and operation state. Startup migration is restart-safe and preserves existing data. Partial connector-health schemas are extended additively. Device/session revocation integration invalidates pending OAuth transactions. Existing encrypted vault storage remains the secret boundary for OAuth token material and PKCE verifier material.

## Focused validation

Recovered focused W6 suite: **60 PASS**.

Additional pre-branch checks:

- Python compileall: PASS
- injected Apps & Tools JavaScript syntax (`node --check`): PASS
- changed-file secret-pattern scan: PASS
- backward compatibility reproduction for legacy integration adapters: PASS after repair

The first integration head exposed one repository-wide compatibility regression in `tests/test_integration_tools.py`: W6 initially passed gateway context keywords to legacy/test adapters that did not accept them. The root cause was repaired by forwarding governed context only to gateway-aware adapters while preserving legacy method signatures. The final repaired candidate then passed the complete repository test suite.

## Exact-head automated evidence

All six required workflows passed on exact repaired integration head `152ef13217b652121917a890de14e20edb139473`:

| Workflow | Run number | Run ID | Conclusion |
| --- | ---: | ---: | --- |
| CI | #569 | `34831726193` | PASS |
| Reliability and Security | #150 | `34831726152` | PASS |
| P3 iPhone PWA | #118 | `34831726271` | PASS |
| Android Instrumentation | #149 | `34831726189` | PASS |
| Package Validation | #149 | `34831726154` | PASS |
| iOS Companion | #131 | `34831726233` | PASS |

CI passed dependency checks, repository compileall and full `pytest -q`. Reliability and Security passed dependency audit, compileall, full pytest, the 45-second soak and encrypted backup/restore qualification. Package Validation passed its macOS, Ubuntu and Windows package jobs.

## Classification

W6.1 is:

- **IMPLEMENTED**
- **INTEGRATED**
- **AUTOMATED VALIDATED**

W6.1 is not:

- **LIVE OAUTH VERIFIED**
- **PRODUCTION VERIFIED**
- **COMPLETE W6**

## Known limitations / remaining W6 work

- Real owner Google/Gmail/Calendar OAuth accounts have not been connected or qualified.
- Provider-specific quotas, revocation and operational behavior have not been live-qualified.
- Google Drive and Google Sheets are W6.2 work and are not implemented by this checkpoint.
- Slack and Home Assistant retain connector foundations/manifests but were not the primary W6.1 migration/qualification target.
- Gmail send has no truthful post-send rollback; uncertain consequential outcomes stop in recovery review.
- Production persistence is not claimed because the main Railway runtime still lacks a persistent volume.
- Physical-device P3 evidence remains a separate release gate.

## Next continuation point

Freeze W6.1 unless a real regression is found. Next engineering batch is **W6.2 — Google Drive and Google Sheets read-first connectors plus provider-specific operational verification**, followed by controlled writes and real OAuth qualification only when the software-side implementation is ready and owner credentials are genuinely required.
