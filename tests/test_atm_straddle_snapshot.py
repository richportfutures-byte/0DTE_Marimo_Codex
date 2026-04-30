from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    ExpirySnapshot,
    MarketDataSource,
    OptionContractKey,
    OptionQuoteSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)


NOW = datetime(2026, 4, 30, 10, 0, tzinfo=ZoneInfo("America/New_York"))
SESSION_DATE = NOW.date()


def source_fixture(**overrides: object) -> MarketDataSource:
    values = {
        "provider": "fixture",
        "adapter": "manual_fixture",
        "retrieved_at": NOW,
    }
    values.update(overrides)
    return MarketDataSource(**values)


def expiry_fixture(**overrides: object) -> ExpirySnapshot:
    values = {
        "expiry_date": SESSION_DATE,
        "session_date": SESSION_DATE,
        "dte": 0,
        "is_0dte": True,
        "settlement": "PM",
        "source": source_fixture(),
    }
    values.update(overrides)
    return ExpirySnapshot(**values)


def key_fixture(**overrides: object) -> OptionContractKey:
    values = {
        "underlying": "SPX",
        "expiry_date": SESSION_DATE,
        "strike": Decimal("5000"),
        "right": "CALL",
        "product": "SPXW",
        "provider_symbol": "fixture-provider-symbol",
    }
    values.update(overrides)
    return OptionContractKey(**values)


def quote_fixture(**overrides: object) -> OptionQuoteSnapshot:
    values = {
        "key": key_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("10.00"),
        "ask": Decimal("10.40"),
    }
    values.update(overrides)
    return OptionQuoteSnapshot(**values)


def underlying_fixture(**overrides: object) -> UnderlyingQuoteSnapshot:
    values = {
        "symbol": "SPX",
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("4999.00"),
        "ask": Decimal("5001.00"),
    }
    values.update(overrides)
    return UnderlyingQuoteSnapshot(**values)


def straddle_fixture(**overrides: object) -> AtmStraddleSnapshot:
    call = quote_fixture(
        key=key_fixture(right="CALL", provider_symbol="call-provider-symbol"),
        bid=Decimal("10.00"),
        ask=Decimal("10.40"),
    )
    put = quote_fixture(
        key=key_fixture(right="PUT", provider_symbol="put-provider-symbol"),
        bid=Decimal("9.80"),
        ask=Decimal("10.20"),
    )
    values = {
        "underlying_symbol": "SPX",
        "underlying_price": Decimal("5000.00"),
        "underlying_quote": underlying_fixture(),
        "expiry": expiry_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "call": call,
        "put": put,
        "width_points": Decimal("20.20"),
        "width_percent": Decimal("0.00404"),
    }
    values.update(overrides)
    return AtmStraddleSnapshot(**values)


def test_atm_straddle_requires_call_and_put_same_strike_and_expiry() -> None:
    wrong_strike_put = quote_fixture(
        key=key_fixture(
            right="PUT",
            strike=Decimal("5010"),
            provider_symbol="wrong-strike-put",
        )
    )

    with pytest.raises(ValueError, match="same strike"):
        straddle_fixture(put=wrong_strike_put)

    wrong_expiry_put = quote_fixture(
        key=key_fixture(
            right="PUT",
            expiry_date=date(2026, 5, 1),
            provider_symbol="wrong-expiry-put",
        )
    )

    with pytest.raises(ValueError, match="same .*expiry"):
        straddle_fixture(put=wrong_expiry_put)


def test_atm_straddle_width_points_equals_call_plus_put_midpoint() -> None:
    straddle = straddle_fixture()

    assert straddle.call.midpoint == Decimal("10.20")
    assert straddle.put.midpoint == Decimal("10.00")
    assert straddle.width_points == Decimal("20.20")


def test_atm_straddle_width_percent_requires_valid_underlying_price() -> None:
    straddle = straddle_fixture()

    assert straddle.width_percent == Decimal("0.00404")

    with pytest.raises(ValueError, match="underlying_price"):
        straddle_fixture(underlying_price=Decimal("0"))


def test_stale_chain_or_stale_underlying_blocks_atm_straddle() -> None:
    stale_underlying = underlying_fixture(freshness=QuoteFreshness.STALE)
    stale_straddle = straddle_fixture(
        underlying_quote=stale_underlying,
        freshness=QuoteFreshness.STALE,
    )

    assert stale_straddle.freshness is QuoteFreshness.STALE
    assert stale_straddle.blocks_derived_outputs is True
