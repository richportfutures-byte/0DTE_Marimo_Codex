from dataclasses import fields

from spx_inventory_playbook.playbook import (
    Permission,
    get_action_permission_matrix,
    get_conversion_triage_table,
    get_structure_quick_reference,
    get_time_of_day_permission_matrix,
)
from spx_inventory_playbook.validators import Action


TIME_PERMISSION_FIELDS = (
    "open_930_945",
    "morning_945_1030",
    "late_morning_1030_1200",
    "midday_1200_1330",
    "early_afternoon_1330_1430",
    "late_afternoon_1430_1515",
    "final_hour_1515_1545",
    "final_15_1545_1555",
    "final_5_1555_1600",
)


def row_by_action(rows, action: str):
    return next(row for row in rows if row.action == action)


def test_action_permission_matrix_has_exactly_twenty_rows() -> None:
    assert len(get_action_permission_matrix()) == 20


def test_playbook_action_labels_are_recognizable() -> None:
    """Ensure playbook action strings are traceable to the Action enum."""
    enum_tokens = {
        token
        for action in Action
        for token in action.name.lower().split("_")
        if len(token) > 2
    }
    bridge_labels = {
        "Scale out": Action.REDUCE,
        "Add to winner": Action.CONVERT_RESTRUCTURE,
        "Add to loser": Action.CONVERT_RESTRUCTURE,
        "Recenter butterfly": Action.CONVERT_RESTRUCTURE,
        "Remove one side of iron condor": Action.CONVERT_RESTRUCTURE,
        "Roll strike": Action.CONVERT_RESTRUCTURE,
        "Widen spread": Action.CONVERT_RESTRUCTURE,
    }

    for row in get_action_permission_matrix():
        action_label = row.action.lower()
        matches = [token for token in enum_tokens if token in action_label]
        assert matches or row.action in bridge_labels, (
            f"Playbook action '{row.action}' has no recognizable token from Action enum; "
            f"known tokens: {sorted(enum_tokens)}"
        )


def test_structure_quick_reference_has_exactly_eight_rows() -> None:
    assert len(get_structure_quick_reference()) == 8


def test_conversion_triage_table_has_exactly_ten_rows() -> None:
    assert len(get_conversion_triage_table()) == 10


def test_time_of_day_permission_matrix_has_exactly_fifteen_rows() -> None:
    assert len(get_time_of_day_permission_matrix()) == 15


def test_every_time_of_day_permission_cell_is_permission() -> None:
    for row in get_time_of_day_permission_matrix():
        for field_name in TIME_PERMISSION_FIELDS:
            assert isinstance(getattr(row, field_name), Permission)


def test_final_five_minutes_forbids_complex_or_risk_adding_actions() -> None:
    rows = get_time_of_day_permission_matrix()

    for action in (
        "Convert to vertical",
        "Convert to fly/BWB",
        "Add risk",
        "Sell new premium",
        "Recenter fly",
        "Roll",
        "Widen",
    ):
        assert row_by_action(rows, action).final_5_1555_1600 is Permission.FORBIDDEN


def test_final_five_minutes_allows_or_limits_close_expiry_and_stop() -> None:
    rows = get_time_of_day_permission_matrix()

    assert row_by_action(rows, "Close").final_5_1555_1600 is Permission.CLOSE_ONLY
    assert row_by_action(rows, "Accept expiry").final_5_1555_1600 is Permission.PREPLANNED_ONLY
    assert row_by_action(rows, "Stop trading").final_5_1555_1600 is Permission.ALLOWED


def test_add_to_loser_is_forbidden_under_loss_repair_conditions() -> None:
    row = row_by_action(get_action_permission_matrix(), "Add to loser")

    assert "forbidden" in row.forbidden.lower()
    assert "loss repair" in row.always_forbidden_if.lower()


def test_widen_spread_marks_stress_widening_forbidden() -> None:
    row = row_by_action(get_action_permission_matrix(), "Widen spread")

    assert "stress widening" in row.restricted.lower()
    assert "stress" in row.always_forbidden_if.lower()


def test_conversion_triage_rows_have_close_superiority_rule() -> None:
    for row in get_conversion_triage_table():
        assert row.closing_superior_when.strip()


def test_playbook_fields_stay_compact() -> None:
    all_rows = [
        *get_action_permission_matrix(),
        *get_structure_quick_reference(),
        *get_conversion_triage_table(),
        *get_time_of_day_permission_matrix(),
    ]

    for row in all_rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if isinstance(value, str):
                assert len(value) <= 180, f"{type(row).__name__}.{field.name} is too long"
