import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    MarketDataHealth,
    OptionChainSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)
from spx_inventory_playbook.adapters.schwab_market_data import SchwabMarketDataMapper


FIXTURES = Path(__file__).parent / "fixtures" / "market_data" / "schwab"
RETRIEVED_AT = datetime(2026, 4, 30, 10, 0, tzinfo=ZoneInfo("America/New_York"))
SESSION_DATE = date(2026, 4, 30)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mapper() -> SchwabMarketDataMapper:
    return SchwabMarketDataMapper()


def test_maps_valid_underlying_quote_to_canonical_snapshot() -> None:
    snapshot = mapper().map_underlying_quote(
        load_fixture("underlying_quote.valid.json"),
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    assert isinstance(snapshot, UnderlyingQuoteSnapshot)
    assert snapshot.symbol == "SPX"
    assert snapshot.source.provider == "schwab"
    assert snapshot.source.adapter == "schwab_market_data_fixture_mapper"
    assert snapshot.freshness is QuoteFreshness.FRESH
    assert snapshot.bid == Decimal("5000.00")
    assert snapshot.ask == Decimal("5001.00")
    assert snapshot.provider_mark == Decimal("5000.50")
    assert snapshot.midpoint == Decimal("5000.50")
    assert snapshot.blocks_derived_prefill is False


def test_mark_only_underlying_fails_closed_without_bid_ask_midpoint() -> None:
    with pytest.raises(ValueError, match="bid|ask|midpoint"):
        mapper().map_underlying_quote(
            load_fixture("option_chain_0dte.mark_only_underlying.json"),
            retrieved_at=RETRIEVED_AT,
            max_age_seconds=30,
        )


def test_maps_valid_0dte_option_chain_to_canonical_snapshot() -> None:
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.valid.json"),
        session_date=SESSION_DATE,
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    assert isinstance(chain, OptionChainSnapshot)
    assert chain.underlying_symbol == "SPX"
    assert chain.expiry.expiry_date == SESSION_DATE
    assert chain.expiry.session_date == SESSION_DATE
    assert chain.expiry.is_0dte is True
    assert chain.expiry.settlement == "PM"
    assert chain.freshness is QuoteFreshness.FRESH
    assert chain.is_partial is False
    assert len(chain.contracts) == 4
    assert {quote.key.right for quote in chain.contracts} == {"CALL", "PUT"}
    assert {quote.key.product for quote in chain.contracts} == {"SPXW"}
    assert {quote.key.expiry_date for quote in chain.contracts} == {SESSION_DATE}
    assert chain.contracts[0].bid == Decimal("10.00")
    assert chain.contracts[0].ask == Decimal("10.40")
    assert chain.contracts[0].midpoint == Decimal("10.20")
    assert chain.contracts[0].bid_size == 12
    assert chain.contracts[0].delta == Decimal("0.51")


def test_partial_chain_maps_to_degraded_chain_with_notes() -> None:
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.partial.json"),
        session_date=SESSION_DATE,
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    assert chain.is_partial is True
    assert chain.is_degraded is True
    assert chain.blocks_structure_ranking is True
    assert chain.completeness_notes == (
        "Fixture chain intentionally omits neighboring put contract.",
    )


def test_crossed_option_quote_fails_closed() -> None:
    with pytest.raises(ValueError, match="crossed|ask"):
        mapper().map_option_chain(
            load_fixture("option_chain_0dte.crossed_quote.json"),
            session_date=SESSION_DATE,
            retrieved_at=RETRIEVED_AT,
            max_age_seconds=30,
        )


def test_locked_option_quote_maps_as_degraded_not_normal() -> None:
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.locked_quote.json"),
        session_date=SESSION_DATE,
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    locked = next(quote for quote in chain.contracts if quote.key.right == "CALL")
    assert locked.is_locked is True
    assert locked.is_degraded is True


def test_missing_greeks_are_allowed_and_remain_unknown() -> None:
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.missing_greeks.json"),
        session_date=SESSION_DATE,
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    for quote in chain.contracts:
        assert quote.delta is None
        assert quote.gamma is None
        assert quote.theta is None
        assert quote.vega is None
        assert quote.iv is None


def test_mismatched_expiry_blocks_0dte_chain_mapping() -> None:
    with pytest.raises(ValueError, match="0DTE|expiry|session_date"):
        mapper().map_option_chain(
            load_fixture("option_chain_0dte.mismatched_expiry.json"),
            session_date=SESSION_DATE,
            retrieved_at=RETRIEVED_AT,
            max_age_seconds=30,
        )


def test_stale_quote_timestamp_maps_to_stale_freshness() -> None:
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.valid.json"),
        session_date=SESSION_DATE,
        retrieved_at=datetime(2026, 4, 30, 10, 2, tzinfo=ZoneInfo("America/New_York")),
        max_age_seconds=30,
    )

    assert chain.freshness is QuoteFreshness.STALE
    assert chain.is_degraded is True
    assert chain.blocks_structure_ranking is True


def test_derives_atm_straddle_from_valid_chain_and_underlying() -> None:
    underlying = mapper().map_underlying_quote(
        load_fixture("underlying_quote.valid.json"),
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )
    chain = mapper().map_option_chain(
        load_fixture("option_chain_0dte.valid.json"),
        session_date=SESSION_DATE,
        retrieved_at=RETRIEVED_AT,
        max_age_seconds=30,
    )

    straddle = mapper().derive_atm_straddle(chain, underlying)

    assert isinstance(straddle, AtmStraddleSnapshot)
    assert straddle.underlying_symbol == "SPX"
    assert straddle.call.key.strike == Decimal("5000")
    assert straddle.put.key.strike == Decimal("5000")
    assert straddle.width_points == Decimal("20.20")
    assert straddle.width_percent == Decimal("0.00404")
    assert straddle.blocks_derived_outputs is False


def test_market_data_health_blocks_when_blockers_exist() -> None:
    health = mapper().map_market_data_health(
        blockers=("Underlying quote missing bid/ask.",),
        warnings=(),
        missing_fields=("underlying.bid", "underlying.ask"),
        stale_fields=(),
    )

    assert isinstance(health, MarketDataHealth)
    assert health.status == "BLOCKED"
    assert health.blockers == ("Underlying quote missing bid/ask.",)
    assert health.missing_fields == ("underlying.bid", "underlying.ask")


def test_market_data_health_degrades_for_partial_chain_warning() -> None:
    health = mapper().map_market_data_health(
        blockers=(),
        warnings=("Option chain is partial.",),
        missing_fields=("contracts.neighboring_put",),
        stale_fields=(),
    )

    assert health.status == "DEGRADED"
    assert health.warnings == ("Option chain is partial.",)
