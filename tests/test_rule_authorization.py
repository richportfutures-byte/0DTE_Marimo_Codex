from pathlib import Path

from spx_inventory_playbook.adapters.option_chain_provider import MarketDataProviderState
from spx_inventory_playbook.fixtures import (
    behavior_not_authorized_state,
    clean_state,
    final_five_minutes_state,
    lockout_state,
    loss_avoidance_state,
    rule_violation_state,
    thesis_invalidated_state,
)
from spx_inventory_playbook.rules import (
    ActionStatus,
    DataSourceClassification,
    DecisionSeverity,
    InvalidationState,
    RuleAuthorizationContext,
    RuleSetup,
    SizeTier,
    evaluate_rule_engine_authorization,
)
from spx_inventory_playbook.validators import Action, PositionStructure


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"


def authorize(
    state=clean_state(),
    market_data_state=MarketDataProviderState.LIVE_FRESH,
    context: RuleAuthorizationContext | None = None,
):
    return evaluate_rule_engine_authorization(
        state,
        market_data_state=market_data_state,
        context=context,
    )


def test_rule_engine_decision_is_top_level_authorization_shape() -> None:
    decision = authorize()

    assert decision.can_act is True
    assert decision.action_status is ActionStatus.AUTHORIZED
    assert decision.market_data_state is MarketDataProviderState.LIVE_FRESH
    assert decision.data_source_classification is DataSourceClassification.LIVE
    assert decision.allowed_actions
    assert decision.allowed_structures
    assert decision.blocked_actions == set(Action) - decision.allowed_actions
    assert decision.required_confirmations == ()
    assert decision.reasons == ["No rule blockers detected."]


def test_missing_market_data_state_fails_closed() -> None:
    decision = authorize(market_data_state=None)

    assert decision.can_act is False
    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.market_data_state is None
    assert decision.data_source_classification is DataSourceClassification.UNKNOWN
    assert decision.allowed_actions == {Action.STOP_TRADING}
    assert "load_fresh_live_market_data" in decision.required_confirmations


def test_fixture_data_is_simulation_only_not_live_authorization() -> None:
    decision = authorize(market_data_state=MarketDataProviderState.FIXTURE)

    assert decision.can_act is False
    assert decision.action_status is ActionStatus.SIMULATION_ONLY
    assert decision.data_source_classification is DataSourceClassification.FIXTURE_SIMULATION
    assert decision.market_data_state is MarketDataProviderState.FIXTURE
    assert decision.allowed_structures == set()
    assert "fixture_simulation_acknowledgement" in decision.required_confirmations


def test_live_fresh_allows_normal_rule_evaluation() -> None:
    decision = authorize(market_data_state=MarketDataProviderState.LIVE_FRESH)

    assert decision.can_act is True
    assert decision.action_status is ActionStatus.AUTHORIZED
    assert decision.severity is DecisionSeverity.NORMAL
    assert Action.CONVERT_RESTRUCTURE in decision.allowed_actions


def test_live_stale_restricts_authorization() -> None:
    decision = authorize(market_data_state=MarketDataProviderState.LIVE_STALE)

    assert decision.can_act is False
    assert decision.action_status is ActionStatus.RESTRICTED
    assert decision.allowed_actions == {Action.STOP_TRADING}
    assert decision.size_tier is SizeTier.FLATTEN_ONLY
    assert "refresh_live_market_data" in decision.required_confirmations


def test_live_unavailable_blocks_live_action() -> None:
    decision = authorize(market_data_state=MarketDataProviderState.LIVE_UNAVAILABLE)

    assert decision.can_act is False
    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.allowed_actions == {Action.STOP_TRADING}
    assert "restore_live_market_data" in decision.required_confirmations


def test_live_parse_error_blocks_live_action() -> None:
    decision = authorize(market_data_state=MarketDataProviderState.LIVE_PARSE_ERROR)

    assert decision.can_act is False
    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.allowed_actions == {Action.STOP_TRADING}
    assert "repair_live_market_data_parse" in decision.required_confirmations


def test_lockout_blocks_discretionary_action() -> None:
    decision = authorize(lockout_state())

    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.size_tier is SizeTier.FLATTEN_ONLY
    assert Action.CLOSE in decision.allowed_actions
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_thesis_invalidation_blocks_thesis_based_action() -> None:
    decision = authorize(thesis_invalidated_state())

    assert decision.action_status is ActionStatus.BLOCKED
    assert decision.invalidation_state is InvalidationState.INVALIDATED
    assert Action.HOLD in decision.blocked_actions
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions


def test_final_five_minutes_restricts_authorization() -> None:
    decision = authorize(final_five_minutes_state())

    assert decision.action_status is ActionStatus.RESTRICTED
    assert decision.allowed_actions == {
        Action.CLOSE,
        Action.EMERGENCY_FLATTEN,
        Action.STOP_TRADING,
    }


def test_missing_foundation_blocks_aggressive_directional_expression() -> None:
    decision = evaluate_rule_engine_authorization(
        clean_state(),
        context=RuleAuthorizationContext(
            market_data_state=MarketDataProviderState.LIVE_FRESH,
            foundation_established=False,
        ),
    )

    assert decision.action_status is ActionStatus.RESTRICTED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert PositionStructure.CREDIT_SPREAD in decision.blocked_structures
    assert "foundation_state_established" in decision.required_confirmations


def test_bounce_never_inherits_reclaim_permissions() -> None:
    decision = evaluate_rule_engine_authorization(
        clean_state(),
        context=RuleAuthorizationContext(
            market_data_state=MarketDataProviderState.LIVE_FRESH,
            setup=RuleSetup.BOUNCE,
        ),
    )

    assert decision.action_status is ActionStatus.RESTRICTED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert "bounce_not_reclaim_acknowledgement" in decision.required_confirmations


def test_failed_continuation_downgrades_authorization() -> None:
    decision = evaluate_rule_engine_authorization(
        clean_state(),
        context=RuleAuthorizationContext(
            market_data_state=MarketDataProviderState.LIVE_FRESH,
            setup=RuleSetup.CONTINUATION,
            continuation_failed=True,
        ),
    )

    assert decision.action_status is ActionStatus.RESTRICTED
    assert decision.size_tier is SizeTier.FLATTEN_ONLY
    assert Action.HOLD in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions
    assert "failed_continuation_downgrade_acknowledgement" in decision.required_confirmations


def test_behavior_impairment_blocks_or_restricts_action() -> None:
    decision = authorize(behavior_not_authorized_state())

    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.REDUCE in decision.allowed_actions


def test_rule_violation_blocks_or_restricts_action() -> None:
    decision = authorize(rule_violation_state())

    assert decision.action_status is ActionStatus.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert Action.STOP_TRADING in decision.allowed_actions


def test_loss_avoidance_risk_requires_confirmation_and_blocks_complex_adjustment() -> None:
    decision = authorize(loss_avoidance_state())

    assert decision.action_status is ActionStatus.CONFIRMATION_REQUIRED
    assert Action.CONVERT_RESTRUCTURE in decision.blocked_actions
    assert "independent_loss_avoidance_justification" in decision.required_confirmations


def test_notebook_operator_authorization_uses_rule_decision_object() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "evaluate_operator_input_authorization" in source
    assert "market_data_state=option_chain_toggle_result.provider_state" in source
    assert "Can I act?" in source
    assert "Allowed" in source
    assert "Blocked" in source
    assert "Required confirmations" in source
    assert "Market data state" in source
    assert "rule_decision.action_status.value" in source
    assert "rule_decision.required_confirmations" in source
    assert "evaluate_inventory_rules" not in source
