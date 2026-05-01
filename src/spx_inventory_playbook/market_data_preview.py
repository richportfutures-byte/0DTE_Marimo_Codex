"""Sanitized broker-neutral market-data preview for notebook display checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    ExpirySnapshot,
    MarketDataSource,
    OptionChainSnapshot,
    OptionContractKey,
    OptionQuoteSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)
from spx_inventory_playbook.market_data_facade import (
    MarketDataFacadeResult,
    evaluate_market_data_facade,
)


NO_MARKET_DATA_MODE_LABEL = "No market data loaded"
SANITIZED_PREVIEW_MODE_LABEL = "Sanitized fixture preview"
PREVIEW_SCENARIO_NAMES = (
    "default_fail_closed",
    "healthy_preview",
    "stale_underlying",
    "partial_chain",
    "locked_liquidity",
    "missing_atm_straddle",
)
PREVIEW_SCENARIO_LABELS = {
    "Default fail-closed": "default_fail_closed",
    "Healthy sanitized preview": "healthy_preview",
    "Stale underlying": "stale_underlying",
    "Partial option chain": "partial_chain",
    "Locked option liquidity": "locked_liquidity",
    "Missing ATM straddle": "missing_atm_straddle",
}
SANITIZED_PREVIEW_DISCLOSURE = (
    "sanitized fixture",
    "not live",
    "not broker data",
    "for display verification only",
)

_PREVIEW_AS_OF = datetime(2026, 4, 30, 10, 15, tzinfo=ZoneInfo("America/New_York"))
_UNDERLYING_SYMBOL = "SPX"
_PRODUCT = "SPXW"
_ATM_STRIKE = Decimal("5000")


@dataclass(frozen=True)
class SanitizedMarketDataPreview:
    scenario_name: str
    mode_label: str
    disclosure: tuple[str, ...]
    source: MarketDataSource | None
    underlying_quote: UnderlyingQuoteSnapshot | None
    option_chain: OptionChainSnapshot | None
    atm_straddle: AtmStraddleSnapshot | None
    facade_result: MarketDataFacadeResult


def build_sanitized_market_data_preview() -> SanitizedMarketDataPreview:
    """Build a deterministic non-live facade result from canonical objects."""
    return build_market_data_preview_scenario("healthy_preview")


def build_market_data_preview_scenario(
    scenario_name: str,
) -> SanitizedMarketDataPreview:
    """Build one deterministic broker-neutral readiness scenario."""
    if scenario_name not in PREVIEW_SCENARIO_NAMES:
        raise ValueError(f"Unknown market-data preview scenario: {scenario_name}.")

    if scenario_name == "default_fail_closed":
        return _preview_result(
            scenario_name=scenario_name,
            mode_label=NO_MARKET_DATA_MODE_LABEL,
            source=None,
            underlying_quote=None,
            option_chain=None,
            atm_straddle=None,
        )

    source = _source()
    underlying_quote = _underlying_quote(source=source)
    expiry = _expiry(source=source)
    call = _option_quote(
        source=source,
        right="CALL",
        bid=Decimal("10.10"),
        ask=Decimal("10.50"),
        delta=Decimal("0.50"),
        theta=Decimal("-0.42"),
        provider_symbol="SPXW-FIXTURE-20260430-5000-C",
    )
    put = _option_quote(
        source=source,
        right="PUT",
        bid=Decimal("9.90"),
        ask=Decimal("10.30"),
        delta=Decimal("-0.50"),
        theta=Decimal("-0.41"),
        provider_symbol="SPXW-FIXTURE-20260430-5000-P",
    )

    if scenario_name == "stale_underlying":
        underlying_quote = _underlying_quote(
            source=source,
            freshness=QuoteFreshness.STALE,
        )

    if scenario_name == "locked_liquidity":
        call = _option_quote(
            source=source,
            right="CALL",
            bid=Decimal("10.20"),
            ask=Decimal("10.20"),
            delta=Decimal("0.50"),
            theta=Decimal("-0.42"),
            provider_symbol="SPXW-FIXTURE-20260430-5000-C",
        )

    option_chain = _option_chain(
        source=source,
        expiry=expiry,
        call=call,
        put=put,
        is_partial=scenario_name == "partial_chain",
    )

    atm_straddle = None
    if scenario_name != "missing_atm_straddle":
        atm_straddle = _atm_straddle(
            source=source,
            expiry=expiry,
            underlying_quote=underlying_quote,
            call=call,
            put=put,
        )

    return _preview_result(
        scenario_name=scenario_name,
        mode_label=_mode_label(scenario_name),
        source=source,
        underlying_quote=underlying_quote,
        option_chain=option_chain,
        atm_straddle=atm_straddle,
    )


def _source() -> MarketDataSource:
    source = MarketDataSource(
        provider="sanitized fixture",
        adapter="broker-neutral display fixture",
        retrieved_at=_PREVIEW_AS_OF,
        is_live=False,
    )
    return source


def _expiry(*, source: MarketDataSource) -> ExpirySnapshot:
    return ExpirySnapshot(
        expiry_date=_PREVIEW_AS_OF.date(),
        session_date=_PREVIEW_AS_OF.date(),
        dte=0,
        is_0dte=True,
        source=source,
        settlement="PM",
        last_trade_time=_PREVIEW_AS_OF.replace(hour=16, minute=0),
    )


def _underlying_quote(
    *,
    source: MarketDataSource,
    freshness: QuoteFreshness = QuoteFreshness.FRESH,
) -> UnderlyingQuoteSnapshot:
    return UnderlyingQuoteSnapshot(
        symbol=_UNDERLYING_SYMBOL,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=freshness,
        bid=Decimal("4999.75"),
        ask=Decimal("5000.25"),
        last=Decimal("5000.00"),
        provider_mark=Decimal("5000.00"),
    )


def _option_chain(
    *,
    source: MarketDataSource,
    expiry: ExpirySnapshot,
    call: OptionQuoteSnapshot,
    put: OptionQuoteSnapshot,
    is_partial: bool = False,
) -> OptionChainSnapshot:
    completeness_notes = ()
    if is_partial:
        completeness_notes = ("Sanitized fixture chain is intentionally partial.",)

    return OptionChainSnapshot(
        underlying_symbol=_UNDERLYING_SYMBOL,
        expiry=expiry,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=QuoteFreshness.FRESH,
        contracts=(call, put),
        is_partial=is_partial,
        completeness_notes=completeness_notes,
    )


def _atm_straddle(
    *,
    source: MarketDataSource,
    expiry: ExpirySnapshot,
    underlying_quote: UnderlyingQuoteSnapshot,
    call: OptionQuoteSnapshot,
    put: OptionQuoteSnapshot,
) -> AtmStraddleSnapshot:
    width_points = call.midpoint + put.midpoint
    return AtmStraddleSnapshot(
        underlying_symbol=_UNDERLYING_SYMBOL,
        underlying_price=underlying_quote.midpoint,
        underlying_quote=underlying_quote,
        expiry=expiry,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=QuoteFreshness.FRESH,
        call=call,
        put=put,
        width_points=width_points,
        width_percent=width_points / underlying_quote.midpoint,
    )


def _preview_result(
    *,
    scenario_name: str,
    mode_label: str,
    source: MarketDataSource | None,
    underlying_quote: UnderlyingQuoteSnapshot | None,
    option_chain: OptionChainSnapshot | None,
    atm_straddle: AtmStraddleSnapshot | None,
) -> SanitizedMarketDataPreview:
    facade_result = evaluate_market_data_facade(
        underlying_quote=underlying_quote,
        option_chain=option_chain,
        atm_straddle=atm_straddle,
    )

    return SanitizedMarketDataPreview(
        scenario_name=scenario_name,
        mode_label=mode_label,
        disclosure=SANITIZED_PREVIEW_DISCLOSURE,
        source=source,
        underlying_quote=underlying_quote,
        option_chain=option_chain,
        atm_straddle=atm_straddle,
        facade_result=facade_result,
    )


def _mode_label(scenario_name: str) -> str:
    return {
        "healthy_preview": SANITIZED_PREVIEW_MODE_LABEL,
        "stale_underlying": "Sanitized fixture: stale underlying",
        "partial_chain": "Sanitized fixture: partial option chain",
        "locked_liquidity": "Sanitized fixture: locked option liquidity",
        "missing_atm_straddle": "Sanitized fixture: missing ATM straddle",
    }.get(scenario_name, NO_MARKET_DATA_MODE_LABEL)


def _option_quote(
    *,
    source: MarketDataSource,
    right: Literal["CALL", "PUT"],
    bid: Decimal,
    ask: Decimal,
    delta: Decimal,
    theta: Decimal,
    provider_symbol: str,
) -> OptionQuoteSnapshot:
    key = OptionContractKey(
        underlying=_UNDERLYING_SYMBOL,
        expiry_date=_PREVIEW_AS_OF.date(),
        strike=_ATM_STRIKE,
        right=right,
        occ_symbol=provider_symbol,
        provider_symbol=provider_symbol,
        settlement="PM",
        product=_PRODUCT,
    )
    return OptionQuoteSnapshot(
        key=key,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=QuoteFreshness.FRESH,
        bid=bid,
        ask=ask,
        last=(bid + ask) / Decimal("2"),
        provider_mark=(bid + ask) / Decimal("2"),
        bid_size=10,
        ask_size=12,
        volume=120,
        open_interest=240,
        delta=delta,
        gamma=Decimal("0.010"),
        theta=theta,
        vega=Decimal("0.08"),
        iv=Decimal("0.18"),
    )
