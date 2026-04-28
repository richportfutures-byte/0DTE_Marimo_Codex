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
- `src/spx_inventory_playbook/rules.py`: deterministic permission logic for inventory actions.
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

## Known Non-Goals

- No live market data.
- No fabricated Greeks, bid/asks, fills, strikes, or P/L.
- No automated trade recommendations.
- No personalized financial advice.
- No strategy encyclopedia or beginner course.
- No live broker or market-data access claims.

## Known Maintenance Hazards

- **`_value_frontend` (marimo private API):** The position-entry click-dedup logic in `notebooks/spx_inventory_app.py` reads `button._value_frontend` to get a monotonic click count from `mo.ui.run_button`. This is a private attribute (leading underscore) with no public-API guarantee. If marimo renames or removes it, the fallback in `run_button_click_count()` silently degrades to the original double-add-on-edit behavior. A CI test (`test_run_button_exposes_value_frontend`) fails loudly on breakage.
- **`app._cell_manager` (marimo private API):** The notebook smoke test uses `app._cell_manager.valid_cells()` to assert cells exist. Same upgrade risk pattern. A CI test (`test_app_exposes_cell_manager`) pins this contract.

## Next Safe Development Steps

- Add official source-link registry for Cboe/OCC/OIC/broker references.
- Refine marimo layout without changing doctrine.
- Add static export or publishing workflow.
- Add optional prompt-template input forms using user-supplied fields only.
- Add stronger app-level smoke tests.
