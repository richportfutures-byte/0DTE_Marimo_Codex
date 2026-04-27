import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # 0DTE SPX Inventory Adjustment Operating Reference

        Scope:

        - Not a signal engine
        - Not personalized financial advice
        - Not a beginner options course
        - Uses abstract rule-state fixtures only
        - No live market data
        - No fabricated Greeks, bid/asks, fills, strikes, or P/L
        - Deterministic rule permissions only
        """
    )
    return


@app.cell
def _():
    from dataclasses import asdict

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
    from spx_inventory_playbook.rules import evaluate_inventory_rules
    from spx_inventory_playbook.validators import validate_inventory_state

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
        asdict,
        calculate_futures_hedge,
        calculate_trade_friction,
        evaluate_inventory_rules,
        fixture_factories,
        get_action_permission_matrix,
        get_conversion_triage_table,
        get_structure_quick_reference,
        get_time_of_day_permission_matrix,
        validate_inventory_state,
    )


@app.cell
def _(fixture_factories, mo):
    fixture_selector = mo.ui.dropdown(
        options=list(fixture_factories),
        value="Clean state",
        label="Abstract fixture state",
    )

    mo.vstack([mo.md("## Fixture State"), fixture_selector])
    return (fixture_selector,)


@app.cell
def _(fixture_factories, fixture_selector):
    selected_state = fixture_factories[fixture_selector.value]()
    return (selected_state,)


@app.cell
def _(mo, selected_state):
    state_summary = [
        {"field": "dealer regime", "value": selected_state.market.dealer_regime.value},
        {"field": "time window", "value": selected_state.market.time_window.value},
        {"field": "position structure", "value": selected_state.position.structure.value},
        {"field": "thesis valid", "value": selected_state.position.thesis_valid},
        {
            "field": "accepted beyond invalidation",
            "value": selected_state.position.accepted_beyond_invalidation,
        },
        {"field": "liquidity acceptable", "value": selected_state.market.liquidity_acceptable},
        {
            "field": "behavior authorized",
            "value": selected_state.behavior.behavior_authorized,
        },
        {
            "field": "daily lockout active",
            "value": selected_state.behavior.daily_lockout_active,
        },
        {
            "field": "weekly lockout active",
            "value": selected_state.behavior.weekly_lockout_active,
        },
        {
            "field": "trying to avoid loss realization",
            "value": selected_state.behavior.trying_to_avoid_loss_realization,
        },
        {
            "field": "rule violation occurred",
            "value": selected_state.behavior.rule_violation_occurred,
        },
    ]

    mo.vstack(
        [
            mo.md("## Selected State Summary"),
            mo.ui.table(
                state_summary,
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


@app.cell
def _(evaluate_inventory_rules, selected_state, validate_inventory_state):
    validation_result = validate_inventory_state(selected_state)
    rule_decision = evaluate_inventory_rules(selected_state)
    return rule_decision, validation_result


@app.cell
def _(mo, validation_result):
    validation_rows = [
        {
            "severity": message.severity.value,
            "code": message.code,
            "message": message.message,
        }
        for message in validation_result.messages
    ] or [{"severity": "", "code": "NONE", "message": "No validation messages."}]

    mo.vstack(
        [
            mo.md("## Validation Messages"),
            mo.ui.table(
                validation_rows,
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


@app.cell
def _(mo, rule_decision):
    rule_summary = [
        {"field": "severity", "value": rule_decision.severity.value},
        {
            "field": "allowed actions",
            "value": ", ".join(sorted(action.value for action in rule_decision.allowed_actions)),
        },
        {
            "field": "blocked actions",
            "value": ", ".join(sorted(action.value for action in rule_decision.blocked_actions))
            or "none",
        },
        {"field": "reasons", "value": "; ".join(rule_decision.reasons) or "none"},
        {"field": "warnings", "value": "; ".join(rule_decision.warnings) or "none"},
    ]

    mo.vstack(
        [
            mo.md("## Rule Decision"),
            mo.ui.table(
                rule_summary,
                pagination=False,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Mechanical Calculators

        - User-entered inputs only.
        - No live data.
        - No recommendation.
        - Hedge sizing is temporary inventory-control math, not trade authorization.
        - Cost calculator uses user-supplied estimates only.
        """
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
        hedge_display = mo.md(f"**Input error:** `{hedge_error}`")
    else:
        hedge_display = mo.ui.table(
            [
                {
                    "metric": "signed dollar delta per SPX point",
                    "value": hedge_result.dollar_delta_per_point,
                },
                {
                    "metric": "target hedge dollars per point",
                    "value": hedge_result.target_hedge_dollars_per_point,
                },
                {"metric": "MES equivalent", "value": hedge_result.mes_equivalent},
                {"metric": "rounded MES", "value": hedge_result.mes_rounded},
                {"metric": "ES equivalent", "value": hedge_result.es_equivalent},
                {"metric": "rounded ES", "value": hedge_result.es_rounded},
            ],
            pagination=False,
            selection=None,
            show_column_summaries=False,
            show_data_types=False,
            show_download=False,
        )

    mo.vstack([mo.md("#### Futures Hedge Output"), hedge_display])
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
        cost_display = mo.md(f"**Input error:** `{cost_error}`")
        friction_warning_display = mo.md("")
    else:
        cost_display = mo.ui.table(
            [
                {
                    "metric": "roundtrip contract count",
                    "value": cost_result.roundtrip_contract_count,
                },
                {"metric": "commission and fees", "value": cost_result.commission_and_fees},
                {"metric": "spread crossing cost", "value": cost_result.spread_crossing_cost},
                {"metric": "total friction", "value": cost_result.total_friction},
                {"metric": "target after friction", "value": cost_result.target_after_friction},
                {
                    "metric": "friction percent of target",
                    "value": cost_result.friction_percent_of_target,
                },
                {"metric": "friction warning", "value": cost_result.friction_warning},
            ],
            pagination=False,
            selection=None,
            show_column_summaries=False,
            show_data_types=False,
            show_download=False,
        )
        friction_warning_display = (
            mo.md(
                "Friction is at least 25% of the gross target. This does not reject the trade "
                "automatically, but it requires explicit justification."
            )
            if cost_result.friction_warning
            else mo.md("")
        )

    mo.vstack([mo.md("#### Cost / Friction Output"), cost_display, friction_warning_display])
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Inventory Adjustment Playbook

        - Static operating reference.
        - Not a strategy encyclopedia.
        - Closing remains superior when adjustment is not clearly justified.
        - Tables are compact by design.
        """
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
def _(get_action_permission_matrix, mo, playbook_display_rows):
    mo.vstack(
        [
            mo.md("### Action Permission Matrix"),
            mo.ui.table(
                playbook_display_rows(get_action_permission_matrix()),
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
def _(get_structure_quick_reference, mo, playbook_display_rows):
    mo.vstack(
        [
            mo.md("### Structure Quick Reference"),
            mo.ui.table(
                playbook_display_rows(get_structure_quick_reference()),
                pagination=True,
                page_size=8,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


@app.cell
def _(get_conversion_triage_table, mo, playbook_display_rows):
    mo.vstack(
        [
            mo.md("### Conversion Triage"),
            mo.ui.table(
                playbook_display_rows(get_conversion_triage_table()),
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
def _(get_time_of_day_permission_matrix, mo, playbook_display_rows):
    mo.vstack(
        [
            mo.md("### Time-of-Day Permission Matrix"),
            mo.ui.table(
                playbook_display_rows(get_time_of_day_permission_matrix()),
                pagination=True,
                page_size=15,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                show_download=False,
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
