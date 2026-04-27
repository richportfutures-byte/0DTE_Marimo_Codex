"""Placeholder reference-card registry."""

REFERENCE_TOPICS = (
    "dealer_gamma",
    "zero_gamma_flip",
    "vanna_charm",
    "skew",
    "variance_risk_premium",
    "pm_settlement",
    "cost_realism",
    "spx_execution_microstructure",
    "futures_hedging",
    "behavioral_lockouts",
)


def list_reference_topics() -> tuple[str, ...]:
    """Return planned static reference topics."""
    return REFERENCE_TOPICS
