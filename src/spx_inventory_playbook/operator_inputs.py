"""Structured operator input workflow for rule-engine authorization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .validators import (
    BehaviorContext,
    DealerRegime,
    InventoryState,
    MarketContext,
    PositionContext,
    PositionStructure,
    TimeWindow,
)


class OperatorInputIssueSeverity(Enum):
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"
    BLOCKING = "blocking"


class OperatorLiquidity(Enum):
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    AMBIGUOUS = "ambiguous"


class OperatorThesisValidity(Enum):
    VALID = "valid"
    INVALIDATED = "invalidated"
    AMBIGUOUS = "ambiguous"


class OperatorGammaRegime(Enum):
    MANAGEABLE = "manageable"
    UNMANAGEABLE = "unmanageable"
    AMBIGUOUS = "ambiguous"


class OperatorDeltaContext(Enum):
    INTENTIONAL = "intentional"
    UNINTENTIONAL = "unintentional"
    AMBIGUOUS = "ambiguous"


class OperatorPositionSize(Enum):
    INSIDE_PLAN = "inside_plan"
    EXCEEDS_PLAN = "exceeds_plan"
    AMBIGUOUS = "ambiguous"


class OperatorLockoutState(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    AMBIGUOUS = "ambiguous"


class OperatorBehaviorAuthorization(Enum):
    AUTHORIZED = "authorized"
    IMPAIRED = "impaired"
    AMBIGUOUS = "ambiguous"


class OperatorRuleViolationState(Enum):
    NONE = "none"
    OCCURRED = "occurred"
    AMBIGUOUS = "ambiguous"


class OperatorLossAvoidanceRisk(Enum):
    ABSENT = "absent"
    PRESENT = "present"
    AMBIGUOUS = "ambiguous"


class OperatorFoundationState(Enum):
    ESTABLISHED = "established"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


class OperatorSetup(Enum):
    NONE = "none"
    RECLAIM = "reclaim"
    BOUNCE = "bounce"
    CONTINUATION = "continuation"
    AMBIGUOUS = "ambiguous"


class OperatorContinuationState(Enum):
    INTACT = "intact"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class OperatorInputState:
    """Real operator-entered state for the R7 authorization workflow."""

    time_window: TimeWindow | None
    dealer_regime: DealerRegime | None
    liquidity: OperatorLiquidity | None
    thesis_validity: OperatorThesisValidity | None
    gamma_regime: OperatorGammaRegime | None
    delta_context: OperatorDeltaContext | None
    position_size: OperatorPositionSize | None
    lockout_state: OperatorLockoutState | None
    behavior_authorization: OperatorBehaviorAuthorization | None
    rule_violations: OperatorRuleViolationState | None
    loss_avoidance_risk: OperatorLossAvoidanceRisk | None
    foundation_state: OperatorFoundationState = OperatorFoundationState.ESTABLISHED
    setup: OperatorSetup = OperatorSetup.NONE
    continuation_state: OperatorContinuationState = OperatorContinuationState.INTACT
    simulation_label: str | None = None

    @property
    def is_simulation(self) -> bool:
        return self.simulation_label is not None


@dataclass(frozen=True)
class OperatorInputIssue:
    severity: OperatorInputIssueSeverity
    field_name: str
    code: str
    message: str


@dataclass(frozen=True)
class OperatorInputValidation:
    issues: tuple[OperatorInputIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def missing_inputs(self) -> tuple[OperatorInputIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is OperatorInputIssueSeverity.MISSING
        )

    @property
    def invalid_inputs(self) -> tuple[OperatorInputIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity
            in {
                OperatorInputIssueSeverity.INVALID,
                OperatorInputIssueSeverity.AMBIGUOUS,
            }
        )

    @property
    def blocking_defects(self) -> tuple[OperatorInputIssue, ...]:
        return self.issues

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(issue.code for issue in self.issues)


@dataclass(frozen=True)
class NormalizedOperatorState:
    inventory_state: InventoryState
    foundation_established: bool
    setup: OperatorSetup
    continuation_failed: bool


_InputFieldSpec = tuple[str, type[Enum], Enum | None]

_REQUIRED_FIELDS: tuple[_InputFieldSpec, ...] = (
    ("time_window", TimeWindow, None),
    ("dealer_regime", DealerRegime, DealerRegime.UNCLEAR),
    ("liquidity", OperatorLiquidity, OperatorLiquidity.AMBIGUOUS),
    ("thesis_validity", OperatorThesisValidity, OperatorThesisValidity.AMBIGUOUS),
    ("gamma_regime", OperatorGammaRegime, OperatorGammaRegime.AMBIGUOUS),
    ("delta_context", OperatorDeltaContext, OperatorDeltaContext.AMBIGUOUS),
    ("position_size", OperatorPositionSize, OperatorPositionSize.AMBIGUOUS),
    ("lockout_state", OperatorLockoutState, OperatorLockoutState.AMBIGUOUS),
    (
        "behavior_authorization",
        OperatorBehaviorAuthorization,
        OperatorBehaviorAuthorization.AMBIGUOUS,
    ),
    ("rule_violations", OperatorRuleViolationState, OperatorRuleViolationState.AMBIGUOUS),
    (
        "loss_avoidance_risk",
        OperatorLossAvoidanceRisk,
        OperatorLossAvoidanceRisk.AMBIGUOUS,
    ),
)


_CONTEXT_FIELDS: tuple[_InputFieldSpec, ...] = (
    ("foundation_state", OperatorFoundationState, OperatorFoundationState.AMBIGUOUS),
    ("setup", OperatorSetup, OperatorSetup.AMBIGUOUS),
    (
        "continuation_state",
        OperatorContinuationState,
        OperatorContinuationState.AMBIGUOUS,
    ),
)


def validate_operator_input_state(state: OperatorInputState) -> OperatorInputValidation:
    """Validate explicit operator input before rule-engine normalization."""

    issues: list[OperatorInputIssue] = []
    for field_name, expected_type, ambiguous_value in _REQUIRED_FIELDS + _CONTEXT_FIELDS:
        value = getattr(state, field_name)
        if value is None:
            issues.append(
                OperatorInputIssue(
                    severity=OperatorInputIssueSeverity.MISSING,
                    field_name=field_name,
                    code=f"{field_name.upper()}_MISSING",
                    message=f"{field_name} is required.",
                )
            )
            continue
        if not isinstance(value, expected_type):
            issues.append(
                OperatorInputIssue(
                    severity=OperatorInputIssueSeverity.INVALID,
                    field_name=field_name,
                    code=f"{field_name.upper()}_INVALID",
                    message=f"{field_name} must be a valid {expected_type.__name__}.",
                )
            )
            continue
        if value is ambiguous_value:
            issues.append(
                OperatorInputIssue(
                    severity=OperatorInputIssueSeverity.AMBIGUOUS,
                    field_name=field_name,
                    code=f"{field_name.upper()}_AMBIGUOUS",
                    message=f"{field_name} is ambiguous.",
                )
            )

    return OperatorInputValidation(issues=tuple(issues))


def normalize_operator_input_state(state: OperatorInputState) -> NormalizedOperatorState:
    """Map valid operator inputs into the existing inventory/rule state."""

    validation = validate_operator_input_state(state)
    if not validation.is_valid:
        raise ValueError("operator inputs must be valid before normalization.")

    thesis_valid = state.thesis_validity is OperatorThesisValidity.VALID
    lockout_state = state.lockout_state
    return NormalizedOperatorState(
        inventory_state=InventoryState(
            market=MarketContext(
                dealer_regime=_required(state.dealer_regime, "dealer_regime"),
                time_window=_required(state.time_window, "time_window"),
                spot_relative_to_flip=None,
                event_pending=False,
                liquidity_acceptable=state.liquidity is OperatorLiquidity.ACCEPTABLE,
            ),
            position=PositionContext(
                structure=PositionStructure.OTHER,
                thesis_valid=thesis_valid,
                accepted_beyond_invalidation=not thesis_valid,
                current_loss_inside_plan=True,
                gamma_manageable=state.gamma_regime is OperatorGammaRegime.MANAGEABLE,
                delta_intentional=state.delta_context is OperatorDeltaContext.INTENTIONAL,
                position_size_exceeds_plan=state.position_size
                is OperatorPositionSize.EXCEEDS_PLAN,
            ),
            behavior=BehaviorContext(
                behavior_authorized=state.behavior_authorization
                is OperatorBehaviorAuthorization.AUTHORIZED,
                daily_lockout_active=lockout_state is OperatorLockoutState.DAILY,
                weekly_lockout_active=lockout_state is OperatorLockoutState.WEEKLY,
                trying_to_avoid_loss_realization=state.loss_avoidance_risk
                is OperatorLossAvoidanceRisk.PRESENT,
                rule_violation_occurred=state.rule_violations
                is OperatorRuleViolationState.OCCURRED,
            ),
        ),
        foundation_established=state.foundation_state is OperatorFoundationState.ESTABLISHED,
        setup=_required(state.setup, "setup"),
        continuation_failed=state.continuation_state is OperatorContinuationState.FAILED,
    )


def operator_input_from_inventory_state(
    state: InventoryState,
    *,
    simulation_label: str,
) -> OperatorInputState:
    """Build clearly labeled simulation/demo inputs from legacy fixtures."""

    lockout_state = OperatorLockoutState.NONE
    if state.behavior.daily_lockout_active:
        lockout_state = OperatorLockoutState.DAILY
    elif state.behavior.weekly_lockout_active:
        lockout_state = OperatorLockoutState.WEEKLY

    return OperatorInputState(
        time_window=state.market.time_window,
        dealer_regime=state.market.dealer_regime,
        liquidity=(
            OperatorLiquidity.ACCEPTABLE
            if state.market.liquidity_acceptable
            else OperatorLiquidity.POOR
        ),
        thesis_validity=(
            OperatorThesisValidity.VALID
            if state.position.thesis_valid and not state.position.accepted_beyond_invalidation
            else OperatorThesisValidity.INVALIDATED
        ),
        gamma_regime=(
            OperatorGammaRegime.MANAGEABLE
            if state.position.gamma_manageable
            else OperatorGammaRegime.UNMANAGEABLE
        ),
        delta_context=(
            OperatorDeltaContext.INTENTIONAL
            if state.position.delta_intentional
            else OperatorDeltaContext.UNINTENTIONAL
        ),
        position_size=(
            OperatorPositionSize.EXCEEDS_PLAN
            if state.position.position_size_exceeds_plan
            else OperatorPositionSize.INSIDE_PLAN
        ),
        lockout_state=lockout_state,
        behavior_authorization=(
            OperatorBehaviorAuthorization.AUTHORIZED
            if state.behavior.behavior_authorized
            else OperatorBehaviorAuthorization.IMPAIRED
        ),
        rule_violations=(
            OperatorRuleViolationState.OCCURRED
            if state.behavior.rule_violation_occurred
            else OperatorRuleViolationState.NONE
        ),
        loss_avoidance_risk=(
            OperatorLossAvoidanceRisk.PRESENT
            if state.behavior.trying_to_avoid_loss_realization
            else OperatorLossAvoidanceRisk.ABSENT
        ),
        simulation_label=simulation_label,
    )


def _required(value: object, field_name: str):
    if value is None:
        raise ValueError(f"{field_name} is required.")
    return value
