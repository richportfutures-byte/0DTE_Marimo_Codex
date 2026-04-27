"""Placeholder prompt workflow names."""

PROMPT_WORKFLOWS = (
    "pre_session_regime_synthesis",
    "dealer_flow_interpretation",
    "adjustment_drill",
    "strategy_audit",
    "edge_hypothesis_stress_test",
    "post_session_review",
)


def list_prompt_workflows() -> tuple[str, ...]:
    """Return planned prompt workflow identifiers."""
    return PROMPT_WORKFLOWS
