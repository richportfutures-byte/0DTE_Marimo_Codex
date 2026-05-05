# Project Handoff

## Current Repo State

- Local branch: `main`
- Remote tracking: `origin/main`
- App entrypoint: `notebooks/spx_inventory_app.py`
- Launch command: `scripts/launch_app.sh`
- Verification command: `scripts/verify.sh`
- Daily export command: `scripts/export_daily_bundle.sh`
- Operator runbook: `docs/OPERATOR_RUNBOOK.md`
- Founder-ready acceptance: `docs/FOUNDER_READY_ACCEPTANCE.md`
- Test count is intentionally not pinned here; run `uv run pytest`, or `uv run pytest --collect-only` if a count is needed.
- The app is a marimo-based reference and operating framework for 0DTE SPX/SPXW inventory work.
- Roadmap status: R12 controlled Marimo live runtime wiring complete; R13
  Single-Active-App Schwab Token Manager is the next active roadmap step.

## Module Responsibilities

- `src/spx_inventory_playbook/reference.py`: compact professional reference cards.
- `src/spx_inventory_playbook/validators.py`: inventory state dataclasses and validation messages.
- `src/spx_inventory_playbook/operator_inputs.py`: typed R7 operator input object, validation, normalization into inventory/rule context, and serializable audit evidence for authorization passes.
- `src/spx_inventory_playbook/rules.py`: deterministic R6 authorization layer. Its top-level `RuleDecision` answers whether the operator can act, what is allowed or blocked, required confirmations, reasons, warnings, market-data state, and fixture/live classification.
- `src/spx_inventory_playbook/daily_export.py`: R8 deterministic local daily export bundle writer and `python -m` command.
- `scripts/launch_app.sh`: R10 fixture-default local Marimo launch wrapper.
- `scripts/verify.sh`: R10 founder-ready verification sequence wrapper.
- `scripts/export_daily_bundle.sh`: R10 fixture/default daily export wrapper.
- `src/spx_inventory_playbook/marimo_option_chain_toggle.py`: controlled
  notebook option-chain source selection, live-gate evaluation, provider result
  classification, and last-successful live-context retention rule.
- `src/spx_inventory_playbook/adapters/live_schwab_option_chain_provider.py`:
  manually gated Schwab `$SPX` option-chain market-data harness. It is
  market-data only and returns sanitized provider metadata.
- `src/spx_inventory_playbook/fixtures.py`: abstract fixture states for tests and UI smoke paths.
- `src/spx_inventory_playbook/calculators.py`: pure hedge and cost/friction calculators.
- `src/spx_inventory_playbook/positions.py`: position tracking, lifecycle helpers, and session summary math.
- `src/spx_inventory_playbook/playbook.py`: static operational playbook tables.
- `src/spx_inventory_playbook/prompts.py`: copy-ready session prompt templates.
- `tests/`: unit tests, row-count checks, compactness checks, and guardrail checks.

## App-Level Regression Coverage

R9 adds `tests/test_app_level_regressions.py`, a fixture-only regression layer over the main workstation boundaries. R11 adds `tests/test_founder_ready_acceptance.py` to pin the final documentation and script-level acceptance boundaries:

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

## R12 Controlled Live Runtime Wiring

R12 connects the already-approved live Schwab option-chain provider boundary to
the notebook's option-chain panel under explicit operator opt-in. This is
display-only market-data wiring, not broker integration, order routing,
execution, account access, positions import, fill import, or P/L import.

R12 is complete and verified at commit
`5e63a7ea5f95fe6cdaca0917627920083e02d004`.

The notebook defaults to `Fixture/static option chain`. A live request can occur
only when the operator selects `Live Schwab option chain`, enters the exact
confirmation phrase `capture-live-option-chain-selection`, launches with a local
token-file source, and clicks **Refresh Option Chain**. The notebook runtime
uses only the repo-native token environment variable
`SPX_OPTION_CHAIN_LIVE_TOKEN_FILE`.

The refresh path stores the current provider result in notebook state and
classifies it as `fixture`, `live_fresh`, `live_stale`, `live_unavailable`, or
`live_parse_error`. Live failures remain live failures and never fall back to
fixture data. Last-successful retained context is limited to explicitly
fresh/aging live option-chain results.

## R13 Next: Single-Active-App Schwab Token Manager

R13 is the next active roadmap step. It means `0DTE_Marimo_Codex` becomes
self-sufficient for Schwab token refresh when it is the active 0DTE live app.
It does not delete, retire, or permanently disable `ntb-marimo-console`.

Schwab live ownership doctrine:

- One Schwab registered developer app / key-secret-callback configuration.
- Multiple local repos may use that Schwab app configuration serially.
- Only one Schwab-authenticated live process should be active at a time.
- Do not run `0DTE_Marimo_Codex` live and `ntb-marimo-console` live
  simultaneously.
- `ntb-marimo-console` remains allowed as a donor/reference repo.
- `ntb-marimo-console` remains allowed as a separate live harness only when
  `0DTE_Marimo_Codex` is shut down.
- `0DTE_Marimo_Codex` is the primary implementation target for the 0DTE
  workstation.

R13 implementation scope is limited to an 0DTE-native token manager, refresh
before a live option-chain REST request when needed, atomic token-file rewrite,
refresh-token preservation when Schwab omits a replacement refresh token,
fail-closed refresh failure handling, no fixture fallback after live failure,
and mocked tests only.

R13 explicitly excludes automatic refresh loops, streaming sidecars, order
routing, account access, fills, positions import, P/L import,
broker/execution integration, and official Schwab REST rate-limit claims.

After R13, the live-data roadmap is hybrid rather than REST-only or
streamer-only. R14 is reserved for a Hybrid Continuous Market Data Architecture
Audit that decides which SPX/SPXW data comes from REST and which comes from
Schwab Streamer, confirms symbol/field support, defines source/freshness labels
for underlying price, selected option quotes, chain snapshots, Greeks, ATM
straddle context, and liquidity, and defines fail-closed behavior when any
required source is stale or unavailable.

R15 is reserved for Hybrid REST Chain/Greeks Refresh + Streamer Quote Cache
Implementation. REST should handle full option-chain discovery, chain
snapshots, expiration/strike universe, ATM straddle context, liquidity, and
Greeks when provided by the REST chain endpoint. Schwab Streamer should handle
continuous underlying and selected option quote updates where the symbols and
fields are supported. Do not claim full-chain streaming or streaming Greeks
unless Schwab documentation proves it. Marimo must read cache/state snapshots
instead of owning a long-running WebSocket loop inside ordinary notebook cells.

R16 is reserved for Continuous Market Data Panel Integration: show source, last
update time, age, and freshness classification for every live market-data
field, and use freshness to gate live-dependent authorization. Open Schwab
questions remain for official REST limits for chains/quotes/pricehistory,
numeric Streamer symbol limits, whether `$SPX`/SPXW options stream through
`LEVELONE_OPTIONS`, `OPTIONS_BOOK`, both, or neither, and whether Greeks are
available via streaming fields or only REST chain snapshots.

## Founder-Ready Acceptance

R11 accepts the repo as a local-first personal 0DTE SPX/SPXW inventory workstation, not a scaffold, SaaS product, broker submission system, order-routing tool, or automated execution system. The accepted envelope is documented in `docs/FOUNDER_READY_ACCEPTANCE.md`.

The supported operator commands are:

```bash
scripts/launch_app.sh
scripts/verify.sh
scripts/export_daily_bundle.sh
```

Default launch, verification, tests, notebook smoke, and fixture/default export paths remain deterministic, non-live, credential-free, and fixture-safe. Live data requires explicit operator opt-in and must fail as live data; it must not silently fall back to fixture authorization. Token files are not read or printed by tests or default commands.

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
