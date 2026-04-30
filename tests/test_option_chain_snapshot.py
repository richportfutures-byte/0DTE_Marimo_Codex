from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from spx_inventory_playbook.market_data import (
    ExpirySnapshot,
    MarketDataSource,
    OptionChainSnapshot,
    OptionContractKey,
    OptionQuoteSnapshot,
    QuoteFreshness,
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


def chain_fixture(**overrides: object) -> OptionChainSnapshot:
    values = {
        "underlying_symbol": "SPX",
        "expiry": expiry_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "contracts": (
            quote_fixture(key=key_fixture(right="CALL")),
            quote_fixture(
                key=key_fixture(right="PUT", provider_symbol="put-provider-symbol")
            ),
        ),
        "is_partial": False,
        "completeness_notes": (),
    }
    values.update(overrides)
    return OptionChainSnapshot(**values)


def test_expiry_snapshot_requires_expiry_date_and_session_date() -> None:
    with pytest.raises(ValueError, match="expiry_date"):
        expiry_fixture(expiry_date=None)

    with pytest.raises(ValueError, match="session_date"):
        expiry_fixture(session_date=None)


def test_expiry_snapshot_rejects_negative_dte() -> None:
    with pytest.raises(ValueError, match="dte"):
        expiry_fixture(dte=-1)


def test_is_0dte_true_only_when_expiry_matches_session_date() -> None:
    with pytest.raises(ValueError, match="is_0dte|expiry_date|session_date"):
        expiry_fixture(
            expiry_date=date(2026, 5, 1),
            session_date=SESSION_DATE,
            dte=1,
            is_0dte=True,
        )


def test_mismatched_0dte_selection_blocks_workflow() -> None:
    expiry = expiry_fixture(
        expiry_date=date(2026, 5, 1),
        session_date=SESSION_DATE,
        dte=1,
        is_0dte=False,
    )

    assert expiry.blocks_0dte_workflow is True


def test_option_chain_requires_nonempty_contracts() -> None:
    with pytest.raises(ValueError, match="contracts"):
        chain_fixture(contracts=())


def test_option_chain_requires_one_underlying() -> None:
    other_underlying = quote_fixture(
        key=key_fixture(
            underlying="SPY",
            provider_symbol="spy-provider-symbol",
        )
    )

    with pytest.raises(ValueError, match="underlying"):
        chain_fixture(contracts=(quote_fixture(), other_underlying))


def test_option_chain_requires_one_expiry() -> None:
    other_expiry_quote = quote_fixture(
        key=key_fixture(
            expiry_date=date(2026, 5, 1),
            provider_symbol="next-expiry-provider-symbol",
        )
    )

    with pytest.raises(ValueError, match="expiry"):
        chain_fixture(contracts=(quote_fixture(), other_expiry_quote))


def test_option_chain_rejects_duplicate_contract_keys() -> None:
    quote = quote_fixture()

    with pytest.raises(ValueError, match="duplicate|unique"):
        chain_fixture(contracts=(quote, quote))


def test_partial_chain_requires_completeness_notes() -> None:
    with pytest.raises(ValueError, match="completeness_notes"):
        chain_fixture(is_partial=True, completeness_notes=())


def test_partial_chain_degrades_or_blocks_ranking() -> None:
    chain = chain_fixture(
        is_partial=True,
        completeness_notes=("Missing put wing near underlying price.",),
    )

    assert chain.is_partial is True
    assert chain.is_degraded is True
    assert chain.blocks_structure_ranking is True
