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
    BehaviorContext,
    DealerRegime,
    InventoryState,
    MarketContext,
    PositionContext,
    PositionStructure,
    TimeWindow,
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


def make_state(
    *,
    behavior_authorized: bool = True,
    daily_lockout_active: bool = False,
    weekly_lockout_active: bool = False,
    trying_to_avoid_loss_realization: bool = False,
    rule_violation_occurred: bool = False,
    accepted_beyond_invalidation: bool = False,
    liquidity_acceptable: bool = True,
    time_window: TimeWindow = TimeWindow.MORNING_945_1030,
    position_size_exceeds_plan: bool = False,
) -> InventoryState:
    return InventoryState(
        market=MarketContext(
            dealer_regime=DealerRegime.UNCLEAR,
            time_window=time_window,
            spot_relative_to_flip=None,
            event_pending=False,
            liquidity_acceptable=liquidity_acceptable,
        ),
        position=PositionContext(
            structure=PositionStructure.OTHER,
            thesis_valid=True,
            accepted_beyond_invalidation=accepted_beyond_invalidation,
            current_loss_inside_plan=True,
            gamma_manageable=True,
            delta_intentional=True,
            position_size_exceeds_plan=position_size_exceeds_plan,
        ),
        behavior=BehaviorContext(
            behavior_authorized=behavior_authorized,
            daily_lockout_active=daily_lockout_active,
            weekly_lockout_active=weekly_lockout_active,
            trying_to_avoid_loss_realization=trying_to_avoid_loss_realization,
            rule_violation_occurred=rule_violation_occurred,
        ),
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
    decision = evaluate_inventory_rules(make_state())

    assert decision.severity is DecisionSeverity.NORMAL
    assert decision.allowed_actions == FULL_DISCRETIONARY_ACTIONS
    assert decision.blocked_actions == set()
    assert decision.reasons == ["No rule blockers detected."]
    assert decision.warnings == []


def test_lockout_returns_blocked_and_flatten_only_actions() -> None:
    decision = evaluate_inventory_rules(make_state(daily_lockout_active=True))

    assert decision.severity is DecisionSeverity.BLOCKED
    assert decision.allowed_actions == FLATTEN_ONLY_ACTIONS
    assert decision.blocked_actions == set(Action) - FLATTEN_ONLY_ACTIONS
    assert decision.reasons == [
        "Daily or weekly lockout is active; discretionary adjustment is blocked."
    ]


def test_behavior_not_authorized_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(make_state(behavior_authorized=False))

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.HOLD in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions


def test_rule_violation_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(make_state(rule_violation_occurred=True))

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.STOP_TRADING in decision.allowed_actions


def test_thesis_invalidated_blocks_hold_and_convert_restructure() -> None:
    decision = evaluate_inventory_rules(make_state(accepted_beyond_invalidation=True))

    assert decision.severity is DecisionSeverity.BLOCKED
    assert Action.HOLD in decision.blocked_actions
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert Action.EMERGENCY_FLATTEN in decision.allowed_actions


def test_final_five_minutes_returns_restricted_and_flatten_only_actions() -> None:
    decision = evaluate_inventory_rules(make_state(time_window=TimeWindow.FINAL_5_1555_1600))

    assert decision.severity is DecisionSeverity.RESTRICTED
    assert decision.allowed_actions == FINAL_FIVE_MINUTE_ACTIONS
    assert decision.blocked_actions == set(Action) - FINAL_FIVE_MINUTE_ACTIONS
    assert decision.reasons == [
        "Final five-minute window; action set collapses to close, flatten, or stop."
    ]


def test_poor_liquidity_blocks_convert_but_allows_hedge_and_close() -> None:
    decision = evaluate_inventory_rules(make_state(liquidity_acceptable=False))

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.HEDGE_MES_ES in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions
    assert decision.warnings == ["Liquidity is poor; complex option-side adjustment is blocked."]


def test_size_exceeds_plan_produces_caution_and_warning() -> None:
    decision = evaluate_inventory_rules(make_state(position_size_exceeds_plan=True))

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.REDUCE in decision.allowed_actions
    assert Action.CLOSE in decision.allowed_actions
    assert decision.warnings == [
        "Position size exceeds plan; reducing exposure should be prioritized."
    ]


def test_loss_avoidance_risk_blocks_convert_restructure() -> None:
    decision = evaluate_inventory_rules(make_state(trying_to_avoid_loss_realization=True))

    assert decision.severity is DecisionSeverity.CAUTION
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert decision.warnings == [
        "Loss-avoidance risk detected; complex adjustment is blocked unless independently justified."
    ]


def test_lockout_overrides_lower_priority_warnings() -> None:
    decision = evaluate_inventory_rules(
        make_state(
            daily_lockout_active=True,
            trying_to_avoid_loss_realization=True,
            liquidity_acceptable=False,
            position_size_exceeds_plan=True,
        )
    )

    assert decision.severity is DecisionSeverity.BLOCKED
    assert decision.allowed_actions == FLATTEN_ONLY_ACTIONS
    assert decision.warnings == []
    assert decision.reasons == [
        "Daily or weekly lockout is active; discretionary adjustment is blocked."
    ]


def test_rule_decision_is_action_allowed() -> None:
    decision = evaluate_inventory_rules(make_state(liquidity_acceptable=False))

    assert decision.is_action_allowed(Action.CLOSE)
    assert not decision.is_action_allowed(Action.CONVERT_RESTRUCTURE)
