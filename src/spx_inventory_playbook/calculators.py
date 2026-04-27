"""Small pure calculation helpers for future rule logic."""


def midpoint(bid: float, ask: float) -> float:
    """Return the midpoint for explicit user-supplied bid and ask values."""
    if bid < 0 or ask < 0:
        raise ValueError("Bid and ask must be non-negative.")
    if ask < bid:
        raise ValueError("Ask must be greater than or equal to bid.")
    return (bid + ask) / 2
