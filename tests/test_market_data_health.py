import pytest

from spx_inventory_playbook.market_data import MarketDataHealth


def test_market_data_health_ok_requires_no_blockers() -> None:
    health = MarketDataHealth(
        status="OK",
        blockers=(),
        warnings=(),
        missing_fields=(),
        stale_fields=(),
    )

    assert health.status == "OK"


def test_market_data_health_rejects_ok_with_blockers() -> None:
    with pytest.raises(ValueError, match="BLOCKED|blockers"):
        MarketDataHealth(
            status="OK",
            blockers=("Chain is missing.",),
            warnings=(),
            missing_fields=("contracts",),
            stale_fields=(),
        )


def test_market_data_health_rejects_degraded_with_blockers() -> None:
    with pytest.raises(ValueError, match="BLOCKED|blockers"):
        MarketDataHealth(
            status="DEGRADED",
            blockers=("Underlying quote is stale.",),
            warnings=("Quote freshness warning.",),
            missing_fields=(),
            stale_fields=("underlying_quote",),
        )


def test_market_data_health_degraded_allows_warnings_without_blockers() -> None:
    health = MarketDataHealth(
        status="DEGRADED",
        blockers=(),
        warnings=("Partial chain; ATM neighborhood incomplete.",),
        missing_fields=("contracts",),
        stale_fields=(),
    )

    assert health.status == "DEGRADED"
    assert health.warnings
    assert not health.blockers


def test_market_data_health_blocked_required_when_blockers_exist() -> None:
    health = MarketDataHealth(
        status="BLOCKED",
        blockers=("Underlying quote is stale.",),
        warnings=(),
        missing_fields=(),
        stale_fields=("underlying_quote",),
    )

    assert health.status == "BLOCKED"


def test_market_data_health_requires_explicit_missing_and_stale_fields() -> None:
    health = MarketDataHealth(
        status="BLOCKED",
        blockers=("Underlying quote is stale and option chain is missing.",),
        warnings=(),
        missing_fields=("contracts",),
        stale_fields=("underlying_quote",),
    )

    assert health.missing_fields == ("contracts",)
    assert health.stale_fields == ("underlying_quote",)
