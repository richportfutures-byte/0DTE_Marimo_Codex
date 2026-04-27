"""Validation helpers for future user-supplied inputs."""


def require_user_supplied(value: object, field_name: str) -> object:
    """Require explicit input instead of generated or fabricated values."""
    if value is None:
        raise ValueError(f"{field_name} must be user supplied.")
    return value
