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
- `daily_export.py`: Local daily export bundle.
- `notebooks/spx_inventory_app.py`: marimo UI shell.
- `scripts/`: Local launch, verification, and export wrappers.
- `tests/`: unit tests and guardrail checks.
- `docs/FOUNDER_READY_ACCEPTANCE.md`: final accepted local operating envelope and hard boundaries.

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

Run founder-ready verification:

```bash
scripts/verify.sh
```

Smoke test the notebook script:

```bash
uv run python notebooks/spx_inventory_app.py
```

Launch the marimo app:

```bash
scripts/launch_app.sh
```

Export a fixture/default daily bundle:

```bash
scripts/export_daily_bundle.sh
```

See [Operator Runbook](docs/OPERATOR_RUNBOOK.md) for normal launch, verification, daily export, live-data safety, restart/recovery, and troubleshooting. See [Founder-Ready Acceptance](docs/FOUNDER_READY_ACCEPTANCE.md) for the final accepted operating envelope and hard boundaries.

## Roadmap Position

R12 controlled Marimo live runtime wiring is complete and verified at commit `5e63a7ea5f95fe6cdaca0917627920083e02d004`.

R13 Single-Active-App Schwab Token Manager is complete. This repo is self-sufficient for Schwab token refresh when it is the active 0DTE live app. R13 does not retire `ntb-marimo-console`; that repo remains allowed as a donor/reference and as a separate live harness only when this app is shut down. Do not run this app live and `ntb-marimo-console` live simultaneously.

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

- R14 Hybrid Continuous Market Data Architecture Audit: determine which SPX/SPXW data comes from Schwab REST versus Streamer, confirm symbol/field support from documentation and donor harness behavior, define source/freshness labels for price, selected option quotes, chain snapshots, Greeks, ATM straddle context, and liquidity, and define fail-closed authorization behavior when any required source is stale or unavailable.
- R15 Hybrid REST Chain/Greeks Refresh + Streamer Quote Cache Implementation: one active Schwab streamer sidecar/cache for supported continuous price and selected option quote fields, conservative REST refresh for full chain discovery/snapshots and Greeks when provided by REST, Marimo cache-snapshot reads, and no long-running WebSocket loop inside ordinary notebook cells.
- R16 Continuous Market Data Panel Integration: surface source, last update time, age, and freshness classification for every live market-data field, and use freshness to gate live-dependent authorization while preserving fixture-safe defaults and explicit live opt-in.
- Open Schwab documentation questions: official REST limits for chains/quotes/pricehistory, numeric Streamer symbol limits, whether `$SPX`/SPXW index options stream through `LEVELONE_OPTIONS`, `OPTIONS_BOOK`, both, or neither, and whether Greeks are available via streaming fields or only REST chain snapshots.
- Optional source-link registry using official Cboe/OCC/OIC/broker references only.
- Optional layout refinement.
- Optional export/static publishing workflow.
- Optional user-input form generation for prompt templates.
- Optional stronger app-level smoke tests.

## Founder-Ready Completion Roadmap

- [Founder-ready roadmap](docs/founder_ready_roadmap.md)
- [Orchestration state](docs/orchestration_state.md)
- [Founder-ready acceptance](docs/FOUNDER_READY_ACCEPTANCE.md)
- [Project handoff](docs/HANDOFF.md)
