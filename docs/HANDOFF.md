# Project Handoff

## Current Repo State

- Local branch: `main`
- Remote tracking: `origin/main`
- App entrypoint: `notebooks/spx_inventory_app.py`
- Expected test count at time of writing: 89
- The app is a marimo-based reference and operating framework for 0DTE SPX/SPXW inventory work.

## Module Responsibilities

- `src/spx_inventory_playbook/reference.py`: compact professional reference cards.
- `src/spx_inventory_playbook/validators.py`: inventory state dataclasses and validation messages.
- `src/spx_inventory_playbook/rules.py`: deterministic permission logic for inventory actions.
- `src/spx_inventory_playbook/fixtures.py`: abstract fixture states for tests and UI smoke paths.
- `src/spx_inventory_playbook/calculators.py`: pure hedge and cost/friction calculators.
- `src/spx_inventory_playbook/playbook.py`: static operational playbook tables.
- `src/spx_inventory_playbook/prompts.py`: copy-ready session prompt templates.
- `tests/`: unit tests, row-count checks, compactness checks, and guardrail checks.

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

## Next Safe Development Steps

- Add official source-link registry for Cboe/OCC/OIC/broker references.
- Refine marimo layout without changing doctrine.
- Add static export or publishing workflow.
- Add optional prompt-template input forms using user-supplied fields only.
- Add stronger app-level smoke tests.
