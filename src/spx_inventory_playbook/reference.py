"""Compact professional reference cards for 0DTE SPX inventory work."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceCard:
    topic: str
    what_it_means: str
    why_it_matters_0dte: str
    operating_implication: str
    common_error: str
    verification_inputs: tuple[str, ...]


REFERENCE_TOPICS = (
    "Dealer gamma / GEX",
    "Zero-gamma flip",
    "Vanna and charm",
    "Skew and structure selection",
    "Variance risk premium",
    "SPX/SPXW execution microstructure",
    "PM cash settlement",
    "Futures hedging",
    "Cost realism",
    "Behavioral lockouts",
    "Modern 0DTE structural risk",
    "Source / broker verification checklist",
)


def list_reference_topics() -> tuple[str, ...]:
    """Return static reference-card topics."""
    return REFERENCE_TOPICS


def get_reference_cards() -> list[ReferenceCard]:
    """Return compact static professional reference cards."""
    return [
        ReferenceCard(
            topic="Dealer gamma / GEX",
            what_it_means="A proxy for how dealer hedging may dampen or amplify spot moves.",
            why_it_matters_0dte="Intraday option expiry can make hedge flows dominate short-window path risk.",
            operating_implication="Treat GEX as regime context, not a price forecast or literal barrier.",
            common_error="Reading a dealer level as simple support or resistance.",
            verification_inputs=(
                "dealer-flow source timestamp",
                "aggregate GEX estimate",
                "OI and volume context",
            ),
        ),
        ReferenceCard(
            topic="Zero-gamma flip",
            what_it_means="A model level where estimated dealer hedge response may change sign.",
            why_it_matters_0dte="Near the flip, small spot moves can change whether flow dampens or accelerates.",
            operating_implication="Use distance from flip as a regime input for hold, reduce, or hedge review.",
            common_error="Treating the flip as a guaranteed reversal level.",
            verification_inputs=(
                "flip estimate source",
                "current spot reference",
                "model timestamp",
            ),
        ),
        ReferenceCard(
            topic="Vanna and charm",
            what_it_means="Sensitivity of delta to implied volatility and time decay.",
            why_it_matters_0dte="Fast IV and time changes can shift hedge needs even if spot is stable.",
            operating_implication="Check whether IV decay or time decay is changing delta exposure.",
            common_error="Explaining every move with spot-only delta.",
            verification_inputs=(
                "surface snapshot",
                "time to expiry",
                "position Greeks from platform",
            ),
        ),
        ReferenceCard(
            topic="Skew and structure selection",
            what_it_means="Relative pricing across strikes and tails, not just headline volatility.",
            why_it_matters_0dte="Skew shapes payoff realism, wing cost, and repair quality.",
            operating_implication="Use skew to judge whether a structure is efficient or overpaying for tails.",
            common_error="Using VIX alone as the pricing guide.",
            verification_inputs=(
                "option chain snapshot",
                "skew measure",
                "term and strike comparison",
            ),
        ),
        ReferenceCard(
            topic="Variance risk premium",
            what_it_means="The gap between implied variance and later realized movement.",
            why_it_matters_0dte="The edge can vanish when intraday realized movement outruns implied pricing.",
            operating_implication="Verify implied versus realized context before relying on premium decay.",
            common_error="Assuming premium is rich without cost and regime checks.",
            verification_inputs=(
                "implied volatility inputs",
                "realized volatility context",
                "event calendar",
            ),
        ),
        ReferenceCard(
            topic="SPX/SPXW execution microstructure",
            what_it_means="Index options have cash settlement, wide markets, and complex routing behavior.",
            why_it_matters_0dte="Small execution friction can dominate short-lived edge and adjustment quality.",
            operating_implication="Use limit discipline, liquidity checks, and route awareness.",
            common_error="Ignoring market width and assuming model value is executable.",
            verification_inputs=(
                "broker quote display",
                "route availability",
                "market width history",
            ),
        ),
        ReferenceCard(
            topic="PM cash settlement",
            what_it_means="SPXW positions settle to cash using the official closing index value.",
            why_it_matters_0dte="Residual exposure can persist into the close even without share delivery.",
            operating_implication="Confirm expiry type, settlement timing, and platform exercise treatment.",
            common_error="Confusing cash settlement with equity-style assignment mechanics.",
            verification_inputs=(
                "exchange product specs",
                "broker expiry notes",
                "position exercise settings",
            ),
        ),
        ReferenceCard(
            topic="Futures hedging",
            what_it_means="ES or MES can offset delta exposure without changing option structure.",
            why_it_matters_0dte="A temporary hedge may control path risk while option liquidity is poor.",
            operating_implication="Define hedge size, exit condition, and inventory purpose before use.",
            common_error="Letting the hedge become a separate directional thesis.",
            verification_inputs=(
                "current option delta",
                "contract multiplier",
                "futures exposure per point",
            ),
        ),
        ReferenceCard(
            topic="Cost realism",
            what_it_means="Commissions, fees, spread crossing, and slippage reduce theoretical edge.",
            why_it_matters_0dte="Frequent adjustments can turn a valid idea into negative expectancy.",
            operating_implication="Use user-supplied friction estimates before judging any adjustment.",
            common_error="Reviewing gross outcome while ignoring execution drag.",
            verification_inputs=(
                "broker fee schedule",
                "actual fills",
                "spread crossing estimate",
            ),
        ),
        ReferenceCard(
            topic="Behavioral lockouts",
            what_it_means="Predefined restrictions after rule breach, loss limit, or impaired discretion.",
            why_it_matters_0dte="Fast expiry compresses decision time and magnifies loss-repair behavior.",
            operating_implication="When lockout is active, restrict actions to reduce, close, hedge, or stop.",
            common_error="Calling a repair an adjustment after discipline has failed.",
            verification_inputs=(
                "daily rule log",
                "loss limit status",
                "authorization checklist",
            ),
        ),
        ReferenceCard(
            topic="Modern 0DTE structural risk",
            what_it_means="Same-day expiry concentrates gamma, liquidity decay, and crowding risk.",
            why_it_matters_0dte="Path, timing, and execution can matter more than end-of-day direction.",
            operating_implication="Require time-of-day, liquidity, and close-by-time checks.",
            common_error="Treating a same-day structure like a longer-dated spread.",
            verification_inputs=(
                "time window",
                "liquidity condition",
                "structure risk map",
            ),
        ),
        ReferenceCard(
            topic="Source / broker verification checklist",
            what_it_means="A checklist for confirming inputs before relying on any workflow output.",
            why_it_matters_0dte="Stale, mismatched, or platform-specific data can corrupt decisions.",
            operating_implication="Verify source time, symbol, expiry, settlement type, and position state.",
            common_error="Assuming the app or prompt has real-time access.",
            verification_inputs=(
                "data timestamp",
                "symbol and expiry",
                "broker position screen",
            ),
        ),
    ]
