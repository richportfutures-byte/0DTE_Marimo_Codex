# Live-Market Rehearsal Readiness

This checklist is fixture/paper-only readiness. It does not prove live Schwab
market-data readiness, does not submit broker orders, and does not connect to
account, order, position, fill, or P&L APIs.

## Local Harness

- Run `uv run pytest tests/test_live_market_rehearsal_readiness.py`.
- Confirm the overall status is `ready_for_fixture_rehearsal`.
- Confirm the fixture provider loads the app-owned sanitized option-chain file.
- Confirm freshness is `static_fixture`, not live or fresh market data.
- Confirm context flags are display-only and do not authorize trades.
- Confirm the paper ledger accepts an acknowledged static-fixture paper intent.
- Confirm the paper ledger rejects the same intent without acknowledgement.
- Confirm the live Schwab provider placeholder remains fail-closed with
  `live_provider_not_implemented`.

## Human Rehearsal Steps

- Open the Marimo app in fixture mode.
- Reload the fixture panel manually and verify the visible static-fixture label.
- Review the display-only option-chain context flags.
- Record a local paper intent only after acknowledging the static fixture context.
- Treat every recorded intent as local practice metadata, not a live order.
- Stop the rehearsal if fixture data is confused with live market data.
