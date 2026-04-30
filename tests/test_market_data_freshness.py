from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from spx_inventory_playbook.market_data import (
    MarketDataSource,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)


NOW = datetime(2026, 4, 30, 10, 0, tzinfo=ZoneInfo("America/New_York"))


def source_fixture(**overrides: object) -> MarketDataSource:
    values = {
        "provider": "fixture",
        "adapter": "manual_fixture",
        "retrieved_at": NOW,
    }
    values.update(overrides)
    return MarketDataSource(**values)


def underlying_fixture(**overrides: object) -> UnderlyingQuoteSnapshot:
    values = {
        "symbol": "SPX",
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("5000.00"),
        "ask": Decimal("5002.00"),
    }
    values.update(overrides)
    return UnderlyingQuoteSnapshot(**values)


def test_quote_freshness_values_are_canonical() -> None:
    assert {freshness.value for freshness in QuoteFreshness} == {
        "fresh",
        "stale",
        "missing",
        "unknown",
    }


@pytest.mark.parametrize(
    "freshness",
    [QuoteFreshness.MISSING, QuoteFreshness.UNKNOWN],
)
def test_missing_and_unknown_freshness_are_not_fresh(
    freshness: QuoteFreshness,
) -> None:
    assert freshness is not QuoteFreshness.FRESH
    assert not freshness.is_fresh


def test_retrieved_at_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="retrieved_at"):
        source_fixture(retrieved_at=datetime(2026, 4, 30, 10, 0))


def test_as_of_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="as_of"):
        underlying_fixture(as_of=datetime(2026, 4, 30, 10, 0))


def test_snapshot_freshness_uses_explicit_freshness_state() -> None:
    fresh = underlying_fixture(freshness=QuoteFreshness.FRESH)
    stale = underlying_fixture(
        as_of=NOW - timedelta(minutes=30),
        freshness=QuoteFreshness.STALE,
    )

    assert fresh.freshness is QuoteFreshness.FRESH
    assert stale.freshness is QuoteFreshness.STALE
    assert stale.blocks_derived_prefill is True
