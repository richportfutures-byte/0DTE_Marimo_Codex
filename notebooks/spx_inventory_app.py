import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.Html(
        '<div style="text-align:center;padding:24px 0 8px">'
        '<div style="font-size:2em;font-weight:800;letter-spacing:-0.02em">'
        '\U0001f3af 0DTE SPX Inventory Workstation</div>'
        '<div style="color:#94a3b8;font-size:0.95em;margin-top:4px">'
        'Operating reference &bull; Position tracker &bull; Rule engine &bull; Calculators</div>'
        '</div>'
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            "**Safety boundaries:** No live market data. No fabricated Greeks, "
            "bid/asks, fills, strikes, or P/L. No automated trade recommendations. "
            "User-supplied inputs only. Not personalized financial advice."
        ),
        kind="warn",
    )
    return


@app.cell
def _():
    from dataclasses import asdict
    from html import escape as html_escape

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

    return (
        Permission,
        PositionSide,
        PositionStatus,
        PositionStructure,
        TimeWindow,
        TIME_WINDOW_LABELS,
        Urgency,
        asdict,
        calculate_futures_hedge,
        calculate_session_summary,
        calculate_trade_friction,
        create_position,
        evaluate_inventory_rules,
        fixture_factories,
        get_action_permission_matrix,
        get_conversion_triage_table,
        get_reference_cards,
        get_session_prompt_templates,
        get_structure_quick_reference,
        get_time_of_day_permission_matrix,
        html_escape,
        time_urgency,
        validate_inventory_state,
    )


@app.cell
def _(mo):
    mo.md("---")
    return


@app.cell
def _(get_reference_cards):
    reference_cards = get_reference_cards()
    reference_card_by_topic = {
        reference_card.topic: reference_card for reference_card in reference_cards
    }
    return reference_card_by_topic, reference_cards


@app.cell
def _(mo, reference_card_by_topic):
    reference_card_selector = mo.ui.dropdown(
        options=list(reference_card_by_topic),
        value="Dealer gamma / GEX",
        label="Select topic",
    )
    mo.hstack(
        [
            mo.md("## \U0001f4da Reference Cards"),
            reference_card_selector,
        ],
        justify="start",
        gap=1,
        align="end",
    )
    return (reference_card_selector,)


@app.cell
def _(reference_card_by_topic, reference_card_selector):
    selected_reference_card = reference_card_by_topic[reference_card_selector.value]
    return (selected_reference_card,)


@app.cell
def _(mo, selected_reference_card):
    card = selected_reference_card
    card_html = (
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">'
        '<div style="background:var(--md-sys-color-surface-container);border-radius:10px;padding:14px">'
        f'<div style="font-size:0.75em;text-transform:uppercase;color:#94a3b8;font-weight:600;letter-spacing:0.05em">What it means</div>'
        f'<div style="margin-top:4px">{card.what_it_means}</div></div>'
        '<div style="background:var(--md-sys-color-surface-container);border-radius:10px;padding:14px">'
        f'<div style="font-size:0.75em;text-transform:uppercase;color:#94a3b8;font-weight:600;letter-spacing:0.05em">Why it matters 0DTE</div>'
        f'<div style="margin-top:4px">{card.why_it_matters_0dte}</div></div>'
        '<div style="background:var(--md-sys-color-surface-container);border-radius:10px;padding:14px">'
        f'<div style="font-size:0.75em;text-transform:uppercase;color:#22c55e;font-weight:600;letter-spacing:0.05em">Operating implication</div>'
        f'<div style="margin-top:4px">{card.operating_implication}</div></div>'
        '<div style="background:var(--md-sys-color-surface-container);border-radius:10px;padding:14px">'
        f'<div style="font-size:0.75em;text-transform:uppercase;color:#ef4444;font-weight:600;letter-spacing:0.05em">Common error</div>'
        f'<div style="margin-top:4px">{card.common_error}</div></div>'
        '</div>'
        f'<div style="margin-top:10px;color:#94a3b8;font-size:0.85em">'
        f'<strong>Verify:</strong> {", ".join(card.verification_inputs)}</div>'
    )
    mo.Html(card_html)
    return


@app.cell
def _(mo, reference_cards):
    reference_overview_rows = [
        {
            "topic": rc.topic,
            "operating implication": rc.operating_implication,
            "common error": rc.common_error,
        }
        for rc in reference_cards
    ]
    mo.accordion(
        {
            "\U0001f4cb All 12 Reference Cards": mo.ui.table(
                reference_overview_rows,
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        }
    )
    return


@app.cell
def _(mo):
    mo.md("---")
    return


@app.cell
def _(fixture_factories, mo):
    fixture_selector = mo.ui.dropdown(
        options=list(fixture_factories),
        value="Clean state",
        label="Select state",
    )
    mo.hstack(
        [mo.md("## \u2696\ufe0f Rule Engine"), fixture_selector],
        justify="start",
        gap=1,
        align="end",
    )
    return (fixture_selector,)


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
def _(mo, rule_decision, validation_result, selected_state):
    sev = rule_decision.severity.value
    sev_colors = {
        "normal": ("#22c55e", "success"),
        "caution": ("#facc15", "warn"),
        "restricted": ("#fb923c", "warn"),
        "blocked": ("#ef4444", "danger"),
    }
    sev_color, sev_kind = sev_colors.get(sev, ("#94a3b8", "info"))

    allowed = ", ".join(sorted(a.value.replace("_", " ") for a in rule_decision.allowed_actions))
    blocked = ", ".join(sorted(a.value.replace("_", " ") for a in rule_decision.blocked_actions)) or "none"

    severity_badge = (
        f'<span style="background:{sev_color};color:#000;padding:3px 10px;'
        f'border-radius:6px;font-weight:700;font-size:0.85em;text-transform:uppercase">{sev}</span>'
    )

    # Validation messages as callouts
    val_elements = []
    for msg in validation_result.messages:
        kind = {"blocker": "danger", "warning": "warn", "info": "info"}.get(msg.severity.value, "info")
        val_elements.append(
            mo.callout(mo.md(f"**{msg.code}** — {msg.message}"), kind=kind)
        )
    if not val_elements:
        val_elements.append(mo.callout(mo.md("No validation issues."), kind="success"))

    # State summary in compact grid
    s = selected_state
    ok_icon = "\u2705"
    fail_icon = "\u274c"
    stop_icon = "\U0001f6d1"
    thesis_valid = ok_icon if s.position.thesis_valid else fail_icon
    behavior_auth = ok_icon if s.behavior.behavior_authorized else fail_icon
    lockout = stop_icon if s.behavior.daily_lockout_active or s.behavior.weekly_lockout_active else f"{ok_icon} None"
    state_html = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:0.85em">'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Dealer Regime</div>{s.market.dealer_regime.value}</div>'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Time Window</div>{s.market.time_window.value}</div>'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Structure</div>{s.position.structure.value}</div>'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Thesis Valid</div>{thesis_valid}</div>'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Behavior Auth</div>{behavior_auth}</div>'
        f'<div style="background:var(--md-sys-color-surface-container);border-radius:8px;padding:10px">'
        f'<div style="color:#94a3b8;font-size:0.8em">Lockout</div>{lockout}</div>'
        '</div>'
    )

    mo.vstack(
        [
            mo.hstack([mo.md("### Decision"), mo.Html(severity_badge)], justify="start", gap=0.5, align="center"),
            mo.Html(state_html),
            *val_elements,
            mo.md(f"**Allowed:** {allowed}"),
            mo.md(f"**Blocked:** {blocked}") if blocked != "none" else mo.md(""),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("---")
    return


@app.cell
def _(mo):
    mo.md("## \U0001f9ee Calculators")
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md("User-entered inputs only. Hedge sizing is temporary inventory-control math, not trade authorization."),
        kind="info",
    )
    return


@app.cell
def _(mo):
    hedge_option_delta = mo.ui.number(
        value=0.30,
        step=0.01,
        label="Option delta",
        full_width=True,
    )
    hedge_contracts = mo.ui.number(
        start=1,
        step=1,
        value=1,
        label="SPX option contracts",
        full_width=True,
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

    mo.vstack(
        [
            mo.md("### Futures Hedge Calculator"),
            hedge_option_delta,
            hedge_contracts,
            hedge_percent,
            mo.md("A futures hedge is temporary inventory control, not a second unmanaged trade."),
        ]
    )
    return hedge_contracts, hedge_option_delta, hedge_percent


@app.cell
def _(calculate_futures_hedge, hedge_contracts, hedge_option_delta, hedge_percent):
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
def _(hedge_error, hedge_result, mo):
    if hedge_error:
        hedge_display = mo.callout(mo.md(f"**Input error:** `{hedge_error}`"), kind="danger")
    else:
        h = hedge_result
        hedge_display = mo.vstack([
            mo.hstack([
                mo.stat(value=f"${h.dollar_delta_per_point:+,.0f}", label="$/SPX pt (signed)", bordered=True),
                mo.stat(value=f"${h.target_hedge_dollars_per_point:,.0f}", label="Hedge target $/pt", bordered=True),
            ]),
            mo.hstack([
                mo.stat(value=str(h.mes_rounded), label="MES contracts", bordered=True),
                mo.stat(value=str(h.es_rounded), label="ES contracts", bordered=True),
            ]),
        ])
    mo.vstack([mo.md("#### Hedge Output"), hedge_display])
    return


@app.cell
def _(mo):
    cost_contracts = mo.ui.number(
        start=1,
        step=1,
        value=1,
        label="Contracts",
        full_width=True,
    )
    cost_legs = mo.ui.number(
        start=1,
        step=1,
        value=4,
        label="Legs",
        full_width=True,
    )
    commission_per_contract = mo.ui.number(
        value=0.0,
        step=0.01,
        label="Commission per contract",
        full_width=True,
    )
    fees_per_contract = mo.ui.number(
        value=0.0,
        step=0.01,
        label="Fees per contract",
        full_width=True,
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
        value=100.0,
        step=1.0,
        label="Gross target dollars",
        full_width=True,
    )

    mo.vstack(
        [
            mo.md("### Cost / Friction Calculator"),
            cost_contracts,
            cost_legs,
            commission_per_contract,
            fees_per_contract,
            entry_spread_crossing,
            exit_spread_crossing,
            gross_target_dollars,
        ]
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
def _(cost_error, cost_result, mo):
    if cost_error:
        cost_display = mo.callout(mo.md(f"**Input error:** `{cost_error}`"), kind="danger")
        friction_warning_display = mo.md("")
    else:
        c = cost_result
        cost_display = mo.vstack([
            mo.hstack([
                mo.stat(value=str(c.roundtrip_contract_count), label="RT contracts", bordered=True),
                mo.stat(value=f"${c.commission_and_fees:,.2f}", label="Comm + fees", bordered=True),
                mo.stat(value=f"${c.spread_crossing_cost:,.2f}", label="Spread crossing", bordered=True),
            ]),
            mo.hstack([
                mo.stat(value=f"${c.total_friction:,.2f}", label="Total friction", bordered=True),
                mo.stat(value=f"${c.target_after_friction:,.2f}", label="After friction", bordered=True),
                mo.stat(value=f"{c.friction_percent_of_target:.1%}", label="Friction %", bordered=True),
            ]),
        ])
        friction_warning_display = (
            mo.callout(
                mo.md(
                    "Friction is \u2265 25% of gross target. Requires explicit justification."
                ),
                kind="danger",
            )
            if c.friction_warning
            else mo.md("")
        )
    mo.vstack([mo.md("#### Cost / Friction Output"), cost_display, friction_warning_display])
    return


@app.cell
def _(mo):
    mo.md("---")
    return


@app.cell
def _(mo):
    mo.md("## \U0001f4d6 Playbook")
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md("Static operating reference. Closing remains superior when adjustment is not clearly justified."),
        kind="info",
    )
    return


@app.cell
def _(Permission, asdict):
    def playbook_display_rows(rows):
        display_rows = []
        for row in rows:
            display_row = {}
            for key, value in asdict(row).items():
                display_row[key] = (
                    value.value.replace("_", " ") if isinstance(value, Permission) else value
                )
            display_rows.append(display_row)
        return display_rows

    return (playbook_display_rows,)


@app.cell
def _(get_action_permission_matrix, get_structure_quick_reference, get_conversion_triage_table, get_time_of_day_permission_matrix, mo, playbook_display_rows):
    mo.accordion(
        {
            "\u2705 Action Permission Matrix (20 actions)": mo.ui.table(
                playbook_display_rows(get_action_permission_matrix()),
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
            "\U0001f4cc Structure Quick Reference (8 structures)": mo.ui.table(
                playbook_display_rows(get_structure_quick_reference()),
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
            "\U0001f504 Conversion Triage (10 scenarios)": mo.ui.table(
                playbook_display_rows(get_conversion_triage_table()),
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
            "\u23f0 Time-of-Day Permissions (15 actions \u00d7 9 windows)": mo.ui.table(
                playbook_display_rows(get_time_of_day_permission_matrix()),
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        }
    )
    return


@app.cell
def _(mo):
    mo.md("---")
    return


@app.cell
def _(mo):
    mo.md("## \U0001f4ac Prompt Templates")
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md("Copy-ready templates. User supplies all data. Missing fields must be marked unknown."),
        kind="info",
    )
    return


@app.cell
def _(get_session_prompt_templates):
    session_prompt_templates = get_session_prompt_templates()
    session_prompt_template_by_name = {
        prompt_template.name: prompt_template for prompt_template in session_prompt_templates
    }
    return session_prompt_template_by_name, session_prompt_templates


@app.cell
def _(mo, session_prompt_template_by_name):
    prompt_template_selector = mo.ui.dropdown(
        options=list(session_prompt_template_by_name),
        value="Pre-session regime synthesis",
        label="Prompt template",
    )

    mo.vstack([mo.md("### Template Selector"), prompt_template_selector])
    return (prompt_template_selector,)


@app.cell
def _(prompt_template_selector, session_prompt_template_by_name):
    selected_prompt_template = session_prompt_template_by_name[prompt_template_selector.value]
    return (selected_prompt_template,)


@app.cell
def _(mo, selected_prompt_template):
    prompt_metadata = [
        {"field": "name", "value": selected_prompt_template.name},
        {"field": "purpose", "value": selected_prompt_template.purpose},
    ]
    required_inputs = [
        {"required input": required_input}
        for required_input in selected_prompt_template.required_inputs
    ]

    mo.vstack(
        [
            mo.md("### Template Metadata"),
            mo.ui.table(
                prompt_metadata,
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
            mo.md("#### Required Inputs"),
            mo.ui.table(
                required_inputs,
                pagination=True,
                page_size=10,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


@app.cell
def _(mo, selected_prompt_template):
    mo.vstack(
        [
            mo.md("### Copy-Ready Template"),
            mo.md("```text\n" + selected_prompt_template.template + "\n```"),
        ]
    )
    return


# ── Position Tracking State ──


@app.cell
def _(mo, TimeWindow, TIME_WINDOW_LABELS):
    positions_state, set_positions = mo.state(())
    add_click_state, set_add_click = mo.state(0)
    manage_click_state, set_manage_click = mo.state({})
    daily_budget_input = mo.ui.number(
        value=2000.0, step=100.0, start=0.0,
        label="Daily loss budget ($)", full_width=True,
    )
    current_time_window_selector = mo.ui.dropdown(
        options={TIME_WINDOW_LABELS[tw]: tw for tw in TimeWindow},
        value="Morning 9:45\u201310:30",
        label="Current time window",
    )
    return (
        current_time_window_selector,
        daily_budget_input,
        add_click_state,
        set_add_click,
        manage_click_state,
        set_manage_click,
        positions_state,
        set_positions,
    )


@app.cell
def _():
    def run_button_click_count(button):
        frontend_count = getattr(button, "_value_frontend", None)
        if frontend_count is not None:
            return int(frontend_count or 0)
        return 1 if button.value else 0

    return (run_button_click_count,)


# ── Position Entry Form ──


@app.cell
def _(
    mo,
    PositionSide,
    PositionStructure,
    TimeWindow,
    TIME_WINDOW_LABELS,
):
    structure_options = {s.value.replace("_", " ").title(): s for s in PositionStructure}
    side_options = {s.value.title(): s for s in PositionSide}
    close_by_options = {TIME_WINDOW_LABELS[tw]: tw for tw in TimeWindow}

    pos_form = mo.ui.dictionary(
        {
            "structure": mo.ui.dropdown(options=structure_options, label="Structure"),
            "side": mo.ui.dropdown(options=side_options, value="Credit", label="Side"),
            "description": mo.ui.text(label="Description", full_width=True),
            "contracts": mo.ui.number(start=1, value=1, step=1, label="Contracts"),
            "entry_price": mo.ui.number(value=0.0, step=0.05, label="Entry price (per contract)"),
            "max_loss": mo.ui.number(value=0.0, step=0.50, label="Max loss (per contract)"),
            "target": mo.ui.number(value=0.0, step=0.25, label="Target profit (per contract)"),
            "thesis": mo.ui.text(label="Thesis", full_width=True),
            "close_by": mo.ui.dropdown(options=close_by_options, value="Final Hour 15:15\u201315:45", label="Close by"),
            "delta": mo.ui.number(value=0.0, step=0.01, label="Delta"),
            "gamma": mo.ui.number(value=0.0, step=0.01, label="Gamma"),
            "theta": mo.ui.number(value=0.0, step=0.01, label="Theta"),
            "friction": mo.ui.number(value=0.0, step=1.0, start=0.0, label="Friction paid ($)"),
        }
    )

    mo.vstack([
        mo.md("## \U0001f4cb Position Entry"),
        mo.md("User-supplied inputs only. No live data. No fabricated values."),
        pos_form,
    ])
    return (pos_form,)


@app.cell
def _(
    mo,
):
    add_button = mo.ui.run_button(label="Add Position")
    mo.hstack([add_button])
    return (add_button,)


@app.cell
def _(
    add_button,
    pos_form,
    positions_state,
    set_positions,
    create_position,
    current_time_window_selector,
    add_click_state,
    set_add_click,
    run_button_click_count,
    html_escape,
    mo,
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
            add_msg = f"\u2705 Added: {html_escape(desc)}"
        except (ValueError, KeyError, TypeError) as exc:
            add_msg = f"\u274c Error: {exc}"
    if add_msg:
        mo.output.replace(mo.md(f"**{add_msg}**"))
    return


# ── Position Management (update marks, close, invalidate) ──


@app.cell
def _(mo, positions_state, PositionStatus):
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
        mo.output.replace(mo.md("*No open positions.*"))
    else:
        pos_options = {f"{p.description} ({p.id})": p.id for p in open_positions}
        manage_selector = mo.ui.dropdown(options=pos_options, label="Select position")
        new_mark = mo.ui.number(value=0.0, step=0.05, label="New mark")
        new_delta = mo.ui.number(value=0.0, step=0.01, label="New delta")
        new_gamma = mo.ui.number(value=0.0, step=0.01, label="New gamma")
        new_theta = mo.ui.number(value=0.0, step=0.01, label="New theta")

        update_mark_btn = mo.ui.run_button(label="Update Mark")
        update_greeks_btn = mo.ui.run_button(label="Update Greeks")
        close_btn = mo.ui.run_button(label="Close Position")
        invalidate_btn = mo.ui.run_button(label="Invalidate Thesis")
        adjust_btn = mo.ui.run_button(label="Record Adjustment")

        mo.vstack([
            mo.md("## \U0001f527 Manage Positions"),
            manage_selector,
            mo.hstack([new_mark, new_delta, new_gamma, new_theta]),
            mo.hstack([update_mark_btn, update_greeks_btn, close_btn, invalidate_btn, adjust_btn]),
        ])
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
    run_button_click_count,
    set_manage_click,
    set_positions,
    update_greeks_btn,
    update_mark_btn,
):
    def _apply(fn):
        pid = manage_selector.value
        try:
            updated = tuple(fn(p) if p.id == pid else p for p in positions_state())
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

    _handle_click("update_mark", update_mark_btn, lambda p: p.with_mark(new_mark.value))
    _handle_click(
        "update_greeks",
        update_greeks_btn,
        lambda p: p.with_greeks(new_delta.value, new_gamma.value, new_theta.value),
    )
    _handle_click("close", close_btn, lambda p: p.closed(new_mark.value))
    _handle_click("invalidate", invalidate_btn, lambda p: p.with_thesis_invalidated())
    _handle_click("adjust", adjust_btn, lambda p: p.with_adjustment())
    return


# ── Sidebar Dashboard ──


@app.cell
def _(
    mo,
    positions_state,
    calculate_session_summary,
    daily_budget_input,
    current_time_window_selector,
    html_escape,
    time_urgency,
    Urgency,
    PositionStatus,
    TIME_WINDOW_LABELS,
):
    all_positions = positions_state()
    summary = calculate_session_summary(all_positions, daily_budget_input.value or 2000.0)
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
        return f'<span style="background:{bg};color:{fg};padding:1px 6px;border-radius:4px;font-size:0.75em;font-weight:600">{u.value.upper()}</span>'

    def _budget_bar(pct):
        pct_clamped = max(0, min(pct, 1.0))
        w = int(pct_clamped * 100)
        color = "#22c55e" if pct_clamped < 0.5 else "#facc15" if pct_clamped < 0.8 else "#ef4444"
        return f'<div style="background:#1e293b;border-radius:4px;height:12px;width:100%;overflow:hidden"><div style="background:{color};height:100%;width:{w}%"></div></div>'

    # Build sidebar HTML
    tw_label = TIME_WINDOW_LABELS.get(current_tw, str(current_tw))
    pnl_c = _pnl_color(summary.net_pnl)

    sidebar_parts = [
        '<div style="font-family:monospace;font-size:0.85em;color:#e2e8f0">',
        '<div style="font-size:1.1em;font-weight:700;margin-bottom:8px">\U0001f4ca SESSION</div>',
        f'<div style="color:#94a3b8;margin-bottom:4px">{tw_label}</div>',
        f'<div style="margin-bottom:4px">Budget: ${daily_budget_input.value or 2000:.0f}</div>',
        _budget_bar(summary.budget_used_pct),
        f'<div style="color:#94a3b8;font-size:0.8em;margin-bottom:12px">{summary.budget_used_pct:.0%} utilized</div>',
        '<hr style="border-color:#334155;margin:8px 0">',
        '<div style="font-weight:700;margin-bottom:6px">\U0001f4b0 P&L</div>',
        f'<div style="font-size:1.3em;font-weight:700;color:{pnl_c}">',
        f'{"" if summary.net_pnl < 0 else "+"}${summary.net_pnl:,.0f}</div>',
        '<div style="color:#94a3b8;font-size:0.8em">',
        f'Open: ${summary.open_pnl:+,.0f} | Closed: ${summary.closed_pnl:+,.0f}</div>',
        '<div style="color:#94a3b8;font-size:0.8em;margin-bottom:12px">',
        f'Friction: -${summary.total_friction:,.0f}</div>',
        '<hr style="border-color:#334155;margin:8px 0">',
        '<div style="font-weight:700;margin-bottom:6px">\U0001f9ee GREEKS</div>',
        f'<div>\u0394 {summary.net_delta:+.2f} &nbsp; \u0393 {summary.net_gamma:+.3f} &nbsp; \u0398 {summary.net_theta:+.2f}</div>',
        f'<div style="color:#94a3b8;font-size:0.8em;margin-bottom:12px">{summary.total_contracts_open} contracts open | {summary.total_adjustments} adj</div>',
    ]

    # Position cards
    open_pos = [p for p in all_positions if p.status is PositionStatus.OPEN]
    if open_pos:
        sidebar_parts.append('<hr style="border-color:#334155;margin:8px 0">')
        sidebar_parts.append(f'<div style="font-weight:700;margin-bottom:6px">\U0001f4c2 OPEN ({len(open_pos)})</div>')
        for p in open_pos:
            urg = time_urgency(current_tw, p.close_by_time)
            pc = _pnl_color(p.total_pnl)
            pct_target = f"{p.pnl_pct_of_target:.0%}" if p.target_total else "--"
            description = p.description
            sidebar_parts.append(
                f'<div style="background:#1e293b;border-radius:6px;padding:8px;margin-bottom:6px">'
                f'<div style="font-weight:600;margin-bottom:2px">{description}</div>'
                f'<div style="font-size:1.1em;color:{pc};font-weight:700">{"" if p.total_pnl < 0 else "+"}${p.total_pnl:,.0f}</div>'
                f'<div style="color:#94a3b8;font-size:0.8em">'
                f'{p.contracts}c | \u0394{p.net_delta:+.2f} | target {pct_target} | {_urgency_badge(urg)}'
                f'</div>'
            )
            if not p.thesis_still_valid:
                sidebar_parts.append('<div style="color:#f87171;font-size:0.8em;font-weight:600">\u26a0 THESIS INVALIDATED</div>')
            sidebar_parts.append('</div>')

    # Closed positions summary
    closed_pos = [p for p in all_positions if p.status is PositionStatus.CLOSED]
    if closed_pos:
        sidebar_parts.append('<hr style="border-color:#334155;margin:8px 0">')
        closed_pnl = sum(p.total_pnl for p in closed_pos)
        cp_color = _pnl_color(closed_pnl)
        sidebar_parts.append(
            f'<div style="font-weight:700;margin-bottom:4px">\u2705 CLOSED ({len(closed_pos)})</div>'
            f'<div style="color:{cp_color}">{"" if closed_pnl < 0 else "+"}${closed_pnl:,.0f}</div>'
        )

    # Behavioral health
    sidebar_parts.append('<hr style="border-color:#334155;margin:8px 0">')
    sidebar_parts.append('<div style="font-weight:700;margin-bottom:4px">\U0001f6e1 DISCIPLINE</div>')
    sidebar_parts.append(f'<div style="color:#94a3b8;font-size:0.85em">Trades: {len(all_positions)} | Adj: {summary.total_adjustments}</div>')
    if summary.budget_used_pct >= 0.8:
        sidebar_parts.append('<div style="color:#f87171;font-weight:600;font-size:0.85em">\u26a0 Budget &ge; 80%</div>')
    if summary.total_adjustments >= 5:
        sidebar_parts.append('<div style="color:#facc15;font-size:0.85em">\u26a0 High adjustment count</div>')
    any_invalid = any(not p.thesis_still_valid and p.status is PositionStatus.OPEN for p in all_positions)
    if any_invalid:
        sidebar_parts.append('<div style="color:#f87171;font-size:0.85em">\u26a0 Invalidated thesis still open</div>')

    sidebar_parts.append('</div>')

    mo.sidebar(
        [
            mo.md("# \U0001f3af Dashboard"),
            current_time_window_selector,
            daily_budget_input,
            mo.Html("\n".join(sidebar_parts)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
