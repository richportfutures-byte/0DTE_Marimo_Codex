# Orchestration State

## Current Position

- Current roadmap position: R7 complete
- Last completed step: R7 Operator Input Workflow
- Current step: operator input workflow verified with audit evidence contract
- Next planned step: R8 Daily Export Bundle
- Known repo role: local-first personal 0DTE SPX/SPXW inventory workstation

## Hard Constraints

- One roadmap prompt at a time.
- Do not start R8 until R7 is verified and committed.
- Do not call live APIs.
- Do not read or print token files.
- Do not introduce commercial SaaS requirements.
- Do not add order routing, broker submission, or automated execution concepts.
- Preserve fail-closed doctrine.
- Preserve fixture/live distinction.
- Use precise language: this is for personal operational use, not public commercial release.

## How To Resume If The Chat Migrates

1. Open this file first.
2. Confirm `docs/founder_ready_roadmap.md` exists and matches the roadmap through R11.
3. Check `git status --short` before making changes.
4. Continue from the current roadmap position unless the user explicitly redirects.
5. For the next step, perform R1 baseline verification before implementation.
6. Keep all routine verification credential-free and fixture-safe.
7. If live-data work is later requested, confirm boundaries first and never read or print credential material.

## Do Not Do Yet

- No implementation before baseline verification.
- No live API calls.
- No credential reads.
- No UI polish.
- No execution or broker-order features.

## R1 Baseline Verification - Results

- Date/time in local shell: Sun May 3 23:04:33 EDT 2026
- Current roadmap position after this step: R1 blocked
- Next step: classify/fix baseline failures before R2 Product Contract and Session Lifecycle

### Exact Commands Run

- `pwd`
- `git branch --show-current`
- `git status --short`
- `python3 --version || python --version`
- `uv --version`
- `date`
- `uv sync`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,220p' docs/orchestration_state.md`
- `git status --short`

### Command Results

- PASS: `pwd`
  - Output confirmed repo root: `/Users/stu/Projects/0DTE_Marimo_Codex`
- PASS: `git branch --show-current`
  - Output: `main`
- PASS: `git status --short`
  - Output before R1 verification matched expected doc/untracked state:
    - ` M README.md`
    - `?? .DS_Store`
    - `?? docs/founder_ready_roadmap.md`
    - `?? docs/orchestration_state.md`
    - `?? notebooks/.DS_Store`
- PASS: `python3 --version || python --version`
  - Output: `Python 3.13.1`
- PASS: `uv --version`
  - Output: `uv 0.10.12 (00d72dac7 2026-03-19 x86_64-apple-darwin)`
- PASS: `date`
  - Output: `Sun May 3 23:04:33 EDT 2026`
- PASS: `uv sync`
  - Output: resolved 32 packages and checked 28 packages.
- FAIL: `uv run pytest`
  - Summary: 360 tests collected; 356 passed; 4 failed.
  - Failure 1: `tests/test_notebook_smoke.py::test_notebook_script_exits_under_timeout` failed because subprocess execution with `sys.executable` could not import `spx_inventory_playbook`.
  - Failure 2: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixture_directory_contains_expected_payloads` failed because `raw_option_chain_0dte.sanitized.json` is an extra JSON file in the Schwab fixture directory.
  - Failure 3: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixtures_are_marked_as_fixtures` failed with `KeyError: 'fixture'` while iterating fixture payloads.
  - Failure 4: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixture_numbers_are_decimal_compatible_strings` failed because at least one numeric field, `ask`, was a number rather than a string.
- FAIL: `uv run ruff check .`
  - Summary: one lint error.
  - Failure: `tests/test_reference.py:3:46` imports `ReferenceCard` but does not use it.
- PASS: `uv run python notebooks/spx_inventory_app.py`
  - Output: no stdout/stderr; command exited 0.
- PASS: `sed -n '1,220p' docs/orchestration_state.md`
  - Output: inspected existing orchestration state before updating this section.
- PASS: `git status --short`
  - Output before editing this section still matched the expected doc/untracked state.

### Files Modified By Commands

No command-generated tracked file modifications were observed before this documentation update. The two `.DS_Store` files were already present as untracked files and were left untouched.

## R1A Baseline Failure Repair - Results

- Date/time in local shell: Sun May 3 23:11:58 EDT 2026
- Current roadmap position: R1 complete
- Next step: R2 Product Contract and Session Lifecycle

### Exact Files Changed

- `tests/test_notebook_smoke.py`
- `tests/test_reference.py`
- `tests/test_schwab_market_data_adapter_boundary.py`
- `docs/orchestration_state.md`

### Root Cause Summary

- Notebook subprocess import failure: the direct command `uv run python notebooks/spx_inventory_app.py` passed from repo root, but the pytest subprocess used `sys.executable` without the pytest-configured `src` import path. The smoke test now passes `PYTHONPATH=<repo>/src` only to that subprocess.
- Ruff unused import: `tests/test_reference.py` imported `ReferenceCard` but did not use it. The unused import was removed.
- Schwab extra raw sanitized JSON failure: `raw_option_chain_0dte.sanitized.json` is app-owned raw sanitized capture data referenced by notebook/provider/parser tests, not stray generated junk. The boundary allowlist now includes it.
- Schwab missing `fixture` key and numeric-string failures: those invariants apply to normalized mapper fixtures, not to the app-owned raw sanitized capture whose sanitizer tests intentionally preserve raw Schwab numeric shape. The boundary helper now applies normalized fixture metadata and decimal-string checks only to the normalized mapper fixture set while still scanning every JSON fixture for sensitive content.

### Exact Commands Run

- `git status --short`
- `uv run pytest -q`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,140p' tests/test_notebook_smoke.py`
- `sed -n '1,180p' tests/test_reference.py`
- `sed -n '1,180p' tests/test_schwab_market_data_adapter_boundary.py`
- `rg -n "raw_option_chain_0dte|sanitized|fixture_payloads|FIXTURES" tests src scripts docs notebooks -g '!*.pyc'`
- `sed -n '1,220p' tests/test_schwab_market_data_fixture_mapper.py`
- `sed -n '1,220p' tests/test_schwab_option_chain_capture_sanitizer.py`
- `sed -n '1,140p' tests/fixtures/market_data/schwab/raw_option_chain_0dte.sanitized.json`
- `sed -n '1,180p' pyproject.toml`
- `sed -n '580,630p' notebooks/spx_inventory_app.py`
- `sed -n '1,130p' src/spx_inventory_playbook/live_market_rehearsal_readiness.py`
- `sed -n '1,230p' src/spx_inventory_playbook/adapters/schwab_market_data.py`
- `uv run pytest -q tests/test_notebook_smoke.py tests/test_schwab_market_data_adapter_boundary.py tests/test_reference.py`
- `uv run ruff check tests/test_notebook_smoke.py tests/test_schwab_market_data_adapter_boundary.py tests/test_reference.py`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `git status --short`
- `date`
- `tail -n 120 docs/orchestration_state.md`

### Verification Results

- PASS: `uv run pytest`
  - Result: 360 passed.
- PASS: `uv run ruff check .`
  - Result: all checks passed.
- PASS: `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

### R1 Status

R1 is complete. The repo has a clean pre-implementation baseline. Do not start R2 until explicitly requested.

## R2 Product Contract and Session Lifecycle - Results

- Date/time in local shell: Sun May 3 23:21:17 EDT 2026
- Current roadmap position: R2 complete
- Next step: R3 Durable Local State

### Files Changed

- `src/spx_inventory_playbook/session_lifecycle.py`
- `tests/test_session_lifecycle.py`
- `src/spx_inventory_playbook/__init__.py`
- `docs/orchestration_state.md`

### Design Summary

Added a pure deterministic session lifecycle model for the local-first personal 0DTE SPX/SPXW workstation. The model has no wall-clock, file, environment, network, credential, market-data-provider, broker, or Marimo dependencies. It does not place trades, route orders, submit broker instructions, or imply automated execution.

Invalid transitions fail closed by returning the same state, `allowed=False`, and at least one structured reason code. Closing is allowed from every non-closed state. Closed sessions are terminal, including reset attempts. Reset before close returns to `NOT_STARTED`.

### Explicit Lifecycle States

- `NOT_STARTED`
- `READY_CHECK`
- `DATA_LOADED`
- `INVENTORY_LOADED`
- `AUTHORIZED`
- `RESTRICTED`
- `BLOCKED`
- `SESSION_CLOSED`

### Explicit Transition Rules

- `NOT_STARTED` + `START_READY_CHECK` -> `READY_CHECK`
- `READY_CHECK` + `LOAD_DATA` -> `DATA_LOADED`
- `DATA_LOADED` + `LOAD_INVENTORY` -> `INVENTORY_LOADED`
- `INVENTORY_LOADED` + `AUTHORIZE` -> `AUTHORIZED`
- `RESTRICT` -> `RESTRICTED` from active operational states only.
- `BLOCK` -> `BLOCKED` from any non-closed state.
- `CLOSE_SESSION` -> `SESSION_CLOSED` from any non-closed state.
- `RESET_SESSION` -> `NOT_STARTED` from any non-closed state.
- Any action from `SESSION_CLOSED` is blocked with `SESSION_CLOSED_TERMINAL`.
- Other invalid transitions return the same state with a structured reason code.

### Tests Added

- Initial ready-check transition.
- Data load transition.
- Inventory load transition.
- Authorization only after inventory load.
- Direct authorization from `NOT_STARTED`, `READY_CHECK`, and `DATA_LOADED` is blocked.
- Restriction from `INVENTORY_LOADED` is allowed.
- Block from every non-closed state is allowed.
- Close from every non-closed state is allowed.
- Closed session is terminal.
- Invalid transitions preserve current state and include a reason code.
- Reset behavior is explicit before and after close.
- Decisions are deterministic and contain structured reason codes.

### Commands Run

- `git status --short`
- `git log -3 --oneline`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,260p' docs/founder_ready_roadmap.md`
- `sed -n '1,260p' docs/orchestration_state.md`
- `cat src/spx_inventory_playbook/__init__.py`
- `sed -n '1,220p' src/spx_inventory_playbook/rules.py`
- `sed -n '1,180p' src/spx_inventory_playbook/validators.py`
- `sed -n '1,200p' tests/test_rules.py`
- `uv run pytest -q tests/test_session_lifecycle.py`
- `uv run ruff check src/spx_inventory_playbook/session_lifecycle.py tests/test_session_lifecycle.py src/spx_inventory_playbook/__init__.py`
- `date`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R2 edits: 360 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R2 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R2 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_session_lifecycle.py`
  - Result: 15 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/session_lifecycle.py tests/test_session_lifecycle.py src/spx_inventory_playbook/__init__.py`
  - Result: all checks passed.

- PASS: post-edit `uv run pytest`
  - Result: 375 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R2 is complete. The next step is R3 Durable Local State. Do not start R3 until explicitly requested.

## R3 Durable Local State - Results

- Date/time in local shell: Sun May 3 23:28:13 EDT 2026
- Current roadmap position: R3 complete
- Next step: R4 Inventory Ledger

### Files Changed

- `src/spx_inventory_playbook/local_state.py`
- `tests/test_local_state.py`
- `src/spx_inventory_playbook/__init__.py`
- `docs/orchestration_state.md`

### Design Summary

Added a deterministic local file-backed state foundation for personal workstation sessions. The module computes local state paths, creates the expected directory tree on request, validates frozen session metadata and lifecycle event records, serializes records through deterministic JSON dictionaries, atomically writes session metadata, and appends session lifecycle events as JSONL.

This is not the R4 inventory ledger. It stores session metadata and lifecycle events only. It has no Marimo, market-data-provider, live API, credential-file, broker, database, background-process, order-routing, or automated-execution dependency.

### Storage Paths

- Root: `.state`
- Session metadata: `.state/sessions/{session_id}.json`
- Session events: `.state/events/{session_id}.events.jsonl`
- Snapshots directory reserved for later durable state work: `.state/snapshots`
- Exports directory reserved for later export work: `.state/exports`

### Safety Rules Implemented

- `build_local_state_paths` computes paths without creating directories.
- `ensure_local_state_dirs` creates only the configured root-local directory tree.
- Session IDs and event IDs must be non-empty and path-safe.
- IDs containing `/`, `\`, `..`, null bytes, or leading/trailing whitespace are rejected.
- Store paths are checked so writes remain inside the configured root.
- Session metadata writes use a same-directory temp file followed by replace.
- Session events append one deterministic JSON object per line.
- Corrupt JSON and malformed records raise safe `ValueError` messages without echoing raw file content.
- Unknown JSON fields are ignored.
- Missing required fields and malformed field types raise `ValueError`.
- `data_mode` preserves fixture/live distinction with allowed values: `none`, `fixture`, `live`, `mixed`, `unknown`.

### Redaction Behavior

`redact_sensitive_text` redacts obvious credential-like substrings before storing notes and summaries. It covers case-insensitive appearances of `access_token=`, `refresh_token=`, `authorization:`, `bearer `, `client_secret=`, `api_key=`, and `token=`, replacing sensitive values with `[REDACTED]`.

### Tests Added

- Path computation does not create directories.
- Directory initialization creates root, sessions, events, snapshots, and exports directories.
- Metadata and event serialization round trips.
- Extra JSON fields are ignored.
- Missing required fields raise `ValueError`.
- Malformed field types raise `ValueError`.
- Invalid session and event IDs are rejected.
- Metadata write/read round trip.
- Event append/read round trip.
- Events remain append-only and ordered.
- Path traversal cannot escape root.
- Corrupt metadata JSON raises safe `ValueError`.
- Corrupt event JSONL raises safe `ValueError`.
- Redaction catches required credential-like substrings.
- Persisted notes and summaries are redacted.
- No Marimo import is required.
- No live API or token-file access is performed.

### Commands Run

- `git status --short`
- `git log -5 --oneline`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,260p' docs/founder_ready_roadmap.md`
- `sed -n '1,340p' docs/orchestration_state.md`
- `sed -n '1,260p' src/spx_inventory_playbook/session_lifecycle.py`
- `sed -n '1,320p' tests/test_session_lifecycle.py`
- `cat src/spx_inventory_playbook/__init__.py`
- `uv run pytest -q tests/test_local_state.py`
- `uv run ruff check src/spx_inventory_playbook/local_state.py tests/test_local_state.py src/spx_inventory_playbook/__init__.py`
- `date`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R3 edits: 375 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R3 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R3 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_local_state.py`
  - Result: 64 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/local_state.py tests/test_local_state.py src/spx_inventory_playbook/__init__.py`
  - Result: all checks passed.

- PASS: post-edit `uv run pytest`
  - Result: 439 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R3 is complete. The next step is R4 Inventory Ledger. Do not start R4 until explicitly requested.

## R4 Inventory Ledger - Results

- Date/time in local shell: Sun May 3 23:42:11 EDT 2026
- Current roadmap position: R4 complete
- Next step: R5 Market Data Provider Unification

### Files Changed

- `src/spx_inventory_playbook/inventory_ledger.py`
- `tests/test_inventory_ledger.py`
- `src/spx_inventory_playbook/__init__.py`
- `docs/orchestration_state.md`

### Design Summary

Added a durable, local, append-only inventory ledger foundation for personal SPX/SPXW 0DTE workstation records. The ledger stores paper-only position and paper-intent records plus ledger events as deterministic JSONL under the existing R3 local-state root. It does not reconstruct position state yet, mutate prior records, wire into the notebook, unify live providers, create export bundles, or add broker/order/execution behavior.

The module defines inventory record kind, status, and event-type enums; frozen dataclasses for legs, records, events, and snapshots; deterministic JSON helpers; an append-only `InventoryLedgerStore`; and an interop helper that maps existing `PaperTradeIntent` values into paper-only `InventoryRecord` values.

### Storage Layout

- Inventory records: `.state/sessions/{session_id}.inventory.records.jsonl`
- Inventory events: `.state/sessions/{session_id}.inventory.events.jsonl`
- Both files are UTF-8 append-only JSONL with one deterministic JSON object per line.

### Safety Rules Implemented

- Uses the R3 `LocalStatePaths` root and does not invent a separate storage root.
- Session, record, event, and leg IDs must be non-empty and path-safe.
- Store paths are checked so reads and writes remain inside the configured R3 root.
- Unknown JSON fields are ignored on read.
- Missing required fields and malformed field types raise `ValueError`.
- Invalid record kind, status, and event type values are rejected.
- Corrupt JSONL raises safe `ValueError` messages without echoing raw file content.
- Notes and event summaries are redacted through the R3 redaction helper before serialization/storage.
- Money/price-like fields are stored as strings and are not coerced to floats.
- Static fixture, stale, unavailable, invalid, and unknown paper-intent contexts require explicit operator acknowledgement.
- No Marimo, live API, token-file, broker integration, database, or background process dependency was added.

### Paper-Only / No-Broker-Submission Invariants

- `InventoryRecord.is_paper_only` must remain `True`.
- `InventoryRecord.broker_submitted` must remain `False`.
- `inventory_record_from_paper_trade_intent` preserves the existing paper-only/no-broker-submission fields from `PaperTradeIntent` and rejects violations through `InventoryRecord` validation.
- The mapper preserves source/freshness/context/playbook fields and does not imply execution.

### Tests Added

- Leg serialization roundtrip.
- Record serialization roundtrip.
- Event serialization roundtrip.
- Snapshot serialization roundtrip.
- Extra JSON fields are ignored.
- Missing required fields fail.
- Malformed field types fail.
- Invalid IDs are rejected.
- Invalid kind, status, and event type are rejected.
- Thesis and invalidation are required unless the record is rejected.
- `broker_submitted=True` is rejected.
- `is_paper_only=False` is rejected.
- Static fixture, stale, unavailable, invalid, and unknown paper-intent contexts require acknowledgement.
- Acknowledged fixture/stale context is accepted for paper-only recordkeeping.
- Notes and summaries are redacted.
- Record and event appends preserve order.
- Snapshot reads return both records and events.
- Corrupt records/events JSONL raise safe `ValueError`.
- Path traversal cannot escape root.
- `PaperTradeIntent` maps into `InventoryRecord`.
- No Marimo import is required.
- No live API or token-file access is performed.

### Commands Run

- `git status --short`
- `git log -6 --oneline`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,260p' docs/founder_ready_roadmap.md`
- `sed -n '1,420p' docs/orchestration_state.md`
- `sed -n '1,340p' src/spx_inventory_playbook/local_state.py`
- `sed -n '1,360p' tests/test_local_state.py`
- `sed -n '1,420p' src/spx_inventory_playbook/positions.py`
- `sed -n '1,420p' src/spx_inventory_playbook/paper_trades.py`
- `sed -n '1,420p' tests/test_positions.py`
- `sed -n '1,420p' tests/test_paper_trades.py`
- `uv run pytest -q tests/test_inventory_ledger.py`
- `uv run ruff check src/spx_inventory_playbook/inventory_ledger.py tests/test_inventory_ledger.py src/spx_inventory_playbook/__init__.py`
- `date`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R4 edits: 439 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R4 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R4 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_inventory_ledger.py`
  - Result: 39 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/inventory_ledger.py tests/test_inventory_ledger.py src/spx_inventory_playbook/__init__.py`
  - Result: all checks passed.

- PASS: post-edit `uv run pytest`
  - Result: 478 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R4 is complete. The next step is R5 Market Data Provider Unification. Do not start R5 until explicitly requested.

## R5 Market Data Provider Unification - Results

- Date/time in local shell: Mon May 4 00:18:20 EDT 2026
- Current roadmap position: R5 complete
- Next step: R6 Rule Engine as Main Authorization Layer

### Files Changed

- `src/spx_inventory_playbook/adapters/option_chain_provider.py`
- `src/spx_inventory_playbook/adapters/option_chain_freshness.py`
- `src/spx_inventory_playbook/marimo_option_chain_toggle.py`
- `notebooks/spx_inventory_app.py`
- `tests/test_market_data_provider_unification.py`
- `tests/test_marimo_option_chain_toggle.py`
- `docs/orchestration_state.md`

### Design Summary

Added an explicit typed R5 provider boundary around option-chain market data. The boundary preserves fixture mode as the default, requires live mode to pass a manual confirmation phrase and token-file path gate, classifies provider/freshness output into the five required states, and exposes the state to downstream code and the notebook display without introducing any broker/order/execution behavior.

The explicit provider states are:

- `FIXTURE`
- `LIVE_FRESH`
- `LIVE_STALE`
- `LIVE_UNAVAILABLE`
- `LIVE_PARSE_ERROR`

### Safety Rules Implemented

- Fixture mode remains the default app/test provider path.
- Live activation is fail-closed unless the exact confirmation phrase and token-file path are both present.
- The live gate evaluates token-file path presence without reading or displaying file contents.
- R5 tests exercise live success/error paths with an injected in-memory token and mocked fetchers, not real token files or network calls.
- Live failures remain live failures; they do not silently fall back to fixture data.
- Stale and fresh live states are derived from deterministic timestamps and configurable freshness thresholds.
- Malformed live payloads map to `LIVE_PARSE_ERROR`.
- Unavailable live conditions map to `LIVE_UNAVAILABLE`.
- Safe provider-state summaries omit token-file paths, auth headers, raw payload bodies, and credential contents.
- The notebook now surfaces the explicit provider state in the existing option-chain panel while keeping fixture/live labels distinct.

### Tests Added/Updated

- Added `tests/test_market_data_provider_unification.py`.
- Updated `tests/test_marimo_option_chain_toggle.py`.
- Covered fixture default behavior.
- Covered live block without confirmation phrase.
- Covered live block without token-file path.
- Covered token-file contents not being read in R5 live-toggle tests.
- Covered no live network calls in fixture default tests.
- Covered `LIVE_STALE`, `LIVE_FRESH`, `LIVE_PARSE_ERROR`, and `LIVE_UNAVAILABLE` mapping.
- Covered no silent fallback from failed live mode to fixture mode.
- Covered safe non-secret provider-state summary.
- Covered notebook source surfacing the provider state.

### Commands Run

- `git status --short`
- `git log -6 --oneline`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `rg -n "Market Data|market_data|OptionChain|FixtureOptionChainProvider|LiveSchwab|LIVE|fixture|freshness|token|confirmation|provider" src notebooks tests docs README.md`
- `sed -n '1,260p' src/spx_inventory_playbook/market_data_facade.py`
- `sed -n '1,360p' src/spx_inventory_playbook/adapters/option_chain_provider.py`
- `sed -n '1,260p' src/spx_inventory_playbook/adapters/option_chain_freshness.py`
- `sed -n '1,280p' src/spx_inventory_playbook/marimo_option_chain_toggle.py`
- `sed -n '1,380p' src/spx_inventory_playbook/adapters/live_schwab_option_chain_provider.py`
- `sed -n '1,280p' tests/test_option_chain_provider.py`
- `sed -n '1,320p' tests/test_marimo_option_chain_toggle.py`
- `sed -n '240,340p' notebooks/spx_inventory_app.py`
- `sed -n '630,880p' notebooks/spx_inventory_app.py`
- `sed -n '1,260p' src/spx_inventory_playbook/adapters/option_chain_context.py`
- `sed -n '1,260p' tests/test_option_chain_freshness.py`
- `uv run pytest -q tests/test_market_data_provider_unification.py tests/test_marimo_option_chain_toggle.py tests/test_option_chain_freshness.py tests/test_option_chain_provider.py`
- `uv run ruff check src/spx_inventory_playbook/adapters/option_chain_provider.py src/spx_inventory_playbook/adapters/option_chain_freshness.py src/spx_inventory_playbook/marimo_option_chain_toggle.py notebooks/spx_inventory_app.py tests/test_market_data_provider_unification.py tests/test_marimo_option_chain_toggle.py`
- `uv run pytest -q tests/test_market_data_provider_unification.py tests/test_marimo_option_chain_toggle.py tests/test_option_chain_freshness.py tests/test_option_chain_provider.py tests/test_notebook_smoke.py`
- `date`
- `git status --short`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R5 edits: 478 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R5 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R5 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_market_data_provider_unification.py tests/test_marimo_option_chain_toggle.py tests/test_option_chain_freshness.py tests/test_option_chain_provider.py tests/test_notebook_smoke.py`
  - Result: 42 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/adapters/option_chain_provider.py src/spx_inventory_playbook/adapters/option_chain_freshness.py src/spx_inventory_playbook/marimo_option_chain_toggle.py notebooks/spx_inventory_app.py tests/test_market_data_provider_unification.py tests/test_marimo_option_chain_toggle.py`
  - Result: all checks passed.

- PASS: post-edit `uv run pytest`
  - Result: 491 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R5 is complete. The next step is R6 Rule Engine as Main Authorization Layer. Do not start R6 until explicitly requested.

## R6 Rule Engine as Main Authorization Layer - Migration Baseline

- Commit: `4c1aa91 Make rule engine primary authorization layer`
- Status at R7 continuation: committed baseline verified by the R7 preflight commands on Mon May 4 2026.
- Summary: the notebook's operator-facing authorization view reads from the typed rule-engine `RuleDecision`, and fixture, stale, unavailable, parse-error, missing, or ambiguous market-data states fail closed or restrict live action.

## R7 Operator Input Workflow - Results

- Date/time in local shell: Mon May 4 01:01:50 EDT 2026
- Current roadmap position: R7 complete
- Next step: R8 Daily Export Bundle

### Files Changed

- `src/spx_inventory_playbook/operator_inputs.py`
- `src/spx_inventory_playbook/rules.py`
- `src/spx_inventory_playbook/__init__.py`
- `tests/test_operator_inputs.py`
- `docs/HANDOFF.md`
- `docs/orchestration_state.md`

### Design Summary

Extended the structured R7 operator-input workflow with serializable audit evidence for each authorization pass. The audit contract distinguishes operator-entered data, fixture simulation data, observed market-data state, calculated normalization, and rule decisions. It preserves validation reason codes, rule reasons, required confirmations, action status, market-data state, fixture/live classification, simulation labels, and the final `can_act` answer.

The implementation remains pure and local: it does not persist files, create export bundles, call live APIs, read token files, place trades, route orders, submit broker instructions, or imply automated execution.

### Tests Added

- Operator-input audit record JSON roundtrip.
- Audit record preserves fail-closed validation defects and required confirmations.
- Fixture-derived operator inputs remain simulation-only in audit evidence.
- Path-unsafe audit/session IDs are rejected.

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R7 edits: 525 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R7 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R7 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_operator_inputs.py tests/test_rule_authorization.py`
  - Result: 38 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/operator_inputs.py src/spx_inventory_playbook/rules.py tests/test_operator_inputs.py`
  - Result: all checks passed.
- PASS: post-edit `uv run pytest`
  - Result: 529 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R7 is complete. Do not start R8 until explicitly requested.
