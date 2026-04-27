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
            what_it_means="Positive GEX can dampen movement; negative GEX can amplify trend or whipsaw.",
            why_it_matters_0dte="Same-day expiry can make hedge-flow character dominate short-window path risk.",
            operating_implication="Use GEX as regime context, never as a trade signal.",
            common_error="Reading GEX as a forecast instead of a regime input.",
            verification_inputs=(
                "dealer-flow source timestamp",
                "aggregate GEX estimate",
                "OI and volume context",
            ),
        ),
        ReferenceCard(
            topic="Zero-gamma flip",
            what_it_means="A regime boundary where estimated hedge-flow character may change.",
            why_it_matters_0dte="Acceptance across the flip can shift expected dampening or amplification.",
            operating_implication="Reduce authorization when spot chops around the flip.",
            common_error="Treating the flip as a literal price barrier.",
            verification_inputs=(
                "flip estimate source",
                "current spot reference",
                "model timestamp",
            ),
        ),
        ReferenceCard(
            topic="Vanna and charm",
            what_it_means="Hedge-flow context from volatility sensitivity and time decay.",
            why_it_matters_0dte="Vol crush and time decay can force hedge changes when positioning is concentrated.",
            operating_implication="Use vanna and charm as context, not standalone entries.",
            common_error="Treating spot movement as the only hedge driver.",
            verification_inputs=(
                "surface snapshot",
                "time to expiry",
                "position Greeks from platform",
            ),
        ),
        ReferenceCard(
            topic="Skew and structure selection",
            what_it_means="Structure choice must account for skew, not direction alone.",
            why_it_matters_0dte="Rich skew may be compensation for real tail risk.",
            operating_implication="Avoid short premium into negative-gamma movement without regime proof.",
            common_error="Choosing structure from direction while ignoring skew.",
            verification_inputs=(
                "option chain snapshot",
                "skew measure",
                "term and strike comparison",
            ),
        ),
        ReferenceCard(
            topic="Variance risk premium",
            what_it_means="Implied volatility must be rich versus expected realized volatility after costs.",
            why_it_matters_0dte="Compressed VRP can make short premium unattractive even with time decay.",
            operating_implication="Judge VRP by regime and costs, not theta alone.",
            common_error="Assuming premium decay is enough without realized-vol context.",
            verification_inputs=(
                "implied volatility inputs",
                "realized volatility context",
                "event calendar",
            ),
        ),
        ReferenceCard(
            topic="SPX/SPXW execution microstructure",
            what_it_means="Multi-leg mids can be non-fillable; routing and wing availability matter.",
            why_it_matters_0dte="A valid adjustment can be operationally invalid if it cannot be filled.",
            operating_implication="Verify actual liquidity, route behavior, and wing availability.",
            common_error="Assuming theoretical mid value is executable.",
            verification_inputs=(
                "broker quote display",
                "route availability",
                "market width history",
            ),
        ),
        ReferenceCard(
            topic="PM cash settlement",
            what_it_means="Same-day PM cash settlement compresses time into the closing window.",
            why_it_matters_0dte="Final-hour short gamma is not justified by theta alone.",
            operating_implication="Use close-by-time discipline over squeezing final pennies.",
            common_error="Treating final-hour gamma as harmless because settlement is cash.",
            verification_inputs=(
                "exchange product specs",
                "broker expiry notes",
                "position exercise settings",
            ),
        ),
        ReferenceCard(
            topic="Futures hedging",
            what_it_means="ES or MES hedging is temporary delta inventory control.",
            why_it_matters_0dte="It can reduce path exposure without changing option structure.",
            operating_implication="Every hedge needs removal, reassessment, or close trigger.",
            common_error="Letting hedge inventory become a directional view.",
            verification_inputs=(
                "current option delta",
                "contract multiplier",
                "futures exposure per point",
            ),
        ),
        ReferenceCard(
            topic="Cost realism",
            what_it_means="Every adjustment must survive commissions, fees, and spread crossing.",
            why_it_matters_0dte="Gross credit or debit is not the same as executable edge.",
            operating_implication="If costs do not improve the position, close is superior.",
            common_error="Judging adjustment quality before friction is counted.",
            verification_inputs=(
                "broker fee schedule",
                "actual fills",
                "spread crossing estimate",
            ),
        ),
        ReferenceCard(
            topic="Behavioral lockouts",
            what_it_means="When behavior is impaired, discretion collapses.",
            why_it_matters_0dte="Fast expiry magnifies loss-repair behavior and rushed discretion.",
            operating_implication="Limit actions to reduce, close, temporary hedge, flatten, or stop.",
            common_error="Using conversions, rolls, widening, or added risk under impairment.",
            verification_inputs=(
                "daily rule log",
                "loss limit status",
                "authorization checklist",
            ),
        ),
        ReferenceCard(
            topic="Modern 0DTE structural risk",
            what_it_means="Modern 0DTE flow can alter intraday dealer positioning quickly.",
            why_it_matters_0dte="Pinning is not guaranteed when flow and gamma shift quickly.",
            operating_implication="Avoid backfitting post-2022 behavior from older option behavior.",
            common_error="Assuming pinning will rescue unmanaged gamma.",
            verification_inputs=(
                "time window",
                "liquidity condition",
                "structure risk map",
            ),
        ),
        ReferenceCard(
            topic="Source / broker verification checklist",
            what_it_means="Product mechanics need Cboe, OCC, OIC, and broker verification.",
            why_it_matters_0dte="Broker rules control margin, routing, spread handling, and liquidation.",
            operating_implication="Verify source, broker rule, symbol, expiry, and position state.",
            common_error="Assuming reference cards have live broker or market-data access.",
            verification_inputs=(
                "Cboe OCC OIC sources",
                "broker rule page",
                "current platform settings",
            ),
        ),
    ]
