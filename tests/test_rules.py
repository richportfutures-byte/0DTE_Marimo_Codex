from spx_inventory_playbook.fixtures import (
    behavior_not_authorized_state,
    clean_state,
    final_five_minutes_state,
    lockout_state,
    loss_avoidance_state,
    poor_liquidity_state,
    rule_violation_state,
    size_exceeds_plan_state,
    state_with_overrides,
    thesis_invalidated_state,
)
from spx_inventory_playbook.rules import (
    FINAL_FIVE_MINUTE_ACTIONS,
    FLATTEN_ONLY_ACTIONS,
    FULL_DISCRETIONARY_ACTIONS,
    DecisionSeverity,
    allowed_actions_from_validation,
    evaluate_inventory_rules,
    list_valid_actions,
)
from spx_inventory_playbook.validators import (
    Action,
    ValidationMessage,
    ValidationResult,
    ValidationSeverity,
)


def test_valid_actions_are_planned_inventory_actions() -> None:
    assert list_valid_actions() == tuple(Action)


def validation_result_with_code(code: str) -> ValidationResult:
    return ValidationResult(
        messages=[
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code=code,
                message="test message",
            )
        ]
    )


def test_allowed_actions_collapse_for_lockout() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("LOCKOUT_ACTIVE")) == {
        Action.EMERGENCY_FLATTEN,
        Action.CLOSE,
        Action.STOP_TRADING,
    }


def test_allowed_actions_collapse_for_behavior_not_authorized() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("BEHAVIOR_NOT_AUTHORIZED")) == {
        Action.REDUCE,
        Action.CLOSE,
        Action.HEDGE_MES_ES,
        Action.STOP_TRADING,
    }


def test_allowed_actions_collapse_for_thesis_invalidated() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("THESIS_INVALIDATED")) == {
        Action.REDUCE,
        Action.CLOSE,
        Action.EMERGENCY_FLATTEN,
        Action.STOP_TRADING,
    }


def test_allowed_actions_are_broad_for_clean_validation() -> None:
    assert allowed_actions_from_validation(ValidationResult(messages=[])) == FULL_DISCRETIONARY_ACTIONS


def test_clean_state_returns_normal_and_full_discretionary_set() -> None:
    decision = evaluate_inventory_rules(clean_state())

    assert decision.severity is DecisionSeverity.NORMAL
    assert decision.allowed_actions == FULL_DISCRETIONARY_ACTIONS
    assert decision.blocked_actions == set()
    assert decision.reasons == ["No rule blockers detected."]
    assert decision.warnings == []


def test_lockout_returns_blocked_and_flatten_only_actions() -> None:
    decision = evaluate_inventory_rules(lockout_state())

    assert decision.severity is DecisionSeverity.BLOCKED
    assert decision.allowed_actions == FLATTEN_ONLY_ACTIONS
    assert decision.blocked_actions == set(Action) - FLATTEN_ONLY_ACTIONS
    assert decision.reasons == [
        "Daily or weekly lockout is active; discretionary adjustment is blocked."
    ]


def test_behavior_not_authorized_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(behavior_not_authorized_state())

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.HOLD in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions


def test_rule_violation_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(rule_violation_state())

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.STOP_TRADING in decision.allowed_actions


def test_thesis_invalidated_blocks_hold_and_convert_restructure() -> None:
    decision = evaluate_inventory_rules(thesis_invalidated_state())

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.HOLD in decision.blocked_actions
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.EMERGENCY_FLATTEN in decision.allowed_actions


def test_final_five_minutes_returns_restricted_and_flatten_only_actions() -> None:
    decision = evaluate_inventory_rules(final_five_minutes_state())

    assert decision.severity is DecisionSeverity.RESTRICTED
    assert decision.allowed_actions == FINAL_FIVE_MINUTE_ACTIONS
    assert decision.blocked_actions == set(Action) - FINAL_FIVE_MINUTE_ACTIONS
    assert decision.reasons == [
        "Final five-minute window; action set collapses to close, flatten, or stop."
    ]


def test_poor_liquidity_blocks_convert_but_allows_hedge_and_close() -> None:
    decision = evaluate_inventory_rules(poor_liquidity_state())

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.HEDGE_MES_ES in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions
    assert decision.warnings == ["Liquidity is poor; complex option-side adjustment is blocked."]


def test_size_exceeds_plan_produces_caution_and_warning() -> None:
    decision = evaluate_inventory_rules(size_exceeds_plan_state())

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.REDUCE in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions
    assert decision.warnings == [
        "Position size exceeds plan; reducing exposure should be prioritized."
    ]


def test_loss_avoidance_risk_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(loss_avoidance_state())

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert decision.warnings == [
        "Loss-avoidance risk detected; complex adjustment is blocked unless independently justified."
    ]


def test_lockout_overrides_lower_priority_warnings() -> None:
    decision = evaluate_inventory_rules(
        state_with_overrides(
            lockout_state(),
            **{
                "behavior.trying_to_avoid_loss_realization": True,
                "market.liquidity_acceptable": False,
                "position.position_size_exceeds_plan": True,
            },
        )
    )

    assert decision.severity is DecisionSeverity.BLOCKED
    assert decision.allowed_actions == FLATTEN_ONLY_ACTIONS
    assert decision.warnings == []
    assert decision.reasons == [
        "Daily or weekly lockout is active; discretionary adjustment is blocked."
    ]


def test_rule_decision_is_action_allowed() -> None:
    decision = evaluate_inventory_rules(poor_liquidity_state())

    assert decision.is_action_allowed(Action.CLOSE)
    assert not decision.is_action_allowed(Action.CONVERT_RESTRUCTURE)
