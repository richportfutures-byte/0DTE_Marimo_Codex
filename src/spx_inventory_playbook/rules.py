"""Deterministic workstation authorization rules."""

from dataclasses import dataclass
from enum import Enum

from .adapters.option_chain_provider import MarketDataProviderState
from .validators import (
    Action,
    InventoryState,
    PositionStructure,
    TimeWindow,
    ValidationResult,
    validate_inventory_state,
)


VALID_ACTIONS = tuple(Action)
LIVE_ACTION_STOP_SET = {Action.STOP_TRADING}
FULL_DISCRETIONARY_ACTIONS = {
    Action.HOLD,
    Action.TAKE_PARTIAL_PROFIT,
    Action.REDUCE,
    Action.HEDGE_MES_ES,
    Action.CONVERT_RESTRUCTURE,
    Action.CLOSE,
    Action.STOP_TRADING,
}
FLATTEN_ONLY_ACTIONS = {Action.CLOSE, Action.EMERGENCY_FLATTEN, Action.STOP_TRADING}
BEHAVIOR_IMPAIRED_ACTIONS = {
    Action.REDUCE,
    Action.CLOSE,
    Action.EMERGENCY_FLATTEN,
    Action.HEDGE_MES_ES,
    Action.STOP_TRADING,
}
THESIS_INVALIDATED_ACTIONS = {
    Action.REDUCE,
    Action.CLOSE,
    Action.EMERGENCY_FLATTEN,
    Action.STOP_TRADING,
}
FINAL_FIVE_MINUTE_ACTIONS = {Action.CLOSE, Action.EMERGENCY_FLATTEN, Action.STOP_TRADING}
FOUNDATION_REQUIRED_STRUCTURES = {
    PositionStructure.LONG_OPTION,
    PositionStructure.DEBIT_SPREAD,
    PositionStructure.CREDIT_SPREAD,
    PositionStructure.RATIO_OR_BACKSPREAD,
}


class DecisionSeverity(Enum):
    """Highest-severity state for deterministic inventory permissions."""

    NORMAL = "normal"
    CAUTION = "caution"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class ActionStatus(Enum):
    """Top-level answer to whether the operator may act."""

    AUTHORIZED = "authorized"
    CONFIRMATION_REQUIRED = "confirmation_required"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    SIMULATION_ONLY = "simulation_only"


class DataSourceClassification(Enum):
    """Explicit fixture/live classification for authorization decisions."""

    FIXTURE_SIMULATION = "fixture_simulation"
    LIVE = "live"
    UNKNOWN = "unknown"


class SizeTier(Enum):
    """Position sizing posture emitted by the rule engine."""

    NORMAL = "normal"
    REDUCE_PRIORITY = "reduce_priority"
    FLATTEN_ONLY = "flatten_only"


class InvalidationState(Enum):
    """Thesis/invalidation posture emitted by the rule engine."""

    VALID = "valid"
    INVALIDATED = "invalidated"
    UNKNOWN = "unknown"


class RuleSetup(Enum):
    """Optional setup context for doctrine-specific authorization downgrades."""

    NONE = "none"
    RECLAIM = "reclaim"
    BOUNCE = "bounce"
    CONTINUATION = "continuation"


@dataclass(frozen=True)
class RuleAuthorizationContext:
    """Optional R6 authorization inputs outside the abstract inventory state."""

    market_data_state: MarketDataProviderState | None = None
    foundation_established: bool = True
    setup: RuleSetup = RuleSetup.NONE
    continuation_failed: bool = False


@dataclass(frozen=True)
class RuleDecision:
    action_status: ActionStatus
    allowed_actions: set[Action]
    blocked_actions: set[Action]
    allowed_structures: set[PositionStructure]
    blocked_structures: set[PositionStructure]
    size_tier: SizeTier
    invalidation_state: InvalidationState
    required_confirmations: tuple[str, ...]
    severity: DecisionSeverity
    reasons: list[str]
    warnings: list[str]
    market_data_state: MarketDataProviderState | None
    data_source_classification: DataSourceClassification

    def is_action_allowed(self, action: Action) -> bool:
        """Return whether the action remains allowed by current permission logic."""
        return action in self.allowed_actions

    @property
    def can_act(self) -> bool:
        """Return whether the decision authorizes live workstation action."""
        return self.action_status is ActionStatus.AUTHORIZED


def list_valid_actions() -> tuple[Action, ...]:
    """Return the planned inventory adjustment action names."""
    return VALID_ACTIONS


def _codes(result: ValidationResult) -> set[str]:
    return {message.code for message in result.messages}


def _all_structures() -> set[PositionStructure]:
    return set(PositionStructure)


def _decision(
    allowed_actions: set[Action],
    severity: DecisionSeverity,
    reasons: list[str],
    warnings: list[str] | None = None,
    blocked_actions: set[Action] | None = None,
    action_status: ActionStatus | None = None,
    allowed_structures: set[PositionStructure] | None = None,
    blocked_structures: set[PositionStructure] | None = None,
    size_tier: SizeTier = SizeTier.NORMAL,
    invalidation_state: InvalidationState = InvalidationState.VALID,
    required_confirmations: tuple[str, ...] = (),
    market_data_state: MarketDataProviderState | None = MarketDataProviderState.LIVE_FRESH,
    data_source_classification: DataSourceClassification = DataSourceClassification.LIVE,
) -> RuleDecision:
    if action_status is None:
        action_status = _action_status_from_severity(severity, required_confirmations)
    return RuleDecision(
        action_status=action_status,
        allowed_actions=set(allowed_actions),
        blocked_actions=set(blocked_actions or set()),
        allowed_structures=set(_all_structures() if allowed_structures is None else allowed_structures),
        blocked_structures=set(set() if blocked_structures is None else blocked_structures),
        size_tier=size_tier,
        invalidation_state=invalidation_state,
        required_confirmations=required_confirmations,
        severity=severity,
        reasons=reasons,
        warnings=warnings or [],
        market_data_state=market_data_state,
        data_source_classification=data_source_classification,
    )


def _action_status_from_severity(
    severity: DecisionSeverity,
    required_confirmations: tuple[str, ...],
) -> ActionStatus:
    if severity is DecisionSeverity.BLOCKED:
        return ActionStatus.BLOCKED
    if severity is DecisionSeverity.RESTRICTED:
        return ActionStatus.RESTRICTED
    if required_confirmations:
        return ActionStatus.CONFIRMATION_REQUIRED
    return ActionStatus.AUTHORIZED


def allowed_actions_from_validation(result: ValidationResult) -> set[Action]:
    """Map validation state to a broad allowed-action set for decision support."""
    codes = _codes(result)

    if "LOCKOUT_ACTIVE" in codes:
        return set(FLATTEN_ONLY_ACTIONS)

    if "BEHAVIOR_NOT_AUTHORIZED" in codes:
        return set(BEHAVIOR_IMPAIRED_ACTIONS)

    if "RULE_VIOLATION" in codes:
        return set(BEHAVIOR_IMPAIRED_ACTIONS)

    if "THESIS_INVALIDATED" in codes:
        return set(THESIS_INVALIDATED_ACTIONS)

    if "FINAL_5_MINUTES" in codes:
        return set(FINAL_FIVE_MINUTE_ACTIONS)

    allowed_actions = set(FULL_DISCRETIONARY_ACTIONS)
    if "LIQUIDITY_POOR" in codes or "LOSS_AVOIDANCE_RISK" in codes:
        allowed_actions.discard(Action.CONVERT_RESTRUCTURE)

    return allowed_actions


def evaluate_inventory_rules(state: InventoryState) -> RuleDecision:
    """Evaluate deterministic inventory permissions without implying order execution."""
    result = validate_inventory_state(state)
    codes = _codes(result)

    if "LOCKOUT_ACTIVE" in codes:
        return _decision(
            allowed_actions=FLATTEN_ONLY_ACTIONS,
            severity=DecisionSeverity.BLOCKED,
            reasons=["Daily or weekly lockout is active; discretionary adjustment is blocked."],
            blocked_actions=set(Action) - FLATTEN_ONLY_ACTIONS,
        )

    if "BEHAVIOR_NOT_AUTHORIZED" in codes:
        return _decision(
            allowed_actions=BEHAVIOR_IMPAIRED_ACTIONS,
            severity=DecisionSeverity.BLOCKED,
            reasons=[
                "Behavioral authorization failed; complex adjustment and added discretion are blocked."
            ],
            blocked_actions=set(Action) - BEHAVIOR_IMPAIRED_ACTIONS,
        )

    if "RULE_VIOLATION" in codes:
        return _decision(
            allowed_actions=BEHAVIOR_IMPAIRED_ACTIONS,
            severity=DecisionSeverity.BLOCKED,
            reasons=["Rule violation occurred; added risk and complex adjustment are blocked."],
            blocked_actions=set(Action) - BEHAVIOR_IMPAIRED_ACTIONS,
        )

    if "THESIS_INVALIDATED" in codes:
        return _decision(
            allowed_actions=THESIS_INVALIDATED_ACTIONS,
            severity=DecisionSeverity.BLOCKED,
            reasons=["Thesis is invalidated; thesis-based hold or conversion is blocked."],
            blocked_actions=set(Action) - THESIS_INVALIDATED_ACTIONS,
        )

    if state.market.time_window is TimeWindow.FINAL_5_1555_1600:
        return _decision(
            allowed_actions=FINAL_FIVE_MINUTE_ACTIONS,
            severity=DecisionSeverity.RESTRICTED,
            reasons=["Final five-minute window; action set collapses to close, flatten, or stop."],
            blocked_actions=set(Action) - FINAL_FIVE_MINUTE_ACTIONS,
        )

    allowed_actions = set(FULL_DISCRETIONARY_ACTIONS)
    blocked_actions: set[Action] = set()
    warnings: list[str] = []

    if "LIQUIDITY_POOR" in codes:
        allowed_actions.discard(Action.CONVERT_RESTRUCTURE)
        blocked_actions.add(Action.CONVERT_RESTRUCTURE)
        warnings.append("Liquidity is poor; complex option-side adjustment is blocked.")

    if "SIZE_EXCEEDS_PLAN" in codes:
        warnings.append("Position size exceeds plan; reducing exposure should be prioritized.")

    if "LOSS_AVOIDANCE_RISK" in codes:
        allowed_actions.discard(Action.CONVERT_RESTRUCTURE)
        blocked_actions.add(Action.CONVERT_RESTRUCTURE)
        warnings.append(
            "Loss-avoidance risk detected; complex adjustment is blocked unless independently justified."
        )

    if warnings:
        return _decision(
            allowed_actions=allowed_actions,
            severity=DecisionSeverity.CAUTION,
            reasons=[],
            warnings=warnings,
            blocked_actions=blocked_actions,
        )

    return _decision(
        allowed_actions=FULL_DISCRETIONARY_ACTIONS,
        severity=DecisionSeverity.NORMAL,
        reasons=["No rule blockers detected."],
    )


def evaluate_rule_engine_authorization(
    state: InventoryState,
    *,
    market_data_state: MarketDataProviderState | None = None,
    context: RuleAuthorizationContext | None = None,
) -> RuleDecision:
    """Evaluate the R6 top-level workstation authorization decision.

    This is the main authorization layer. Market data state is required and only
    LIVE_FRESH can proceed to normal inventory-rule evaluation. Fixture data is
    simulation-only, and unavailable, parse-error, stale, or missing live data
    fails closed before discretionary action can be authorized.
    """

    authorization_context = context or RuleAuthorizationContext(
        market_data_state=market_data_state
    )
    effective_market_data_state = (
        market_data_state
        if market_data_state is not None
        else authorization_context.market_data_state
    )
    inventory_decision = evaluate_inventory_rules(state)

    market_data_decision = _market_data_override_decision(
        effective_market_data_state,
        inventory_decision,
    )
    if market_data_decision is not None:
        return market_data_decision

    return _apply_r6_context_rules(
        state=state,
        inventory_decision=inventory_decision,
        context=authorization_context,
        market_data_state=effective_market_data_state,
    )


def _market_data_override_decision(
    market_data_state: MarketDataProviderState | None,
    inventory_decision: RuleDecision,
) -> RuleDecision | None:
    if market_data_state is None:
        return _closed_market_data_decision(
            market_data_state=None,
            classification=DataSourceClassification.UNKNOWN,
            reason="Market data state is missing; live authorization fails closed.",
            required_confirmation="load_fresh_live_market_data",
        )

    if market_data_state is MarketDataProviderState.FIXTURE:
        return _closed_market_data_decision(
            market_data_state=market_data_state,
            classification=DataSourceClassification.FIXTURE_SIMULATION,
            reason=(
                "Fixture market data is simulation-only; no live authorization is granted."
            ),
            required_confirmation="fixture_simulation_acknowledgement",
            action_status=ActionStatus.SIMULATION_ONLY,
            warnings=inventory_decision.warnings,
        )

    if market_data_state is MarketDataProviderState.LIVE_STALE:
        return _decision(
            action_status=ActionStatus.RESTRICTED,
            allowed_actions=LIVE_ACTION_STOP_SET,
            blocked_actions=set(Action) - LIVE_ACTION_STOP_SET,
            allowed_structures=set(),
            blocked_structures=_all_structures(),
            size_tier=SizeTier.FLATTEN_ONLY,
            invalidation_state=inventory_decision.invalidation_state,
            severity=DecisionSeverity.RESTRICTED,
            reasons=["Live market data is stale; discretionary action is blocked."],
            warnings=inventory_decision.warnings,
            required_confirmations=("refresh_live_market_data",),
            market_data_state=market_data_state,
            data_source_classification=DataSourceClassification.LIVE,
        )

    if market_data_state is MarketDataProviderState.LIVE_UNAVAILABLE:
        return _closed_market_data_decision(
            market_data_state=market_data_state,
            classification=DataSourceClassification.LIVE,
            reason="Live market data is unavailable; live action is blocked.",
            required_confirmation="restore_live_market_data",
            warnings=inventory_decision.warnings,
        )

    if market_data_state is MarketDataProviderState.LIVE_PARSE_ERROR:
        return _closed_market_data_decision(
            market_data_state=market_data_state,
            classification=DataSourceClassification.LIVE,
            reason="Live market data parse error; live action is blocked.",
            required_confirmation="repair_live_market_data_parse",
            warnings=inventory_decision.warnings,
        )

    if market_data_state is MarketDataProviderState.LIVE_FRESH:
        return None

    return _closed_market_data_decision(
        market_data_state=market_data_state,
        classification=DataSourceClassification.UNKNOWN,
        reason="Market data state is ambiguous; live authorization fails closed.",
        required_confirmation="load_fresh_live_market_data",
        warnings=inventory_decision.warnings,
    )


def _closed_market_data_decision(
    *,
    market_data_state: MarketDataProviderState | None,
    classification: DataSourceClassification,
    reason: str,
    required_confirmation: str,
    action_status: ActionStatus = ActionStatus.BLOCKED,
    warnings: list[str] | None = None,
) -> RuleDecision:
    return _decision(
        action_status=action_status,
        allowed_actions=LIVE_ACTION_STOP_SET,
        blocked_actions=set(Action) - LIVE_ACTION_STOP_SET,
        allowed_structures=set(),
        blocked_structures=_all_structures(),
        size_tier=SizeTier.FLATTEN_ONLY,
        invalidation_state=InvalidationState.UNKNOWN,
        severity=DecisionSeverity.BLOCKED,
        reasons=[reason],
        warnings=warnings or [],
        required_confirmations=(required_confirmation,),
        market_data_state=market_data_state,
        data_source_classification=classification,
    )


def _apply_r6_context_rules(
    *,
    state: InventoryState,
    inventory_decision: RuleDecision,
    context: RuleAuthorizationContext,
    market_data_state: MarketDataProviderState | None,
) -> RuleDecision:
    allowed_actions = set(inventory_decision.allowed_actions)
    blocked_actions = set(inventory_decision.blocked_actions)
    allowed_structures = set(inventory_decision.allowed_structures)
    blocked_structures = set(inventory_decision.blocked_structures)
    reasons = list(inventory_decision.reasons)
    warnings = list(inventory_decision.warnings)
    required_confirmations = list(inventory_decision.required_confirmations)
    severity = inventory_decision.severity

    size_tier = _size_tier_for_state(state, allowed_actions)
    invalidation_state = _invalidation_state_for_state(state)

    if "LOSS_AVOIDANCE_RISK" in _codes(validate_inventory_state(state)):
        required_confirmations.append("independent_loss_avoidance_justification")

    if not context.foundation_established:
        allowed_actions.discard(Action.CONVERT_RESTRUCTURE)
        blocked_actions.add(Action.CONVERT_RESTRUCTURE)
        allowed_structures -= FOUNDATION_REQUIRED_STRUCTURES
        blocked_structures |= FOUNDATION_REQUIRED_STRUCTURES
        required_confirmations.append("foundation_state_established")
        reasons.append(
            "Required foundation state is missing; aggressive directional expression is blocked."
        )
        severity = _max_severity(severity, DecisionSeverity.RESTRICTED)

    if context.setup is RuleSetup.BOUNCE:
        allowed_actions.discard(Action.CONVERT_RESTRUCTURE)
        blocked_actions.add(Action.CONVERT_RESTRUCTURE)
        required_confirmations.append("bounce_not_reclaim_acknowledgement")
        reasons.append("Bounce context never inherits reclaim permissions.")
        severity = _max_severity(severity, DecisionSeverity.RESTRICTED)

    if context.continuation_failed:
        allowed_actions &= THESIS_INVALIDATED_ACTIONS
        blocked_actions |= set(Action) - THESIS_INVALIDATED_ACTIONS
        allowed_structures = set()
        blocked_structures = _all_structures()
        size_tier = SizeTier.FLATTEN_ONLY
        required_confirmations.append("failed_continuation_downgrade_acknowledgement")
        reasons.append(
            "Failed continuation detected; authorization downgrades to reduce, close, flatten, or stop."
        )
        severity = _max_severity(severity, DecisionSeverity.RESTRICTED)

    blocked_actions |= set(Action) - allowed_actions
    allowed_structures -= blocked_structures
    action_status = _action_status_from_severity(severity, tuple(required_confirmations))

    return _decision(
        action_status=action_status,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        allowed_structures=allowed_structures,
        blocked_structures=blocked_structures,
        size_tier=size_tier,
        invalidation_state=invalidation_state,
        severity=severity,
        reasons=_unique_text(reasons) or ["No rule blockers detected."],
        warnings=_unique_text(warnings),
        required_confirmations=tuple(_unique_text(required_confirmations)),
        market_data_state=market_data_state,
        data_source_classification=DataSourceClassification.LIVE,
    )


def _size_tier_for_state(
    state: InventoryState,
    allowed_actions: set[Action],
) -> SizeTier:
    if allowed_actions <= FLATTEN_ONLY_ACTIONS:
        return SizeTier.FLATTEN_ONLY
    if state.position.position_size_exceeds_plan:
        return SizeTier.REDUCE_PRIORITY
    return SizeTier.NORMAL


def _invalidation_state_for_state(state: InventoryState) -> InvalidationState:
    if state.position.accepted_beyond_invalidation or not state.position.thesis_valid:
        return InvalidationState.INVALIDATED
    return InvalidationState.VALID


def _max_severity(
    current: DecisionSeverity,
    candidate: DecisionSeverity,
) -> DecisionSeverity:
    order = {
        DecisionSeverity.NORMAL: 0,
        DecisionSeverity.CAUTION: 1,
        DecisionSeverity.RESTRICTED: 2,
        DecisionSeverity.BLOCKED: 3,
    }
    return candidate if order[candidate] > order[current] else current


def _unique_text(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
