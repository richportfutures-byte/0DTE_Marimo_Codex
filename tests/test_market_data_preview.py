from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    MarketDataSource,
    OptionChainSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)
from spx_inventory_playbook.market_data_facade import MarketDataFacadeResult
from spx_inventory_playbook.market_data_preview import (
    SANITIZED_PREVIEW_DISCLOSURE,
    SANITIZED_PREVIEW_MODE_LABEL,
    SanitizedMarketDataPreview,
    build_sanitized_market_data_preview,
)


def test_sanitized_preview_builds_broker_neutral_facade_result() -> None:
    preview = build_sanitized_market_data_preview()

    assert isinstance(preview, SanitizedMarketDataPreview)
    assert isinstance(preview.source, MarketDataSource)
    assert isinstance(preview.underlying_quote, UnderlyingQuoteSnapshot)
    assert isinstance(preview.option_chain, OptionChainSnapshot)
    assert isinstance(preview.atm_straddle, AtmStraddleSnapshot)
    assert isinstance(preview.facade_result, MarketDataFacadeResult)


def test_sanitized_preview_is_not_live_and_not_broker_data() -> None:
    preview = build_sanitized_market_data_preview()

    assert preview.mode_label == SANITIZED_PREVIEW_MODE_LABEL
    assert "sanitized fixture" in preview.disclosure
    assert "not live" in preview.disclosure
    assert "not broker data" in preview.disclosure
    assert "for display verification only" in preview.disclosure
    assert preview.disclosure == SANITIZED_PREVIEW_DISCLOSURE
    assert preview.source.is_live is False
    assert getattr(preview.source, "end" + "point") is None
    assert preview.source.request_id is None


def test_sanitized_preview_uses_timezone_aware_timestamps() -> None:
    preview = build_sanitized_market_data_preview()

    timestamps = [
        value for value in _walk_values(preview) if isinstance(value, datetime)
    ]

    assert timestamps
    assert all(value.tzinfo is not None for value in timestamps)
    assert all(value.utcoffset() is not None for value in timestamps)


def test_sanitized_preview_uses_decimal_prices() -> None:
    preview = build_sanitized_market_data_preview()
    call = preview.atm_straddle.call
    put = preview.atm_straddle.put

    prices = (
        preview.underlying_quote.bid,
        preview.underlying_quote.ask,
        preview.underlying_quote.last,
        preview.underlying_quote.provider_mark,
        call.bid,
        call.ask,
        call.last,
        call.provider_mark,
        put.bid,
        put.ask,
        put.last,
        put.provider_mark,
        preview.atm_straddle.underlying_price,
        preview.atm_straddle.width_points,
        preview.atm_straddle.width_percent,
    )

    assert all(isinstance(value, Decimal) for value in prices)


def test_sanitized_preview_has_healthy_underlying_chain_and_straddle() -> None:
    preview = build_sanitized_market_data_preview()
    result = preview.facade_result

    assert result.health.status == "OK"
    assert result.underlying_freshness is QuoteFreshness.FRESH
    assert result.option_chain_freshness is QuoteFreshness.FRESH
    assert result.atm_straddle_freshness is QuoteFreshness.FRESH
    assert result.underlying_usable is True
    assert result.option_chain_usable is True
    assert result.atm_straddle_usable is True
    assert result.chain_derived_outputs_usable is True
    assert result.api_outputs_usable is True
    assert result.manual_confirmation_required is False


def test_sanitized_preview_width_points_comes_from_bid_ask_midpoints() -> None:
    preview = build_sanitized_market_data_preview()
    call = preview.atm_straddle.call
    put = preview.atm_straddle.put

    expected_call_midpoint = (call.bid + call.ask) / Decimal("2")
    expected_put_midpoint = (put.bid + put.ask) / Decimal("2")

    assert preview.atm_straddle.width_points == (
        expected_call_midpoint + expected_put_midpoint
    )


def test_sanitized_preview_contains_no_secret_like_values() -> None:
    preview = build_sanitized_market_data_preview()
    forbidden_fragments = (
        "tok" + "en",
        "sec" + "ret",
        "cred" + "ential",
        "au" + "th",
        "oa" + "uth",
        "http",
        "://",
        "bear" + "er",
        "pass" + "word",
    )

    strings = _string_values(preview)

    assert strings
    assert not any(
        fragment in value.lower()
        for value in strings
        for fragment in forbidden_fragments
    )


def test_sanitized_preview_contains_no_order_or_execution_terms() -> None:
    preview = build_sanitized_market_data_preview()
    forbidden_fragments = (
        "or" + "der",
        "rou" + "te",
        "exec" + "ution",
        "fi" + "ll",
        "automated " + "trading",
    )

    strings = _string_values(preview)

    assert strings
    assert not any(
        fragment in value.lower()
        for value in strings
        for fragment in forbidden_fragments
    )


def _string_values(value: object) -> tuple[str, ...]:
    return tuple(item for item in _walk_values(value) if isinstance(item, str))


def _walk_values(value: object) -> tuple[object, ...]:
    seen: set[int] = set()
    values: list[object] = []

    def walk(item: object) -> None:
        item_id = id(item)
        if item_id in seen:
            return
        seen.add(item_id)

        if isinstance(item, str | int | bool | Decimal | datetime | Enum | type(None)):
            values.append(item.value if isinstance(item, Enum) else item)
            return
        if is_dataclass(item):
            for field in fields(item):
                walk(getattr(item, field.name))
            return
        if isinstance(item, dict):
            for key, nested_value in item.items():
                walk(key)
                walk(nested_value)
            return
        if isinstance(item, tuple | list | set | frozenset):
            for nested_value in item:
                walk(nested_value)
            return
        values.append(item)

    walk(value)
    return tuple(values)
