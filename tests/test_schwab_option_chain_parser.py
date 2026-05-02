from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest

from spx_inventory_playbook.adapters.schwab_option_chain import (
    SchwabOptionChainParserError,
    parse_schwab_option_chain,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)


def load_raw_chain() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def raw_contract_count(payload: dict[str, object]) -> int:
    count = 0
    for side_key in ("callExpDateMap", "putExpDateMap"):
        side_map = payload[side_key]
        assert isinstance(side_map, dict)
        for strike_map in side_map.values():
            assert isinstance(strike_map, dict)
            for contracts in strike_map.values():
                assert isinstance(contracts, list)
                count += len(contracts)
    return count


def parsed_contracts() -> tuple[object, ...]:
    snapshot = parse_schwab_option_chain(load_raw_chain())
    return tuple(contract for expiry in snapshot.expirations for contract in expiry.contracts)


def test_captured_fixture_parses_successfully_and_preserves_provider_symbol() -> None:
    snapshot = parse_schwab_option_chain(load_raw_chain())

    assert snapshot.provider_symbol == "$SPX"
    assert snapshot.captured_status == "SUCCESS"
    assert snapshot.is_delayed is False


def test_underlying_symbol_normalizes_to_spx() -> None:
    snapshot = parse_schwab_option_chain(load_raw_chain())

    assert snapshot.underlying is not None
    assert snapshot.underlying.symbol == "SPX"
    assert snapshot.underlying_symbol == "SPX"
    assert snapshot.underlying.bid is not None
    assert snapshot.underlying.ask is not None
    assert snapshot.underlying.quote_time_ms is not None
    assert snapshot.underlying.trade_time_ms is not None


def test_walks_both_call_and_put_maps_and_preserves_raw_contract_count() -> None:
    payload = load_raw_chain()
    snapshot = parse_schwab_option_chain(payload)
    contracts = tuple(contract for expiry in snapshot.expirations for contract in expiry.contracts)

    assert len(contracts) == raw_contract_count(payload)
    assert {contract.side for contract in contracts} == {"CALL", "PUT"}


def test_expiration_key_and_strike_keys_parse_to_normalized_values() -> None:
    snapshot = parse_schwab_option_chain(load_raw_chain())

    assert len(snapshot.expirations) == 1
    expiration = snapshot.expirations[0]
    assert expiration.expiration_date == date(2026, 5, 4)
    assert expiration.days_to_expiration == 2
    assert {contract.expiration for contract in expiration.contracts} == {date(2026, 5, 4)}
    assert {contract.days_to_expiration for contract in expiration.contracts} == {2}
    assert {contract.strike for contract in expiration.contracts} == {7230.0, 7235.0}


def test_put_call_maps_to_call_and_put_sides() -> None:
    contracts = parsed_contracts()

    assert {contract.side for contract in contracts} == {"CALL", "PUT"}
    assert sum(1 for contract in contracts if contract.side == "CALL") == 2
    assert sum(1 for contract in contracts if contract.side == "PUT") == 2


def test_quote_fields_map_correctly() -> None:
    call = next(
        contract
        for contract in parsed_contracts()
        if contract.side == "CALL" and contract.strike == 7235.0
    )

    assert call.bid == pytest.approx(14.3)
    assert call.ask == pytest.approx(14.7)
    assert call.last == pytest.approx(17.2)
    assert call.mark == pytest.approx(14.5)
    assert call.quote_time_ms is not None
    assert call.trade_time_ms is not None


def test_greeks_implied_volatility_volume_and_open_interest_map_correctly() -> None:
    put = next(
        contract
        for contract in parsed_contracts()
        if contract.side == "PUT" and contract.strike == 7230.0
    )

    assert put.delta == pytest.approx(-0.578)
    assert put.gamma == pytest.approx(0.007)
    assert put.theta == pytest.approx(-6.357)
    assert put.vega == pytest.approx(2.524)
    assert put.implied_volatility == pytest.approx(8.609)
    assert put.volume == 5246
    assert put.open_interest == 0


def test_missing_or_null_optional_quote_and_greek_fields_are_tolerated() -> None:
    payload = copy.deepcopy(load_raw_chain())
    call_contract = payload["callExpDateMap"]["2026-05-04:2"]["7230.0"][0]
    assert isinstance(call_contract, dict)
    for field_name in (
        "bid",
        "ask",
        "last",
        "mark",
        "delta",
        "gamma",
        "theta",
        "vega",
        "volatility",
        "totalVolume",
        "openInterest",
    ):
        call_contract.pop(field_name, None)
    call_contract["quoteTimeInLong"] = None
    call_contract["tradeTimeInLong"] = None

    snapshot = parse_schwab_option_chain(payload)
    contract = snapshot.expirations[0].contracts[0]

    assert contract.bid is None
    assert contract.ask is None
    assert contract.last is None
    assert contract.mark is None
    assert contract.delta is None
    assert contract.gamma is None
    assert contract.theta is None
    assert contract.vega is None
    assert contract.implied_volatility is None
    assert contract.volume is None
    assert contract.open_interest is None
    assert contract.quote_time_ms is None
    assert contract.trade_time_ms is None


def test_malformed_top_level_maps_raise_clear_parser_error() -> None:
    payload = load_raw_chain()
    payload["callExpDateMap"] = ["not", "a", "map"]

    with pytest.raises(SchwabOptionChainParserError, match="callExpDateMap.*object"):
        parse_schwab_option_chain(payload)


def test_strike_price_mismatch_raises_clear_parser_error() -> None:
    payload = copy.deepcopy(load_raw_chain())
    call_contract = payload["callExpDateMap"]["2026-05-04:2"]["7230.0"][0]
    assert isinstance(call_contract, dict)
    call_contract["strikePrice"] = 9999.0

    with pytest.raises(SchwabOptionChainParserError, match="strikePrice.*strike key"):
        parse_schwab_option_chain(payload)


def test_parser_errors_do_not_expose_raw_payload_bodies() -> None:
    payload = {
        "symbol": "$SPX",
        "callExpDateMap": "secret-token-value raw-payload-body",
        "putExpDateMap": {},
    }

    with pytest.raises(SchwabOptionChainParserError) as exc_info:
        parse_schwab_option_chain(payload)

    rendered = f"{exc_info.value!r} {exc_info.value!s}"
    assert "secret-token-value" not in rendered
    assert "raw-payload-body" not in rendered
