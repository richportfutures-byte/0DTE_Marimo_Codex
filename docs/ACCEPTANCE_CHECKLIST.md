# Acceptance Checklist

- Repo is clean: `git status --short`
- Tests pass: `uv run pytest`
- Notebook smoke test passes: `uv run python notebooks/spx_inventory_app.py`
- marimo browser launches: `uv run marimo run notebooks/spx_inventory_app.py`
- All dropdowns work.
- Calculators accept valid input and reject invalid input.
- Position Entry adds one position per click.
- Manage Positions can update marks and Greeks.
- Manage Positions can record adjustments, invalidate thesis, and close positions.
- Sidebar Dashboard / Position Summary updates after position add/manage actions.
- Playbook tables render.
- Prompt templates render.
- Reference cards render.
- No fabricated market data appears.
- Bounded decision-support language remains risk-gated.
- No automated order execution language appears.
