# Acceptance Checklist

- Repo is clean: `git status --short`
- Tests pass: `uv run pytest`
- Notebook smoke test passes: `uv run python notebooks/spx_inventory_app.py`
- marimo browser launches: `uv run marimo run notebooks/spx_inventory_app.py`
- All dropdowns work.
- Calculators accept valid input and reject invalid input.
- Playbook tables render.
- Prompt templates render.
- Reference cards render.
- No fake market data appears.
- No trade recommendations appear.
