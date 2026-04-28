"""Tests for position tracking and session P&L."""

import ast
from pathlib import Path
import re
import tokenize

import pytest

from spx_inventory_playbook.positions import (
    Urgency,
    PositionSide,
    PositionStatus,
    SPX_MULTIPLIER,
    create_position,
    time_urgency,
    calculate_session_summary,
)
from spx_inventory_playbook.validators import PositionStructure, TimeWindow


ROOT = Path(__file__).resolve().parents[1]
POSITIONS_GUARDRAIL_FILES = (
    ROOT / "src/spx_inventory_playbook/positions.py",
    ROOT / "tests/test_positions.py",
)
FORBIDDEN_MARKET_EXAMPLE_MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("55", "50"),
        ("55", "40"),
        ("56", "00"),
        ("56", "10"),
        ("55", "90"),
        ("2", ".50"),
        ("3", ".00"),
        ("7", ".50"),
    )
)
FOUR_DIGIT_MARKET_LIKE_RE = re.compile(r"\b[1-9]\d{3}\b")


def _tokens_for_guardrail(path: Path):
    with path.open("rb") as source:
        yield from tokenize.tokenize(source.readline)


def _string_value(token: tokenize.TokenInfo) -> str:
    try:
        value = ast.literal_eval(token.string)
    except (SyntaxError, ValueError):
        return token.string
    return value if isinstance(value, str) else ""


def test_positions_source_does_not_embed_fake_market_examples() -> None:
    """Keep positions code/tests free of strike-like levels and premium examples."""
    for path in POSITIONS_GUARDRAIL_FILES:
        source = path.read_text()
        for marker in FORBIDDEN_MARKET_EXAMPLE_MARKERS:
            assert marker not in source, f"{path} contains forbidden market marker {marker!r}"

        for token in _tokens_for_guardrail(path):
            if token.type == tokenize.NUMBER:
                assert not FOUR_DIGIT_MARKET_LIKE_RE.fullmatch(token.string), (
                    f"{path}:{token.start[0]} contains market-like numeric literal {token.string!r}"
                )
            if token.type == tokenize.STRING:
                value = _string_value(token)
                assert not FOUR_DIGIT_MARKET_LIKE_RE.search(value), (
                    f"{path}:{token.start[0]} contains market-like string {value!r}"
                )


def _credit_spread(**overrides):
    defaults = dict(
        structure=PositionStructure.CREDIT_SPREAD,
        side=PositionSide.CREDIT,
        description="Alpha/Beta credit spread",
        contracts=1,
        entry_price=1.0,
        max_loss_per_contract=2.0,
        target_per_contract=1.0,
        thesis="Abstract credit thesis.",
        close_by_time=TimeWindow.FINAL_HOUR_1515_1545,
        entry_time_window=TimeWindow.MORNING_945_1030,
    )
    defaults.update(overrides)
    return create_position(**defaults)


def _debit_spread(**overrides):
    defaults = dict(
        structure=PositionStructure.DEBIT_SPREAD,
        side=PositionSide.DEBIT,
        description="Gamma/Delta debit spread",
        contracts=2,
        entry_price=1.0,
        max_loss_per_contract=1.0,
        target_per_contract=2.0,
        thesis="Abstract debit thesis.",
        close_by_time=TimeWindow.LATE_AFTERNOON_1430_1515,
        entry_time_window=TimeWindow.LATE_MORNING_1030_1200,
    )
    defaults.update(overrides)
    return create_position(**defaults)


class TestCreatePosition:
    def test_creates_with_valid_inputs(self):
        pos = _credit_spread()
        assert pos.status is PositionStatus.OPEN
        assert pos.current_mark == pos.entry_price
        assert pos.adjustments == 0
        assert pos.thesis_still_valid is True
        assert len(pos.id) == 8

    def test_rejects_zero_contracts(self):
        with pytest.raises(ValueError, match="contracts"):
            _credit_spread(contracts=0)

    def test_rejects_negative_entry_price(self):
        with pytest.raises(ValueError, match="entry_price"):
            _credit_spread(entry_price=-1.0)

    def test_rejects_empty_description(self):
        with pytest.raises(ValueError, match="description"):
            _credit_spread(description="  ")

    def test_rejects_empty_thesis(self):
        with pytest.raises(ValueError, match="thesis"):
            _credit_spread(thesis="")

    def test_rejects_negative_friction(self):
        with pytest.raises(ValueError, match="friction_paid"):
            _credit_spread(friction_paid=-5.0)


class TestPnLCalculation:
    def test_credit_position_profit_when_mark_drops(self):
        pos = _credit_spread().with_mark(0.5)
        expected = (1.0 - 0.5) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl == pytest.approx(expected * 1)

    def test_credit_position_loss_when_mark_rises(self):
        pos = _credit_spread().with_mark(2.0)
        expected = (1.0 - 2.0) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl < 0

    def test_debit_position_profit_when_mark_rises(self):
        pos = _debit_spread().with_mark(2.0)
        expected = (2.0 - 1.0) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl == pytest.approx(expected * 2)

    def test_debit_position_loss_when_mark_drops(self):
        pos = _debit_spread().with_mark(0.0)
        expected = (0.0 - 1.0) * SPX_MULTIPLIER
        assert pos.total_pnl < 0

    def test_net_pnl_subtracts_friction(self):
        pos = _credit_spread(friction_paid=1.0).with_mark(0.5)
        assert pos.net_pnl == pytest.approx(pos.total_pnl - 1.0)

    def test_pnl_at_entry_is_zero(self):
        pos = _credit_spread()
        assert pos.total_pnl == pytest.approx(0.0)

    def test_max_loss_total(self):
        pos = _credit_spread(contracts=3, max_loss_per_contract=2.0)
        assert pos.max_loss_total == pytest.approx(2.0 * 100 * 3)

    def test_target_total(self):
        pos = _debit_spread(contracts=2, target_per_contract=2.0)
        assert pos.target_total == pytest.approx(2.0 * 100 * 2)


class TestPositionMutations:
    def test_with_mark_does_not_mutate_original(self):
        pos = _credit_spread()
        updated = pos.with_mark(0.5)
        assert pos.current_mark == 1.0
        assert updated.current_mark == 0.5

    def test_with_greeks(self):
        pos = _credit_spread()
        updated = pos.with_greeks(delta=-1.0, gamma=-2.0, theta=3.0)
        assert updated.delta == -1.0
        assert updated.gamma == -2.0
        assert updated.theta == 3.0

    def test_with_adjustment_increments_count(self):
        pos = _credit_spread()
        updated = pos.with_adjustment("Recorded adjustment")
        assert updated.adjustments == 1
        assert "Recorded" in updated.notes

    def test_multiple_adjustments_preserve_note_order_and_separation(self):
        pos = _credit_spread()
        updated = pos.with_adjustment("First adjustment").with_adjustment("Second adjustment")

        assert updated.adjustments == 2
        assert updated.notes == "First adjustment\nSecond adjustment"

    def test_thesis_invalidated(self):
        pos = _credit_spread()
        updated = pos.with_thesis_invalidated()
        assert updated.thesis_still_valid is False
        assert pos.thesis_still_valid is True

    def test_closed_sets_status_and_exit_mark(self):
        pos = _credit_spread()
        closed = pos.closed(exit_mark=0.0)
        assert closed.status is PositionStatus.CLOSED
        assert closed.current_mark == 0.0

    def test_closed_rejects_already_closed_position(self):
        closed = _credit_spread().closed(exit_mark=0.0)

        with pytest.raises(ValueError, match="already closed"):
            closed.closed(exit_mark=1.0)

    def test_net_greeks_scale_by_contracts(self):
        pos = _debit_spread(contracts=3).with_greeks(1.0, 2.0, -3.0)
        assert pos.net_delta == pytest.approx(3.0)
        assert pos.net_gamma == pytest.approx(6.0)
        assert pos.net_theta == pytest.approx(-9.0)


class TestTimeUrgency:
    def test_critical_when_past_close_by(self):
        assert time_urgency(TimeWindow.FINAL_5_1555_1600, TimeWindow.FINAL_HOUR_1515_1545) is Urgency.CRITICAL

    def test_critical_when_at_close_by(self):
        assert time_urgency(TimeWindow.FINAL_HOUR_1515_1545, TimeWindow.FINAL_HOUR_1515_1545) is Urgency.CRITICAL

    def test_high_when_one_window_away(self):
        assert time_urgency(TimeWindow.LATE_AFTERNOON_1430_1515, TimeWindow.FINAL_HOUR_1515_1545) is Urgency.HIGH

    def test_medium_when_two_windows_away(self):
        assert time_urgency(TimeWindow.EARLY_AFTERNOON_1330_1430, TimeWindow.FINAL_HOUR_1515_1545) is Urgency.MEDIUM

    def test_low_when_many_windows_away(self):
        assert time_urgency(TimeWindow.MORNING_945_1030, TimeWindow.FINAL_HOUR_1515_1545) is Urgency.LOW

    def test_rejects_unsupported_current_window(self):
        with pytest.raises(ValueError, match="Unsupported current_window"):
            time_urgency(object(), TimeWindow.FINAL_HOUR_1515_1545)

    def test_rejects_unsupported_close_by_window(self):
        with pytest.raises(ValueError, match="Unsupported close_by"):
            time_urgency(TimeWindow.MORNING_945_1030, object())


class TestSessionSummary:
    def test_empty_session(self):
        summary = calculate_session_summary((), daily_budget=20.0)
        assert summary.open_count == 0
        assert summary.total_pnl == 0.0
        assert summary.budget_used_pct == 0.0

    def test_open_positions_contribute_to_pnl(self):
        p1 = _credit_spread().with_mark(0.5)
        p2 = _debit_spread().with_mark(2.0)
        summary = calculate_session_summary((p1, p2), daily_budget=20.0)
        assert summary.open_count == 2
        assert summary.closed_count == 0
        assert summary.open_pnl == pytest.approx(p1.total_pnl + p2.total_pnl)

    def test_closed_positions_separate_from_open(self):
        p1 = _credit_spread().with_mark(0.5)
        p2 = _credit_spread().closed(exit_mark=0.0)
        summary = calculate_session_summary((p1, p2), daily_budget=20.0)
        assert summary.open_count == 1
        assert summary.closed_count == 1
        assert summary.total_pnl == pytest.approx(p1.total_pnl + p2.total_pnl)

    def test_budget_utilization(self):
        p = _credit_spread(contracts=2, max_loss_per_contract=1.0)
        summary = calculate_session_summary((p,), daily_budget=20.0)
        expected_exposure = 1.0 * 100 * 2
        assert summary.max_loss_exposure == pytest.approx(expected_exposure)
        assert summary.budget_used_pct == pytest.approx(expected_exposure / 20.0)

    def test_zero_daily_budget_preserves_zero_budget_used_pct(self):
        p = _credit_spread(contracts=2, max_loss_per_contract=1.0)
        summary = calculate_session_summary((p,), daily_budget=0.0)

        assert summary.daily_budget == 0.0
        assert summary.max_loss_exposure == pytest.approx(1.0 * 100 * 2)
        assert summary.budget_used_pct == 0.0

    def test_aggregate_greeks(self):
        p1 = _credit_spread(contracts=1).with_greeks(-1.0, -2.0, 3.0)
        p2 = _debit_spread(contracts=2).with_greeks(4.0, 5.0, -6.0)
        summary = calculate_session_summary((p1, p2), daily_budget=20.0)
        assert summary.net_delta == pytest.approx(-1.0 + 8.0)
        assert summary.net_gamma == pytest.approx(-2.0 + 10.0)
        assert summary.net_theta == pytest.approx(3.0 + -12.0)

    def test_friction_tracked_across_session(self):
        p1 = _credit_spread(friction_paid=1.0)
        p2 = _debit_spread(friction_paid=2.0)
        summary = calculate_session_summary((p1, p2), daily_budget=20.0)
        assert summary.total_friction == pytest.approx(3.0)

    def test_adjustment_count_aggregated(self):
        p1 = _credit_spread().with_adjustment("adj 1").with_adjustment("adj 2")
        p2 = _debit_spread().with_adjustment("adj 1")
        summary = calculate_session_summary((p1, p2), daily_budget=20.0)
        assert summary.total_adjustments == 3
