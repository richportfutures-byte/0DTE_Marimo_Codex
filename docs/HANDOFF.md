# Project Handoff

## Current Repo State

- Local branch: `main`
- Remote tracking: `origin/main`
- App entrypoint: `notebooks/spx_inventory_app.py`
- Launch command: `scripts/launch_app.sh`
- Verification command: `scripts/verify.sh`
- Daily export command: `scripts/export_daily_bundle.sh`
- Operator runbook: `docs/OPERATOR_RUNBOOK.md`
- Test count is intentionally not pinned here; run `uv run pytest`, or `uv run pytest --collect-only` if a count is needed.
- The app is a marimo-based reference and operating framework for 0DTE SPX/SPXW inventory work.

## Module Responsibilities

- `src/spx_inventory_playbook/reference.py`: compact professional reference cards.
- `src/spx_inventory_playbook/validators.py`: inventory state dataclasses and validation messages.
- `src/spx_inventory_playbook/operator_inputs.py`: typed R7 operator input object, validation, normalization into inventory/rule context, and serializable audit evidence for authorization passes.
- `src/spx_inventory_playbook/rules.py`: deterministic R6 authorization layer. Its top-level `RuleDecision` answers whether the operator can act, what is allowed or blocked, required confirmations, reasons, warnings, market-data state, and fixture/live classification.
- `src/spx_inventory_playbook/daily_export.py`: R8 deterministic local daily export bundle writer and `python -m` command.
- `scripts/launch_app.sh`: R10 fixture-default local Marimo launch wrapper.
- `scripts/verify.sh`: R10 founder-ready verification sequence wrapper.
- `scripts/export_daily_bundle.sh`: R10 fixture/default daily export wrapper.
- `src/spx_inventory_playbook/fixtures.py`: abstract fixture states for tests and UI smoke paths.
- `src/spx_inventory_playbook/calculators.py`: pure hedge and cost/friction calculators.
- `src/spx_inventory_playbook/positions.py`: position tracking, lifecycle helpers, and session summary math.
- `src/spx_inventory_playbook/playbook.py`: static operational playbook tables.
- `src/spx_inventory_playbook/prompts.py`: copy-ready session prompt templates.
- `tests/`: unit tests, row-count checks, compactness checks, and guardrail checks.

## App-Level Regression Coverage

R9 adds `tests/test_app_level_regressions.py`, a fixture-only regression layer over the main workstation boundaries:

- Notebook import and direct script execution remain valid without live credentials.
- Session lifecycle start, authorization, close, and invalid authorization paths remain deterministic and fail closed.
- Local session metadata, lifecycle events, and inventory ledger records can be written, restored after restart, and exported.
- Missing or corrupt required state raises explicit safe errors.
- Fixture option-chain mode remains the default and does not call live fetchers.
- Live activation failures remain live failures and do not silently fall back to fixture data.
- Stale, unavailable, and parse-error market-data states remain distinct in rule/audit decisions.
- Daily exports preserve required sections, provenance, and fixture/live classifications.
- Rule-engine authorization remains the app/operator decision layer and operator-input audit evidence remains JSON-serializable.
- Token-like and credential-like strings are redacted from app/export artifacts using abstract placeholder values only.

Default verification remains non-live, credential-free, and fixture-safe.

## Notebook Position UI

- Position Entry: user-supplied position form and add action.
- Manage Positions: update mark, update Greeks, record adjustment, invalidate thesis, and close actions for open positions.
- Sidebar Dashboard / Position Summary: session summary and open/closed position display.

## Verification Commands

```bash
scripts/verify.sh
uv run marimo run notebooks/spx_inventory_app.py
```

`scripts/verify.sh` runs `uv run pytest`, `uv run ruff check .`, and `uv run python notebooks/spx_inventory_app.py` without hiding failed command output.

## Launch And Runbooks

R10 adds repo-owned local ergonomics:

```bash
scripts/launch_app.sh
scripts/verify.sh
scripts/export_daily_bundle.sh
```

`scripts/launch_app.sh` starts the Marimo workstation on `127.0.0.1:27182` by default. It is fixture-safe, does not require live credentials, does not read or print token files, does not call live APIs by default, and reports a port conflict instead of killing processes. Set `SPX_WORKSTATION_PORT` to use another local port.

`scripts/export_daily_bundle.sh` writes a fixture/default daily export under `.state/exports/daily/{trading_date}/{session_id}/`. It reuses the R8 export module, preserving redaction and provenance behavior.

Operational runbooks live in `docs/OPERATOR_RUNBOOK.md` and cover normal launch, verification, daily export, fixture/default operation, live-data gate behavior, degraded data, restart/recovery, troubleshooting, and the no-push boundary.

## Daily Export Bundle

R8/R10 provide a local, deterministic export path under the repo-owned state tree:

```bash
scripts/export_daily_bundle.sh 2026-05-04 fixture-2026-05-04
```

The command writes plain files under `.state/exports/daily/{trading_date}/{session_id}/`:

- `manifest.json`
- `daily_summary.md`
- `session.json`
- `event_ledger.json`
- `inventory_snapshot.json`
- `paper_intents.json`
- `market_data_summary.json`
- `authorization_snapshot.json`
- `operator_inputs.json`

The bundle records export schema/version, created timestamp, session id, trading date, app version when available, market-data provenance, session events, inventory snapshot, paper-intent records or an explicit empty collection, rule/authorization audit records, operator notes, and structured operator inputs when supplied.

Fixture, `live_fresh`, `live_stale`, `live_unavailable`, `live_parse_error`, and `missing` market-data states remain distinct. The export path does not call live APIs, read token files, print credentials, route orders, submit broker instructions, or imply automated execution. Secret-like fields and strings are redacted before writing.

## Live-Data-Safe Boundaries

- Live or near-live market data is permitted only from an approved adapter with source, timestamp, and freshness checks.
- User-supplied inputs remain permitted, but they are not the only permitted input source.
- Greeks, IV, bid/ask, strikes, expiries, marks, fills, and P/L must never be fabricated.
- Missing, stale, partial, or unverifiable data must fail closed, degrade confidence, or require manual confirmation.
- Operator-facing authorization in the notebook must derive from the rule-engine `RuleDecision`; fixture data is simulation-only and cannot grant live authorization.
- The Decision Console default path is structured operator input; fixture presets are available only as labeled simulation/demo inputs and still pass through validation.
- Daily exports are local evidence bundles only; they are not broker artifacts or order tickets.
- R10 launch, verify, and export wrappers are fixture-safe by default and do not read credential material.
- The app may provide bounded decision support: no-trade states, structure ranking, invalidation logic, risk warnings, and trade-plan checks.
- The app must not place trades, route orders, or present itself as an automated execution system.
- The app supports operator judgment; it does not replace trader responsibility.

## Known Non-Goals

- No strategy encyclopedia or beginner course.
- No automated order execution or broker order routing.

## Known Maintenance Hazards

- **`_value_frontend` (marimo private API):** The position-entry click-dedup logic in `notebooks/spx_inventory_app.py` reads `button._value_frontend` to get a monotonic click count from `mo.ui.run_button`. This is a private attribute (leading underscore) with no public-API guarantee. If marimo renames or removes it, the fallback in `run_button_click_count()` silently degrades to the original double-add-on-edit behavior. A CI test (`test_run_button_exposes_value_frontend`) fails loudly on breakage.
- **`app._cell_manager` (marimo private API):** The notebook smoke test uses `app._cell_manager.valid_cells()` to assert cells exist. Same upgrade risk pattern. A CI test (`test_app_exposes_cell_manager`) pins this contract.

## Next Safe Development Steps

- Add official source-link registry for Cboe/OCC/OIC/broker references.
- Refine marimo layout without changing doctrine.
- Add static export or publishing workflow.
- Add optional prompt-template input forms with explicit source and freshness fields.
- Add stronger app-level smoke tests.
