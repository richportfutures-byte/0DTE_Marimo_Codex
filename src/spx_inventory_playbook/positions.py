"""Position tracking and session P&L for 0DTE SPX inventory.

Inputs may be user-supplied or adapter-sourced. Marks, Greeks, fills,
and P&L must never be fabricated.
"""

from dataclasses import dataclass, replace
from enum import Enum
from html import escape as html_escape
from uuid import uuid4

from .validators import PositionStructure, TimeWindow


class PositionSide(Enum):
    """Whether the position was entered for a net credit or debit."""

    CREDIT = "credit"
    DEBIT = "debit"


class PositionStatus(Enum):
    """Lifecycle status of a tracked position."""

    OPEN = "open"
    CLOSED = "closed"


class Urgency(Enum):
    """Time urgency relative to close-by-time."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SPX_MULTIPLIER = 100.0

TIME_WINDOW_ORDER: tuple[TimeWindow, ...] = (
    TimeWindow.OPEN_930_945,
    TimeWindow.MORNING_945_1030,
    TimeWindow.LATE_MORNING_1030_1200,
    TimeWindow.MIDDAY_1200_1330,
    TimeWindow.EARLY_AFTERNOON_1330_1430,
    TimeWindow.LATE_AFTERNOON_1430_1515,
    TimeWindow.FINAL_HOUR_1515_1545,
    TimeWindow.FINAL_15_1545_1555,
    TimeWindow.FINAL_5_1555_1600,
)

_WINDOW_INDEX = {w: i for i, w in enumerate(TIME_WINDOW_ORDER)}

TIME_WINDOW_LABELS = {
    TimeWindow.OPEN_930_945: "Open 9:30–9:45",
    TimeWindow.MORNING_945_1030: "Morning 9:45–10:30",
    TimeWindow.LATE_MORNING_1030_1200: "Late Morning 10:30–12:00",
    TimeWindow.MIDDAY_1200_1330: "Midday 12:00–13:30",
    TimeWindow.EARLY_AFTERNOON_1330_1430: "Early PM 13:30–14:30",
    TimeWindow.LATE_AFTERNOON_1430_1515: "Late PM 14:30–15:15",
    TimeWindow.FINAL_HOUR_1515_1545: "Final Hour 15:15–15:45",
    TimeWindow.FINAL_15_1545_1555: "Final 15 min 15:45–15:55",
    TimeWindow.FINAL_5_1555_1600: "Final 5 min 15:55–16:00",
}


@dataclass(frozen=True)
class Position:
    """A single tracked 0DTE SPX/SPXW position."""

    id: str
    structure: PositionStructure
    side: PositionSide
    description: str
    contracts: int
    entry_price: float
    current_mark: float
    max_loss_per_contract: float
    target_per_contract: float
    thesis: str
    thesis_still_valid: bool
    delta: float
    gamma: float
    theta: float
    close_by_time: TimeWindow
    entry_time_window: TimeWindow
    adjustments: int
    status: PositionStatus
    friction_paid: float
    notes: str

    @property
    def pnl_per_contract(self) -> float:
        """Unrealized P&L per contract in dollars."""
        if self.side is PositionSide.CREDIT:
            return (self.entry_price - self.current_mark) * SPX_MULTIPLIER
        return (self.current_mark - self.entry_price) * SPX_MULTIPLIER

    @property
    def total_pnl(self) -> float:
        """Total P&L in dollars before friction."""
        return self.pnl_per_contract * self.contracts

    @property
    def net_pnl(self) -> float:
        """Total P&L in dollars after friction."""
        return self.total_pnl - self.friction_paid

    @property
    def max_loss_total(self) -> float:
        """Total max planned loss in dollars."""
        return self.max_loss_per_contract * SPX_MULTIPLIER * self.contracts

    @property
    def target_total(self) -> float:
        """Total target profit in dollars."""
        return self.target_per_contract * SPX_MULTIPLIER * self.contracts

    @property
    def pnl_pct_of_max_loss(self) -> float:
        """P&L as fraction of max planned loss."""
        if self.max_loss_total == 0:
            return 0.0
        return self.total_pnl / abs(self.max_loss_total)

    @property
    def pnl_pct_of_target(self) -> float:
        """P&L as fraction of target profit."""
        if self.target_total == 0:
            return 0.0
        return self.total_pnl / self.target_total

    @property
    def net_delta(self) -> float:
        return self.delta * self.contracts

    @property
    def net_gamma(self) -> float:
        return self.gamma * self.contracts

    @property
    def net_theta(self) -> float:
        return self.theta * self.contracts

    def with_mark(self, new_mark: float) -> "Position":
        if self.status is PositionStatus.CLOSED:
            raise ValueError("Cannot modify a closed position.")
        return replace(self, current_mark=new_mark)

    def with_greeks(self, delta: float, gamma: float, theta: float) -> "Position":
        if self.status is PositionStatus.CLOSED:
            raise ValueError("Cannot modify a closed position.")
        return replace(self, delta=delta, gamma=gamma, theta=theta)

    def with_adjustment(self, notes: str = "") -> "Position":
        if self.status is PositionStatus.CLOSED:
            raise ValueError("Cannot modify a closed position.")
        escaped = html_escape(notes) if notes else ""
        new_notes = f"{self.notes}\n{escaped}".strip() if escaped else self.notes
        return replace(self, adjustments=self.adjustments + 1, notes=new_notes)

    def with_thesis_invalidated(self) -> "Position":
        if self.status is PositionStatus.CLOSED:
            raise ValueError("Cannot modify a closed position.")
        return replace(self, thesis_still_valid=False)

    def closed(self, exit_mark: float) -> "Position":
        if self.status is PositionStatus.CLOSED:
            raise ValueError("Position is already closed.")
        return replace(self, current_mark=exit_mark, status=PositionStatus.CLOSED)


def create_position(
    structure: PositionStructure,
    side: PositionSide,
    description: str,
    contracts: int,
    entry_price: float,
    max_loss_per_contract: float,
    target_per_contract: float,
    thesis: str,
    close_by_time: TimeWindow,
    entry_time_window: TimeWindow,
    delta: float = 0.0,
    gamma: float = 0.0,
    theta: float = 0.0,
    friction_paid: float = 0.0,
) -> Position:
    """Create a new tracked position from explicit position inputs."""
    if contracts <= 0:
        raise ValueError("contracts must be positive.")
    if entry_price < 0:
        raise ValueError("entry_price must be non-negative.")
    if max_loss_per_contract < 0:
        raise ValueError("max_loss_per_contract must be non-negative.")
    if target_per_contract < 0:
        raise ValueError("target_per_contract must be non-negative.")
    if not description.strip():
        raise ValueError("description must not be empty.")
    if not thesis.strip():
        raise ValueError("thesis must not be empty.")
    if friction_paid < 0:
        raise ValueError("friction_paid must be non-negative.")

    return Position(
        id=uuid4().hex[:8],
        structure=structure,
        side=side,
        description=html_escape(description.strip()),
        contracts=contracts,
        entry_price=entry_price,
        current_mark=entry_price,
        max_loss_per_contract=max_loss_per_contract,
        target_per_contract=target_per_contract,
        thesis=html_escape(thesis.strip()),
        thesis_still_valid=True,
        delta=delta,
        gamma=gamma,
        theta=theta,
        close_by_time=close_by_time,
        entry_time_window=entry_time_window,
        adjustments=0,
        status=PositionStatus.OPEN,
        friction_paid=friction_paid,
        notes="",
    )


def time_urgency(current_window: TimeWindow, close_by: TimeWindow) -> Urgency:
    """Compute urgency from current time window vs position close-by-time."""
    if current_window not in _WINDOW_INDEX:
        raise ValueError(f"Unsupported current_window: {current_window!r}")
    if close_by not in _WINDOW_INDEX:
        raise ValueError(f"Unsupported close_by: {close_by!r}")

    current_idx = _WINDOW_INDEX[current_window]
    close_idx = _WINDOW_INDEX[close_by]
    remaining = close_idx - current_idx
    if remaining <= 0:
        return Urgency.CRITICAL
    if remaining == 1:
        return Urgency.HIGH
    if remaining == 2:
        return Urgency.MEDIUM
    return Urgency.LOW


@dataclass(frozen=True)
class SessionSummary:
    """Aggregate session metrics computed from all positions."""

    open_count: int
    closed_count: int
    open_pnl: float
    closed_pnl: float
    total_pnl: float
    total_friction: float
    net_pnl: float
    net_delta: float
    net_gamma: float
    net_theta: float
    total_contracts_open: int
    total_adjustments: int
    max_loss_exposure: float
    daily_budget: float
    budget_used_pct: float


def calculate_session_summary(
    positions: tuple[Position, ...],
    daily_budget: float,
) -> SessionSummary:
    """Compute aggregate session metrics from all tracked positions."""
    open_positions = [p for p in positions if p.status is PositionStatus.OPEN]
    closed_positions = [p for p in positions if p.status is PositionStatus.CLOSED]

    open_pnl = sum(p.total_pnl for p in open_positions)
    closed_pnl = sum(p.total_pnl for p in closed_positions)
    total_friction = sum(p.friction_paid for p in positions)

    max_loss_exposure = sum(abs(p.max_loss_total) for p in open_positions)
    budget_used = max_loss_exposure / daily_budget if daily_budget > 0 else 0.0

    return SessionSummary(
        open_count=len(open_positions),
        closed_count=len(closed_positions),
        open_pnl=open_pnl,
        closed_pnl=closed_pnl,
        total_pnl=open_pnl + closed_pnl,
        total_friction=total_friction,
        net_pnl=open_pnl + closed_pnl - total_friction,
        net_delta=sum(p.net_delta for p in open_positions),
        net_gamma=sum(p.net_gamma for p in open_positions),
        net_theta=sum(p.net_theta for p in open_positions),
        total_contracts_open=sum(p.contracts for p in open_positions),
        total_adjustments=sum(p.adjustments for p in positions),
        max_loss_exposure=max_loss_exposure,
        daily_budget=daily_budget,
        budget_used_pct=budget_used,
    )
