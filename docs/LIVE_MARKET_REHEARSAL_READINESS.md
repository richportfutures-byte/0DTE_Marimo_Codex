# Live-Market Rehearsal Readiness

This checklist separates fixture rehearsal readiness from the manually gated
Schwab market-data harness. The current state is:

- Fixture rehearsal readiness is complete for local paper practice.
- The manual live Schwab option-chain harness has been proven once after a token
  refresh.
- Marimo now has controlled live runtime wiring for display-only option-chain
  cells under explicit operator opt-in.
- The current step is not broker integration and not execution.

All live harness work is market-data-only. It does not submit broker orders and
does not connect to account, order, position, fill, or P&L APIs. Option-chain
data remains display-only context and must not change trade authorization.

## Fixture Rehearsal Readiness

- Run `uv run pytest tests/test_live_market_rehearsal_readiness.py`.
- Confirm the overall status is `ready_for_fixture_rehearsal`.
- Confirm the fixture provider loads the app-owned sanitized option-chain file.
- Confirm freshness is `static_fixture`, not live or fresh market data.
- Confirm context flags are display-only and do not authorize trades.
- Confirm the paper ledger accepts an acknowledged static-fixture paper intent.
- Confirm the paper ledger rejects the same intent without acknowledgement.
- Confirm no live provider is active inside the Marimo fixture rehearsal path.

## Human Rehearsal Steps

- Open the Marimo app in fixture mode.
- Reload the fixture panel manually and verify the visible static-fixture label.
- Review the display-only option-chain context flags.
- Record a local paper intent only after acknowledging the static fixture context.
- Treat every recorded intent as local practice metadata, not a live order.
- Stop the rehearsal if fixture data is confused with live market data.

## Manual Live Schwab Harness

Purpose: run one operator-initiated Schwab `$SPX` option-chain market-data
request, parse it through the existing selection path, and print sanitized
summary diagnostics only. This harness remains the separate manual live
rehearsal command; the notebook uses the same approved provider boundary only
after explicit live source selection, the exact confirmation phrase, a
configured token-file source, and a manual refresh.

Safe command shape with a local token JSON file:

```bash
uv run python scripts/capture_live_schwab_option_chain_selection.py \
  --confirm-live capture-live-option-chain-selection \
  --access-token-file <PATH_TO_LOCAL_SCHWAB_TOKEN_JSON>
```

Safe command shape with a token supplied on standard input:

```bash
printf '<ACCESS_TOKEN_OR_LOCAL_TOKEN_JSON>' | uv run python scripts/capture_live_schwab_option_chain_selection.py \
  --confirm-live capture-live-option-chain-selection \
  --access-token-stdin
```

The required manual gate phrase is:

```text
capture-live-option-chain-selection
```

For notebook runtime wiring, launch with the repo-native token-file source
configured outside Marimo:

```bash
SPX_OPTION_CHAIN_LIVE_TOKEN_FILE=<PATH_TO_LOCAL_SCHWAB_TOKEN_JSON> scripts/launch_app.sh
```

`SCHWAB_TOKEN_PATH` is not used by the notebook runtime path. In plain text:
SCHWAB_TOKEN_PATH is not used by the notebook runtime path.

The notebook does not display the token path or token contents.

Expected sanitized success fields from the proven manual run:

```text
live_mode_used: yes
provider_status: available
provider_symbol: $SPX
underlying_symbol: SPX
selected_expiration: 2026-05-04
selected_dte: 2
atm_strike: 7230.0
atm_straddle_status: available
atm_straddle_value: 43.25
selected_contract_count: 4
freshness_status: fresh
data_context: fresh_live
operator_warning_level: info
```

Known precondition: an expired or stale Schwab token can fail safely with
`http_401_unauthorized`. Refresh the token through the existing local helper
workflow before retrying the manual harness. The harness must not print raw
payload bodies, token values, secrets, Authorization headers, API keys, client
secrets, callback URL values, or token contents.

## Boundaries

- Marimo live option-chain wiring is controlled, display-only, operator-gated,
  and fail-closed.
- Fixture mode remains the default for launch, tests, verification, and fixture
  rehearsal.
- This documentation does not add timed or automatic refresh loops.
- This documentation does not add Schwab account, order, position, fill, or P&L
  integration.
- This documentation does not add broker execution affordances or order buttons.
- This documentation does not alter playbook authorization or state-machine
  logic.
