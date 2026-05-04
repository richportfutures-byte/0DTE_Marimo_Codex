# 0DTE SPX/SPXW Inventory Reference App

A standalone Python/marimo app for professional 0DTE SPX/SPXW inventory reference and operating discipline.

This repo is a compact reference and operator decision-support shell for 0DTE SPX/SPXW inventory work.

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

## Live-Data-Safe Boundaries

- Live or near-live market data is permitted only from an approved adapter with source, timestamp, and freshness checks.
- User-supplied inputs remain permitted, but they are not the only permitted input source.
- Greeks, IV, bid/ask, strikes, expiries, marks, fills, and P/L must never be fabricated.
- Missing, stale, partial, or unverifiable data must fail closed, degrade confidence, or require manual confirmation.
- The app may provide bounded decision support: no-trade states, structure ranking, invalidation logic, risk warnings, and trade-plan checks.
- The app must not place trades, route orders, or present itself as an automated execution system.
- The app supports operator judgment; it does not replace trader responsibility.

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
- Confirm no fabricated market data appears
- Confirm bounded decision-support language remains risk-gated
- Confirm no automated order execution language appears

## Future Work Backlog

- Optional source-link registry using official Cboe/OCC/OIC/broker references only.
- Optional layout refinement.
- Optional export/static publishing workflow.
- Optional user-input form generation for prompt templates.
- Optional stronger app-level smoke tests.

## Founder-Ready Completion Roadmap

- [Founder-ready roadmap](docs/founder_ready_roadmap.md)
- [Orchestration state](docs/orchestration_state.md)
