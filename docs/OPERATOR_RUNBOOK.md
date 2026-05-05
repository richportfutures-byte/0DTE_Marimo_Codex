# Operator Runbook

This workstation is local-first, fixture-default, and fail-closed. It provides bounded decision support and local evidence capture only. It does not place trades, route orders, submit broker instructions, or automate execution.

## Normal Launch

From the repo root:

```bash
scripts/launch_app.sh
```

Default launch uses `127.0.0.1:27182`, fixture-safe app behavior, and no live credentials. The script does not read token files, print environment variables, or call live APIs.

To choose another local port:

```bash
SPX_WORKSTATION_PORT=27183 scripts/launch_app.sh
```

If the port is already in use, the script exits and reports the conflict. Choose another port or stop the existing local server yourself.

## Verification

Run the founder-ready local verification sequence:

```bash
scripts/verify.sh
```

This runs:

```bash
uv run pytest
uv run ruff check .
uv run python notebooks/spx_inventory_app.py
```

The script is non-live by default and exits nonzero on the first failed command. It does not hide command output.

## Daily Export

Create a fixture/default local evidence bundle:

```bash
scripts/export_daily_bundle.sh
```

The default output path is:

```text
.state/exports/daily/{trading_date}/fixture-{trading_date}/
```

To export a specific date and session id:

```bash
scripts/export_daily_bundle.sh 2026-05-04 fixture-2026-05-04
```

The export command uses the R8 daily export module, writes under the repo-owned `.state` tree, preserves provenance classification, and redacts token-like fields. It does not require live credentials.

## Fixture Operation

Fixture mode is the safe default for launch, verification, tests, and example exports. Fixture data is simulation-only and cannot grant live authorization. Missing, stale, partial, malformed, or unverifiable data remains blocked, restricted, or manually confirmed by the rule engine.

## Live-Data Gate

Live option-chain data is controlled runtime wiring in the notebook, not broker integration or execution. Live mode requires explicit operator selection, the exact confirmation phrase enforced by the provider boundary, a configured local credential source initialized outside the notebook, and a manual **Refresh Option Chain** click. Dropdown changes alone do not call the live provider.

The notebook expects the repo-native token-file environment variable:

```bash
SPX_OPTION_CHAIN_LIVE_TOKEN_FILE=/path/to/local/token.json scripts/launch_app.sh
```

When the token manager determines that the access token is expired or near
expiry, the explicit live path reads `SCHWAB_APP_KEY` and `SCHWAB_APP_SECRET`
from the local environment to refresh before the Schwab option-chain REST
request. `SCHWAB_OAUTH_TOKEN_URL` may override the OAuth token endpoint for
tests or local override. Fixture/default mode does not require those variables
and does not read real token files. `SCHWAB_TOKEN_PATH` is not used by the
notebook runtime path.

Inside the notebook:

1. Set **Option-chain source** to `Live Schwab option chain`.
2. Enter the exact phrase `capture-live-option-chain-selection`.
3. Click **Refresh Option Chain**.

Default launch and verification commands do not activate live mode, read token files, or call live APIs.

Do not print credential environment variables. Do not paste tokens into docs, tests, or runbooks. A live failure must remain a live failure; do not treat it as fixture authorization.

## Single-Active Schwab Ownership

The 0DTE workstation is the primary implementation target for live 0DTE
option-chain work. R13 adds an 0DTE-native Schwab token manager so
`0DTE_Marimo_Codex` can refresh tokens when it is the active live app.

Use one Schwab registered developer app / key-secret-callback configuration
serially across local repos. Do not run `0DTE_Marimo_Codex` live and
`ntb-marimo-console` live at the same time. `ntb-marimo-console` remains allowed
as a donor/reference repo, and it may be used as a separate live harness only
when `0DTE_Marimo_Codex` is shut down.

R13 remains fail-closed: token refresh failures must surface as live failures,
must not fall back to fixture data, and must not print, display, commit, export,
or log credential material. R13 does not add automatic refresh loops, streaming
sidecars, order routing, account access, fills, positions import, P/L import,
broker/execution integration, or official Schwab REST rate-limit claims.

## Hybrid Continuous Market Data Direction

After R13, the planned live-data architecture is hybrid. REST remains the
source for option-chain discovery, full chain snapshots, expiration/strike
universe, ATM straddle context, chain-level liquidity, and Greeks when the REST
chain endpoint provides them. Schwab Streamer/WebSocket is planned for
continuous underlying price and selected option quote updates where Schwab
supports the symbols and fields.

The app must not claim full-chain streaming or streaming Greeks unless Schwab
documentation proves those capabilities. Full chain and Greeks should update
continuously only to the extent safely allowed by documented Schwab REST limits
or conservative operational assumptions; do not use aggressive undocumented
REST polling. Every live market-data field must expose source, last update
time, age, and freshness classification, and stale or unavailable data must
block live-dependent authorization.

Marimo should read cache/state snapshots from a single-active sidecar/cache. It
must not own a long-running WebSocket loop inside ordinary notebook cells.

Open Schwab support/documentation questions remain for official REST limits for
chains/quotes/pricehistory, numeric Streamer symbol limits, whether
`$SPX`/SPXW index options stream through `LEVELONE_OPTIONS`, `OPTIONS_BOOK`,
both, or neither, and whether Greeks are available via streaming fields or only
REST chain snapshots.

## Data Degradation

- `fixture`: simulation-only, not live authorization.
- `live_fresh`: eligible for rule-engine evaluation.
- `live_stale`: restricted; refresh live data before discretionary action.
- `live_unavailable`: blocked; restore live data before live action.
- `live_parse_error`: blocked; repair parsing/data shape before live action.
- `missing`: blocked or unknown; load valid data before live action.

## Restart And Recovery

Local state lives under `.state/`. The app and export tooling should treat missing or corrupt state as explicit failure, not as permission to invent values.

If state is missing or corrupt:

1. Stop and preserve the existing `.state` directory for review.
2. Run `scripts/verify.sh` to separate code failures from local data failures.
3. Use fixture/default launch or export to continue safe review without live authorization.
4. Record any manual correction as a new audit-preserving event when a workflow exists for that correction.

## Troubleshooting

- Dirty git status before roadmap work: stop, inspect `git status --short`, and do not mix unrelated edits into the roadmap step.
- Failed pytest: read the failing test and fix the narrow behavior it protects before rerunning verification.
- Failed ruff: fix the reported file/line; do not suppress lint without a specific reason.
- Notebook smoke failure: run `uv run python notebooks/spx_inventory_app.py` and inspect the traceback; default smoke must not require credentials.
- Port already in use: rerun with `SPX_WORKSTATION_PORT=<free-local-port> scripts/launch_app.sh`.
- Missing local state: use fixture/default mode or restore the expected `.state` files; do not invent session evidence.
- Corrupt local state: preserve the corrupt file, fail closed, and restore from a known-good local backup if available.
- Export failure: check session id, trading date, `.state` path, and corrupt JSONL messages; rerun only after the source state is valid or use an explicit fixture/default export.

## Git Boundary

Do not push unless explicitly instructed.
