from pathlib import Path

from spx_inventory_playbook.adapters.option_chain_provider import MarketDataProviderState
from spx_inventory_playbook.fixtures import clean_state, state_with_overrides
from spx_inventory_playbook.operator_inputs import (
    OperatorBehaviorAuthorization,
    OperatorContinuationState,
    OperatorDeltaContext,
    OperatorFoundationState,
    OperatorGammaRegime,
    OperatorInputState,
    OperatorLiquidity,
    OperatorLockoutState,
    OperatorLossAvoidanceRisk,
    OperatorPositionSize,
    OperatorRuleViolationState,
    OperatorSetup,
    OperatorThesisValidity,
    normalize_operator_input_state,
    operator_input_from_inventory_state,
)
from spx_inventory_playbook.rules import (
    ActionStatus,
    DataSourceClassification,
    SizeTier,
    evaluate_operator_input_authorization,
)
from spx_inventory_playbook.validators import Action, DealerRegime, TimeWindow


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"


def valid_operator_input(**overrides: object) -> OperatorInputState:
    values = {
        "time_window": TimeWindow.MORNING_945_1030,
        "dealer_regime": DealerRegime.POSITIVE_GEX,
        "liquidity": OperatorLiquidity.ACCEPTABLE,
        "thesis_validity": OperatorThesisValidity.VALID,
        "gamma_regime": OperatorGammaRegime.MANAGEABLE,
        "delta_context": OperatorDeltaContext.INTENTIONAL,
        "position_size": OperatorPositionSize.INSIDE_PLAN,
        "lockout_state": OperatorLockoutState.NONE,
        "behavior_authorization": OperatorBehaviorAuthorization.AUTHORIZED,
        "rule_violations": OperatorRuleViolationState.NONE,
        "loss_avoidance_risk": OperatorLossAvoidanceRisk.ABSENT,
        "foundation_state": OperatorFoundationState.ESTABLISHED,
        "setup": OperatorSetup.NONE,
        "continuation_state": OperatorContinuationState.INTACT,
    }
    values.update(overrides)
    return OperatorInputState(**values)


def authorize(operator_input: OperatorInputState, state=MarketDataProviderState.LIVE_FRESH):
    decision, validation = evaluate_operator_input_authorization(
        operator_input,
        market_data_state=state,
    )
    return decision, validation


def test_operator_input_object_includes_all_required_fields() -> None:
    fields = set(OperatorInputState.__dataclass_fields__)

    assert {
        "time_window",
        "dealer_regime",
        "liquidity",
        "thesis_validity",
        "gamma_regime",
        "delta_context",
        "position_size",
        "lockout_state",
        "behavior_authorization",
        "rule_violations",
        "loss_avoidance_risk",
    } <= fields


def test_missing_required_inputs_fail_closed() -> None:
    decision, validation = authorize(valid_operator_input(dealer_regime=None))

    assert validation.is_valid is False
    assert validation.missing_inputs[0].field_name == "dealer_regime"
    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.allowed_actions == {Action.STOP_TRADING}
    assert "resolve_operator_input_defects" in decision.required_confirmations


def test_ambiguous_inputs_fail_closed() -> None:
    decision, validation = authorize(
        valid_operator_input(liquidity=OperatorLiquidity.AMBIGUOUS)
    )

    assert validation.is_valid is False
    assert validation.invalid_inputs[0].code == "LIQUIDITY_AMBIGUOUS"
    assert decision.action_status is ActionStatus.BLOCKED


def test_invalid_inputs_fail_closed() -> None:
    decision, validation = authorize(valid_operator_input(delta_context="unknown"))

    assert validation.is_valid is False
    assert validation.invalid_inputs[0].code == "DELTA_CONTEXT_INVALID"
    assert decision.action_status is ActionStatus.BLOCKED


def test_valid_complete_inputs_reach_rule_engine() -> None:
    decision, validation = authorize(valid_operator_input())
    normalized = normalize_operator_input_state(valid_operator_input())

    assert validation.is_valid is True
    assert normalized.inventory_state.market.dealer_regime is DealerRegime.POSITIVE_GEX
    assert decision.action_status is ActionStatus.AUTHORIZED
    assert decision.can_act is True


def test_fixture_demo_inputs_are_clearly_labeled_simulation() -> None:
    operator_input = operator_input_from_inventory_state(
        state_with_overrides(
            clean_state(),
            **{"market.dealer_regime": DealerRegime.POSITIVE_GEX},
        ),
        simulation_label="Fixture/simulation demo: Clean state",
    )
    decision, validation = authorize(operator_input, state=MarketDataProviderState.FIXTURE)

    assert validation.is_valid is True
    assert operator_input.is_simulation is True
    assert "Fixture/simulation demo" in operator_input.simulation_label
    assert decision.action_status is ActionStatus.SIMULATION_ONLY
    assert decision.data_source_classification is DataSourceClassification.FIXTURE_SIMULATION


def test_live_fixture_distinction_is_preserved() -> None:
    live_decision, _ = authorize(valid_operator_input(), MarketDataProviderState.LIVE_FRESH)
    fixture_decision, _ = authorize(valid_operator_input(), MarketDataProviderState.FIXTURE)

    assert live_decision.data_source_classification is DataSourceClassification.LIVE
    assert fixture_decision.data_source_classification is DataSourceClassification.FIXTURE_SIMULATION
    assert fixture_decision.can_act is False


def test_lockout_input_blocks_action() -> None:
    decision, validation = authorize(
        valid_operator_input(lockout_state=OperatorLockoutState.DAILY)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_thesis_invalidation_input_blocks_action() -> None:
    decision, validation = authorize(
        valid_operator_input(thesis_validity=OperatorThesisValidity.INVALIDATED)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.HOLD in decision.blocked_actions


def test_behavior_impairment_input_blocks_or_restricts_action() -> None:
    decision, validation = authorize(
        valid_operator_input(
            behavior_authorization=OperatorBehaviorAuthorization.IMPAIRED
        )
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_rule_violation_input_blocks_or_restricts_action() -> None:
    decision, validation = authorize(
        valid_operator_input(rule_violations=OperatorRuleViolationState.OCCURRED)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.STOP_TRADING in decision.allowed_actions


def test_loss_avoidance_risk_input_blocks_or_restricts_action() -> None:
    decision, validation = authorize(
        valid_operator_input(loss_avoidance_risk=OperatorLossAvoidanceRisk.PRESENT)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.CONFIRMATION_REQUIRED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_final_five_minutes_input_blocks_or_restricts_action() -> None:
    decision, validation = authorize(
        valid_operator_input(time_window=TimeWindow.FINAL_5_1555_1600)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.RESTRICTED
    assert decision.size_tier is SizeTier.FLATTEN_ONLY


def test_missing_foundation_blocks_aggressive_directional_action() -> None:
    decision, validation = authorize(
        valid_operator_input(foundation_state=OperatorFoundationState.MISSING)
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.RESTRICTED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_bounce_does_not_inherit_reclaim_permissions() -> None:
    decision, validation = authorize(valid_operator_input(setup=OperatorSetup.BOUNCE))

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.RESTRICTED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_failed_continuation_downgrades_authorization() -> None:
    decision, validation = authorize(
        valid_operator_input(
            setup=OperatorSetup.CONTINUATION,
            continuation_state=OperatorContinuationState.FAILED,
        )
    )

    assert validation.is_valid is True
    assert decision.action_status is ActionStatus.RESTRICTED
    assert decision.size_tier is SizeTier.FLATTEN_ONLY
    assert Action.HOLD in decision.blocked_actions


def test_notebook_facing_workflow_consumes_rule_decision_object() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "OperatorInputState" in source
    assert "evaluate_operator_input_authorization" in source
    assert "operator_input_validation.missing_inputs" in source
    assert "operator_input_validation.invalid_inputs" in source
    assert "Blocking authorization defects" in source
    assert "rule_decision.action_status.value" in source
    assert "Fixture/simulation demo inputs" in source
