# 0DTE SPX Inventory Reference App

This project is a standalone Python/marimo reference app for an experienced intraday trader managing 0DTE SPX/SPXW option inventory.

The app is planned as a compact operator reference, not as a live trading system. Future work will organize reference material, deterministic inventory adjustment rules, and session-specific prompt workflows that rely only on user-supplied live or recent market context.

## Non-Goals

- Not a signal engine
- Not personalized financial advice
- Not a beginner options course
- No fabricated live data
- No automated trade recommendations

## Planned Architecture

- `reference.py`: static reference card definitions for market structure and options concepts.
- `rules.py`: deterministic rule scaffolding for hold, reduce, hedge, convert, close, and stop actions.
- `calculators.py`: small pure calculation helpers that avoid fabricated market inputs.
- `prompts.py`: prompt workflow templates that require user-supplied data.
- `validators.py`: input validation helpers for future app and rule layers.
- `notebooks/spx_inventory_app.py`: marimo interface entrypoint.
- `tests/`: focused unit tests for deterministic behavior.

## Commands

Run tests:

```bash
uv run pytest
```

Smoke test the notebook script:

```bash
uv run python notebooks/spx_inventory_app.py
```

Launch the marimo app:

```bash
uv run marimo run notebooks/spx_inventory_app.py
```
