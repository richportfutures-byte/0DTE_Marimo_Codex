"""Freshness classification for option-chain provider results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from spx_inventory_playbook.adapters.option_chain_provider import (
    MarketDataProviderState,
    OptionChainProviderResult,
)


OptionChainFreshnessStatus = Literal[
    "fresh",
    "aging",
    "stale",
    "invalid",
    "unavailable",
    "static_fixture",
]


@dataclass(frozen=True)
class OptionChainFreshnessThresholds:
    fresh_seconds: float = 15.0
    aging_seconds: float = 60.0


@dataclass(frozen=True)
class OptionChainFreshness:
    status: OptionChainFreshnessStatus
    source_type: str
    loaded_at: datetime | None
    age_seconds: float | None
    reason_code: str | None = None


def classify_option_chain_freshness(
    provider_result: OptionChainProviderResult | None,
    *,
    now: datetime | None = None,
    thresholds: OptionChainFreshnessThresholds = OptionChainFreshnessThresholds(),
) -> OptionChainFreshness:
    """Classify provider data recency without implying fixture data is live."""

    if provider_result is None:
        return OptionChainFreshness(
            status="unavailable",
            source_type="unknown",
            loaded_at=None,
            age_seconds=None,
            reason_code="provider_result_unavailable",
        )

    if provider_result.status == "error":
        return OptionChainFreshness(
            status="invalid",
            source_type=provider_result.source_type,
            loaded_at=provider_result.loaded_at,
            age_seconds=None,
            reason_code=provider_result.reason_code or "provider_error",
        )

    if provider_result.status == "unavailable":
        return OptionChainFreshness(
            status="unavailable",
            source_type=provider_result.source_type,
            loaded_at=provider_result.loaded_at,
            age_seconds=None,
            reason_code=provider_result.reason_code or "provider_unavailable",
        )

    if provider_result.is_static_source:
        return OptionChainFreshness(
            status="static_fixture",
            source_type=provider_result.source_type,
            loaded_at=provider_result.loaded_at,
            age_seconds=None,
            reason_code="static_fixture_not_live",
        )

    if provider_result.loaded_at is None:
        return OptionChainFreshness(
            status="invalid",
            source_type=provider_result.source_type,
            loaded_at=None,
            age_seconds=None,
            reason_code="loaded_at_unavailable",
        )

    now_value = _as_utc(now or datetime.now(timezone.utc))
    loaded_at = _as_utc(provider_result.loaded_at)
    age_seconds = max(0.0, (now_value - loaded_at).total_seconds())
    if age_seconds <= thresholds.fresh_seconds:
        status: OptionChainFreshnessStatus = "fresh"
    elif age_seconds <= thresholds.aging_seconds:
        status = "aging"
    else:
        status = "stale"
    return OptionChainFreshness(
        status=status,
        source_type=provider_result.source_type,
        loaded_at=provider_result.loaded_at,
        age_seconds=age_seconds,
    )


def classify_market_data_provider_state(
    provider_result: OptionChainProviderResult | None,
    freshness: OptionChainFreshness,
) -> MarketDataProviderState:
    """Map provider/freshness details into the explicit R5 provider states."""

    if provider_result is None:
        return MarketDataProviderState.LIVE_UNAVAILABLE

    if provider_result.source_type == "fixture" or provider_result.is_static_source:
        return MarketDataProviderState.FIXTURE

    if provider_result.source_type != "live":
        return MarketDataProviderState.LIVE_UNAVAILABLE

    if provider_result.status == "unavailable":
        return MarketDataProviderState.LIVE_UNAVAILABLE

    if provider_result.status == "error":
        if provider_result.reason_code in {
            "response_parse_error",
            "fixture_parse_error",
            "live_harness_error",
        }:
            return MarketDataProviderState.LIVE_PARSE_ERROR
        return MarketDataProviderState.LIVE_UNAVAILABLE

    if freshness.status == "stale":
        return MarketDataProviderState.LIVE_STALE
    if freshness.status in {"fresh", "aging"}:
        return MarketDataProviderState.LIVE_FRESH
    if freshness.status == "invalid":
        return MarketDataProviderState.LIVE_PARSE_ERROR
    return MarketDataProviderState.LIVE_UNAVAILABLE


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


__all__ = [
    "OptionChainFreshness",
    "OptionChainFreshnessStatus",
    "OptionChainFreshnessThresholds",
    "classify_market_data_provider_state",
    "classify_option_chain_freshness",
]
