# Project Handoff

## Current Repo State

- Local branch: `main`
- Remote tracking: `origin/main`
- App entrypoint: `notebooks/spx_inventory_app.py`
- Test count is intentionally not pinned here; run `uv run pytest`, or `uv run pytest --collect-only` if a count is needed.
- The app is a marimo-based reference and operating framework for 0DTE SPX/SPXW inventory work.

## Module Responsibilities

- `src/spx_inventory_playbook/reference.py`: compact professional reference cards.
- `src/spx_inventory_playbook/validators.py`: inventory state dataclasses and validation messages.
- `src/spx_inventory_playbook/operator_inputs.py`: typed R7 operator input object, validation, normalization into inventory/rule context, and serializable audit evidence for authorization passes.
- `src/spx_inventory_playbook/rules.py`: deterministic R6 authorization layer. Its top-level `RuleDecision` answers whether the operator can act, what is allowed or blocked, required confirmations, reasons, warnings, market-data state, and fixture/live classification.
- `src/spx_inventory_playbook/fixtures.py`: abstract fixture states for tests and UI smoke paths.
- `src/spx_inventory_playbook/calculators.py`: pure hedge and cost/friction calculators.
- `src/spx_inventory_playbook/positions.py`: position tracking, lifecycle helpers, and session summary math.
- `src/spx_inventory_playbook/playbook.py`: static operational playbook tables.
- `src/spx_inventory_playbook/prompts.py`: copy-ready session prompt templates.
- `tests/`: unit tests, row-count checks, compactness checks, and guardrail checks.

## Notebook Position UI

- Position Entry: user-supplied position form and add action.
- Manage Positions: update mark, update Greeks, record adjustment, invalidate thesis, and close actions for open positions.
- Sidebar Dashboard / Position Summary: session summary and open/closed position display.

## Verification Commands

```bash
uv run pytest
uv run python notebooks/spx_inventory_app.py
uv run marimo run notebooks/spx_inventory_app.py
```

## Live-Data-Safe Boundaries

- Live or near-live market data is permitted only from an approved adapter with source, timestamp, and freshness checks.
- User-supplied inputs remain permitted, but they are not the only permitted input source.
- Greeks, IV, bid/ask, strikes, expiries, marks, fills, and P/L must never be fabricated.
- Missing, stale, partial, or unverifiable data must fail closed, degrade confidence, or require manual confirmation.
- Operator-facing authorization in the notebook must derive from the rule-engine `RuleDecision`; fixture data is simulation-only and cannot grant live authorization.
- The Decision Console default path is structured operator input; fixture presets are available only as labeled simulation/demo inputs and still pass through validation.
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
