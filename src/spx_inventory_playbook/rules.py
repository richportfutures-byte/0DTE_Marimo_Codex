"""Placeholder deterministic inventory action definitions."""

from .validators import Action, ValidationResult


VALID_ACTIONS = tuple(Action)


def list_valid_actions() -> tuple[Action, ...]:
    """Return the planned inventory adjustment action names."""
    return VALID_ACTIONS


def allowed_actions_from_validation(result: ValidationResult) -> set[Action]:
    """Map validation state to a broad allowed-action set without recommendations."""
    codes = {message.code for message in result.messages}

    if "LOCKOUT_ACTIVE" in codes:
        return {Action.EMERGENCY_FLATTEN, Action.CLOSE, Action.STOP_TRADING}

    if "BEHAVIOR_NOT_AUTHORIZED" in codes:
        return {Action.REDUCE, Action.CLOSE, Action.HEDGE_MES_ES, Action.STOP_TRADING}

    if "THESIS_INVALIDATED" in codes:
        return {Action.REDUCE, Action.CLOSE, Action.EMERGENCY_FLATTEN, Action.STOP_TRADING}

    return {
        Action.HOLD,
        Action.TAKE_PARTIAL_PROFIT,
        Action.REDUCE,
        Action.HEDGE_MES_ES,
        Action.CONVERT_RESTRUCTURE,
        Action.CLOSE,
        Action.STOP_TRADING,
    }
