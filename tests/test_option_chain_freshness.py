from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from spx_inventory_playbook.adapters.option_chain_freshness import (
    OptionChainFreshnessThresholds,
    classify_option_chain_freshness,
)
from spx_inventory_playbook.adapters.option_chain_provider import (
    FixtureOptionChainProvider,
    OptionChainProviderResult,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)
NOW = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)


def provider_result(
    *,
    status: str = "available",
    loaded_at: datetime | None = NOW,
    source_type: str = "live",
    is_static_source: bool = False,
    reason_code: str | None = None,
) -> OptionChainProviderResult:
    return OptionChainProviderResult(
        provider_name="sample_provider",
        source_label="sample",
        source_type=source_type,
        status=status,
        reason_code=reason_code,
        loaded_at=loaded_at,
        is_static_source=is_static_source,
    )


def test_freshness_classifier_returns_static_fixture_for_fixture_provider_result() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH, clock=lambda: NOW).get_spx_0dte_selection()

    freshness = classify_option_chain_freshness(result, now=NOW)

    assert freshness.status == "static_fixture"
    assert freshness.source_type == "fixture"
    assert freshness.loaded_at == NOW
    assert freshness.age_seconds is None
    assert freshness.reason_code == "static_fixture_not_live"


def test_freshness_classifier_uses_configured_thresholds_for_non_fixture_results() -> None:
    thresholds = OptionChainFreshnessThresholds(fresh_seconds=15, aging_seconds=60)

    fresh = classify_option_chain_freshness(
        provider_result(loaded_at=NOW - timedelta(seconds=15)),
        now=NOW,
        thresholds=thresholds,
    )
    aging = classify_option_chain_freshness(
        provider_result(loaded_at=NOW - timedelta(seconds=45)),
        now=NOW,
        thresholds=thresholds,
    )
    stale = classify_option_chain_freshness(
        provider_result(loaded_at=NOW - timedelta(seconds=61)),
        now=NOW,
        thresholds=thresholds,
    )

    assert fresh.status == "fresh"
    assert fresh.age_seconds == 15
    assert aging.status == "aging"
    assert aging.age_seconds == 45
    assert stale.status == "stale"
    assert stale.age_seconds == 61


def test_freshness_classifier_returns_invalid_or_unavailable_for_bad_results() -> None:
    invalid = classify_option_chain_freshness(
        provider_result(status="error", reason_code="fixture_json_malformed"),
        now=NOW,
    )
    unavailable = classify_option_chain_freshness(None, now=NOW)
    provider_unavailable = classify_option_chain_freshness(
        provider_result(status="unavailable", reason_code="live_provider_not_implemented"),
        now=NOW,
    )

    assert invalid.status == "invalid"
    assert invalid.reason_code == "fixture_json_malformed"
    assert unavailable.status == "unavailable"
    assert unavailable.reason_code == "provider_result_unavailable"
    assert provider_unavailable.status == "unavailable"
    assert provider_unavailable.reason_code == "live_provider_not_implemented"


def test_fixture_provider_result_exposes_static_source_and_loaded_timestamp() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH, clock=lambda: NOW).get_spx_0dte_selection()

    assert result.status == "available"
    assert result.source_type == "fixture"
    assert result.is_static_source is True
    assert result.loaded_at == NOW
    assert result.source_label == "fixture"


def test_provider_result_repr_does_not_expose_raw_payload_body() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH, clock=lambda: NOW).get_spx_0dte_selection()

    rendered = repr(result)

    assert "callExpDateMap" not in rendered
    assert "putExpDateMap" not in rendered
    assert "SPXW  " not in rendered
    assert "loaded_at='2026-05-02T12:00:00+00:00'" in rendered
