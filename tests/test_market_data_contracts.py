from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from spx_inventory_playbook.market_data import (
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


def option_key_fixture(**overrides: object) -> OptionContractKey:
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


def option_quote_fixture(**overrides: object) -> OptionQuoteSnapshot:
    values = {
        "key": option_key_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("10.00"),
        "ask": Decimal("10.40"),
    }
    values.update(overrides)
    return OptionQuoteSnapshot(**values)


def test_market_data_source_requires_provider() -> None:
    with pytest.raises(ValueError, match="provider"):
        source_fixture(provider="")


def test_market_data_source_requires_adapter() -> None:
    with pytest.raises(ValueError, match="adapter"):
        source_fixture(adapter=" ")


def test_market_data_source_requires_timezone_aware_retrieved_at() -> None:
    with pytest.raises(ValueError, match="retrieved_at"):
        source_fixture(retrieved_at=datetime(2026, 4, 30, 10, 0))


@pytest.mark.parametrize(
    "field_name, secret_value",
    [
        ("provider", "client_secret_fixture"),
        ("adapter", "auth_token_fixture"),
    ],
)
def test_market_data_source_repr_excludes_secret_like_values(
    field_name: str,
    secret_value: str,
) -> None:
    source = source_fixture(**{field_name: secret_value})

    rendered = f"{source!r} {source!s}".lower()

    assert secret_value not in rendered
    assert "secret" not in rendered
    assert "token" not in rendered


def test_underlying_quote_requires_symbol_source_and_aware_as_of() -> None:
    with pytest.raises(ValueError, match="symbol"):
        UnderlyingQuoteSnapshot(
            symbol="",
            source=source_fixture(),
            as_of=NOW,
            freshness=QuoteFreshness.FRESH,
        )

    with pytest.raises(ValueError, match="source"):
        UnderlyingQuoteSnapshot(
            symbol="SPX",
            source=None,
            as_of=NOW,
            freshness=QuoteFreshness.FRESH,
        )

    with pytest.raises(ValueError, match="as_of"):
        UnderlyingQuoteSnapshot(
            symbol="SPX",
            source=source_fixture(),
            as_of=datetime(2026, 4, 30, 10, 0),
            freshness=QuoteFreshness.FRESH,
        )


@pytest.mark.parametrize(
    "bid, ask",
    [
        (Decimal("-0.01"), Decimal("10.00")),
        (Decimal("10.00"), Decimal("-0.01")),
    ],
)
def test_underlying_quote_rejects_negative_bid_or_ask(
    bid: Decimal,
    ask: Decimal,
) -> None:
    with pytest.raises(ValueError, match="bid|ask"):
        UnderlyingQuoteSnapshot(
            symbol="SPX",
            source=source_fixture(),
            as_of=NOW,
            freshness=QuoteFreshness.FRESH,
            bid=bid,
            ask=ask,
        )


def test_underlying_quote_rejects_crossed_bid_ask() -> None:
    with pytest.raises(ValueError, match="crossed|ask"):
        UnderlyingQuoteSnapshot(
            symbol="SPX",
            source=source_fixture(),
            as_of=NOW,
            freshness=QuoteFreshness.FRESH,
            bid=Decimal("5001.00"),
            ask=Decimal("5000.00"),
        )


def test_underlying_quote_midpoint_requires_valid_bid_ask() -> None:
    quote = UnderlyingQuoteSnapshot(
        symbol="SPX",
        source=source_fixture(),
        as_of=NOW,
        freshness=QuoteFreshness.FRESH,
        bid=Decimal("5000.00"),
        ask=Decimal("5002.00"),
    )

    assert quote.midpoint == Decimal("5001.00")

    with pytest.raises(ValueError, match="midpoint|bid|ask"):
        UnderlyingQuoteSnapshot(
            symbol="SPX",
            source=source_fixture(),
            as_of=NOW,
            freshness=QuoteFreshness.FRESH,
            last=Decimal("5001.00"),
            provider_mark=Decimal("5001.00"),
        )


@pytest.mark.parametrize(
    "freshness",
    [QuoteFreshness.STALE, QuoteFreshness.MISSING],
)
def test_underlying_quote_stale_or_missing_blocks_derived_prefill(
    freshness: QuoteFreshness,
) -> None:
    quote = UnderlyingQuoteSnapshot(
        symbol="SPX",
        source=source_fixture(),
        as_of=NOW,
        freshness=freshness,
        bid=Decimal("5000.00"),
        ask=Decimal("5002.00"),
    )

    assert quote.blocks_derived_prefill is True


def test_option_contract_key_requires_underlying_and_expiry_date() -> None:
    with pytest.raises(ValueError, match="underlying"):
        option_key_fixture(underlying="")

    with pytest.raises(ValueError, match="expiry_date"):
        option_key_fixture(expiry_date=None)


@pytest.mark.parametrize("strike", [Decimal("0"), Decimal("-1")])
def test_option_contract_key_rejects_nonpositive_strike(strike: Decimal) -> None:
    with pytest.raises(ValueError, match="strike"):
        option_key_fixture(strike=strike)


@pytest.mark.parametrize("right", ["BUY", "SELL", "C", "P", ""])
def test_option_contract_key_limits_right_to_call_or_put(right: str) -> None:
    with pytest.raises(ValueError, match="right"):
        option_key_fixture(right=right)


@pytest.mark.parametrize("product", ["SPX", "SPXW"])
def test_option_contract_key_preserves_spx_vs_spxw_product(product: str) -> None:
    key = option_key_fixture(product=product)

    assert key.product == product


def test_provider_symbol_cannot_replace_canonical_identity() -> None:
    with pytest.raises(ValueError, match="underlying"):
        option_key_fixture(underlying="", provider_symbol="provider-only-symbol")

    with pytest.raises(ValueError, match="expiry_date"):
        option_key_fixture(expiry_date=None, provider_symbol="provider-only-symbol")


def test_option_quote_requires_key_source_and_aware_as_of() -> None:
    with pytest.raises(ValueError, match="key"):
        option_quote_fixture(key=None)

    with pytest.raises(ValueError, match="source"):
        option_quote_fixture(source=None)

    with pytest.raises(ValueError, match="as_of"):
        option_quote_fixture(as_of=datetime(2026, 4, 30, 10, 0))


@pytest.mark.parametrize(
    "bid, ask",
    [
        (Decimal("-0.01"), Decimal("10.00")),
        (Decimal("10.00"), Decimal("-0.01")),
    ],
)
def test_option_quote_rejects_negative_bid_or_ask(
    bid: Decimal,
    ask: Decimal,
) -> None:
    with pytest.raises(ValueError, match="bid|ask"):
        option_quote_fixture(bid=bid, ask=ask)


def test_option_quote_rejects_crossed_quote() -> None:
    with pytest.raises(ValueError, match="crossed|ask"):
        option_quote_fixture(bid=Decimal("10.50"), ask=Decimal("10.00"))


def test_option_quote_locked_quote_is_degraded_not_silently_normal() -> None:
    quote = option_quote_fixture(bid=Decimal("10.00"), ask=Decimal("10.00"))

    assert quote.is_locked is True
    assert quote.is_degraded is True


def test_option_quote_midpoint_requires_bid_ask() -> None:
    quote = option_quote_fixture(bid=Decimal("10.00"), ask=Decimal("10.40"))

    assert quote.midpoint == Decimal("10.20")

    with pytest.raises(ValueError, match="midpoint|bid|ask"):
        option_quote_fixture(
            bid=None,
            ask=None,
            last=Decimal("10.20"),
            provider_mark=Decimal("10.20"),
        )


def test_option_quote_allows_missing_greeks() -> None:
    quote = option_quote_fixture(
        delta=None,
        gamma=None,
        theta=None,
        vega=None,
        iv=None,
    )

    assert quote.delta is None
    assert quote.gamma is None
    assert quote.theta is None
    assert quote.vega is None
    assert quote.iv is None


def test_provider_mark_does_not_replace_midpoint() -> None:
    quote = option_quote_fixture(
        bid=Decimal("10.00"),
        ask=Decimal("10.40"),
        provider_mark=Decimal("12.00"),
    )

    assert quote.midpoint == Decimal("10.20")
    assert quote.provider_mark == Decimal("12.00")
    assert quote.provider_mark != quote.midpoint
