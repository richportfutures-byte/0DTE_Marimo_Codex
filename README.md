# 0DTE SPX/SPXW Inventory Reference App

A standalone Python/marimo app for professional 0DTE SPX/SPXW inventory reference and operating discipline.

This repo is a compact reference and workflow shell. It is not a signal engine, not a live trading system, and not personalized financial advice.

## Architecture Map

- `reference.py`: Professional Reference Cards.
- `validators.py`: Inventory State Validation.
- `rules.py`: Deterministic Rule Evaluation.
- `fixtures.py`: Abstract Fixture States.
- `calculators.py`: Mechanical Calculators.
- `positions.py`: Position tracking, lifecycle helpers, and session summary math.
- `playbook.py`: Inventory Adjustment Playbook.
- `prompts.py`: Session-Specific Prompt Workflow.
- `notebooks/spx_inventory_app.py`: marimo UI shell.
- `tests/`: unit tests and guardrail checks.

## Safety Boundaries

- No live market data.
- No fabricated Greeks, bid/asks, fills, strikes, or P/L.
- No automated trade recommendations.
- Not personalized financial advice.
- User-supplied inputs only for calculators and prompt workflow.
- Reference cards are encoded from prompt-supplied doctrine, not assumed uploaded documents.

## Commands

Install or sync the environment:

```bash
uv sync
```

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

## Current App Sections

- Professional Reference Cards
- Fixture State
- Selected State Summary
- Validation Messages
- Rule Decision
- Mechanical Calculators
- Inventory Adjustment Playbook
- Session-Specific Prompt Workflow
- Position Entry
- Manage Positions
- Sidebar Dashboard / Position Summary

## Acceptance Checklist

- `uv run pytest`
- `uv run python notebooks/spx_inventory_app.py`
- Browser review of dropdowns and calculators
- Browser review of Position Entry add flow
- Browser review of Manage Positions update, adjustment, thesis invalidation, and close flows
- Browser review of Sidebar Dashboard / Position Summary updates after position changes
- Confirm no fake market data appears
- Confirm no recommendation language appears

## Future Work Backlog

- Optional source-link registry using official Cboe/OCC/OIC/broker references only.
- Optional layout refinement.
- Optional export/static publishing workflow.
- Optional user-input form generation for prompt templates.
- Optional stronger app-level smoke tests.
