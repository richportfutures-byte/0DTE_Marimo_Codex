"""Pure parser for raw Schwab option-chain payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal


class SchwabOptionChainParserError(ValueError):
    """Raised when a Schwab option-chain payload shape cannot be parsed."""


@dataclass(frozen=True)
class SchwabUnderlyingQuote:
    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    mark: float | None
    quote_time_ms: int | None
    trade_time_ms: int | None


@dataclass(frozen=True)
class SchwabOptionContract:
    provider_symbol: str
    side: Literal["CALL", "PUT"]
    expiration: date
    days_to_expiration: int | None
    strike: float
    bid: float | None
    ask: float | None
    last: float | None
    mark: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    implied_volatility: float | None
    volume: int | None
    open_interest: int | None
    quote_time_ms: int | None
    trade_time_ms: int | None


@dataclass(frozen=True)
class SchwabOptionExpiration:
    expiration_date: date
    days_to_expiration: int | None
    contracts: tuple[SchwabOptionContract, ...]


@dataclass(frozen=True)
class SchwabOptionChainSnapshot:
    provider_symbol: str
    underlying_symbol: str
    underlying: SchwabUnderlyingQuote | None
    expirations: tuple[SchwabOptionExpiration, ...]
    is_delayed: bool | None
    captured_status: str | None


def parse_schwab_option_chain(payload: object) -> SchwabOptionChainSnapshot:
    """Parse a raw Schwab option-chain payload into a minimal normalized shape."""

    root = _require_mapping(payload, "payload")
    provider_symbol = _optional_text(root.get("symbol"), "symbol") or ""
    if not provider_symbol:
        raise SchwabOptionChainParserError("symbol is required.")

    underlying = _parse_underlying(root.get("underlying"))
    underlying_symbol = (
        underlying.symbol
        if underlying is not None
        else _normalize_underlying_symbol(provider_symbol)
    )
    if not underlying_symbol:
        raise SchwabOptionChainParserError("underlying symbol is required.")

    contracts_by_expiration: dict[tuple[date, int | None], list[SchwabOptionContract]] = {}
    for map_key, expected_side in (
        ("callExpDateMap", "CALL"),
        ("putExpDateMap", "PUT"),
    ):
        side_map = _optional_mapping(root.get(map_key), map_key)
        if side_map is None:
            continue
        _parse_side_map(
            side_map,
            expected_side=expected_side,
            contracts_by_expiration=contracts_by_expiration,
        )

    expirations = tuple(
        SchwabOptionExpiration(
            expiration_date=expiration_date,
            days_to_expiration=days_to_expiration,
            contracts=tuple(contracts),
        )
        for (expiration_date, days_to_expiration), contracts in sorted(
            contracts_by_expiration.items(),
            key=lambda item: (item[0][0], item[0][1] if item[0][1] is not None else 10**9),
        )
    )

    return SchwabOptionChainSnapshot(
        provider_symbol=provider_symbol,
        underlying_symbol=underlying_symbol,
        underlying=underlying,
        expirations=expirations,
        is_delayed=_optional_bool(root.get("isDelayed"), "isDelayed"),
        captured_status=_optional_text(root.get("status"), "status"),
    )


def _parse_underlying(value: object) -> SchwabUnderlyingQuote | None:
    if value is None:
        return None
    underlying = _require_mapping(value, "underlying")
    symbol = _normalize_underlying_symbol(
        _optional_text(underlying.get("symbol"), "underlying.symbol") or ""
    )
    if not symbol:
        raise SchwabOptionChainParserError("underlying.symbol is required.")
    return SchwabUnderlyingQuote(
        symbol=symbol,
        bid=_optional_float(underlying.get("bid"), "underlying.bid"),
        ask=_optional_float(underlying.get("ask"), "underlying.ask"),
        last=_optional_float(underlying.get("last"), "underlying.last"),
        mark=_optional_float(underlying.get("mark"), "underlying.mark"),
        quote_time_ms=_optional_int(underlying.get("quoteTime"), "underlying.quoteTime"),
        trade_time_ms=_optional_int(underlying.get("tradeTime"), "underlying.tradeTime"),
    )


def _parse_side_map(
    side_map: dict[str, Any],
    *,
    expected_side: Literal["CALL", "PUT"],
    contracts_by_expiration: dict[tuple[date, int | None], list[SchwabOptionContract]],
) -> None:
    for expiration_key, strike_map_value in side_map.items():
        expiration_date, days_to_expiration = _parse_expiration_key(str(expiration_key))
        strike_map = _require_mapping(strike_map_value, f"{expected_side} expiration")
        for strike_key, contracts_value in strike_map.items():
            strike_from_key = _parse_float(strike_key, f"{expected_side} strike key")
            if not isinstance(contracts_value, list):
                raise SchwabOptionChainParserError(
                    f"{expected_side} strike contracts must be a list."
                )
            for contract_value in contracts_value:
                contract = _parse_contract(
                    contract_value,
                    expected_side=expected_side,
                    expiration_date=expiration_date,
                    days_to_expiration=days_to_expiration,
                    strike_from_key=strike_from_key,
                )
                contracts_by_expiration.setdefault(
                    (expiration_date, days_to_expiration),
                    [],
                ).append(contract)


def _parse_contract(
    value: object,
    *,
    expected_side: Literal["CALL", "PUT"],
    expiration_date: date,
    days_to_expiration: int | None,
    strike_from_key: float,
) -> SchwabOptionContract:
    contract = _require_mapping(value, "option contract")
    side = _optional_text(contract.get("putCall"), "putCall")
    if side != expected_side:
        raise SchwabOptionChainParserError("putCall does not match option map side.")

    provider_symbol = _optional_text(contract.get("symbol"), "symbol")
    if not provider_symbol:
        raise SchwabOptionChainParserError("contract symbol is required.")

    contract_expiration = _optional_contract_expiration_date(contract.get("expirationDate"))
    if contract_expiration is not None and contract_expiration != expiration_date:
        raise SchwabOptionChainParserError("contract expirationDate does not match map key.")

    strike = _optional_float(contract.get("strikePrice"), "strikePrice")
    if strike is None:
        strike = strike_from_key
    elif abs(strike - strike_from_key) > 0.0001:
        raise SchwabOptionChainParserError("contract strikePrice does not match strike key.")

    return SchwabOptionContract(
        provider_symbol=provider_symbol,
        side=side,
        expiration=expiration_date,
        days_to_expiration=days_to_expiration,
        strike=strike,
        bid=_optional_float(contract.get("bid"), "bid"),
        ask=_optional_float(contract.get("ask"), "ask"),
        last=_optional_float(contract.get("last"), "last"),
        mark=_optional_float(contract.get("mark"), "mark"),
        delta=_optional_float(contract.get("delta"), "delta"),
        gamma=_optional_float(contract.get("gamma"), "gamma"),
        theta=_optional_float(contract.get("theta"), "theta"),
        vega=_optional_float(contract.get("vega"), "vega"),
        implied_volatility=_optional_float(contract.get("volatility"), "volatility"),
        volume=_optional_int(contract.get("totalVolume"), "totalVolume"),
        open_interest=_optional_int(contract.get("openInterest"), "openInterest"),
        quote_time_ms=_optional_int(contract.get("quoteTimeInLong"), "quoteTimeInLong"),
        trade_time_ms=_optional_int(contract.get("tradeTimeInLong"), "tradeTimeInLong"),
    )


def _parse_expiration_key(value: str) -> tuple[date, int | None]:
    date_part, separator, dte_part = value.partition(":")
    if not separator:
        raise SchwabOptionChainParserError("expiration key must use YYYY-MM-DD:DTE format.")
    try:
        expiration_date = date.fromisoformat(date_part)
    except ValueError as exc:
        raise SchwabOptionChainParserError("expiration key date is malformed.") from exc
    try:
        days_to_expiration = int(dte_part)
    except ValueError as exc:
        raise SchwabOptionChainParserError("expiration key DTE is malformed.") from exc
    if days_to_expiration < 0:
        raise SchwabOptionChainParserError("expiration key DTE must be non-negative.")
    return expiration_date, days_to_expiration


def _optional_contract_expiration_date(value: object) -> date | None:
    text = _optional_text(value, "expirationDate")
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError as exc:
        raise SchwabOptionChainParserError("expirationDate is malformed.") from exc


def _normalize_underlying_symbol(value: str) -> str:
    return value.strip().lstrip("$")


def _require_mapping(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchwabOptionChainParserError(f"{field_name} must be an object.")
    return value


def _optional_mapping(value: object, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return _require_mapping(value, field_name)


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SchwabOptionChainParserError(f"{field_name} must be a string.")
    return value.strip() or None


def _optional_bool(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise SchwabOptionChainParserError(f"{field_name} must be a boolean.")
    return value


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SchwabOptionChainParserError(f"{field_name} must be numeric.")
    return float(value)


def _parse_float(value: object, field_name: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise SchwabOptionChainParserError(f"{field_name} must be numeric.") from exc
    raise SchwabOptionChainParserError(f"{field_name} must be numeric.")


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchwabOptionChainParserError(f"{field_name} must be an integer.")
    return value


__all__ = [
    "SchwabOptionChainParserError",
    "SchwabOptionChainSnapshot",
    "SchwabOptionContract",
    "SchwabOptionExpiration",
    "SchwabUnderlyingQuote",
    "parse_schwab_option_chain",
]
