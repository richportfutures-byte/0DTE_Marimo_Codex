"""Validation helpers for future user-supplied inventory state."""

from dataclasses import dataclass
from enum import Enum


class DealerRegime(Enum):
    """User-supplied dealer-flow regime classification."""

    POSITIVE_GEX = "positive_gex"
    NEGATIVE_GEX = "negative_gex"
    NEAR_FLIP = "near_flip"
    EVENT_PINNED = "event_pinned"
    POST_EVENT_VOL_CRUSH = "post_event_vol_crush"
    UNCLEAR = "unclear"


class TimeWindow(Enum):
    """Intraday time windows relevant to 0DTE inventory handling."""

    OPEN_930_945 = "open_930_945"
    MORNING_945_1030 = "morning_945_1030"
    LATE_MORNING_1030_1200 = "late_morning_1030_1200"
    MIDDAY_1200_1330 = "midday_1200_1330"
    EARLY_AFTERNOON_1330_1430 = "early_afternoon_1330_1430"
    LATE_AFTERNOON_1430_1515 = "late_afternoon_1430_1515"
    FINAL_HOUR_1515_1545 = "final_hour_1515_1545"
    FINAL_15_1545_1555 = "final_15_1545_1555"
    FINAL_5_1555_1600 = "final_5_1555_1600"


class PositionStructure(Enum):
    """High-level user-supplied option inventory structure."""

    LONG_OPTION = "long_option"
    DEBIT_SPREAD = "debit_spread"
    CREDIT_SPREAD = "credit_spread"
    BUTTERFLY = "butterfly"
    BROKEN_WING_BUTTERFLY = "broken_wing_butterfly"
    IRON_FLY = "iron_fly"
    IRON_CONDOR = "iron_condor"
    RATIO_OR_BACKSPREAD = "ratio_or_backspread"
    OTHER = "other"


class Action(Enum):
    """Action labels for later deterministic rule filtering."""

    HOLD = "hold"
    TAKE_PARTIAL_PROFIT = "take_partial_profit"
    REDUCE = "reduce"
    HEDGE_MES_ES = "hedge_mes_es"
    CONVERT_RESTRUCTURE = "convert_restructure"
    CLOSE = "close"
    EMERGENCY_FLATTEN = "emergency_flatten"
    STOP_TRADING = "stop_trading"


class ValidationSeverity(Enum):
    """Severity level for inventory-state validation messages."""

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


@dataclass(frozen=True)
class MarketContext:
    dealer_regime: DealerRegime
    time_window: TimeWindow
    spot_relative_to_flip: str | None
    event_pending: bool
    liquidity_acceptable: bool


@dataclass(frozen=True)
class PositionContext:
    structure: PositionStructure
    thesis_valid: bool
    accepted_beyond_invalidation: bool
    current_loss_inside_plan: bool
    gamma_manageable: bool
    delta_intentional: bool
    position_size_exceeds_plan: bool


@dataclass(frozen=True)
class BehaviorContext:
    behavior_authorized: bool
    daily_lockout_active: bool
    weekly_lockout_active: bool
    trying_to_avoid_loss_realization: bool
    rule_violation_occurred: bool


@dataclass(frozen=True)
class InventoryState:
    market: MarketContext
    position: PositionContext
    behavior: BehaviorContext


@dataclass(frozen=True)
class ValidationMessage:
    severity: ValidationSeverity
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    messages: list[ValidationMessage]

    def has_blockers(self) -> bool:
        """Return whether validation found any blocking input state."""
        return any(message.severity is ValidationSeverity.BLOCKER for message in self.messages)


def require_user_supplied(value: object, field_name: str) -> object:
    """Require explicit input instead of generated or fabricated values."""
    if value is None:
        raise ValueError(f"{field_name} must be user supplied.")
    return value


def validate_inventory_state(state: InventoryState) -> ValidationResult:
    """Validate user-supplied inventory state without recommending trades."""
    messages: list[ValidationMessage] = []

    if state.behavior.daily_lockout_active or state.behavior.weekly_lockout_active:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code="LOCKOUT_ACTIVE",
                message=(
                    "Only close, emergency flatten, or stop-trading actions may remain "
                    "permissible in later rule logic."
                ),
            )
        )

    if not state.behavior.behavior_authorized:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code="BEHAVIOR_NOT_AUTHORIZED",
                message="Discretionary adjustment is blocked.",
            )
        )

    if state.behavior.trying_to_avoid_loss_realization:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                code="LOSS_AVOIDANCE_RISK",
                message="Complex adjustment requires rejection unless independently justified.",
            )
        )

    if state.behavior.rule_violation_occurred:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code="RULE_VIOLATION",
                message="Added risk and complex adjustment are blocked.",
            )
        )

    if state.position.accepted_beyond_invalidation:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code="THESIS_INVALIDATED",
                message="Thesis-based hold or conversion is blocked.",
            )
        )

    if not state.market.liquidity_acceptable:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                code="LIQUIDITY_POOR",
                message="Complex option-side adjustment may be impractical.",
            )
        )

    if state.market.time_window is TimeWindow.FINAL_5_1555_1600:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                code="FINAL_5_MINUTES",
                message=(
                    "Action set should collapse to close, flatten, preplanned expiry "
                    "acceptance, or stop."
                ),
            )
        )

    if state.position.position_size_exceeds_plan:
        messages.append(
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                code="SIZE_EXCEEDS_PLAN",
                message="Reducing exposure should be prioritized.",
            )
        )

    return ValidationResult(messages=messages)
