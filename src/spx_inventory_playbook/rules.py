"""Deterministic inventory permission rules."""

from dataclasses import dataclass
from enum import Enum

from .validators import Action, InventoryState, TimeWindow, ValidationResult, validate_inventory_state


VALID_ACTIONS = tuple(Action)
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


class DecisionSeverity(Enum):
    """Highest-severity state for deterministic inventory permissions."""

    NORMAL = "normal"
    CAUTION = "caution"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RuleDecision:
    allowed_actions: set[Action]
    blocked_actions: set[Action]
    severity: DecisionSeverity
    reasons: list[str]
    warnings: list[str]

    def is_action_allowed(self, action: Action) -> bool:
        """Return whether the action remains allowed by current permission logic."""
        return action in self.allowed_actions


def list_valid_actions() -> tuple[Action, ...]:
    """Return the planned inventory adjustment action names."""
    return VALID_ACTIONS


def _codes(result: ValidationResult) -> set[str]:
    return {message.code for message in result.messages}


def _decision(
    allowed_actions: set[Action],
    severity: DecisionSeverity,
    reasons: list[str],
    warnings: list[str] | None = None,
    blocked_actions: set[Action] | None = None,
) -> RuleDecision:
    return RuleDecision(
        allowed_actions=set(allowed_actions),
        blocked_actions=set(blocked_actions or set()),
        severity=severity,
        reasons=reasons,
        warnings=warnings or [],
    )


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
