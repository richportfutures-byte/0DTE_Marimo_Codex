"""Broker-neutral facade for notebook market-data readiness."""

from __future__ import annotations

from dataclasses import dataclass

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    MarketDataHealth,
    OptionChainSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)


@dataclass(frozen=True)
class MarketDataFacadeResult:
    health: MarketDataHealth
    underlying_freshness: QuoteFreshness
    option_chain_freshness: QuoteFreshness
    atm_straddle_freshness: QuoteFreshness
    underlying_available: bool
    option_chain_available: bool
    atm_straddle_available: bool
    underlying_usable: bool
    option_chain_usable: bool
    atm_straddle_usable: bool
    chain_derived_outputs_usable: bool
    api_outputs_usable: bool
    manual_confirmation_required: bool
    greek_checks_available: bool


def evaluate_market_data_facade(
    *,
    underlying_quote: UnderlyingQuoteSnapshot | None,
    option_chain: OptionChainSnapshot | None,
    atm_straddle: AtmStraddleSnapshot | None = None,
) -> MarketDataFacadeResult:
    blockers: list[str] = []
    warnings: list[str] = []
    missing_fields: list[str] = []
    stale_fields: list[str] = []

    underlying_freshness = _underlying_freshness(underlying_quote)
    option_chain_freshness = _option_chain_freshness(option_chain)
    atm_straddle_freshness = _atm_straddle_freshness(atm_straddle)

    if underlying_quote is None:
        blockers.append("Underlying quote is missing.")
        missing_fields.append("underlying_quote")
    elif underlying_quote.freshness is not QuoteFreshness.FRESH:
        blockers.append("Underlying quote is not fresh.")
        stale_fields.append("underlying_quote")

    if option_chain is None:
        blockers.append("Option chain is missing.")
        missing_fields.append("option_chain")
    else:
        if option_chain.freshness is not QuoteFreshness.FRESH:
            blockers.append("Option chain is not fresh.")
            stale_fields.append("option_chain")
        if option_chain.is_partial:
            warnings.extend(option_chain.completeness_notes)
            if not option_chain.completeness_notes:
                warnings.append("Option chain is partial.")

    locked_quote_detected = _has_locked_quote(option_chain)
    if locked_quote_detected:
        warnings.append("Locked option quote detected; liquidity is degraded.")

    greek_checks_available = _greek_checks_available(option_chain)
    if option_chain is not None and not greek_checks_available:
        warnings.append("Greeks unavailable for at least one option quote.")

    if atm_straddle is None:
        missing_fields.append("atm_straddle")
        if underlying_quote is not None and option_chain is not None:
            warnings.append("ATM straddle is unavailable.")
    elif atm_straddle.blocks_derived_outputs:
        warnings.append("ATM straddle is not fresh.")
        stale_fields.append("atm_straddle")

    underlying_usable = (
        underlying_quote is not None
        and underlying_quote.freshness is QuoteFreshness.FRESH
    )
    option_chain_usable = (
        option_chain is not None
        and option_chain.freshness is QuoteFreshness.FRESH
        and not option_chain.blocks_structure_ranking
        and not locked_quote_detected
    )
    atm_straddle_usable = (
        atm_straddle is not None
        and atm_straddle.freshness is QuoteFreshness.FRESH
        and not atm_straddle.blocks_derived_outputs
    )
    chain_derived_outputs_usable = underlying_usable and option_chain_usable
    api_outputs_usable = (
        chain_derived_outputs_usable
        and atm_straddle_usable
    )

    health = MarketDataHealth(
        status=_health_status(blockers, warnings, missing_fields, stale_fields),
        blockers=tuple(blockers),
        warnings=tuple(_unique(warnings)),
        missing_fields=tuple(_unique(missing_fields)),
        stale_fields=tuple(_unique(stale_fields)),
    )

    return MarketDataFacadeResult(
        health=health,
        underlying_freshness=underlying_freshness,
        option_chain_freshness=option_chain_freshness,
        atm_straddle_freshness=atm_straddle_freshness,
        underlying_available=underlying_quote is not None,
        option_chain_available=option_chain is not None,
        atm_straddle_available=atm_straddle is not None,
        underlying_usable=underlying_usable,
        option_chain_usable=option_chain_usable,
        atm_straddle_usable=atm_straddle_usable,
        chain_derived_outputs_usable=chain_derived_outputs_usable,
        api_outputs_usable=api_outputs_usable,
        manual_confirmation_required=health.status != "OK",
        greek_checks_available=greek_checks_available,
    )


def _underlying_freshness(
    underlying_quote: UnderlyingQuoteSnapshot | None,
) -> QuoteFreshness:
    if underlying_quote is None:
        return QuoteFreshness.MISSING
    return underlying_quote.freshness


def _option_chain_freshness(
    option_chain: OptionChainSnapshot | None,
) -> QuoteFreshness:
    if option_chain is None:
        return QuoteFreshness.MISSING
    return option_chain.freshness


def _atm_straddle_freshness(
    atm_straddle: AtmStraddleSnapshot | None,
) -> QuoteFreshness:
    if atm_straddle is None:
        return QuoteFreshness.MISSING
    return atm_straddle.freshness


def _has_locked_quote(option_chain: OptionChainSnapshot | None) -> bool:
    if option_chain is None:
        return False
    return any(quote.is_locked for quote in option_chain.contracts)


def _greek_checks_available(option_chain: OptionChainSnapshot | None) -> bool:
    if option_chain is None:
        return False
    greek_fields = ("delta", "gamma", "theta", "vega", "iv")
    return all(
        all(getattr(quote, field_name) is not None for field_name in greek_fields)
        for quote in option_chain.contracts
    )


def _health_status(
    blockers: list[str],
    warnings: list[str],
    missing_fields: list[str],
    stale_fields: list[str],
) -> str:
    if blockers:
        return "BLOCKED"
    if warnings or missing_fields or stale_fields:
        return "DEGRADED"
    return "OK"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
