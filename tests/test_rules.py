from spx_inventory_playbook.rules import allowed_actions_from_validation, list_valid_actions
from spx_inventory_playbook.validators import Action, ValidationMessage, ValidationResult, ValidationSeverity


def test_valid_actions_are_planned_inventory_actions() -> None:
    assert list_valid_actions() == tuple(Action)


def validation_result_with_code(code: str) -> ValidationResult:
    return ValidationResult(
        messages=[
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code=code,
                message="test message",
            )
        ]
    )


def test_allowed_actions_collapse_for_lockout() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("LOCKOUT_ACTIVE")) == {
        Action.EMERGENCY_FLATTEN,
        Action.CLOSE,
        Action.STOP_TRADING,
    }


def test_allowed_actions_collapse_for_behavior_not_authorized() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("BEHAVIOR_NOT_AUTHORIZED")) == {
        Action.REDUCE,
        Action.CLOSE,
        Action.HEDGE_MES_ES,
        Action.STOP_TRADING,
    }


def test_allowed_actions_collapse_for_thesis_invalidated() -> None:
    assert allowed_actions_from_validation(validation_result_with_code("THESIS_INVALIDATED")) == {
        Action.REDUCE,
        Action.CLOSE,
        Action.EMERGENCY_FLATTEN,
        Action.STOP_TRADING,
    }


def test_allowed_actions_are_broad_for_clean_validation() -> None:
    assert allowed_actions_from_validation(ValidationResult(messages=[])) == {
        Action.HOLD,
        Action.TAKE_PARTIAL_PROFIT,
        Action.REDUCE,
        Action.HEDGE_MES_ES,
        Action.CONVERT_RESTRUCTURE,
        Action.CLOSE,
        Action.STOP_TRADING,
    }
