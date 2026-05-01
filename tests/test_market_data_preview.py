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
    PREVIEW_SCENARIO_NAMES,
    SANITIZED_PREVIEW_DISCLOSURE,
    SANITIZED_PREVIEW_MODE_LABEL,
    SanitizedMarketDataPreview,
    build_market_data_preview_scenario,
    build_sanitized_market_data_preview,
)


def test_preview_scenario_names_are_canonical() -> None:
    assert PREVIEW_SCENARIO_NAMES == (
        "default_fail_closed",
        "healthy_preview",
        "stale_underlying",
        "partial_chain",
        "locked_liquidity",
        "missing_atm_straddle",
    )


def test_default_fail_closed_scenario_blocks_api_outputs() -> None:
    preview = build_market_data_preview_scenario("default_fail_closed")
    result = preview.facade_result

    assert preview.underlying_quote is None
    assert preview.option_chain is None
    assert preview.atm_straddle is None
    assert result.health.status == "BLOCKED"
    assert result.api_outputs_usable is False
    assert result.manual_confirmation_required is True


def test_healthy_preview_scenario_is_usable_but_non_live() -> None:
    preview = build_market_data_preview_scenario("healthy_preview")
    result = preview.facade_result

    assert preview.source is not None
    assert preview.source.is_live is False
    assert result.health.status == "OK"
    assert result.underlying_usable is True
    assert result.option_chain_usable is True
    assert result.atm_straddle_usable is True
    assert result.api_outputs_usable is True


def test_stale_underlying_scenario_requires_manual_confirmation() -> None:
    preview = build_market_data_preview_scenario("stale_underlying")
    result = preview.facade_result

    assert preview.underlying_quote is not None
    assert preview.underlying_quote.freshness is QuoteFreshness.STALE
    assert result.health.status == "BLOCKED"
    assert "underlying_quote" in result.health.stale_fields
    assert result.underlying_usable is False
    assert result.chain_derived_outputs_usable is False
    assert result.api_outputs_usable is False
    assert result.manual_confirmation_required is True


def test_partial_chain_scenario_preserves_completeness_notes() -> None:
    preview = build_market_data_preview_scenario("partial_chain")
    result = preview.facade_result

    assert preview.option_chain is not None
    assert preview.option_chain.is_partial is True
    assert preview.option_chain.completeness_notes
    assert preview.option_chain.completeness_notes[0] in result.health.warnings
    assert result.health.status == "DEGRADED"
    assert result.option_chain_usable is False
    assert result.api_outputs_usable is False


def test_locked_liquidity_scenario_degrades_readiness() -> None:
    preview = build_market_data_preview_scenario("locked_liquidity")
    result = preview.facade_result

    assert preview.option_chain is not None
    assert any(quote.is_locked for quote in preview.option_chain.contracts)
    assert result.health.status == "DEGRADED"
    assert result.option_chain_usable is False
    assert result.api_outputs_usable is False
    assert any("Locked option quote" in warning for warning in result.health.warnings)


def test_missing_atm_straddle_scenario_blocks_width_outputs() -> None:
    preview = build_market_data_preview_scenario("missing_atm_straddle")
    result = preview.facade_result

    assert preview.underlying_quote is not None
    assert preview.option_chain is not None
    assert preview.atm_straddle is None
    assert result.health.status == "DEGRADED"
    assert result.atm_straddle_usable is False
    assert result.api_outputs_usable is False
    assert "atm_straddle" in result.health.missing_fields


def test_all_preview_scenarios_are_sanitized_and_not_broker_data() -> None:
    for preview in _all_scenarios():
        assert preview.disclosure == SANITIZED_PREVIEW_DISCLOSURE
        assert "sanitized fixture" in preview.disclosure
        assert "not live" in preview.disclosure
        assert "not broker data" in preview.disclosure
        if preview.source is not None:
            assert preview.source.is_live is False
            assert getattr(preview.source, "end" + "point") is None
            assert preview.source.request_id is None


def test_all_preview_scenarios_use_canonical_facade_result() -> None:
    for preview in _all_scenarios():
        assert isinstance(preview.facade_result, MarketDataFacadeResult)
        assert preview.scenario_name in PREVIEW_SCENARIO_NAMES
        if preview.underlying_quote is not None:
            assert isinstance(preview.underlying_quote, UnderlyingQuoteSnapshot)
        if preview.option_chain is not None:
            assert isinstance(preview.option_chain, OptionChainSnapshot)
        if preview.atm_straddle is not None:
            assert isinstance(preview.atm_straddle, AtmStraddleSnapshot)


def test_preview_scenarios_contain_no_secret_like_values() -> None:
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

    strings = tuple(
        string_value
        for preview in _all_scenarios()
        for string_value in _string_values(preview)
    )

    assert strings
    assert not any(
        fragment in value.lower()
        for value in strings
        for fragment in forbidden_fragments
    )


def test_preview_scenarios_contain_no_order_or_execution_terms() -> None:
    forbidden_fragments = (
        "or" + "der",
        "rou" + "te",
        "exec" + "ution",
        "fi" + "ll",
        "automated " + "trading",
    )

    strings = tuple(
        string_value
        for preview in _all_scenarios()
        for string_value in _string_values(preview)
    )

    assert strings
    assert not any(
        fragment in value.lower()
        for value in strings
        for fragment in forbidden_fragments
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


def _all_scenarios() -> tuple[SanitizedMarketDataPreview, ...]:
    return tuple(
        build_market_data_preview_scenario(scenario_name)
        for scenario_name in PREVIEW_SCENARIO_NAMES
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
