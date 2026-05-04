# 0DTE SPX Inventory Workstation — Operator Tutorial

This tutorial maps every UI control in `notebooks/spx_inventory_app.py` to the
exact function it calls and the exact domain object it produces. Every behavioral
rule is sourced from the code (file:line). Examples use realistic 0DTE SPX
values (SPX ~5240, 5230/5220 put credit spread for $4.50, delta −0.08, etc.).

---

## 1. Boot order and harness facts

Run the app:

```
uv run marimo run notebooks/spx_inventory_app.py
```

Smoke-test the script entrypoint (used by `tests/test_notebook_smoke.py:31`):

```
uv run python notebooks/spx_inventory_app.py
```

What the notebook is **not** (enforced by source and tests):

- It does **not** place, route, modify, or cancel broker orders.
  `paper_trades.py:42` hardcodes `paper_disclaimer = "local_paper_intent_only_no_broker_submission"`,
  `paper_trades.py:79` rejects `broker_submitted=True` with reason
  `broker_submission_not_allowed`, and `tests/test_paper_trades.py:182` enforces
  that `paper_trades.py` does not import any module whose name contains
  `schwab`, `broker`, `account`, `order`, `fill`, `pnl`, `playbook`, `rules`,
  or `validators`.
- The live option-chain toggle does not import authorization modules.
  `tests/test_marimo_option_chain_toggle.py:218` enforces that
  `marimo_option_chain_toggle.py` imports none of
  `spx_inventory_playbook.playbook`, `.rules`, `.validators`, `.positions`.
- There is **no persistence**: `notebooks/spx_inventory_app.py:253-262`
  initializes session state via `mo.state(())` / `mo.state(0)` /
  `mo.state(PaperTradeLedger())`. Closing the browser tab discards positions,
  click counters, the option-chain provider result, and the paper ledger.

---

## 2. Top header strip — `@app.cell` at `notebooks/spx_inventory_app.py:325`

The header is a non-interactive HTML banner displaying live-derived values:

| Pill | Source value | Code |
|---|---|---|
| **Window** | `TIME_WINDOW_LABELS[current_time_window_selector.value]` | `notebooks/spx_inventory_app.py:352` |
| **Open** | `sum(1 for p in positions_state() if p.status is PositionStatus.OPEN)` | `notebooks/spx_inventory_app.py:338-340` |
| **Net P&L** | `calculate_session_summary(positions_state(), daily_budget_input.value or 2000.0).net_pnl` | `notebooks/spx_inventory_app.py:335-341` |
| **Budget used** | `summary.budget_used_pct` (color thresholds: <0.5 green, <0.8 yellow, ≥0.8 red) | `notebooks/spx_inventory_app.py:344-351` |

The `2000.0` fallback is hardcoded (`notebooks/spx_inventory_app.py:336,300`)
when the daily budget is `None` or `0`.

The **live-data-safe ribbon** (`notebooks/spx_inventory_app.py:377-390`) is
static copy; nothing on this app reads or writes broker state.

---

## 3. Market Data Readiness — `notebooks/spx_inventory_app.py:393-598`

### 3.1 Control: "Market-data display mode" dropdown
- Defined at `notebooks/spx_inventory_app.py:275-279`,
  `mo.ui.dropdown(options=PREVIEW_SCENARIO_LABELS, value="Default fail-closed", label="Market-data display mode")`.
- Values come from `market_data_preview.PREVIEW_SCENARIO_LABELS`
  (`market_data_preview.py:37-44`):
  - `"Default fail-closed"` → `default_fail_closed`
  - `"Healthy sanitized preview"` → `healthy_preview`
  - `"Stale underlying"` → `stale_underlying`
  - `"Partial option chain"` → `partial_chain`
  - `"Locked option liquidity"` → `locked_liquidity`
  - `"Missing ATM straddle"` → `missing_atm_straddle`
- Selection calls `build_market_data_preview_scenario(scenario_name)`
  (`market_data_preview.py:75`), which produces a
  `SanitizedMarketDataPreview` (`market_data_preview.py:58`) that wraps a
  `MarketDataFacadeResult` (`market_data_facade.py:16`) computed by
  `evaluate_market_data_facade(...)` (`market_data_facade.py:34`).

### 3.2 Fixture mechanics

The sanitized preview is keyed off `_PREVIEW_AS_OF =
datetime(2026, 4, 30, 10, 15, tzinfo=ZoneInfo("America/New_York"))` with
`_ATM_STRIKE = Decimal("5000")` (`market_data_preview.py:52-55`). The
underlying is hardcoded to bid 4999.75 / ask 5000.25 / last 5000.00
(`market_data_preview.py:191-194`); ATM call/put midpoints are 10.30 / 10.10.
**These are display fixtures, not market data.** The disclosure tuple
`("sanitized fixture", "not live", "not broker data", "for display verification only")`
(`market_data_preview.py:46-50`) is rendered as red chips at
`notebooks/spx_inventory_app.py:515-518`.

### 3.3 Health rules (sourced from `market_data_facade.py`)

`evaluate_market_data_facade` produces `health.status` per these rules:

| Code line | Rule |
|---|---|
| `market_data_facade.py:49-51` | If `underlying_quote is None` → blocker `"Underlying quote is missing."` |
| `market_data_facade.py:52-54` | If `underlying_quote.freshness is not FRESH` → blocker `"Underlying quote is not fresh."` |
| `market_data_facade.py:56-58` | If `option_chain is None` → blocker `"Option chain is missing."` |
| `market_data_facade.py:60-62` | If chain `freshness is not FRESH` → blocker `"Option chain is not fresh."` |
| `market_data_facade.py:63-66` | If `is_partial` → warning (uses `completeness_notes`, or fallback `"Option chain is partial."`) |
| `market_data_facade.py:68-70` | Any locked quote (`bid == ask`, see `market_data.py:211-212`) → warning `"Locked option quote detected; liquidity is degraded."` |
| `market_data_facade.py:72-74` | Any contract missing `delta/gamma/theta/vega/iv` → warning `"Greeks unavailable for at least one option quote."` |
| `market_data_facade.py:171-181` | `status = "BLOCKED"` if any blocker, else `"DEGRADED"` if any warning/missing/stale, else `"OK"` |

`api_outputs_usable` is True only when the underlying is fresh, the chain is
fresh and not partial and has no locked quote, and the ATM straddle is fresh
(`market_data_facade.py:99-103`).

`manual_confirmation_required = health.status != "OK"`
(`market_data_facade.py:126`).

### 3.4 Display panel — `notebooks/spx_inventory_app.py:451-597`

The panel renders three cards plus four lists:
- Severity ribbon: green/yellow/red per `_status_meta`
  (`notebooks/spx_inventory_app.py:466-485`).
- 12 `app-stat` tiles for mode, scenario, status, API outputs usable,
  manual-confirm-required, and three freshness pills
  (`notebooks/spx_inventory_app.py:526-565`).
- ATM straddle width: shown only when
  `atm_straddle is not None and market_data_readiness.atm_straddle_usable`
  (`notebooks/spx_inventory_app.py:436-439`).
- Blockers / warnings / missing fields / stale fields lists rendered from
  `_health.blockers`, `.warnings`, `.missing_fields`, `.stale_fields`
  (`notebooks/spx_inventory_app.py:568-579`).

> **Code gap (noted, not editorialized):** The Market Data Readiness panel and
> the Option Chain panel (Section 4) are independent — switching the readiness
> dropdown does **not** change the option-chain provider. They are two separate
> facades fed by separate fixtures.

---

## 4. Option Chain Source — `notebooks/spx_inventory_app.py:601-966`

### 4.1 Controls

| Widget | Defined at | Default | Maps to |
|---|---|---|---|
| `option_chain_mode_selector` (dropdown) | `notebooks/spx_inventory_app.py:280-287` | `FIXTURE_OPTION_CHAIN_MODE_LABEL = "Fixture/static option chain"` | `MarimoOptionChainControlState.selected_mode` (`marimo_option_chain_toggle.py:50`) |
| `option_chain_live_confirmation_input` (text) | `notebooks/spx_inventory_app.py:288-291` | `""` | Compared to `MANUAL_LIVE_CONFIRM_PHRASE = "capture-live-option-chain-selection"` (`live_schwab_option_chain_provider.py:40`) |
| `option_chain_refresh_button` (run_button) | `notebooks/spx_inventory_app.py:610` | not pressed | Triggers `load_marimo_option_chain_provider(...)` (`marimo_option_chain_toggle.py:138`) |

### 4.2 Refresh dispatch — `notebooks/spx_inventory_app.py:614-675`

1. Resolve token-file path: `resolve_live_token_file_path()` reads
   `SPX_OPTION_CHAIN_LIVE_TOKEN_FILE`, falling back to `SCHWAB_TOKEN_PATH`
   (`marimo_option_chain_toggle.py:101-112`). The file is never displayed —
   `marimo_option_chain_toggle.py:128-134` only stores the boolean flag and a
   label `"local token file configured"` or `"local token file missing"`. The
   regression test `tests/test_marimo_option_chain_toggle.py:201` enforces the
   path string is not in `repr(control_state)`.
2. Compute click count via `run_button_click_count(...)`
   (`notebooks/spx_inventory_app.py:317-322`). Refresh is only triggered when
   the count exceeds `option_chain_refresh_click_state()`
   (`notebooks/spx_inventory_app.py:638-642`); the first render also forces a
   refresh because `_previous_result is None`.
3. On refresh, calls `load_marimo_option_chain_provider(...)`
   (`marimo_option_chain_toggle.py:138-193`).
4. The result is stored via `set_option_chain_provider_result(...)`. If
   `status == "available"`, `set_option_chain_last_successful_result(...)` is
   also updated, so a failed refresh keeps the most recent successful payload
   visible below the failure (`notebooks/spx_inventory_app.py:653-661`).

### 4.3 Source-selection rules — `marimo_option_chain_toggle.py:138`

The function returns a `MarimoOptionChainToggleResult`
(`marimo_option_chain_toggle.py:82`) wrapping a
`OptionChainProviderResult` (`option_chain_provider.py:37`),
`OptionChainFreshness` (`option_chain_freshness.py:30`), and
`OptionChainContextFlags` (`option_chain_context.py:30`).

| Branch | Condition | Outcome |
|---|---|---|
| `marimo_option_chain_toggle.py:156-162` | `selected_mode != LIVE_OPTION_CHAIN_MODE_LABEL` | Calls `FixtureOptionChainProvider(...).get_spx_0dte_selection()`. Source type `"fixture"`, `is_static_source=True`. Verified by `tests/test_marimo_option_chain_toggle.py:55-72`. |
| `marimo_option_chain_toggle.py:164-169` | live mode but `confirm_live != "capture-live-option-chain-selection"` | Returns blocked live `OptionChainProviderResult` with `reason_code="manual_live_confirmation_required"`. Verified by `tests/test_marimo_option_chain_toggle.py:87-105`. |
| `marimo_option_chain_toggle.py:171-176` | live mode + correct phrase but `live_token_file_path is None` | Blocked with `reason_code="access_token_required"`. Verified by `tests/test_marimo_option_chain_toggle.py:107-123`. |
| `marimo_option_chain_toggle.py:178-193` | live mode + correct phrase + token path configured | Calls `run_manual_live_schwab_option_chain_selection(...)` (`live_schwab_option_chain_provider.py:168`) which performs one HTTPS GET to `SCHWAB_OPTION_CHAIN_ENDPOINT = "https://api.schwabapi.com/marketdata/v1/chains"` (`live_schwab_option_chain_provider.py:41`). |

The live HTTP call is governed by `build_schwab_option_chain_request_spec`
(`live_schwab_option_chain_provider.py:104`):
- Symbol must be `"$SPX"` exactly (`:109-110`).
- `contractType` must be `"ALL"` (`:111-112`).
- `strategy` must be `"SINGLE"` (`:113-114`).
- `strikeCount` must be 1–20 inclusive (`:115-116`).
- `includeUnderlyingQuote` must be enabled (`:117-118`).

> **Live provider placeholder:** `LiveSchwabOptionChainProvider`
> (`option_chain_provider.py:137-151`) used by the rehearsal-readiness harness
> always returns `status="unavailable"`, `reason_code="live_provider_not_implemented"`.
> Only the manual-gated `run_manual_live_schwab_option_chain_selection` path
> can actually fetch live data. `tests/test_live_market_rehearsal_readiness.py`
> drives the placeholder via
> `live_market_rehearsal_readiness.py:165-171`.

### 4.4 Freshness classification — `option_chain_freshness.py:39`

Thresholds (`option_chain_freshness.py:24-27`): fresh ≤ 15.0s,
aging ≤ 60.0s, otherwise stale.

| Provider state | Result |
|---|---|
| `provider_result is None` | `status="unavailable"`, reason `provider_result_unavailable` |
| `status == "error"` | `status="invalid"` |
| `status == "unavailable"` | `status="unavailable"` |
| `is_static_source=True` (fixture) | `status="static_fixture"`, reason `static_fixture_not_live` |
| `loaded_at is None` and not static | `status="invalid"`, reason `loaded_at_unavailable` |
| Live & age ≤ 15.0s | `fresh` |
| Live & 15.0s < age ≤ 60.0s | `aging` |
| Live & age > 60.0s | `stale` |

### 4.5 Display-only context flags — `option_chain_context.py:40`

`build_option_chain_context_flags` produces an `OptionChainContextFlags`
(`option_chain_context.py:30`) with these fields. The rendered panel at
`notebooks/spx_inventory_app.py:782-803` calls them out as **"display only"**
and "These flags do not authorize trades or change playbook rules" — the
toggle module is firewalled from the rule engine
(see Section 1, and `tests/test_marimo_option_chain_toggle.py:218`).

`operator_warning_level` (`option_chain_context.py:154-167`):
- `data_context in {"invalid","unavailable"}` → `"blocked"`
- `data_context in {"static_fixture","stale_live"}` → `"caution"`
- Any reason code starting with `liquidity_`, `greeks_`, or `atm_straddle_` → `"caution"`
- Otherwise → `"info"`

Liquidity rule: `wide_spread_threshold = 1.0` in
`build_spx_0dte_selection_view(...)` (`schwab_option_chain_selection.py:69`).
A contract's spread is `wide` when `ask − bid > 1.0`, otherwise `acceptable`
(`schwab_option_chain_selection.py:114-135`).

### 4.6 Realistic example

Pretend SPX is at 5240 and the operator selects **Live Schwab option chain**,
types `capture-live-option-chain-selection` exactly, has
`SPX_OPTION_CHAIN_LIVE_TOKEN_FILE` pointing at a JSON file containing
`{"access_token": "..."}`, and clicks **Refresh Option Chain** at 10:32 ET.

If the GET succeeds and the parser returns one expiration with strikes
spaced 5 wide (5230/5235/5240/5245/5250), the ATM strike is 5240
(`schwab_option_chain_selection.py:84`). Because `strikes_below=2` and
`strikes_above=2` (default), the panel renders 5 strikes × 2 sides = up to 10
rows. If the 5230 put quotes 4.40 / 4.60 (spread 0.20) and the 5230 call
quotes 13.10 / 13.30 (spread 0.20), both rows render with the green
"acceptable" chip. If the 5220 put quotes 3.50 / 4.80 (spread 1.30 > 1.0),
the chain renders with `liquidity_context = "mixed"`
(`option_chain_context.py:114-126`) and a `liquidity_mixed` reason code.

If the request fails with HTTP 401 (`live_schwab_option_chain_provider.py:325-329`
maps codes 400 → `http_400_bad_request`, 401 → `http_401_unauthorized`,
others → `http_<code>_error`), the panel title becomes
`"Option Chain Failed Live Request"` (`notebooks/spx_inventory_app.py:828`),
the previous successful fixture/live result is preserved under
"Last successful result retained" (`notebooks/spx_inventory_app.py:804-823`),
and `tests/test_marimo_option_chain_toggle.py:147-183` confirms the access
token, raw payload markers, `Authorization` header, `Bearer` keyword,
`callExpDateMap`, and `putExpDateMap` strings never appear in the rendered
output.

---

## 5. Inventory Decision Console — `notebooks/spx_inventory_app.py:969-1179`

### 5.1 Controls

| Widget | Defined at | Default | Maps to |
|---|---|---|---|
| `fixture_selector` (dropdown) | `notebooks/spx_inventory_app.py:980-986` | `"Clean state"` | `fixture_factories[name]()` (`notebooks/spx_inventory_app.py:178-190`) → `InventoryState` |
| `current_time_window_selector` (dropdown) | `notebooks/spx_inventory_app.py:270-274` | `"Morning 9:45–10:30"` (`TimeWindow.MORNING_945_1030`) | Used by header, sidebar, and `time_urgency(...)` |
| `daily_budget_input` (number) | `notebooks/spx_inventory_app.py:263-269` | `2000.0`, step `100.0`, min `0.0` | `calculate_session_summary(positions, daily_budget=...)` |
| `market_data_mode_selector` | (Section 3) | — | Independent display facade |

The fixture dropdown options are the keys of `fixture_factories`
(`notebooks/spx_inventory_app.py:178-190`):

| Label | Factory | Module:line |
|---|---|---|
| Clean state | `clean_state` | `fixtures.py:43` |
| Lockout active | `lockout_state` | `fixtures.py:98` |
| Behavior not authorized | `behavior_not_authorized_state` | `fixtures.py:103` |
| Rule violation | `rule_violation_state` | `fixtures.py:108` |
| Thesis invalidated | `thesis_invalidated_state` | `fixtures.py:113` |
| Poor liquidity | `poor_liquidity_state` | `fixtures.py:124` |
| Final five minutes | `final_five_minutes_state` | `fixtures.py:129` |
| Size exceeds plan | `size_exceeds_plan_state` | `fixtures.py:137` |
| Loss avoidance risk | `loss_avoidance_state` | `fixtures.py:142` |
| Negative GEX credit spread | `negative_gex_credit_spread_state` | `fixtures.py:150` |
| Near flip unclear | `near_flip_unclear_state` | `fixtures.py:161` |

### 5.2 Pipeline — `notebooks/spx_inventory_app.py:1011-1021`

```
selected_state = fixture_factories[fixture_selector.value]()   # InventoryState
validation_result = validate_inventory_state(selected_state)    # ValidationResult
rule_decision = evaluate_inventory_rules(selected_state)        # RuleDecision
```

### 5.3 Validation rules — `validators.py:126`

Run in this fixed order (so the first to match in any later precedence layer
is the one displayed first). Each emits a `ValidationMessage`:

| Code | Severity | Trigger | Source |
|---|---|---|---|
| `LOCKOUT_ACTIVE` | BLOCKER | `daily_lockout_active or weekly_lockout_active` | `validators.py:130-140` |
| `BEHAVIOR_NOT_AUTHORIZED` | BLOCKER | `not behavior_authorized` | `validators.py:142-149` |
| `LOSS_AVOIDANCE_RISK` | WARNING | `trying_to_avoid_loss_realization` | `validators.py:151-158` |
| `RULE_VIOLATION` | BLOCKER | `rule_violation_occurred` | `validators.py:160-167` |
| `THESIS_INVALIDATED` | BLOCKER | `accepted_beyond_invalidation` | `validators.py:169-176` |
| `LIQUIDITY_POOR` | WARNING | `not market.liquidity_acceptable` | `validators.py:178-185` |
| `FINAL_5_MINUTES` | WARNING | `time_window is FINAL_5_1555_1600` | `validators.py:187-197` |
| `SIZE_EXCEEDS_PLAN` | WARNING | `position_size_exceeds_plan` | `validators.py:199-206` |

`ValidationResult.has_blockers()` returns True if any message has severity
BLOCKER (`validators.py:114-116`).

### 5.4 Rule decision precedence — `rules.py:109`

`evaluate_inventory_rules(state)` returns a `RuleDecision` (`rules.py:46`).
**Precedence is strict and hard-coded; the first match wins:**

| Order | Trigger code | `severity` | `allowed_actions` | Source |
|---|---|---|---|---|
| 1 | `LOCKOUT_ACTIVE` | `BLOCKED` | `FLATTEN_ONLY_ACTIONS = {CLOSE, EMERGENCY_FLATTEN, STOP_TRADING}` | `rules.py:19, 114-120` |
| 2 | `BEHAVIOR_NOT_AUTHORIZED` | `BLOCKED` | `BEHAVIOR_IMPAIRED_ACTIONS = {REDUCE, CLOSE, EMERGENCY_FLATTEN, HEDGE_MES_ES, STOP_TRADING}` | `rules.py:20-26, 122-130` |
| 3 | `RULE_VIOLATION` | `BLOCKED` | `BEHAVIOR_IMPAIRED_ACTIONS` | `rules.py:132-138` |
| 4 | `THESIS_INVALIDATED` | `BLOCKED` | `THESIS_INVALIDATED_ACTIONS = {REDUCE, CLOSE, EMERGENCY_FLATTEN, STOP_TRADING}` | `rules.py:27-32, 140-146` |
| 5 | `time_window is FINAL_5_1555_1600` | `RESTRICTED` | `FINAL_FIVE_MINUTE_ACTIONS = {CLOSE, EMERGENCY_FLATTEN, STOP_TRADING}` | `rules.py:33, 148-154` |
| 6 (compose) | `LIQUIDITY_POOR` and/or `LOSS_AVOIDANCE_RISK` | `CAUTION` | `FULL_DISCRETIONARY_ACTIONS − {CONVERT_RESTRUCTURE}` | `rules.py:160-173` |
| 7 (compose) | `SIZE_EXCEEDS_PLAN` (alone) | `CAUTION` (warning only) | `FULL_DISCRETIONARY_ACTIONS` | `rules.py:165-167, 175-182` |
| 8 (default) | no codes | `NORMAL` | `FULL_DISCRETIONARY_ACTIONS = {HOLD, TAKE_PARTIAL_PROFIT, REDUCE, HEDGE_MES_ES, CONVERT_RESTRUCTURE, CLOSE, STOP_TRADING}` | `rules.py:10-18, 184-188` |

Notes:
- `EMERGENCY_FLATTEN` is **never** in `FULL_DISCRETIONARY_ACTIONS`
  (`rules.py:10-18`). It is only allowed under lockout, behavior-impaired,
  rule-violation, thesis-invalidated, and final-5-minute states.
- Lockout overrides every lower-priority signal:
  `tests/test_rules.py:216-233` confirms that loss-avoidance + poor-liquidity +
  size-over-plan layered onto a lockout still yields exactly the lockout
  decision with `warnings == []`.
- `tests/test_rules.py:90-119` enforces that
  `allowed_actions_from_validation(validate_inventory_state(state)) ==
  evaluate_inventory_rules(state).allowed_actions` for every `*_state` fixture.

### 5.5 Worked example: 5230/5220 put credit spread, near-flip unclear

Operator at 10:32 ET, SPX 5240, holding 1× 5230/5220 put credit spread for
$4.50 entry credit, spread delta −0.08, gamma 0.012, theta +18 ($/day), max
loss per contract = $5.50 (= 10 width − 4.50). They select the
**Near flip unclear** fixture.

`near_flip_unclear_state()` (`fixtures.py:161-169`) overrides
`market.dealer_regime = NEAR_FLIP` and `market.spot_relative_to_flip = "unclear"`.
All other fields stay at `clean_state()` defaults.

Validation: no codes match — none of the BLOCKER/WARNING checks in
`validators.py:130-206` are triggered by `dealer_regime` or
`spot_relative_to_flip`.

> **Code gap (noted, not editorialized):** `validators.py:7-15` defines the
> `DealerRegime` enum with values `POSITIVE_GEX`, `NEGATIVE_GEX`, `NEAR_FLIP`,
> `EVENT_PINNED`, `POST_EVENT_VOL_CRUSH`, `UNCLEAR`, but neither
> `validate_inventory_state` (`validators.py:126`) nor `evaluate_inventory_rules`
> (`rules.py:109`) reads `state.market.dealer_regime`,
> `state.market.spot_relative_to_flip`, `state.market.event_pending`,
> `state.position.structure`, `state.position.thesis_valid` (only
> `accepted_beyond_invalidation` is read), `state.position.current_loss_inside_plan`,
> `state.position.gamma_manageable`, or `state.position.delta_intentional`.
> The dealer-regime, structure, and gamma/delta fields are surfaced in the
> "Inventory state" tile (`notebooks/spx_inventory_app.py:1134-1149`) but do
> not change the rule decision today.

Decision: severity `NORMAL`, allowed = `FULL_DISCRETIONARY_ACTIONS`
(`rules.py:184-188`). The panel renders green `app-severity--normal` ribbon
plus 7 green chips for HOLD / TAKE_PARTIAL_PROFIT / REDUCE / HEDGE_MES_ES /
CONVERT_RESTRUCTURE / CLOSE / STOP_TRADING and one red chip for
EMERGENCY_FLATTEN.

### 5.6 Worked example: same trade, **Final five minutes**

Same 5230/5220 put credit spread, now at 15:57. Operator selects
**Final five minutes** fixture. `final_five_minutes_state()`
(`fixtures.py:129-134`) sets `market.time_window = FINAL_5_1555_1600`.

Validation produces `FINAL_5_MINUTES` (WARNING).
`evaluate_inventory_rules` matches branch 5 (`rules.py:148-154`): severity
`RESTRICTED`, allowed = {CLOSE, EMERGENCY_FLATTEN, STOP_TRADING}, blocked =
all 5 others. The panel shows the orange "Restricted action set" ribbon and
exactly 3 green chips.

### 5.7 Worked example: lockout from a $2,300 day

Daily budget $2,000 already breached at 14:10 with closed-day P&L of −$2,300.
The operator selects **Lockout active**. `lockout_state()` sets
`behavior.daily_lockout_active = True` (`fixtures.py:98-100`). `LOCKOUT_ACTIVE`
fires (severity BLOCKER) and `evaluate_inventory_rules` matches branch 1:
allowed = `{CLOSE, EMERGENCY_FLATTEN, STOP_TRADING}`. The panel renders the
red "Action blocked" ribbon and reason
`"Daily or weekly lockout is active; discretionary adjustment is blocked."`.

The notebook does **not** wire `daily_budget_input` or `summary.budget_used_pct`
into `behavior.daily_lockout_active`; lockout is only set via the fixture
selector.

> **Code gap (noted, not editorialized):** Live trade flow does not flip
> lockout automatically. `validate_inventory_state` (`validators.py:126`)
> never reads session P&L, the daily budget, or position counts. Operator
> must select the lockout fixture to exercise that branch.

---

## 6. Paper Intent Ledger — `notebooks/spx_inventory_app.py:1182-1344`

### 6.1 Controls — `notebooks/spx_inventory_app.py:1183-1212`

`paper_intent_form` is a `mo.ui.dictionary` with five fields:

| Key | Widget | Default |
|---|---|---|
| `strategy_label` | `mo.ui.text(label="Paper strategy label", full_width=True)` | `""` |
| `thesis` | `mo.ui.text(label="Paper thesis", full_width=True)` | `""` |
| `invalidation` | `mo.ui.text(label="Paper invalidation", full_width=True)` | `""` |
| `notes` | `mo.ui.text(label="Practice notes", full_width=True)` | `""` |
| `acknowledge_context` | `mo.ui.checkbox(label="I acknowledge this is fixture/static context and a local paper record only", value=False)` | False |

`record_paper_intent_button = mo.ui.run_button(label="Record Paper Intent")`.

### 6.2 Click handler — `notebooks/spx_inventory_app.py:1215-1284`

On every click count > previous handled count:
1. Read the current option-chain provider result and its
   `selection_view.selected_expiration`.
2. Set `_entry_reference = selected_expiration.atm_straddle.value`
   (a float, the ATM call+put midpoints from
   `schwab_option_chain_selection.py:184-214`) when available.
3. Build legs from `expiration.contracts` filtered to
   `contract.strike == expiration.atm_strike` (so only the ATM call and ATM
   put end up as `PaperTradeLeg` entries).
4. Call `create_paper_trade_intent(...)` (`paper_trades.py:96`) producing a
   `PaperTradeIntent` (`paper_trades.py:23`). The intent always carries:
   - `is_paper_only=True` (`paper_trades.py:131`)
   - `broker_submitted=False` (`paper_trades.py:132`)
   - `paper_disclaimer="local_paper_intent_only_no_broker_submission"` (`paper_trades.py:42`)
   - The current `rule_decision.severity.value` and sorted allowed-action names.
5. Call `paper_trade_ledger_state().append(intent)` (`paper_trades.py:59-66`)
   which validates and either appends or returns the original ledger
   unchanged.

### 6.3 Validation rules — `paper_trades.py:69`

| Check | Reason code | Source |
|---|---|---|
| `strategy_label` empty/whitespace | `strategy_label_required` | `paper_trades.py:71-72` |
| `thesis` empty/whitespace | `thesis_required` | `paper_trades.py:73-74` |
| `invalidation` empty/whitespace | `invalidation_required` | `paper_trades.py:75-76` |
| `is_paper_only is False` | `paper_only_required` | `paper_trades.py:77-78` |
| `broker_submitted is True` | `broker_submission_not_allowed` | `paper_trades.py:79-80` |
| `data_context in {"static_fixture","stale_live","invalid","unavailable"}` AND `not operator_acknowledged_context` | `option_chain_context_acknowledgement_required` | `paper_trades.py:81-86` |

`tests/test_paper_trades.py:121-156` confirms that **fresh live** context
does *not* require the acknowledgement, but `static_fixture`, `stale_live`,
`invalid`, and `unavailable` all do.

### 6.4 Realistic example

SPX 5240, the option-chain panel is in fixture mode (data_context =
`static_fixture`). The operator types:
- strategy_label: `"5230/5220 put credit spread paper observation"`
- thesis: `"Hold to take 50% of $4.50 credit while SPX > 5230 with skew flat."`
- invalidation: `"Close if SPX trades < 5230 or short delta exceeds −0.20."`
- notes: `"Practice run; not a live order."`
- `acknowledge_context = True`

The intent is appended; the ledger row renders with
`Source = fixture`, `Context = static_fixture`, `Warning = caution`,
`Legs = 2` (ATM call and ATM put at the fixture's atm_strike), `Scope = paper only`.

If `acknowledge_context` is left unchecked while the option chain is in any
non-fresh-live state, `paper_intent_message` becomes
`"Paper intent not recorded: option_chain_context_acknowledgement_required"`
(`notebooks/spx_inventory_app.py:1280-1284`) and the ledger is unchanged.

> **Code gap (noted, not editorialized):** Ledger entries live in
> `mo.state(PaperTradeLedger())` (`notebooks/spx_inventory_app.py:261`).
> There is no `to_json` / `from_json`, no file persistence, and no removal
> action; closing the tab discards the ledger.

---

## 7. Position Tracker — `notebooks/spx_inventory_app.py:1347-1660`

### 7.1 "Add Position" form — `notebooks/spx_inventory_app.py:1357-1400`

`pos_form` is a `mo.ui.dictionary`:

| Key | Widget | Domain |
|---|---|---|
| `structure` | `dropdown(options=structure_options)` | `PositionStructure` (9 values, `validators.py:32-43`) |
| `side` | `dropdown(options=side_options, value="Credit")` | `PositionSide.{CREDIT, DEBIT}` (`positions.py:15-19`) |
| `description` | `text(full_width=True)` | `str` |
| `contracts` | `number(start=1, value=1, step=1)` | `int` (cast from `float` if integer-valued, `notebooks/spx_inventory_app.py:1481-1483`) |
| `entry_price` | `number(value=0.0, step=0.05)` | `float` (per contract option premium) |
| `max_loss` | `number(value=0.0, step=0.50)` | `float` per contract |
| `target` | `number(value=0.0, step=0.25)` | `float` per contract |
| `thesis` | `text(full_width=True)` | `str` |
| `close_by` | `dropdown(value="Final Hour 15:15–15:45")` | `TimeWindow` |
| `delta` | `number(value=0.0, step=0.01)` | `float` |
| `gamma` | `number(value=0.0, step=0.01)` | `float` |
| `theta` | `number(value=0.0, step=0.01)` | `float` |
| `friction` | `number(value=0.0, step=1.0, start=0.0)` | `float` (dollars) |

`add_button = mo.ui.run_button(label="Add Position")`
(`notebooks/spx_inventory_app.py:1453`).

### 7.2 Add handler — `notebooks/spx_inventory_app.py:1458-1506`

1. Validate description and thesis non-empty
   (`notebooks/spx_inventory_app.py:1479-1480`).
2. Coerce `contracts` to `int` if it's a float that `is_integer()`
   (`notebooks/spx_inventory_app.py:1481-1483`).
3. Call `create_position(...)` (`positions.py:173-226`). Builds a `Position`
   (`positions.py:67`) with:
   - `id = uuid4().hex[:8]` (8-char hex)
   - `current_mark = entry_price`
   - `thesis_still_valid = True`
   - `status = PositionStatus.OPEN`
   - `adjustments = 0`, `notes = ""`
   - `entry_time_window = current_time_window_selector.value`
4. Update state via `set_positions(positions_state() + (new_pos,))`. Tuples,
   not lists — positions are immutable and re-tuple on every mutation.

`create_position` rejects:
- `contracts <= 0` → `"contracts must be positive."` (`positions.py:190-191`,
  `tests/test_positions.py:122-124`)
- `entry_price < 0` (`positions.py:192-193`)
- `max_loss_per_contract < 0` (`positions.py:194-195`)
- `target_per_contract < 0` (`positions.py:196-197`)
- empty/whitespace description (`positions.py:198-199`)
- empty/whitespace thesis (`positions.py:200-201`)
- `friction_paid < 0` (`positions.py:202-203`)

All of `description` and `thesis` are passed through `html.escape(...)` on
write (`positions.py:209, 215`) and any adjustment notes are escaped on
append (`positions.py:158`).

### 7.3 Realistic add example

SPX 5240, time window `MORNING_945_1030`, sell 1× 5230/5220 put credit
spread for $4.50:

| Field | Value |
|---|---|
| structure | `PositionStructure.CREDIT_SPREAD` |
| side | `PositionSide.CREDIT` |
| description | `"5230/5220 put credit spread"` |
| contracts | `1` |
| entry_price | `4.50` |
| max_loss | `5.50` (= 10 width − 4.50 credit) |
| target | `2.25` (50% of credit) |
| thesis | `"Hold while SPX > 5230 and skew flat; take 50%."` |
| close_by | `TimeWindow.FINAL_HOUR_1515_1545` |
| delta | `-0.08` |
| gamma | `0.012` |
| theta | `0.18` |
| friction | `4.0` |

Result: a `Position` with `pnl_per_contract = 0.0`, `total_pnl = 0.0`,
`max_loss_total = 5.50 × 100 × 1 = $550.00`,
`target_total = 2.25 × 100 × 1 = $225.00`, `net_delta = -0.08`,
`net_gamma = 0.012`, `net_theta = 0.18`.

### 7.4 Manage open positions — `notebooks/spx_inventory_app.py:1509-1606`

Visible only when at least one position is `OPEN`
(`notebooks/spx_inventory_app.py:1523-1541`). When open positions exist:

| Widget | Role |
|---|---|
| `manage_selector` (dropdown) | Selects position by `f"{description} ({id})"` → `id` |
| `new_mark` | float, used by Update Mark and Close Position |
| `new_delta`, `new_gamma`, `new_theta` | floats, used by Update Greeks |
| `update_mark_btn` | Button: `Position.with_mark(new_mark.value)` (`positions.py:145-148`) |
| `update_greeks_btn` | Button: `Position.with_greeks(delta, gamma, theta)` (`positions.py:150-153`) |
| `close_btn` | Button: `Position.closed(new_mark.value)` (`positions.py:167-170`) |
| `invalidate_btn` | Button: `Position.with_thesis_invalidated()` (`positions.py:162-165`) |
| `adjust_btn` | Button: `Position.with_adjustment()` (`positions.py:155-160`) |

Each button uses the same dispatcher `_handle_click(key, button, fn)`
(`notebooks/spx_inventory_app.py:1637-1645`) that:
1. Reads `run_button_click_count(button)` (`notebooks/spx_inventory_app.py:317`).
2. Compares to `manage_click_state().get(key, 0)`.
3. If newer, persists the new count and calls `_apply(fn)` which rebuilds
   the positions tuple by calling `fn(p)` for the matching id.

#### 7.4.1 Closed-position guard

Every mutation method on `Position` raises
`"Cannot modify a closed position."` if `status is PositionStatus.CLOSED`
(`positions.py:146-147, 151-152, 156-157, 163-164`). `closed()` itself
raises `"Position is already closed."` if called twice (`positions.py:168-169`).
`tests/test_positions.py:228-246` enforces all five guards.

#### 7.4.2 Adjustment notes

`with_adjustment(notes="")` increments `adjustments` by 1 and appends the
HTML-escaped note text on a new line (`positions.py:155-160`). The notebook's
`adjust_btn` always calls `p.with_adjustment()` with no argument
(`notebooks/spx_inventory_app.py:1659`), so the count increments without
adding a note.

> **Code gap (noted, not editorialized):** The notebook does not expose a UI
> field for `with_adjustment(notes=...)`; only the count is incremented.

### 7.5 P&L math

For credit-side positions: `pnl_per_contract = (entry_price - current_mark) * 100`
(`positions.py:92-97`). For debit-side positions, `(current_mark - entry_price) * 100`.
`net_pnl = total_pnl - friction_paid` (`positions.py:104-107`).

Update flow on the 5230/5220 example: at 14:00 the spread mid drops to $2.10
(profit-taking territory). Operator types `2.10` in `new_mark`, clicks
**Update Mark**:
- `pnl_per_contract = (4.50 − 2.10) × 100 = $240`
- `total_pnl = $240`, `net_pnl = $240 − $4 friction = $236`
- `pnl_pct_of_target = 240 / 225 = 106.7%` (above target)
- `pnl_pct_of_max_loss = 240 / 550 = 43.6%`

Operator types `2.10` again in `new_mark` and clicks **Close Position**:
- `closed(2.10)` returns a new `Position` with `current_mark=2.10`,
  `status=CLOSED`. P&L stays at $240 / net $236.

### 7.6 Time urgency — `positions.py:229-245`

`time_urgency(current_window, close_by)` indexes both windows in
`TIME_WINDOW_ORDER` (`positions.py:40-50`, 9 entries) and computes
`remaining = close_idx − current_idx`:

| `remaining` | `Urgency` |
|---|---|
| ≤ 0 | `CRITICAL` |
| 1 | `HIGH` |
| 2 | `MEDIUM` |
| ≥ 3 | `LOW` |

Verified at `tests/test_positions.py:255-269`. Used in the sidebar's
`_urgency_badge` (`notebooks/spx_inventory_app.py:2311-2323`):
LOW = grey, MEDIUM = yellow, HIGH = orange, CRITICAL = red.

For our 5230/5220 spread with `close_by_time = FINAL_HOUR_1515_1545`:
- header `current_time_window = MORNING_945_1030` → remaining = 6 → LOW
- header advances to `EARLY_AFTERNOON_1330_1430` → remaining = 2 → MEDIUM
- header advances to `LATE_AFTERNOON_1430_1515` → remaining = 1 → HIGH
- header advances to `FINAL_HOUR_1515_1545` → remaining = 0 → CRITICAL

---

## 8. Calculators — `notebooks/spx_inventory_app.py:1663-1975`

A two-tab `mo.ui.tabs` panel (`notebooks/spx_inventory_app.py:1969-1974`):
"Futures hedge" and "Cost / friction".

### 8.1 Futures hedge — `notebooks/spx_inventory_app.py:1673-1793`

| Widget | Default | Domain |
|---|---|---|
| `hedge_option_delta` (number, step 0.01) | `0.30` | per-contract delta |
| `hedge_contracts` (number, start 1, step 1) | `1` | SPX option contracts |
| `hedge_percent` (slider 0–100, step 1) | `100` | percent (divided by 100 before passing in) |

Calls `calculate_futures_hedge(option_delta, contracts, hedge_percent)`
(`calculators.py:68`) returning `HedgeCalculation` (`calculators.py:12`).
Constants: `SPX_OPTION_MULTIPLIER = 100.0`, `ES_DOLLARS_PER_POINT = 50.0`,
`MES_DOLLARS_PER_POINT = 5.0` (`calculators.py:7-9`).

Math (`calculators.py:80-83`):
- `dollar_delta_per_point = option_delta × 100 × contracts` (signed)
- `target_hedge_dollars_per_point = |dollar_delta_per_point| × hedge_percent`
- `mes_equivalent = target / 5.0`, `es_equivalent = target / 50.0`
- `mes_rounded = int(round(mes_equivalent))`, `es_rounded = int(round(es_equivalent))`

Validation (`calculators.py:74-78`):
- `option_delta` must be finite.
- `contracts` must be a positive int (no booleans).
- `hedge_percent` must be in `[0, 1]` (slider sends 0–100, divided by 100
  before the call at `notebooks/spx_inventory_app.py:1716`).

Realistic example: hedging a portfolio of 4× short 5230/5220 put credit
spreads with delta = −0.08 each. Operator enters `option_delta = -0.32`
(net per-spread delta), `contracts = 4`, slider `100`.
- `dollar_delta_per_point = -0.32 × 100 × 4 = -128`
- `target_hedge_dollars_per_point = 128`
- `mes_equivalent = 128/5 = 25.6` → `mes_rounded = 26`
- `es_equivalent = 128/50 = 2.56` → `es_rounded = 3`

The displayed stat card shows `−$128 $/SPX pt (signed)`,
`$128 Hedge target $/pt`, `26 MES contracts`, `3 ES contracts`.

> **Code gap (noted, not editorialized):** The hedge calculator does not
> wire to any open position. It is a freestanding calculator. The operator
> manually copies position deltas into the input.

### 8.2 Cost / friction — `notebooks/spx_inventory_app.py:1797-1964`

| Widget | Default | Domain |
|---|---|---|
| `cost_contracts` (number, start 1, step 1) | `1` | int |
| `cost_legs` (number, start 1, step 1) | `4` | int |
| `commission_per_contract` (number, step 0.01) | `0.0` | $/contract |
| `fees_per_contract` (number, step 0.01) | `0.0` | $/contract |
| `entry_spread_crossing` (number, step 0.01) | `0.0` | $/contract |
| `exit_spread_crossing` (number, step 0.01) | `0.0` | $/contract |
| `gross_target_dollars` (number, step 1.0) | `100.0` | $ |

Calls `calculate_trade_friction(...)` (`calculators.py:98`) returning
`CostCalculation` (`calculators.py:25`).

Math (`calculators.py:124-149`):
- `roundtrip_contract_count = contracts × legs × 2`
- `commission_and_fees = roundtrip_contract_count × (commission + fees)`
- `spread_crossing_cost = contracts × legs × (entry_cross + exit_cross)`
- `total_friction = commission_and_fees + spread_crossing_cost`
- `target_after_friction = gross_target − total_friction`
- `friction_percent_of_target = total_friction / gross_target`
- `friction_warning = friction_percent_of_target >= 0.25`

Validation (`calculators.py:108-122`):
- `contracts` and `legs` must be positive ints (no booleans).
- All cost inputs must be finite, non-negative.
- `gross_target_dollars` must be `> 0`.

Friction-warning banner (`notebooks/spx_inventory_app.py:1927-1937`) shows
`"Friction is ≥ 25% of gross target. Requires explicit justification."` when
`friction_warning` is True.

Realistic example: 1× 5230/5220 put credit spread, target = $225
(50% of $4.50 credit per contract), $0.65 commission, $0.10 fees, $0.05
slippage per leg per side:
- contracts=1, legs=2, commission=0.65, fees=0.10, entry_cross=5.00 (i.e.
  $0.05 × 100 multiplier), exit_cross=5.00, gross_target=225.
- `roundtrip_contract_count = 1 × 2 × 2 = 4`
- `commission_and_fees = 4 × 0.75 = 3.00`
- `spread_crossing_cost = 1 × 2 × 10.00 = 20.00`
- `total_friction = 23.00`
- `target_after_friction = 202.00`
- `friction_percent_of_target = 23/225 ≈ 10.2%` → no warning.

Same trade scaled up to 4 contracts and a 4-leg iron condor on top of the
spread (legs=4): RT count = 32, comm+fees = $24, crossing = $80, total
friction = $104. If the operator's gross target is still $225, friction is
46% of target — `friction_warning = True`, red banner.

---

## 9. Operating Library — `notebooks/spx_inventory_app.py:1978-2282`

Three accordion sections (`notebooks/spx_inventory_app.py:2273-2282`):

### 9.1 Reference cards — `notebooks/spx_inventory_app.py:1988-2111`

`reference_card_selector` (`notebooks/spx_inventory_app.py:1996-2002`)
defaults to `"Dealer gamma / GEX"`. Backed by
`get_reference_cards()` → list of `ReferenceCard`
(`reference.py:6-16, 40`). 12 topics in `REFERENCE_TOPICS`
(`reference.py:19-32`):

1. Dealer gamma / GEX
2. Zero-gamma flip
3. Vanna and charm
4. Skew and structure selection
5. Variance risk premium
6. SPX/SPXW execution microstructure
7. PM cash settlement
8. Futures hedging
9. Cost realism
10. Behavioral lockouts
11. Modern 0DTE structural risk
12. Source / broker verification checklist

Each card renders mental model, four quick-reference quadrants, key
mechanics, deep dive, and verification inputs. Pure read-only static text.

### 9.2 Playbook tables — `notebooks/spx_inventory_app.py:2114-2191`

Four nested accordion tables, all rendered via `playbook_display_rows`
(`notebooks/spx_inventory_app.py:2115-2129`) which converts `Permission`
enum values to spaces-separated strings:

| Accordion key | Source | Row count |
|---|---|---|
| Action permission matrix (20 actions) | `get_action_permission_matrix()` | `playbook.py:60-222`, 20 rows |
| Structure quick reference (8 structures) | `get_structure_quick_reference()` | `playbook.py:225-291`, 8 rows |
| Conversion triage (10 scenarios) | `get_conversion_triage_table()` | `playbook.py:294-366`, 10 rows |
| Time-of-day permissions (15 actions × 9 windows) | `get_time_of_day_permission_matrix()` | `playbook.py:369-567`, 15 rows |

`Permission` enum values (`playbook.py:7-13`): `ALLOWED`, `RESTRICTED`,
`FORBIDDEN`, `CLOSE_ONLY`, `HEDGE_ONLY`, `PREPLANNED_ONLY`.

> **Code gap (noted, not editorialized):** These tables are static reference
> material. `evaluate_inventory_rules` (`rules.py:109`) does not consult any
> of them. Time-of-day finer-grained permissions (e.g. "Convert to vertical
> = FORBIDDEN at FINAL_HOUR_1515_1545") exist only as on-screen text;
> the rule engine's only time check is `FINAL_5_1555_1600`.

### 9.3 Prompt templates — `notebooks/spx_inventory_app.py:2194-2269`

`prompt_template_selector` defaults to `"Pre-session regime synthesis"`.
Six templates from `get_session_prompt_templates()`
(`prompts.py:39, 24-31`):

1. `pre_session_regime_synthesis`
2. `dealer_flow_interpretation`
3. `adjustment_drill`
4. `strategy_audit`
5. `edge_hypothesis_stress_test`
6. `post_session_review`

Every template is prefixed with `DATA_GUARDRAIL` (`prompts.py:6-13`):

> "Use only explicitly sourced inputs: user-supplied data or approved
> adapter data with source, timestamp, and freshness status. Mark missing,
> stale, partial, or unverifiable fields unknown or require manual
> confirmation. Do not invent fake data. Provide bounded decision support
> only; do not place, route, or imply automated order execution. Do not
> generate batch examples unless explicitly requested."

The panel renders metadata, required-inputs table, and a copy-ready
markdown code block at `notebooks/spx_inventory_app.py:2244-2266`.

---

## 10. Risk Console sidebar — `notebooks/spx_inventory_app.py:2287-2462`

A persistent left sidebar emitted via `mo.sidebar([...])` showing:

| Block | Source | Code lines |
|---|---|---|
| Session header | `current_time_window_selector.value` → `TIME_WINDOW_LABELS` | `2341-2348` |
| Daily budget bar | `summary.budget_used_pct` (color: <0.5 green, <0.8 yellow, ≥0.8 red) | `2325-2339, 2350-2353` |
| Net P&L | `summary.net_pnl` (signed, `+` prefix) | `2356-2358` |
| Open / Closed P&L breakdown | `summary.open_pnl`, `summary.closed_pnl`, `summary.total_friction` | `2359-2363` |
| Aggregate Greeks | `summary.net_delta`, `.net_gamma`, `.net_theta` | `2366-2369` |
| Open positions list | per-position card with description, total_pnl, contracts, net_delta, `pnl_pct_of_target`, urgency badge | `2375-2407` |
| Closed roll-up | sum of `total_pnl` for closed | `2409-2419` |
| Discipline counters | `len(all_positions)`, `summary.total_adjustments` | `2422-2428` |
| Budget warning | `summary.budget_used_pct >= 0.8` → red `"⚠ Budget ≥ 80%"` | `2429-2433` |
| Adjustment warning | `summary.total_adjustments >= 5` → yellow `"⚠ High adjustment count"` | `2434-2438` |
| Invalidated thesis warning | any open position with `not thesis_still_valid` → red `"⚠ Invalidated thesis still open"` | `2439-2447` |

Per-position thesis invalidation also shows `"⚠ Thesis invalidated"` inline
on the position card (`notebooks/spx_inventory_app.py:2401-2406`).

These warnings are display-only; they do not flip `behavior.daily_lockout_active`
or invoke `evaluate_inventory_rules`.

---

## 11. Cross-component permissions cheat sheet (sourced)

| Allowed actions set | Members | Where |
|---|---|---|
| `FULL_DISCRETIONARY_ACTIONS` | HOLD, TAKE_PARTIAL_PROFIT, REDUCE, HEDGE_MES_ES, CONVERT_RESTRUCTURE, CLOSE, STOP_TRADING (no EMERGENCY_FLATTEN) | `rules.py:10-18` |
| `FLATTEN_ONLY_ACTIONS` | CLOSE, EMERGENCY_FLATTEN, STOP_TRADING | `rules.py:19` |
| `BEHAVIOR_IMPAIRED_ACTIONS` | REDUCE, CLOSE, EMERGENCY_FLATTEN, HEDGE_MES_ES, STOP_TRADING | `rules.py:20-26` |
| `THESIS_INVALIDATED_ACTIONS` | REDUCE, CLOSE, EMERGENCY_FLATTEN, STOP_TRADING (no HEDGE_MES_ES) | `rules.py:27-32` |
| `FINAL_FIVE_MINUTE_ACTIONS` | CLOSE, EMERGENCY_FLATTEN, STOP_TRADING | `rules.py:33` |

What the rule engine **never** allows from a clean state: `EMERGENCY_FLATTEN`
(only escalation states unlock it).

What the rule engine **always** allows from any non-`NORMAL` state: `CLOSE`
and `STOP_TRADING` are members of every set above.

What is **never** authorized by any code path in this repo: real broker
order routing. The notebook contains no broker client; the only network call
in the codebase is the manually-gated Schwab option-chain GET at
`live_schwab_option_chain_provider.py:295-311`, which is read-only market
data.

---

## 12. Suggested operator walkthrough (5 minutes)

1. Launch the app. Header shows `Window: Morning 9:45–10:30`,
   `Open: 0`, `Net P&L: +$0`, `Budget used: 0%`. Market Data Readiness =
   `BLOCKED` (`default_fail_closed`). Option Chain panel = `Option Chain
   Fixture View` with `freshness=static_fixture` and orange caution chip.

2. Switch the Market-data display mode dropdown to **Healthy sanitized
   preview**. The severity ribbon turns green, all three freshness pills
   read `fresh`, and all `usable` chips turn green.

3. Switch fixture selector to **Lockout active**. Decision Console turns
   red, allowed-action chips collapse to `close`, `emergency flatten`,
   `stop trading`. Validation panel displays
   `LOCKOUT_ACTIVE — Only close, emergency flatten, or stop-trading actions
   may remain permissible in later rule logic.`

4. Switch fixture selector back to **Clean state**. Severity reverts to
   green NORMAL, 7 allowed action chips, EMERGENCY_FLATTEN is the only
   blocked chip.

5. In Position Tracker, fill the 5230/5220 put credit spread example
   from §7.3 and click **Add Position**. Header counters update; the
   sidebar shows the new card with a LOW urgency badge. Click **Update
   Mark** with `2.10` to flip the trade into +$240 unrealized; click
   **Close Position** at the same mark to lock it in.

6. In Calculators → **Cost / friction**, plug in 1 contract / 2 legs /
   commission $0.65 / fees $0.10 / entry crossing $5.00 / exit crossing
   $5.00 / gross target $225. Total friction = $23 (≈10.2%). Re-enter
   contracts=4 and legs=4 to see the red 25%-warning banner trigger
   at $104 / $225 ≈ 46%.

7. In Paper Intent Ledger, leave the option-chain panel in fixture mode,
   uncheck the acknowledgement, fill in strategy/thesis/invalidation, and
   click **Record Paper Intent**. The ledger remains empty and the message
   line displays
   `Paper intent not recorded: option_chain_context_acknowledgement_required`.
   Tick the acknowledgement and click again — a row appears with
   `Source: fixture`, `Context: static_fixture`, `Warning: caution`,
   `Scope: paper only`.

8. Refresh the browser. All state resets — positions, paper ledger, click
   counters, refresh timestamp. The notebook has no persistence.
