"""Tests for position tracking and session P&L."""

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


def _credit_spread(**overrides):
    defaults = dict(
        structure=PositionStructure.CREDIT_SPREAD,
        side=PositionSide.CREDIT,
        description="5550/5540 put credit spread",
        contracts=1,
        entry_price=2.50,
        max_loss_per_contract=7.50,
        target_per_contract=2.00,
        thesis="Positive GEX dampening, morning fade thesis.",
        close_by_time=TimeWindow.FINAL_HOUR_1515_1545,
        entry_time_window=TimeWindow.MORNING_945_1030,
    )
    defaults.update(overrides)
    return create_position(**defaults)


def _debit_spread(**overrides):
    defaults = dict(
        structure=PositionStructure.DEBIT_SPREAD,
        side=PositionSide.DEBIT,
        description="5600/5610 call debit spread",
        contracts=2,
        entry_price=3.00,
        max_loss_per_contract=3.00,
        target_per_contract=5.00,
        thesis="Breakout above 5590 with volume confirmation.",
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
        pos = _credit_spread().with_mark(1.20)
        expected = (2.50 - 1.20) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl == pytest.approx(expected * 1)

    def test_credit_position_loss_when_mark_rises(self):
        pos = _credit_spread().with_mark(5.00)
        expected = (2.50 - 5.00) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl < 0

    def test_debit_position_profit_when_mark_rises(self):
        pos = _debit_spread().with_mark(5.50)
        expected = (5.50 - 3.00) * SPX_MULTIPLIER
        assert pos.pnl_per_contract == pytest.approx(expected)
        assert pos.total_pnl == pytest.approx(expected * 2)

    def test_debit_position_loss_when_mark_drops(self):
        pos = _debit_spread().with_mark(1.00)
        expected = (1.00 - 3.00) * SPX_MULTIPLIER
        assert pos.total_pnl < 0

    def test_net_pnl_subtracts_friction(self):
        pos = _credit_spread(friction_paid=15.0).with_mark(1.20)
        assert pos.net_pnl == pytest.approx(pos.total_pnl - 15.0)

    def test_pnl_at_entry_is_zero(self):
        pos = _credit_spread()
        assert pos.total_pnl == pytest.approx(0.0)

    def test_max_loss_total(self):
        pos = _credit_spread(contracts=3, max_loss_per_contract=7.50)
        assert pos.max_loss_total == pytest.approx(7.50 * 100 * 3)

    def test_target_total(self):
        pos = _debit_spread(contracts=2, target_per_contract=5.00)
        assert pos.target_total == pytest.approx(5.00 * 100 * 2)


class TestPositionMutations:
    def test_with_mark_does_not_mutate_original(self):
        pos = _credit_spread()
        updated = pos.with_mark(1.50)
        assert pos.current_mark == 2.50
        assert updated.current_mark == 1.50

    def test_with_greeks(self):
        pos = _credit_spread()
        updated = pos.with_greeks(delta=-0.15, gamma=-0.03, theta=0.08)
        assert updated.delta == -0.15
        assert updated.gamma == -0.03
        assert updated.theta == 0.08

    def test_with_adjustment_increments_count(self):
        pos = _credit_spread()
        updated = pos.with_adjustment("Rolled short strike up 5 pts")
        assert updated.adjustments == 1
        assert "Rolled" in updated.notes

    def test_thesis_invalidated(self):
        pos = _credit_spread()
        updated = pos.with_thesis_invalidated()
        assert updated.thesis_still_valid is False
        assert pos.thesis_still_valid is True

    def test_closed_sets_status_and_exit_mark(self):
        pos = _credit_spread()
        closed = pos.closed(exit_mark=0.10)
        assert closed.status is PositionStatus.CLOSED
        assert closed.current_mark == 0.10

    def test_net_greeks_scale_by_contracts(self):
        pos = _debit_spread(contracts=3).with_greeks(0.40, 0.05, -0.12)
        assert pos.net_delta == pytest.approx(1.20)
        assert pos.net_gamma == pytest.approx(0.15)
        assert pos.net_theta == pytest.approx(-0.36)


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


class TestSessionSummary:
    def test_empty_session(self):
        summary = calculate_session_summary((), daily_budget=5000.0)
        assert summary.open_count == 0
        assert summary.total_pnl == 0.0
        assert summary.budget_used_pct == 0.0

    def test_open_positions_contribute_to_pnl(self):
        p1 = _credit_spread().with_mark(1.20)
        p2 = _debit_spread().with_mark(4.00)
        summary = calculate_session_summary((p1, p2), daily_budget=5000.0)
        assert summary.open_count == 2
        assert summary.closed_count == 0
        assert summary.open_pnl == pytest.approx(p1.total_pnl + p2.total_pnl)

    def test_closed_positions_separate_from_open(self):
        p1 = _credit_spread().with_mark(1.20)
        p2 = _credit_spread().closed(exit_mark=0.10)
        summary = calculate_session_summary((p1, p2), daily_budget=5000.0)
        assert summary.open_count == 1
        assert summary.closed_count == 1
        assert summary.total_pnl == pytest.approx(p1.total_pnl + p2.total_pnl)

    def test_budget_utilization(self):
        p = _credit_spread(contracts=2, max_loss_per_contract=7.50)
        summary = calculate_session_summary((p,), daily_budget=3000.0)
        expected_exposure = 7.50 * 100 * 2
        assert summary.max_loss_exposure == pytest.approx(expected_exposure)
        assert summary.budget_used_pct == pytest.approx(expected_exposure / 3000.0)

    def test_aggregate_greeks(self):
        p1 = _credit_spread(contracts=1).with_greeks(-0.15, -0.03, 0.08)
        p2 = _debit_spread(contracts=2).with_greeks(0.40, 0.05, -0.12)
        summary = calculate_session_summary((p1, p2), daily_budget=5000.0)
        assert summary.net_delta == pytest.approx(-0.15 + 0.80)
        assert summary.net_gamma == pytest.approx(-0.03 + 0.10)
        assert summary.net_theta == pytest.approx(0.08 + -0.24)

    def test_friction_tracked_across_session(self):
        p1 = _credit_spread(friction_paid=12.50)
        p2 = _debit_spread(friction_paid=18.00)
        summary = calculate_session_summary((p1, p2), daily_budget=5000.0)
        assert summary.total_friction == pytest.approx(30.50)

    def test_adjustment_count_aggregated(self):
        p1 = _credit_spread().with_adjustment("adj 1").with_adjustment("adj 2")
        p2 = _debit_spread().with_adjustment("adj 1")
        summary = calculate_session_summary((p1, p2), daily_budget=5000.0)
        assert summary.total_adjustments == 3
