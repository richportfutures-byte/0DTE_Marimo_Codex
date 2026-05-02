import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    # Restrained "operator console" styling. Defines a small set of utility
    # classes used throughout the app for header, sections, cards, chips, and
    # severity banners. Kept intentionally calm — no neon, no gradients beyond
    # subtle tinted backgrounds.
    mo.Html(
        """<style>
        .app-shell{padding:0 4px}
        .app-header{display:flex;align-items:center;gap:14px;padding:12px 16px;
          border:1px solid var(--md-sys-color-outline-variant,#334155);
          border-radius:10px;
          background:var(--md-sys-color-surface-container-low,#0f172a)}
        .app-header__title{font-size:1.05em;font-weight:700;letter-spacing:-0.01em;
          color:var(--md-sys-color-on-surface,#e2e8f0)}
        .app-header__subtitle{color:#94a3b8;font-size:0.78em;margin-top:2px}
        .app-header__pills{margin-left:auto;display:flex;gap:8px;
          align-items:center;flex-wrap:wrap;justify-content:flex-end}
        .app-pill{display:inline-flex;align-items:center;gap:6px;
          background:var(--md-sys-color-surface-container,#1e293b);
          color:var(--md-sys-color-on-surface,#e2e8f0);
          border:1px solid var(--md-sys-color-outline-variant,#334155);
          padding:4px 10px;border-radius:6px;font-size:0.8em;font-weight:500}
        .app-pill__label{color:#94a3b8;font-size:0.72em;text-transform:uppercase;
          letter-spacing:0.06em;font-weight:600}
        .app-pill__value{font-weight:700;font-variant-numeric:tabular-nums}
        .app-ribbon{padding:6px 12px;border-radius:6px;font-size:0.78em;
          color:#94a3b8;
          background:var(--md-sys-color-surface-container-lowest,#0b1220);
          border:1px dashed var(--md-sys-color-outline-variant,#334155);
          margin:8px 0 14px}
        .app-section{margin:18px 0 6px;padding:0 4px;
          display:flex;align-items:center;gap:10px}
        .app-section__title{font-size:0.78em;font-weight:700;letter-spacing:0.1em;
          text-transform:uppercase;color:#94a3b8}
        .app-section__rule{flex:1;height:1px;
          background:var(--md-sys-color-outline-variant,#334155)}
        .app-card{background:var(--md-sys-color-surface-container,#1e293b);
          border:1px solid var(--md-sys-color-outline-variant,#334155);
          border-radius:10px;padding:14px;margin:6px 0}
        .app-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
        .app-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
        .app-stat{background:var(--md-sys-color-surface-container-high,#1e293b);
          border-radius:8px;padding:10px;
          border:1px solid var(--md-sys-color-outline-variant,#334155)}
        .app-stat__label{color:#94a3b8;font-size:0.72em;text-transform:uppercase;
          letter-spacing:0.06em;font-weight:600}
        .app-stat__value{margin-top:4px;color:#e2e8f0;font-size:0.95em;
          font-variant-numeric:tabular-nums}
        .app-severity{display:flex;align-items:center;gap:14px;
          padding:14px 16px;border-radius:10px;border:1px solid;margin-bottom:10px}
        .app-severity__badge{font-weight:800;font-size:0.78em;letter-spacing:0.1em;
          text-transform:uppercase;padding:4px 10px;border-radius:6px;color:#0b1220}
        .app-severity__title{font-size:1em;font-weight:700;color:#e2e8f0}
        .app-severity__subtitle{color:#94a3b8;font-size:0.85em;margin-top:2px}
        .app-severity--normal{border-color:#1f5132;background:rgba(34,197,94,0.07)}
        .app-severity--caution{border-color:#7a5b15;background:rgba(250,204,21,0.07)}
        .app-severity--restricted{border-color:#7c4214;background:rgba(251,146,60,0.07)}
        .app-severity--blocked{border-color:#7f1d1d;background:rgba(239,68,68,0.08)}
        .app-chip{display:inline-flex;align-items:center;padding:3px 9px;
          border-radius:14px;font-size:0.78em;font-weight:600;border:1px solid;
          margin:2px 4px 2px 0;font-variant-numeric:tabular-nums}
        .app-chip--allowed{color:#86efac;border-color:#1f5132;
          background:rgba(34,197,94,0.07)}
        .app-chip--blocked{color:#fca5a5;border-color:#7f1d1d;
          background:rgba(239,68,68,0.07)}
        .app-muted{color:#94a3b8;font-size:0.85em}
        .app-list{margin:6px 0 0;padding:0;list-style:none}
        .app-list li{padding:5px 0;color:#cbd5e1;
          border-top:1px dashed var(--md-sys-color-outline-variant,#334155)}
        .app-list li:first-child{border-top:none}
        .app-mental{background:rgba(99,102,241,0.07);
          border-left:3px solid #818cf8;border-radius:8px;
          padding:14px;margin-bottom:12px}
        </style>"""
    )
    return


@app.cell
def _():
    from dataclasses import asdict
    from html import escape as html_escape
    from pathlib import Path

    from spx_inventory_playbook.adapters.option_chain_freshness import (
        classify_option_chain_freshness,
    )
    from spx_inventory_playbook.adapters.option_chain_provider import (
        FixtureOptionChainProvider,
    )
    from spx_inventory_playbook.calculators import (
        calculate_futures_hedge,
        calculate_trade_friction,
    )
    from spx_inventory_playbook.fixtures import (
        behavior_not_authorized_state,
        clean_state,
        final_five_minutes_state,
        lockout_state,
        loss_avoidance_state,
        near_flip_unclear_state,
        negative_gex_credit_spread_state,
        poor_liquidity_state,
        rule_violation_state,
        size_exceeds_plan_state,
        thesis_invalidated_state,
    )
    from spx_inventory_playbook.market_data_facade import (
        evaluate_market_data_facade,
    )
    from spx_inventory_playbook.market_data_preview import (
        PREVIEW_SCENARIO_LABELS,
        build_market_data_preview_scenario,
    )
    from spx_inventory_playbook.playbook import (
        Permission,
        get_action_permission_matrix,
        get_conversion_triage_table,
        get_structure_quick_reference,
        get_time_of_day_permission_matrix,
    )
    from spx_inventory_playbook.positions import (
        PositionSide,
        PositionStatus,
        Urgency,
        TIME_WINDOW_LABELS,
        calculate_session_summary,
        create_position,
        time_urgency,
    )
    from spx_inventory_playbook.prompts import get_session_prompt_templates
    from spx_inventory_playbook.reference import get_reference_cards
    from spx_inventory_playbook.rules import evaluate_inventory_rules
    from spx_inventory_playbook.validators import (
        PositionStructure,
        TimeWindow,
        validate_inventory_state,
    )

    fixture_factories = {
        "Clean state": clean_state,
        "Lockout active": lockout_state,
        "Behavior not authorized": behavior_not_authorized_state,
        "Rule violation": rule_violation_state,
        "Thesis invalidated": thesis_invalidated_state,
        "Poor liquidity": poor_liquidity_state,
        "Final five minutes": final_five_minutes_state,
        "Size exceeds plan": size_exceeds_plan_state,
        "Loss avoidance risk": loss_avoidance_state,
        "Negative GEX credit spread": negative_gex_credit_spread_state,
        "Near flip unclear": near_flip_unclear_state,
    }
    market_data_scenario_names = (
        "default_fail_closed",
        "healthy_preview",
        "stale_underlying",
        "partial_chain",
        "locked_liquidity",
        "missing_atm_straddle",
    )
    return (
        FixtureOptionChainProvider,
        Permission,
        PositionSide,
        PositionStatus,
        PositionStructure,
        TIME_WINDOW_LABELS,
        TimeWindow,
        Urgency,
        PREVIEW_SCENARIO_LABELS,
        Path,
        asdict,
        build_market_data_preview_scenario,
        calculate_futures_hedge,
        calculate_session_summary,
        calculate_trade_friction,
        classify_option_chain_freshness,
        create_position,
        evaluate_inventory_rules,
        evaluate_market_data_facade,
        fixture_factories,
        get_action_permission_matrix,
        get_conversion_triage_table,
        get_reference_cards,
        get_session_prompt_templates,
        get_structure_quick_reference,
        get_time_of_day_permission_matrix,
        html_escape,
        market_data_scenario_names,
        time_urgency,
        validate_inventory_state,
    )


@app.cell
def _(PREVIEW_SCENARIO_LABELS, TIME_WINDOW_LABELS, TimeWindow, mo):
    positions_state, set_positions = mo.state(())
    add_click_state, set_add_click = mo.state(0)
    manage_click_state, set_manage_click = mo.state({})
    option_chain_refresh_click_state, set_option_chain_refresh_click = mo.state(0)
    daily_budget_input = mo.ui.number(
        value=2000.0,
        step=100.0,
        start=0.0,
        label="Daily loss budget ($)",
        full_width=True,
    )
    current_time_window_selector = mo.ui.dropdown(
        options={TIME_WINDOW_LABELS[tw]: tw for tw in TimeWindow},
        value="Morning 9:45–10:30",
        label="Current time window",
    )
    market_data_mode_selector = mo.ui.dropdown(
        options=PREVIEW_SCENARIO_LABELS,
        value="Default fail-closed",
        label="Market-data display mode",
    )
    return (
        add_click_state,
        current_time_window_selector,
        daily_budget_input,
        market_data_mode_selector,
        manage_click_state,
        option_chain_refresh_click_state,
        positions_state,
        set_add_click,
        set_manage_click,
        set_option_chain_refresh_click,
        set_positions,
    )


@app.function
def run_button_click_count(button):
    frontend_count = getattr(button, "_value_frontend", None)
    if frontend_count is not None:
        return int(frontend_count or 0)
    return 1 if button.value else 0


@app.cell
def _(
    PositionStatus,
    TIME_WINDOW_LABELS,
    calculate_session_summary,
    current_time_window_selector,
    daily_budget_input,
    mo,
    positions_state,
):
    _summary_for_header = calculate_session_summary(
        positions_state(), daily_budget_input.value or 2000.0
    )
    _open_count = sum(
        1 for p in positions_state() if p.status is PositionStatus.OPEN
    )
    _net = _summary_for_header.net_pnl
    _pnl_color = "#22c55e" if _net > 0 else ("#ef4444" if _net < 0 else "#94a3b8")
    _pnl_sign = "" if _net < 0 else "+"
    _budget_pct = _summary_for_header.budget_used_pct
    _budget_color = (
        "#22c55e"
        if _budget_pct < 0.5
        else "#facc15"
        if _budget_pct < 0.8
        else "#ef4444"
    )
    _tw_label = TIME_WINDOW_LABELS.get(current_time_window_selector.value, "—")

    mo.Html(
        '<div class="app-shell"><div class="app-header">'
        '<div>'
        '<div class="app-header__title">0DTE SPX Inventory Workstation</div>'
        '<div class="app-header__subtitle">'
        'Operator console &middot; rule engine &middot; position tracker'
        '</div></div>'
        '<div class="app-header__pills">'
        '<span class="app-pill"><span class="app-pill__label">Window</span>'
        f'<span class="app-pill__value">{_tw_label}</span></span>'
        '<span class="app-pill"><span class="app-pill__label">Open</span>'
        f'<span class="app-pill__value">{_open_count}</span></span>'
        '<span class="app-pill"><span class="app-pill__label">Net P&amp;L</span>'
        f'<span class="app-pill__value" style="color:{_pnl_color}">'
        f'{_pnl_sign}${_net:,.0f}</span></span>'
        '<span class="app-pill"><span class="app-pill__label">Budget used</span>'
        f'<span class="app-pill__value" style="color:{_budget_color}">'
        f'{_budget_pct:.0%}</span></span>'
        '</div></div></div>'
    )
    return


@app.cell
def _(mo):
    mo.Html(
        '<div class="app-ribbon">'
        '<strong>Live-data-safe boundaries:</strong> '
        'Live data requires approved source, timestamp, and freshness checks; '
        'this notebook has no live mode. Greeks, IV, bid/ask, strikes, '
        'expiries, and marks must be labeled by source. Missing or stale data '
        'fails closed, degrades confidence, or requires manual confirmation. '
        'Bounded decision support is allowed; automated live actions are '
        'outside this app.'
        '</div>'
    )
    return


@app.cell
def _(
    PREVIEW_SCENARIO_LABELS,
    build_market_data_preview_scenario,
    market_data_mode_selector,
    market_data_scenario_names,
):
    market_data_scenario_name = market_data_mode_selector.value
    if market_data_scenario_name not in market_data_scenario_names:
        market_data_scenario_name = PREVIEW_SCENARIO_LABELS.get(
            str(market_data_scenario_name),
            "default_fail_closed",
        )

    _preview = build_market_data_preview_scenario(market_data_scenario_name)
    market_data_scenario_label = next(
        label
        for label, name in PREVIEW_SCENARIO_LABELS.items()
        if name == market_data_scenario_name
    )
    market_data_scenario_note = {
        "default_fail_closed": (
            "No underlying quote, option chain, or ATM straddle is loaded."
        ),
        "healthy_preview": (
            "Healthy sanitized fixture for display verification only."
        ),
        "stale_underlying": (
            "Underlying quote is stale; derived outputs must stay blocked."
        ),
        "partial_chain": (
            "Option chain is intentionally partial; ranking is not fully usable."
        ),
        "locked_liquidity": (
            "Locked option quote detected; liquidity readiness is degraded."
        ),
        "missing_atm_straddle": (
            "ATM straddle is unavailable; width outputs are intentionally hidden."
        ),
    }[market_data_scenario_name]
    market_data_readiness = _preview.facade_result
    market_data_mode_label = _preview.mode_label
    market_data_preview_disclosure = _preview.disclosure
    if _preview.atm_straddle is not None and market_data_readiness.atm_straddle_usable:
        market_data_atm_width_points = _preview.atm_straddle.width_points
    else:
        market_data_atm_width_points = None
    return (
        market_data_atm_width_points,
        market_data_mode_label,
        market_data_preview_disclosure,
        market_data_readiness,
        market_data_scenario_label,
        market_data_scenario_name,
        market_data_scenario_note,
    )


@app.cell
def _(
    html_escape,
    market_data_atm_width_points,
    market_data_mode_label,
    market_data_preview_disclosure,
    market_data_readiness,
    market_data_scenario_label,
    market_data_scenario_name,
    market_data_scenario_note,
    mo,
):
    _mdr = market_data_readiness
    _health = _mdr.health
    _status = _health.status
    _status_meta = {
        "OK": {
            "modifier": "normal",
            "badge": "#22c55e",
            "title": "Healthy",
            "subtitle": "Canonical market data is fresh and usable.",
        },
        "DEGRADED": {
            "modifier": "caution",
            "badge": "#facc15",
            "title": "Degraded",
            "subtitle": "Some market-data outputs require caution.",
        },
        "BLOCKED": {
            "modifier": "blocked",
            "badge": "#ef4444",
            "title": "Blocked",
            "subtitle": "Fail-closed until canonical market data is loaded.",
        },
    }
    _meta = _status_meta.get(_status, _status_meta["BLOCKED"])

    def _flag_chip(value, true_label="YES", false_label="NO", true_good=True):
        if value:
            kind = "allowed" if true_good else "blocked"
            label = true_label
        else:
            kind = "blocked" if true_good else "allowed"
            label = false_label
        return f'<span class="app-chip app-chip--{kind}">{label}</span>'

    def _list_html(values, empty_label):
        if not values:
            return f'<span class="app-muted">{empty_label}</span>'
        return (
            '<ul class="app-list">'
            + "".join(f"<li>{html_escape(str(value))}</li>" for value in values)
            + "</ul>"
        )

    _severity_html = (
        f'<div class="app-severity app-severity--{_meta["modifier"]}">'
        f'<span class="app-severity__badge" style="background:{_meta["badge"]}">'
        f'{html_escape(_status)}</span>'
        '<div>'
        f'<div class="app-severity__title">{_meta["title"]}</div>'
        f'<div class="app-severity__subtitle">{_meta["subtitle"]}</div>'
        '</div></div>'
    )
    _disclosure_html = "".join(
        f"<span class=\"app-chip app-chip--blocked\">{html_escape(str(note))}</span>"
        for note in market_data_preview_disclosure
    )
    _width_value = (
        f"{market_data_atm_width_points} pts"
        if market_data_atm_width_points is not None
        else "unavailable"
    )

    _freshness_html = (
        '<div class="app-grid-3">'
        '<div class="app-stat"><div class="app-stat__label">Mode</div>'
        f'<div class="app-stat__value">{html_escape(market_data_mode_label)}</div>'
        f'<div style="margin-top:6px">{_disclosure_html}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Scenario</div>'
        f'<div class="app-stat__value">{html_escape(market_data_scenario_label)}</div>'
        f'<div class="app-muted" style="margin-top:6px">'
        f'{html_escape(market_data_scenario_note)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Health status</div>'
        f'<div class="app-stat__value">{html_escape(_status.lower())}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'API-derived outputs usable</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.api_outputs_usable, "USABLE", "BLOCKED")}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Manual confirmation required</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.manual_confirmation_required, "REQUIRED", "not required", False)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Underlying freshness</div>'
        f'<div class="app-stat__value">{_mdr.underlying_freshness.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Chain freshness</div>'
        f'<div class="app-stat__value">{_mdr.option_chain_freshness.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'ATM straddle freshness</div>'
        f'<div class="app-stat__value">{_mdr.atm_straddle_freshness.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Underlying quote usable</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.underlying_usable)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Option chain usable</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.option_chain_usable)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'ATM straddle usable</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.atm_straddle_usable)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Chain-derived outputs usable</div>'
        f'<div class="app-stat__value">{_flag_chip(_mdr.chain_derived_outputs_usable)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'ATM straddle width</div>'
        f'<div class="app-stat__value">{html_escape(_width_value)}</div></div>'
        '</div>'
    )

    _detail_html = (
        '<div class="app-grid-2" style="margin-top:10px">'
        '<div><div class="app-stat__label">Blockers</div>'
        f'{_list_html(_health.blockers, "none")}</div>'
        '<div><div class="app-stat__label">Warnings</div>'
        f'{_list_html(_health.warnings, "none")}</div>'
        '<div><div class="app-stat__label">Missing fields</div>'
        f'{_list_html(_health.missing_fields, "none")}</div>'
        '<div><div class="app-stat__label">Stale fields</div>'
        f'{_list_html(_health.stale_fields, "none")}</div>'
        '</div>'
    )

    mo.Html(
        '<div class="app-section">'
        '<div class="app-section__title">Market Data Readiness</div>'
        '<div class="app-section__rule"></div></div>'
        '<div class="app-card">'
        '<div class="app-muted" style="margin-bottom:10px">'
        'No market data loaded is the default state: not live, no broker data '
        'loaded, and no raw provider payloads in the notebook. Sanitized fixture '
        'scenarios are not live and not broker data; they exist for '
        'display verification only. API-derived outputs remain unavailable '
        'until canonical market-data snapshots pass freshness checks.'
        '</div>'
        + _severity_html
        + _freshness_html
        + _detail_html
        + '</div>'
    )
    return


@app.cell
def _(Path, mo):
    option_chain_fixture_path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "market_data"
        / "schwab"
        / "raw_option_chain_0dte.sanitized.json"
    )
    option_chain_refresh_button = mo.ui.run_button(label="Reload Fixture")
    return option_chain_fixture_path, option_chain_refresh_button


@app.cell
def _(
    FixtureOptionChainProvider,
    classify_option_chain_freshness,
    option_chain_fixture_path,
    option_chain_refresh_button,
    option_chain_refresh_click_state,
    set_option_chain_refresh_click,
):
    _refresh_click_count = run_button_click_count(option_chain_refresh_button)
    if _refresh_click_count > option_chain_refresh_click_state():
        set_option_chain_refresh_click(_refresh_click_count)

    option_chain_provider_result = FixtureOptionChainProvider(
        option_chain_fixture_path,
        source_label="fixture: sanitized Schwab option-chain capture",
    ).get_spx_0dte_selection()
    option_chain_freshness = classify_option_chain_freshness(
        option_chain_provider_result
    )
    return option_chain_freshness, option_chain_provider_result


@app.cell
def _(
    html_escape,
    mo,
    option_chain_freshness,
    option_chain_provider_result,
    option_chain_refresh_button,
):
    _result = option_chain_provider_result
    _freshness = option_chain_freshness

    def _fmt(value, precision=2):
        if value is None:
            return "unavailable"
        if isinstance(value, float):
            return f"{value:,.{precision}f}"
        return str(value)

    def _chip(value, kind="allowed"):
        return (
            f'<span class="app-chip app-chip--{kind}">'
            f"{html_escape(str(value))}</span>"
        )

    _status_kind = "allowed" if _result.status == "available" else "blocked"
    _reason = _result.reason_code or "none"
    _loaded_at = (
        _result.loaded_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        if _result.loaded_at is not None
        else "unavailable"
    )
    _freshness_kind = (
        "allowed"
        if _freshness.status in {"fresh", "static_fixture"}
        else "blocked"
    )
    _source_html = (
        '<div class="app-grid-3">'
        '<div class="app-stat"><div class="app-stat__label">Source</div>'
        f'<div class="app-stat__value">{html_escape(_result.source_label)}</div>'
        '<div class="app-muted" style="margin-top:6px">'
        'Fixture data only. Not live. No broker connection.</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Provider</div>'
        f'<div class="app-stat__value">{html_escape(_result.provider_name)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Status</div>'
        f'<div class="app-stat__value">{_chip(_result.status, _status_kind)}</div>'
        f'<div class="app-muted" style="margin-top:6px">Reason: {html_escape(_reason)}</div></div>'
        '</div>'
    )
    _freshness_html = (
        '<div class="app-grid-3" style="margin-top:10px">'
        '<div class="app-stat"><div class="app-stat__label">Freshness status</div>'
        f'<div class="app-stat__value">{_chip(_freshness.status, _freshness_kind)}</div>'
        '<div class="app-muted" style="margin-top:6px">'
        'static_fixture means display-only fixture data, not live market data.</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Source type</div>'
        f'<div class="app-stat__value">{html_escape(_freshness.source_type)}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Loaded at</div>'
        f'<div class="app-stat__value">{html_escape(_loaded_at)}</div></div>'
        '</div>'
    )

    if _result.status != "available" or _result.selection_view is None:
        mo.vstack(
            [
                option_chain_refresh_button,
                mo.Html(
                    '<div class="app-section">'
                    '<div class="app-section__title">Option Chain Fixture View</div>'
                    '<div class="app-section__rule"></div></div>'
                    '<div class="app-card">'
                    '<div class="app-muted" style="margin-bottom:10px">'
                    'Read-only fixture-backed option-chain panel. Manual reload '
                    'only; no live refresh, no orders, and no trading '
                    'authorization changes.'
                    '</div>'
                    + _source_html
                    + _freshness_html
                    + '<div style="margin-top:10px">'
                    + _chip("option chain unavailable", "blocked")
                    + '</div></div>'
                ),
            ]
        )
    else:
        _view = _result.selection_view
        _snapshot = _result.snapshot
        _underlying = _snapshot.underlying if _snapshot is not None else None
        _expiration = _view.selected_expiration
        _underlying_symbol = _view.underlying_symbol
        _underlying_html = (
            '<div class="app-grid-3" style="margin-top:10px">'
            '<div class="app-stat"><div class="app-stat__label">Underlying</div>'
            f'<div class="app-stat__value">{html_escape(_underlying_symbol)}</div></div>'
            '<div class="app-stat"><div class="app-stat__label">Bid / Ask</div>'
            f'<div class="app-stat__value">{_fmt(getattr(_underlying, "bid", None))} / '
            f'{_fmt(getattr(_underlying, "ask", None))}</div></div>'
            '<div class="app-stat"><div class="app-stat__label">Last / Mark</div>'
            f'<div class="app-stat__value">{_fmt(getattr(_underlying, "last", None))} / '
            f'{_fmt(getattr(_underlying, "mark", None))}</div></div>'
            '</div>'
        )

        if _expiration is None:
            _selection_html = (
                '<div style="margin-top:10px">'
                + _chip("selection unavailable", "blocked")
                + '</div>'
            )
        else:
            _straddle = _expiration.atm_straddle
            _straddle_value = (
                f"{_straddle.value:,.2f}"
                if _straddle.status == "available" and _straddle.value is not None
                else "unavailable"
            )
            _rows = []
            for _item in _expiration.contracts:
                _contract = _item.contract
                _liq = _item.liquidity
                _spread_kind = (
                    "allowed"
                    if _liq.spread_state == "acceptable"
                    else "blocked"
                )
                _rows.append(
                    "<tr>"
                    f"<td>{html_escape(_contract.side)}</td>"
                    f"<td>{_contract.strike:,.1f}</td>"
                    f"<td>{_fmt(_contract.bid)}</td>"
                    f"<td>{_fmt(_contract.ask)}</td>"
                    f"<td>{_fmt(_contract.mark)}</td>"
                    f"<td>{_fmt(_liq.spread)}</td>"
                    f"<td>{_fmt(_liq.midpoint)}</td>"
                    f"<td>{_chip(_liq.spread_state, _spread_kind)}</td>"
                    "</tr>"
                )
            _selection_html = (
                '<div class="app-grid-3" style="margin-top:10px">'
                '<div class="app-stat"><div class="app-stat__label">Expiration</div>'
                f'<div class="app-stat__value">{_expiration.expiration_date}</div>'
                f'<div class="app-muted" style="margin-top:6px">DTE {_fmt(_expiration.days_to_expiration, 0)}</div></div>'
                '<div class="app-stat"><div class="app-stat__label">ATM strike</div>'
                f'<div class="app-stat__value">{_expiration.atm_strike:,.1f}</div>'
                f'<div class="app-muted" style="margin-top:6px">Ref {_expiration.reference_underlying_price:,.2f}</div></div>'
                '<div class="app-stat"><div class="app-stat__label">ATM straddle</div>'
                f'<div class="app-stat__value">{html_escape(_straddle_value)}</div>'
                f'<div class="app-muted" style="margin-top:6px">Status {_straddle.status}</div></div>'
                '</div>'
                '<div style="overflow-x:auto;margin-top:12px">'
                '<table style="width:100%;border-collapse:collapse;font-size:0.86em">'
                '<thead><tr>'
                '<th align="left">Side</th><th align="right">Strike</th>'
                '<th align="right">Bid</th><th align="right">Ask</th>'
                '<th align="right">Mark</th><th align="right">Spread</th>'
                '<th align="right">Mid</th><th align="left">Liquidity</th>'
                '</tr></thead><tbody>'
                + "".join(_rows)
                + '</tbody></table></div>'
            )

        mo.vstack(
            [
                option_chain_refresh_button,
                mo.Html(
                    '<div class="app-section">'
                    '<div class="app-section__title">Option Chain Fixture View</div>'
                    '<div class="app-section__rule"></div></div>'
                    '<div class="app-card">'
                    '<div class="app-muted" style="margin-bottom:10px">'
                    'Read-only SPX option-chain display from an app-owned sanitized '
                    'fixture. Not live market data, not broker data, manual reload '
                    'only, no automatic refresh, no orders, and no trading '
                    'authorization changes.'
                    '</div>'
                    + _source_html
                    + _freshness_html
                    + _underlying_html
                    + _selection_html
                    + '</div>'
                ),
            ]
        )
    return


@app.cell
def _(mo):
    mo.Html(
        '<div class="app-section">'
        '<div class="app-section__title">Decision Console</div>'
        '<div class="app-section__rule"></div></div>'
    )
    return


@app.cell
def _(fixture_factories, mo):
    fixture_selector = mo.ui.dropdown(
        options=list(fixture_factories),
        value="Clean state",
        label="Inventory state fixture",
    )
    return (fixture_selector,)


@app.cell
def _(
    current_time_window_selector,
    daily_budget_input,
    fixture_selector,
    market_data_mode_selector,
    mo,
):
    mo.hstack(
        [
            fixture_selector,
            current_time_window_selector,
            market_data_mode_selector,
            daily_budget_input,
        ],
        gap=1,
        justify="start",
        wrap=True,
    )
    return


@app.cell
def _(fixture_factories, fixture_selector):
    selected_state = fixture_factories[fixture_selector.value]()
    return (selected_state,)


@app.cell
def _(evaluate_inventory_rules, selected_state, validate_inventory_state):
    validation_result = validate_inventory_state(selected_state)
    rule_decision = evaluate_inventory_rules(selected_state)
    return rule_decision, validation_result


@app.cell
def _(mo, rule_decision, selected_state, validation_result):
    _sev = rule_decision.severity.value
    _sev_meta = {
        "normal": {
            "badge": "#22c55e",
            "title": "Action allowed",
            "subtitle": "No rule blockers detected.",
            "modifier": "normal",
        },
        "caution": {
            "badge": "#facc15",
            "title": "Caution",
            "subtitle": "Discretionary actions allowed with constraints.",
            "modifier": "caution",
        },
        "restricted": {
            "badge": "#fb923c",
            "title": "Restricted action set",
            "subtitle": "Action permissions reduced by current state.",
            "modifier": "restricted",
        },
        "blocked": {
            "badge": "#ef4444",
            "title": "Action blocked",
            "subtitle": "Discretionary inventory adjustment is blocked.",
            "modifier": "blocked",
        },
    }
    _meta = _sev_meta.get(
        _sev,
        {
            "badge": "#94a3b8",
            "title": _sev.title(),
            "subtitle": "",
            "modifier": "normal",
        },
    )

    _allowed_actions = sorted(
        a.value.replace("_", " ") for a in rule_decision.allowed_actions
    )
    _blocked_actions = sorted(
        a.value.replace("_", " ") for a in rule_decision.blocked_actions
    )

    _allowed_chips = (
        "".join(
            f'<span class="app-chip app-chip--allowed">{a}</span>'
            for a in _allowed_actions
        )
        or '<span class="app-muted">—</span>'
    )
    _blocked_chips = (
        "".join(
            f'<span class="app-chip app-chip--blocked">{a}</span>'
            for a in _blocked_actions
        )
        or '<span class="app-muted">none</span>'
    )

    _severity_html = (
        f'<div class="app-severity app-severity--{_meta["modifier"]}">'
        f'<span class="app-severity__badge" style="background:{_meta["badge"]}">'
        f'{_sev}</span>'
        '<div>'
        f'<div class="app-severity__title">{_meta["title"]}</div>'
        f'<div class="app-severity__subtitle">{_meta["subtitle"]}</div>'
        '</div></div>'
    )

    _actions_html = (
        '<div class="app-grid-2">'
        '<div><div class="app-stat__label">Allowed actions</div>'
        f'<div style="margin-top:6px">{_allowed_chips}</div></div>'
        '<div><div class="app-stat__label">Blocked actions</div>'
        f'<div style="margin-top:6px">{_blocked_chips}</div></div>'
        '</div>'
    )

    _reason_items = "".join(f"<li>{r}</li>" for r in rule_decision.reasons)
    _warning_items = "".join(f"<li>{w}</li>" for w in rule_decision.warnings)
    _reasoning_parts = []
    if _reason_items:
        _reasoning_parts.append(
            '<div><div class="app-stat__label">Why</div>'
            f'<ul class="app-list">{_reason_items}</ul></div>'
        )
    if _warning_items:
        _reasoning_parts.append(
            '<div><div class="app-stat__label">Warnings</div>'
            f'<ul class="app-list">{_warning_items}</ul></div>'
        )
    _reasoning_html = (
        '<div class="app-grid-2" style="margin-top:10px">'
        + "".join(_reasoning_parts)
        + '</div>'
    ) if _reasoning_parts else ""

    _s = selected_state
    _ok = "✅"
    _fail = "❌"
    _stop = "\U0001f6d1"
    _thesis_valid = _ok if _s.position.thesis_valid else _fail
    _behavior_auth = _ok if _s.behavior.behavior_authorized else _fail
    _lockout = (
        _stop
        if _s.behavior.daily_lockout_active or _s.behavior.weekly_lockout_active
        else f"{_ok} None"
    )
    _state_html = (
        '<div class="app-grid-3">'
        '<div class="app-stat"><div class="app-stat__label">Dealer regime</div>'
        f'<div class="app-stat__value">{_s.market.dealer_regime.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Time window</div>'
        f'<div class="app-stat__value">{_s.market.time_window.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Structure</div>'
        f'<div class="app-stat__value">{_s.position.structure.value}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Thesis valid</div>'
        f'<div class="app-stat__value">{_thesis_valid}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Behavior auth</div>'
        f'<div class="app-stat__value">{_behavior_auth}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">Lockout</div>'
        f'<div class="app-stat__value">{_lockout}</div></div>'
        '</div>'
    )

    _val_elements = []
    for _msg in validation_result.messages:
        _kind = {"blocker": "danger", "warning": "warn", "info": "info"}.get(
            _msg.severity.value, "info"
        )
        _val_elements.append(
            mo.callout(mo.md(f"**{_msg.code}** — {_msg.message}"), kind=_kind)
        )
    if not _val_elements:
        _val_elements.append(
            mo.callout(mo.md("No validation issues."), kind="success")
        )

    mo.vstack(
        [
            mo.Html(_severity_html + _actions_html + _reasoning_html),
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:14px 0 6px;padding:0 4px">Inventory state</div>'
            ),
            mo.Html(_state_html),
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:14px 0 6px;padding:0 4px">Validation</div>'
            ),
            *_val_elements,
        ]
    )
    return


@app.cell
def _(mo):
    mo.Html(
        '<div class="app-section">'
        '<div class="app-section__title">Position Tracker</div>'
        '<div class="app-section__rule"></div></div>'
    )
    return


@app.cell
def _(PositionSide, PositionStructure, TIME_WINDOW_LABELS, TimeWindow, mo):
    structure_options = {
        s.value.replace("_", " ").title(): s for s in PositionStructure
    }
    side_options = {s.value.title(): s for s in PositionSide}
    close_by_options = {TIME_WINDOW_LABELS[tw]: tw for tw in TimeWindow}

    pos_form = mo.ui.dictionary(
        {
            "structure": mo.ui.dropdown(
                options=structure_options, label="Structure"
            ),
            "side": mo.ui.dropdown(
                options=side_options, value="Credit", label="Side"
            ),
            "description": mo.ui.text(label="Description", full_width=True),
            "contracts": mo.ui.number(
                start=1, value=1, step=1, label="Contracts"
            ),
            "entry_price": mo.ui.number(
                value=0.0, step=0.05, label="Entry price (per contract)"
            ),
            "max_loss": mo.ui.number(
                value=0.0, step=0.50, label="Max loss (per contract)"
            ),
            "target": mo.ui.number(
                value=0.0, step=0.25, label="Target profit (per contract)"
            ),
            "thesis": mo.ui.text(label="Thesis", full_width=True),
            "close_by": mo.ui.dropdown(
                options=close_by_options,
                value="Final Hour 15:15–15:45",
                label="Close by",
            ),
            "delta": mo.ui.number(value=0.0, step=0.01, label="Delta"),
            "gamma": mo.ui.number(value=0.0, step=0.01, label="Gamma"),
            "theta": mo.ui.number(value=0.0, step=0.01, label="Theta"),
            "friction": mo.ui.number(
                value=0.0, step=1.0, start=0.0, label="Friction paid ($)"
            ),
        }
    )
    return (pos_form,)


@app.cell
def _(mo, pos_form):
    # Render the dictionary's children in operationally-grouped sections.
    # `pos_form.value` continues to expose the same flat dict the add-handler
    # consumes — only the rendering layout changes.
    mo.vstack(
        [
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:4px 0 4px;padding:0 4px">Identity</div>'
            ),
            mo.hstack(
                [pos_form["structure"], pos_form["side"], pos_form["close_by"]],
                gap=1,
                wrap=True,
            ),
            pos_form["description"],
            pos_form["thesis"],
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:10px 0 4px;padding:0 4px">'
                'Sizing &amp; risk (per contract)</div>'
            ),
            mo.hstack(
                [pos_form["contracts"], pos_form["entry_price"]],
                gap=1,
                wrap=True,
            ),
            mo.hstack(
                [pos_form["max_loss"], pos_form["target"], pos_form["friction"]],
                gap=1,
                wrap=True,
            ),
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:10px 0 4px;padding:0 4px">'
                'Greeks (per contract)</div>'
            ),
            mo.hstack(
                [pos_form["delta"], pos_form["gamma"], pos_form["theta"]],
                gap=1,
                wrap=True,
            ),
        ]
    )
    return


@app.cell
def _(mo):
    add_button = mo.ui.run_button(label="Add Position")
    mo.hstack([add_button], justify="start")
    return (add_button,)


@app.cell
def _(
    add_button,
    add_click_state,
    create_position,
    current_time_window_selector,
    html_escape,
    mo,
    pos_form,
    positions_state,
    set_add_click,
    set_positions,
):
    add_msg = ""
    click_count = run_button_click_count(add_button)
    if click_count > add_click_state():
        set_add_click(click_count)
        v = pos_form.value
        try:
            desc = v["description"] or ""
            thesis = v["thesis"] or ""
            if not desc.strip() or not thesis.strip():
                raise ValueError("Description and thesis are required.")
            contracts_val = v["contracts"]
            if isinstance(contracts_val, float) and contracts_val.is_integer():
                contracts_val = int(contracts_val)
            new_pos = create_position(
                structure=v["structure"],
                side=v["side"],
                description=desc,
                contracts=contracts_val,
                entry_price=v["entry_price"],
                max_loss_per_contract=v["max_loss"],
                target_per_contract=v["target"],
                thesis=thesis,
                close_by_time=v["close_by"],
                entry_time_window=current_time_window_selector.value,
                delta=v["delta"],
                gamma=v["gamma"],
                theta=v["theta"],
                friction_paid=v["friction"],
            )
            set_positions(positions_state() + (new_pos,))
            add_msg = f"✅ Added: {html_escape(desc)}"
        except (ValueError, KeyError, TypeError) as exc:
            add_msg = f"❌ Error: {exc}"
    if add_msg:
        mo.output.replace(mo.md(f"**{add_msg}**"))
    return


@app.cell
def _(PositionStatus, mo, positions_state):
    open_positions = [p for p in positions_state() if p.status is PositionStatus.OPEN]
    manage_selector = None
    new_mark = None
    new_delta = None
    new_gamma = None
    new_theta = None
    update_mark_btn = None
    update_greeks_btn = None
    close_btn = None
    invalidate_btn = None
    adjust_btn = None

    if not open_positions:
        mo.output.replace(
            mo.vstack(
                [
                    mo.Html(
                        '<div class="app-stat__label" '
                        'style="margin:14px 0 6px;padding:0 4px">'
                        'Manage open positions</div>'
                    ),
                    mo.callout(
                        mo.md(
                            "No open positions yet. Add one in **Position "
                            "Entry** above to enable management actions."
                        ),
                        kind="info",
                    ),
                ]
            )
        )
    else:
        pos_options = {
            f"{p.description} ({p.id})": p.id for p in open_positions
        }
        manage_selector = mo.ui.dropdown(
            options=pos_options, label="Select position", full_width=True
        )
        new_mark = mo.ui.number(value=0.0, step=0.05, label="New mark")
        new_delta = mo.ui.number(value=0.0, step=0.01, label="New delta")
        new_gamma = mo.ui.number(value=0.0, step=0.01, label="New gamma")
        new_theta = mo.ui.number(value=0.0, step=0.01, label="New theta")

        update_mark_btn = mo.ui.run_button(label="Update Mark")
        update_greeks_btn = mo.ui.run_button(label="Update Greeks")
        close_btn = mo.ui.run_button(label="Close Position")
        invalidate_btn = mo.ui.run_button(label="Invalidate Thesis")
        adjust_btn = mo.ui.run_button(label="Record Adjustment")

        mo.vstack(
            [
                mo.Html(
                    '<div class="app-stat__label" '
                    'style="margin:14px 0 6px;padding:0 4px">'
                    'Manage open positions</div>'
                ),
                manage_selector,
                mo.Html(
                    '<div class="app-stat__label" '
                    'style="margin:8px 0 4px;padding:0 4px">'
                    'Marks &amp; greeks</div>'
                ),
                mo.hstack(
                    [new_mark, new_delta, new_gamma, new_theta],
                    gap=1,
                    wrap=True,
                ),
                mo.Html(
                    '<div class="app-stat__label" '
                    'style="margin:8px 0 4px;padding:0 4px">Actions</div>'
                ),
                mo.hstack(
                    [
                        update_mark_btn,
                        update_greeks_btn,
                        close_btn,
                        invalidate_btn,
                        adjust_btn,
                    ],
                    gap=1,
                    wrap=True,
                ),
            ]
        )
    return (
        adjust_btn,
        close_btn,
        invalidate_btn,
        manage_selector,
        new_delta,
        new_gamma,
        new_mark,
        new_theta,
        update_greeks_btn,
        update_mark_btn,
    )


@app.cell
def _(
    adjust_btn,
    close_btn,
    invalidate_btn,
    manage_click_state,
    manage_selector,
    mo,
    new_delta,
    new_gamma,
    new_mark,
    new_theta,
    positions_state,
    set_manage_click,
    set_positions,
    update_greeks_btn,
    update_mark_btn,
):
    def _apply(fn):
        pid = manage_selector.value
        try:
            updated = tuple(
                fn(p) if p.id == pid else p for p in positions_state()
            )
            set_positions(updated)
        except ValueError as exc:
            mo.output.replace(mo.md(f"**❌ {exc}**"))

    def _handle_click(key, button, fn):
        if button is None or manage_selector is None or not manage_selector.value:
            return
        click_count = run_button_click_count(button)
        handled = manage_click_state().get(key, 0)
        if click_count <= handled:
            return
        set_manage_click({**manage_click_state(), key: click_count})
        _apply(fn)

    _handle_click(
        "update_mark", update_mark_btn, lambda p: p.with_mark(new_mark.value)
    )
    _handle_click(
        "update_greeks",
        update_greeks_btn,
        lambda p: p.with_greeks(new_delta.value, new_gamma.value, new_theta.value),
    )
    _handle_click("close", close_btn, lambda p: p.closed(new_mark.value))
    _handle_click(
        "invalidate", invalidate_btn, lambda p: p.with_thesis_invalidated()
    )
    _handle_click("adjust", adjust_btn, lambda p: p.with_adjustment())
    return


@app.cell
def _(mo):
    mo.Html(
        '<div class="app-section">'
        '<div class="app-section__title">Calculators</div>'
        '<div class="app-section__rule"></div></div>'
    )
    return


@app.cell
def _(mo):
    hedge_option_delta = mo.ui.number(
        value=0.30, step=0.01, label="Option delta", full_width=True
    )
    hedge_contracts = mo.ui.number(
        start=1, step=1, value=1, label="SPX option contracts", full_width=True
    )
    hedge_percent = mo.ui.slider(
        start=0,
        stop=100,
        step=1,
        value=100,
        show_value=True,
        include_input=True,
        label="Hedge percent",
        full_width=True,
    )
    return hedge_contracts, hedge_option_delta, hedge_percent


@app.cell
def _(
    calculate_futures_hedge,
    hedge_contracts,
    hedge_option_delta,
    hedge_percent,
):
    def integer_input_value(value, field_name):
        if value is None:
            raise ValueError(f"{field_name} is required.")
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be an integer.")
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        raise ValueError(f"{field_name} must be an integer.")

    try:
        hedge_result = calculate_futures_hedge(
            option_delta=hedge_option_delta.value,
            contracts=integer_input_value(hedge_contracts.value, "contracts"),
            hedge_percent=hedge_percent.value / 100,
        )
        hedge_error = None
    except ValueError as exc:
        hedge_result = None
        hedge_error = str(exc)
    return hedge_error, hedge_result, integer_input_value


@app.cell
def _(
    hedge_contracts,
    hedge_error,
    hedge_option_delta,
    hedge_percent,
    hedge_result,
    mo,
):
    if hedge_error:
        _output = mo.callout(
            mo.md(f"**Input error:** `{hedge_error}`"), kind="danger"
        )
    else:
        _h = hedge_result
        _output = mo.vstack(
            [
                mo.hstack(
                    [
                        mo.stat(
                            value=f"${_h.dollar_delta_per_point:+,.0f}",
                            label="$/SPX pt (signed)",
                            bordered=True,
                        ),
                        mo.stat(
                            value=f"${_h.target_hedge_dollars_per_point:,.0f}",
                            label="Hedge target $/pt",
                            bordered=True,
                        ),
                    ]
                ),
                mo.hstack(
                    [
                        mo.stat(
                            value=str(_h.mes_rounded),
                            label="MES contracts",
                            bordered=True,
                        ),
                        mo.stat(
                            value=str(_h.es_rounded),
                            label="ES contracts",
                            bordered=True,
                        ),
                    ]
                ),
            ]
        )

    hedge_panel = mo.vstack(
        [
            mo.callout(
                mo.md(
                    "Temporary inventory-control math. Not trade authorization. "
                    "User-entered inputs only."
                ),
                kind="info",
            ),
            mo.hstack(
                [hedge_option_delta, hedge_contracts], gap=1, wrap=True
            ),
            hedge_percent,
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:8px 0 4px;padding:0 4px">Output</div>'
            ),
            _output,
        ]
    )
    return (hedge_panel,)


@app.cell
def _(mo):
    cost_contracts = mo.ui.number(
        start=1, step=1, value=1, label="Contracts", full_width=True
    )
    cost_legs = mo.ui.number(
        start=1, step=1, value=4, label="Legs", full_width=True
    )
    commission_per_contract = mo.ui.number(
        value=0.0, step=0.01, label="Commission per contract", full_width=True
    )
    fees_per_contract = mo.ui.number(
        value=0.0, step=0.01, label="Fees per contract", full_width=True
    )
    entry_spread_crossing = mo.ui.number(
        value=0.0,
        step=0.01,
        label="Entry spread crossing per contract",
        full_width=True,
    )
    exit_spread_crossing = mo.ui.number(
        value=0.0,
        step=0.01,
        label="Exit spread crossing per contract",
        full_width=True,
    )
    gross_target_dollars = mo.ui.number(
        value=100.0, step=1.0, label="Gross target dollars", full_width=True
    )
    return (
        commission_per_contract,
        cost_contracts,
        cost_legs,
        entry_spread_crossing,
        exit_spread_crossing,
        fees_per_contract,
        gross_target_dollars,
    )


@app.cell
def _(
    calculate_trade_friction,
    commission_per_contract,
    cost_contracts,
    cost_legs,
    entry_spread_crossing,
    exit_spread_crossing,
    fees_per_contract,
    gross_target_dollars,
    integer_input_value,
):
    try:
        cost_result = calculate_trade_friction(
            contracts=integer_input_value(cost_contracts.value, "contracts"),
            legs=integer_input_value(cost_legs.value, "legs"),
            commission_per_contract=commission_per_contract.value,
            fees_per_contract=fees_per_contract.value,
            entry_spread_crossing_per_contract=entry_spread_crossing.value,
            exit_spread_crossing_per_contract=exit_spread_crossing.value,
            gross_target_dollars=gross_target_dollars.value,
        )
        cost_error = None
    except ValueError as exc:
        cost_result = None
        cost_error = str(exc)
    return cost_error, cost_result


@app.cell
def _(
    commission_per_contract,
    cost_contracts,
    cost_error,
    cost_legs,
    cost_result,
    entry_spread_crossing,
    exit_spread_crossing,
    fees_per_contract,
    gross_target_dollars,
    mo,
):
    if cost_error:
        _cost_display = mo.callout(
            mo.md(f"**Input error:** `{cost_error}`"), kind="danger"
        )
        _friction_warning = mo.md("")
    else:
        _c = cost_result
        _cost_display = mo.vstack(
            [
                mo.hstack(
                    [
                        mo.stat(
                            value=str(_c.roundtrip_contract_count),
                            label="RT contracts",
                            bordered=True,
                        ),
                        mo.stat(
                            value=f"${_c.commission_and_fees:,.2f}",
                            label="Comm + fees",
                            bordered=True,
                        ),
                        mo.stat(
                            value=f"${_c.spread_crossing_cost:,.2f}",
                            label="Spread crossing",
                            bordered=True,
                        ),
                    ]
                ),
                mo.hstack(
                    [
                        mo.stat(
                            value=f"${_c.total_friction:,.2f}",
                            label="Total friction",
                            bordered=True,
                        ),
                        mo.stat(
                            value=f"${_c.target_after_friction:,.2f}",
                            label="After friction",
                            bordered=True,
                        ),
                        mo.stat(
                            value=f"{_c.friction_percent_of_target:.1%}",
                            label="Friction %",
                            bordered=True,
                        ),
                    ]
                ),
            ]
        )
        _friction_warning = (
            mo.callout(
                mo.md(
                    "Friction is ≥ 25% of gross target. Requires "
                    "explicit justification."
                ),
                kind="danger",
            )
            if _c.friction_warning
            else mo.md("")
        )

    friction_panel = mo.vstack(
        [
            mo.callout(
                mo.md(
                    "Friction sanity check. User-entered inputs only. "
                    "Not trade authorization."
                ),
                kind="info",
            ),
            mo.hstack([cost_contracts, cost_legs], gap=1, wrap=True),
            mo.hstack(
                [commission_per_contract, fees_per_contract], gap=1, wrap=True
            ),
            mo.hstack(
                [entry_spread_crossing, exit_spread_crossing], gap=1, wrap=True
            ),
            gross_target_dollars,
            mo.Html(
                '<div class="app-stat__label" '
                'style="margin:8px 0 4px;padding:0 4px">Output</div>'
            ),
            _cost_display,
            _friction_warning,
        ]
    )
    return (friction_panel,)


@app.cell
def _(friction_panel, hedge_panel, mo):
    mo.ui.tabs(
        {
            "Futures hedge": hedge_panel,
            "Cost / friction": friction_panel,
        }
    )
    return


@app.cell
def _(mo):
    mo.Html(
        '<div class="app-section">'
        '<div class="app-section__title">Operating Library</div>'
        '<div class="app-section__rule"></div></div>'
    )
    return


@app.cell
def _(get_reference_cards):
    reference_cards = get_reference_cards()
    reference_card_by_topic = {rc.topic: rc for rc in reference_cards}
    return reference_card_by_topic, reference_cards


@app.cell
def _(mo, reference_card_by_topic):
    reference_card_selector = mo.ui.dropdown(
        options=list(reference_card_by_topic),
        value="Dealer gamma / GEX",
        label="Reference topic",
    )
    return (reference_card_selector,)


@app.cell
def _(reference_card_by_topic, reference_card_selector):
    selected_reference_card = reference_card_by_topic[reference_card_selector.value]
    return (selected_reference_card,)


@app.cell
def _(mo, reference_card_selector, reference_cards, selected_reference_card):
    card = selected_reference_card

    mental_model_html = ""
    if card.mental_model:
        mental_model_html = (
            '<div class="app-mental">'
            '<div class="app-stat__label" style="color:#818cf8">Mental model</div>'
            f'<div style="margin-top:6px;color:#cbd5e1;line-height:1.6">'
            f'{card.mental_model}</div>'
            '</div>'
        )

    quick_ref_html = (
        '<div class="app-grid-2">'
        '<div class="app-stat"><div class="app-stat__label">What it means</div>'
        f'<div class="app-stat__value" style="font-size:0.9em">'
        f'{card.what_it_means}</div></div>'
        '<div class="app-stat"><div class="app-stat__label">'
        'Why it matters 0DTE</div>'
        f'<div class="app-stat__value" style="font-size:0.9em">'
        f'{card.why_it_matters_0dte}</div></div>'
        '<div class="app-stat"><div class="app-stat__label" '
        'style="color:#22c55e">Operating implication</div>'
        f'<div class="app-stat__value" style="font-size:0.9em">'
        f'{card.operating_implication}</div></div>'
        '<div class="app-stat"><div class="app-stat__label" '
        'style="color:#ef4444">Common error</div>'
        f'<div class="app-stat__value" style="font-size:0.9em">'
        f'{card.common_error}</div></div>'
        '</div>'
    )

    mechanics_html = ""
    if card.key_mechanics:
        items = "".join(
            '<div style="display:flex;gap:8px;margin-bottom:6px">'
            '<span style="color:#22c55e">▸</span>'
            f'<span style="color:#cbd5e1;line-height:1.5">{m}</span></div>'
            for m in card.key_mechanics
        )
        mechanics_html = (
            '<div class="app-card">'
            '<div class="app-stat__label" style="color:#22c55e">'
            'Key mechanics</div>'
            f'<div style="margin-top:8px">{items}</div></div>'
        )

    deep_dive_html = ""
    if card.deep_dive:
        paragraphs = card.deep_dive.split("\n\n")
        para_html = "".join(
            f'<p style="margin:0 0 10px;line-height:1.7;color:#cbd5e1">{p}</p>'
            for p in paragraphs
        )
        deep_dive_html = (
            '<div class="app-card">'
            '<div class="app-stat__label" style="color:#60a5fa">Deep dive</div>'
            f'<div style="margin-top:8px">{para_html}</div></div>'
        )

    verify_html = (
        '<div class="app-muted" style="margin-top:10px;padding:0 4px">'
        f'<strong>Verify:</strong> {", ".join(card.verification_inputs)}</div>'
    )

    _all_rows = [
        {
            "topic": rc.topic,
            "operating implication": rc.operating_implication,
            "common error": rc.common_error,
        }
        for rc in reference_cards
    ]

    reference_panel = mo.vstack(
        [
            reference_card_selector,
            mo.Html(
                mental_model_html
                + quick_ref_html
                + mechanics_html
                + deep_dive_html
                + verify_html
            ),
            mo.accordion(
                {
                    "All 12 reference cards (overview)": mo.ui.table(
                        _all_rows,
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                }
            ),
        ]
    )
    return (reference_panel,)


@app.cell
def _(Permission, asdict):
    def playbook_display_rows(rows):
        display_rows = []
        for row in rows:
            display_row = {}
            for key, value in asdict(row).items():
                display_row[key] = (
                    value.value.replace("_", " ")
                    if isinstance(value, Permission)
                    else value
                )
            display_rows.append(display_row)
        return display_rows

    return (playbook_display_rows,)


@app.cell
def _(
    get_action_permission_matrix,
    get_conversion_triage_table,
    get_structure_quick_reference,
    get_time_of_day_permission_matrix,
    mo,
    playbook_display_rows,
):
    playbook_panel = mo.vstack(
        [
            mo.callout(
                mo.md(
                    "Static operating reference. Closing remains superior "
                    "when adjustment is not clearly justified."
                ),
                kind="info",
            ),
            mo.accordion(
                {
                    "Action permission matrix (20 actions)": mo.ui.table(
                        playbook_display_rows(get_action_permission_matrix()),
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                    "Structure quick reference (8 structures)": mo.ui.table(
                        playbook_display_rows(get_structure_quick_reference()),
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                    "Conversion triage (10 scenarios)": mo.ui.table(
                        playbook_display_rows(get_conversion_triage_table()),
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                    "Time-of-day permissions "
                    "(15 actions × 9 windows)": mo.ui.table(
                        playbook_display_rows(
                            get_time_of_day_permission_matrix()
                        ),
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                }
            ),
        ]
    )
    return (playbook_panel,)


@app.cell
def _(get_session_prompt_templates):
    session_prompt_templates = get_session_prompt_templates()
    session_prompt_template_by_name = {
        prompt_template.name: prompt_template
        for prompt_template in session_prompt_templates
    }
    return (session_prompt_template_by_name,)


@app.cell
def _(mo, session_prompt_template_by_name):
    prompt_template_selector = mo.ui.dropdown(
        options=list(session_prompt_template_by_name),
        value="Pre-session regime synthesis",
        label="Prompt template",
    )
    return (prompt_template_selector,)


@app.cell
def _(prompt_template_selector, session_prompt_template_by_name):
    selected_prompt_template = session_prompt_template_by_name[
        prompt_template_selector.value
    ]
    return (selected_prompt_template,)


@app.cell
def _(mo, prompt_template_selector, selected_prompt_template):
    prompt_metadata = [
        {"field": "name", "value": selected_prompt_template.name},
        {"field": "purpose", "value": selected_prompt_template.purpose},
    ]
    required_inputs = [
        {"required input": required_input}
        for required_input in selected_prompt_template.required_inputs
    ]

    prompts_panel = mo.vstack(
        [
            mo.callout(
                mo.md(
                    "Copy-ready templates. Inputs may be user-supplied or "
                    "adapter-sourced. Missing, stale, partial, or unverifiable "
                    "fields must be marked unknown or require confirmation."
                ),
                kind="info",
            ),
            prompt_template_selector,
            mo.accordion(
                {
                    "Template metadata": mo.ui.table(
                        prompt_metadata,
                        pagination=False,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                    "Required inputs": mo.ui.table(
                        required_inputs,
                        pagination=True,
                        page_size=10,
                        selection=None,
                        show_column_summaries=False,
                        show_data_types=False,
                        show_download=False,
                    ),
                }
            ),
            mo.md("**Copy-ready template:**"),
            mo.md("```text\n" + selected_prompt_template.template + "\n```"),
        ]
    )
    return (prompts_panel,)


@app.cell
def _(mo, playbook_panel, prompts_panel, reference_panel):
    # Whole library is collapsed by default — visually subordinate to the
    # decision console and position tracker, but one click away.
    mo.accordion(
        {
            "\U0001f4da Reference cards": reference_panel,
            "\U0001f4d6 Playbook": playbook_panel,
            "\U0001f4ac Prompt templates": prompts_panel,
        }
    )
    return


@app.cell
def _(
    PositionStatus,
    TIME_WINDOW_LABELS,
    Urgency,
    calculate_session_summary,
    current_time_window_selector,
    daily_budget_input,
    mo,
    positions_state,
    time_urgency,
):
    all_positions = positions_state()
    summary = calculate_session_summary(
        all_positions, daily_budget_input.value or 2000.0
    )
    current_tw = current_time_window_selector.value

    def _pnl_color(val):
        if val > 0:
            return "#22c55e"
        if val < 0:
            return "#ef4444"
        return "#94a3b8"

    def _urgency_badge(u):
        colors = {
            Urgency.LOW: ("#334155", "#94a3b8"),
            Urgency.MEDIUM: ("#854d0e", "#facc15"),
            Urgency.HIGH: ("#9a3412", "#fb923c"),
            Urgency.CRITICAL: ("#7f1d1d", "#f87171"),
        }
        bg, fg = colors.get(u, ("#334155", "#94a3b8"))
        return (
            f'<span style="background:{bg};color:{fg};padding:1px 6px;'
            f'border-radius:4px;font-size:0.75em;font-weight:600">'
            f'{u.value.upper()}</span>'
        )

    def _budget_bar(pct):
        pct_clamped = max(0, min(pct, 1.0))
        w = int(pct_clamped * 100)
        color = (
            "#22c55e"
            if pct_clamped < 0.5
            else "#facc15"
            if pct_clamped < 0.8
            else "#ef4444"
        )
        return (
            f'<div style="background:#1e293b;border-radius:4px;height:10px;'
            f'width:100%;overflow:hidden">'
            f'<div style="background:{color};height:100%;width:{w}%"></div></div>'
        )

    tw_label = TIME_WINDOW_LABELS.get(current_tw, str(current_tw))
    pnl_c = _pnl_color(summary.net_pnl)

    sidebar_parts = [
        '<div style="font-size:0.85em;color:#e2e8f0">',
        '<div style="font-size:0.72em;text-transform:uppercase;color:#94a3b8;'
        'letter-spacing:0.08em;font-weight:700;margin-bottom:6px">Session</div>',
        f'<div style="color:#cbd5e1;margin-bottom:4px">{tw_label}</div>',
        f'<div style="margin-bottom:4px;color:#94a3b8;font-size:0.8em">'
        f'Daily budget ${daily_budget_input.value or 2000:.0f}</div>',
        _budget_bar(summary.budget_used_pct),
        f'<div style="color:#94a3b8;font-size:0.78em;margin-top:4px;'
        f'margin-bottom:14px">{summary.budget_used_pct:.0%} utilized</div>',
        '<div style="font-size:0.72em;text-transform:uppercase;color:#94a3b8;'
        'letter-spacing:0.08em;font-weight:700;margin-bottom:6px">P&amp;L</div>',
        f'<div style="font-size:1.3em;font-weight:700;color:{pnl_c};'
        'font-variant-numeric:tabular-nums">'
        f'{"" if summary.net_pnl < 0 else "+"}${summary.net_pnl:,.0f}</div>',
        '<div style="color:#94a3b8;font-size:0.78em">'
        f'Open ${summary.open_pnl:+,.0f} &middot; '
        f'Closed ${summary.closed_pnl:+,.0f}</div>',
        '<div style="color:#94a3b8;font-size:0.78em;margin-bottom:14px">'
        f'Friction −${summary.total_friction:,.0f}</div>',
        '<div style="font-size:0.72em;text-transform:uppercase;color:#94a3b8;'
        'letter-spacing:0.08em;font-weight:700;margin-bottom:6px">Greeks</div>',
        '<div style="font-variant-numeric:tabular-nums">'
        f'Δ {summary.net_delta:+.2f} &nbsp; '
        f'Γ {summary.net_gamma:+.3f} &nbsp; '
        f'Θ {summary.net_theta:+.2f}</div>',
        '<div style="color:#94a3b8;font-size:0.78em;margin-bottom:14px">'
        f'{summary.total_contracts_open} contracts open '
        f'&middot; {summary.total_adjustments} adjustments</div>',
    ]

    open_pos = [p for p in all_positions if p.status is PositionStatus.OPEN]
    if open_pos:
        sidebar_parts.append(
            '<div style="font-size:0.72em;text-transform:uppercase;'
            'color:#94a3b8;letter-spacing:0.08em;font-weight:700;'
            f'margin-bottom:6px">Open ({len(open_pos)})</div>'
        )
        for p in open_pos:
            urg = time_urgency(current_tw, p.close_by_time)
            pc = _pnl_color(p.total_pnl)
            pct_target = (
                f"{p.pnl_pct_of_target:.0%}" if p.target_total else "--"
            )
            description = p.description
            sidebar_parts.append(
                '<div style="background:#1e293b;border:1px solid #334155;'
                'border-radius:6px;padding:8px;margin-bottom:6px">'
                f'<div style="font-weight:600;margin-bottom:2px">{description}</div>'
                f'<div style="font-size:1.05em;color:{pc};font-weight:700;'
                'font-variant-numeric:tabular-nums">'
                f'{"" if p.total_pnl < 0 else "+"}${p.total_pnl:,.0f}</div>'
                '<div style="color:#94a3b8;font-size:0.78em">'
                f'{p.contracts}c &middot; Δ{p.net_delta:+.2f} '
                f'&middot; target {pct_target} &middot; {_urgency_badge(urg)}'
                '</div>'
            )
            if not p.thesis_still_valid:
                sidebar_parts.append(
                    '<div style="color:#f87171;font-size:0.78em;'
                    'font-weight:600;margin-top:4px">'
                    '⚠ Thesis invalidated</div>'
                )
            sidebar_parts.append('</div>')

    closed_pos = [p for p in all_positions if p.status is PositionStatus.CLOSED]
    if closed_pos:
        closed_pnl = sum(p.total_pnl for p in closed_pos)
        cp_color = _pnl_color(closed_pnl)
        sidebar_parts.append(
            '<div style="font-size:0.72em;text-transform:uppercase;'
            'color:#94a3b8;letter-spacing:0.08em;font-weight:700;'
            f'margin:14px 0 6px">Closed ({len(closed_pos)})</div>'
            f'<div style="color:{cp_color};font-variant-numeric:tabular-nums">'
            f'{"" if closed_pnl < 0 else "+"}${closed_pnl:,.0f}</div>'
        )

    sidebar_parts.append(
        '<div style="font-size:0.72em;text-transform:uppercase;'
        'color:#94a3b8;letter-spacing:0.08em;font-weight:700;'
        'margin:14px 0 6px">Discipline</div>'
        '<div style="color:#94a3b8;font-size:0.82em">'
        f'Trades {len(all_positions)} &middot; '
        f'Adjustments {summary.total_adjustments}</div>'
    )
    if summary.budget_used_pct >= 0.8:
        sidebar_parts.append(
            '<div style="color:#f87171;font-weight:600;font-size:0.82em;'
            'margin-top:4px">⚠ Budget ≥ 80%</div>'
        )
    if summary.total_adjustments >= 5:
        sidebar_parts.append(
            '<div style="color:#facc15;font-size:0.82em;margin-top:4px">'
            '⚠ High adjustment count</div>'
        )
    any_invalid = any(
        not p.thesis_still_valid and p.status is PositionStatus.OPEN
        for p in all_positions
    )
    if any_invalid:
        sidebar_parts.append(
            '<div style="color:#f87171;font-size:0.82em;margin-top:4px">'
            '⚠ Invalidated thesis still open</div>'
        )

    sidebar_parts.append('</div>')

    mo.sidebar(
        [
            mo.md("# \U0001f4ca Risk Console"),
            mo.Html(
                '<div class="app-muted" style="margin-bottom:10px">'
                'Persistent session view. Inputs that drive these numbers '
                '(window, budget) live in the top header strip.'
                '</div>'
            ),
            mo.Html("\n".join(sidebar_parts)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
