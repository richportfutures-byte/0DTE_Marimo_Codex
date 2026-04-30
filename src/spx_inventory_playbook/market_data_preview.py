"""Sanitized broker-neutral market-data preview for notebook display checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
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
    mode_label: str
    disclosure: tuple[str, ...]
    source: MarketDataSource
    underlying_quote: UnderlyingQuoteSnapshot
    option_chain: OptionChainSnapshot
    atm_straddle: AtmStraddleSnapshot
    facade_result: MarketDataFacadeResult


def build_sanitized_market_data_preview() -> SanitizedMarketDataPreview:
    """Build a deterministic non-live facade result from canonical objects."""
    source = MarketDataSource(
        provider="sanitized fixture",
        adapter="broker-neutral display fixture",
        retrieved_at=_PREVIEW_AS_OF,
        is_live=False,
    )
    expiry = ExpirySnapshot(
        expiry_date=_PREVIEW_AS_OF.date(),
        session_date=_PREVIEW_AS_OF.date(),
        dte=0,
        is_0dte=True,
        source=source,
        settlement="PM",
        last_trade_time=_PREVIEW_AS_OF.replace(hour=16, minute=0),
    )
    underlying_quote = UnderlyingQuoteSnapshot(
        symbol=_UNDERLYING_SYMBOL,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=QuoteFreshness.FRESH,
        bid=Decimal("4999.75"),
        ask=Decimal("5000.25"),
        last=Decimal("5000.00"),
        provider_mark=Decimal("5000.00"),
    )
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
    option_chain = OptionChainSnapshot(
        underlying_symbol=_UNDERLYING_SYMBOL,
        expiry=expiry,
        source=source,
        as_of=_PREVIEW_AS_OF,
        freshness=QuoteFreshness.FRESH,
        contracts=(call, put),
        is_partial=False,
    )
    width_points = call.midpoint + put.midpoint
    atm_straddle = AtmStraddleSnapshot(
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
    facade_result = evaluate_market_data_facade(
        underlying_quote=underlying_quote,
        option_chain=option_chain,
        atm_straddle=atm_straddle,
    )

    return SanitizedMarketDataPreview(
        mode_label=SANITIZED_PREVIEW_MODE_LABEL,
        disclosure=SANITIZED_PREVIEW_DISCLOSURE,
        source=source,
        underlying_quote=underlying_quote,
        option_chain=option_chain,
        atm_straddle=atm_straddle,
        facade_result=facade_result,
    )


def _option_quote(
    *,
    source: MarketDataSource,
    right: str,
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
