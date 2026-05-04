# Founder-Ready Acceptance

R11 accepts this repo as a founder-ready, local-first personal workstation for disciplined 0DTE SPX/SPXW inventory review and evidence capture.

## Accepted Operating Envelope

- Local-first personal workstation: runs from the local checkout with repo-owned scripts and local `.state/` files.
- Fixture default: launch, verification, tests, notebook smoke, and example export paths are fixture-safe by default.
- Live data requires explicit operator opt-in: live market-data paths require the existing manual gate and configured local credential source.
- No silent fallback from live to fixture: a live-data failure remains a live failure and cannot become fixture authorization.
- Restart-safe durable local state: session metadata, lifecycle events, and inventory evidence live in inspectable local files and fail closed when missing or corrupt.
- Inventory ledger and event/audit evidence: position records, lifecycle events, authorization snapshots, and operator notes are preserved as local evidence.
- Rule engine as primary authorization layer: operator-facing authorization must derive from deterministic rule decisions, with unsafe, stale, partial, unknown, or fixture-only states blocked or restricted.
- Operator input audit evidence: structured operator inputs, validation results, confirmations, and rule outcomes remain serializable and auditable.
- Daily export bundle: local daily exports capture the session summary, event ledger, inventory snapshot, paper intents, market-data provenance, authorization evidence, and operator inputs.
- Launch, verify, and export scripts: `scripts/launch_app.sh`, `scripts/verify.sh`, and `scripts/export_daily_bundle.sh` are the supported local operator commands.
- App-level smoke/regression coverage: routine tests cover notebook smoke, restart-safe state, fixture/live boundaries, rule authorization, operator-input evidence, export bundles, and secret redaction.

## Hard Boundaries

- No broker submission.
- No order routing.
- No automated execution.
- No broker order tickets or execution-ready artifacts.
- Default verification does not call live APIs.
- Tests and default commands do not read or print token files.
- Credential values, token-file contents, authorization headers, API keys, and client secrets must not be committed, printed, exported, or pasted into docs.

## Accepted Verification

Routine founder-ready verification is:

```bash
uv run pytest
uv run ruff check .
uv run python notebooks/spx_inventory_app.py
scripts/verify.sh
```

Those commands are expected to remain deterministic, non-live, credential-free, and fixture-safe unless an operator makes a separate explicit live-data rehearsal request.
