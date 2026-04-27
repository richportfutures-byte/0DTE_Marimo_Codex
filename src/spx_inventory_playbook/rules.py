"""Placeholder deterministic inventory action definitions."""

VALID_ACTIONS = ("hold", "reduce", "hedge", "convert", "close", "stop")


def list_valid_actions() -> tuple[str, ...]:
    """Return the planned inventory adjustment action names."""
    return VALID_ACTIONS
