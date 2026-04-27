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

    return evaluate_inventory_rules, fixture_factories, validate_inventory_state


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


if __name__ == "__main__":
    app.run()
