import pytest

from spx_inventory_playbook.fixtures import (
    behavior_not_authorized_state,
    clean_state,
    final_five_minutes_state,
    lockout_state,
    poor_liquidity_state,
    state_with_overrides,
    thesis_invalidated_state,
)
from spx_inventory_playbook.rules import (
    FINAL_FIVE_MINUTE_ACTIONS,
    DecisionSeverity,
    evaluate_inventory_rules,
)
from spx_inventory_playbook.validators import (
    TimeWindow,
    ValidationMessage,
    ValidationResult,
    ValidationSeverity,
    validate_inventory_state,
)


def messages_by_code(result: ValidationResult) -> dict[str, ValidationMessage]:
    return {message.code: message for message in result.messages}


def test_clean_state_validates_without_blockers() -> None:
    result = validate_inventory_state(clean_state())

    assert result.messages == []
    assert not result.has_blockers()


def test_lockout_state_produces_lockout_blocker() -> None:
    result = validate_inventory_state(lockout_state())

    message = messages_by_code(result)["LOCKOUT_ACTIVE"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_behavior_not_authorized_state_produces_behavior_blocker() -> None:
    result = validate_inventory_state(behavior_not_authorized_state())

    message = messages_by_code(result)["BEHAVIOR_NOT_AUTHORIZED"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_thesis_invalidated_state_produces_thesis_invalidation_blocker() -> None:
    result = validate_inventory_state(thesis_invalidated_state())

    message = messages_by_code(result)["THESIS_INVALIDATED"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_poor_liquidity_state_produces_warning_not_blocker() -> None:
    result = validate_inventory_state(poor_liquidity_state())

    message = messages_by_code(result)["LIQUIDITY_POOR"]
    assert message.severity is ValidationSeverity.WARNING
    assert not result.has_blockers()


def test_final_five_minutes_state_produces_warning_and_rule_restriction() -> None:
    result = validate_inventory_state(final_five_minutes_state())
    decision = evaluate_inventory_rules(final_five_minutes_state())

    message = messages_by_code(result)["FINAL_5_MINUTES"]
    assert message.severity is ValidationSeverity.WARNING
    assert not result.has_blockers()
    assert decision.severity is DecisionSeverity.RESTRICTED
    assert decision.allowed_actions == FINAL_FIVE_MINUTE_ACTIONS


def test_state_with_overrides_changes_requested_field() -> None:
    state = state_with_overrides(
        clean_state(),
        **{"market.time_window": TimeWindow.MIDDAY_1200_1330},
    )

    assert state.market.time_window is TimeWindow.MIDDAY_1200_1330


def test_state_with_overrides_does_not_mutate_original_state() -> None:
    original = clean_state()
    changed = state_with_overrides(original, **{"market.liquidity_acceptable": False})

    assert original.market.liquidity_acceptable is True
    assert changed.market.liquidity_acceptable is False


def test_state_with_overrides_rejects_unknown_override_key() -> None:
    with pytest.raises(ValueError, match="Unsupported override key"):
        state_with_overrides(clean_state(), **{"market.unknown": True})
