"""Broker-neutral market-data contracts for 0DTE SPX/SPXW preparation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return value


def _require_timezone_aware(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    return value


def _require_date(value: object, field_name: str) -> date:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"{field_name} is required.")
    return value


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal.")
    return value


def _require_non_negative_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _require_decimal(value, field_name)
    if decimal_value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return decimal_value


def _require_positive_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _require_decimal(value, field_name)
    if decimal_value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return decimal_value


def _validate_optional_non_negative_decimal(
    value: object,
    field_name: str,
) -> Decimal | None:
    if value is None:
        return None
    return _require_non_negative_decimal(value, field_name)


def _require_bid_ask_midpoint(
    bid: Decimal | None,
    ask: Decimal | None,
    *,
    context: str,
) -> Decimal:
    if bid is None or ask is None:
        raise ValueError(f"{context} midpoint requires bid and ask.")
    _require_non_negative_decimal(bid, "bid")
    _require_non_negative_decimal(ask, "ask")
    if ask < bid:
        raise ValueError(f"{context} quote is crossed: ask must be >= bid.")
    return (bid + ask) / Decimal("2")


class QuoteFreshness(Enum):
    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"
    UNKNOWN = "unknown"

    @property
    def is_fresh(self) -> bool:
        return self is QuoteFreshness.FRESH


@dataclass(frozen=True)
class MarketDataSource:
    provider: str
    adapter: str
    retrieved_at: datetime
    is_live: bool = False
    endpoint: str | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.provider, "provider")
        _require_text(self.adapter, "adapter")
        _require_timezone_aware(self.retrieved_at, "retrieved_at")

    def __repr__(self) -> str:
        return (
            "MarketDataSource(provider=<redacted>, adapter=<redacted>, "
            f"retrieved_at={self.retrieved_at!r}, is_live={self.is_live!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class UnderlyingQuoteSnapshot:
    symbol: str
    source: MarketDataSource
    as_of: datetime
    freshness: QuoteFreshness
    last: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    provider_mark: Decimal | None = None
    is_proxy: bool = False
    proxy_for: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.symbol, "symbol")
        if not isinstance(self.source, MarketDataSource):
            raise ValueError("source is required.")
        _require_timezone_aware(self.as_of, "as_of")
        if not isinstance(self.freshness, QuoteFreshness):
            raise ValueError("freshness is required.")
        _validate_optional_non_negative_decimal(self.last, "last")
        _validate_optional_non_negative_decimal(self.provider_mark, "provider_mark")
        _require_bid_ask_midpoint(self.bid, self.ask, context="underlying")

    @property
    def midpoint(self) -> Decimal:
        return _require_bid_ask_midpoint(self.bid, self.ask, context="underlying")

    @property
    def blocks_derived_prefill(self) -> bool:
        return self.freshness is not QuoteFreshness.FRESH


@dataclass(frozen=True)
class OptionContractKey:
    underlying: str
    expiry_date: date
    strike: Decimal
    right: Literal["CALL", "PUT"]
    occ_symbol: str | None = None
    provider_symbol: str | None = None
    settlement: Literal["AM", "PM"] | None = None
    product: Literal["SPX", "SPXW"] | None = None

    def __post_init__(self) -> None:
        _require_text(self.underlying, "underlying")
        _require_date(self.expiry_date, "expiry_date")
        _require_positive_decimal(self.strike, "strike")
        if self.right not in {"CALL", "PUT"}:
            raise ValueError("right must be CALL or PUT.")
        if self.product is not None and self.product not in {"SPX", "SPXW"}:
            raise ValueError("product must be SPX or SPXW.")
        if self.settlement is not None and self.settlement not in {"AM", "PM"}:
            raise ValueError("settlement must be AM or PM.")


@dataclass(frozen=True)
class OptionQuoteSnapshot:
    key: OptionContractKey
    source: MarketDataSource
    as_of: datetime
    freshness: QuoteFreshness
    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    provider_mark: Decimal | None = None
    bid_size: int | None = None
    ask_size: int | None = None
    volume: int | None = None
    open_interest: int | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    iv: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, OptionContractKey):
            raise ValueError("key is required.")
        if not isinstance(self.source, MarketDataSource):
            raise ValueError("source is required.")
        _require_timezone_aware(self.as_of, "as_of")
        if not isinstance(self.freshness, QuoteFreshness):
            raise ValueError("freshness is required.")
        _validate_optional_non_negative_decimal(self.last, "last")
        _validate_optional_non_negative_decimal(self.provider_mark, "provider_mark")
        for field_name in ("delta", "gamma", "theta", "vega", "iv"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, Decimal):
                raise ValueError(f"{field_name} must be a Decimal when provided.")
        _require_bid_ask_midpoint(self.bid, self.ask, context="option")
        for field_name in ("bid_size", "ask_size", "volume", "open_interest"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"{field_name} must be a non-negative integer.")

    @property
    def midpoint(self) -> Decimal:
        return _require_bid_ask_midpoint(self.bid, self.ask, context="option")

    @property
    def is_locked(self) -> bool:
        return self.bid is not None and self.ask is not None and self.bid == self.ask

    @property
    def is_degraded(self) -> bool:
        return self.is_locked or self.freshness is not QuoteFreshness.FRESH


@dataclass(frozen=True)
class ExpirySnapshot:
    expiry_date: date
    session_date: date
    dte: int
    is_0dte: bool
    source: MarketDataSource
    settlement: Literal["AM", "PM"] | None = None
    last_trade_time: datetime | None = None

    def __post_init__(self) -> None:
        _require_date(self.expiry_date, "expiry_date")
        _require_date(self.session_date, "session_date")
        if not isinstance(self.dte, int) or self.dte < 0:
            raise ValueError("dte must be non-negative.")
        if not isinstance(self.source, MarketDataSource):
            raise ValueError("source is required.")
        if self.settlement is not None and self.settlement not in {"AM", "PM"}:
            raise ValueError("settlement must be AM or PM.")
        if self.last_trade_time is not None:
            _require_timezone_aware(self.last_trade_time, "last_trade_time")
        if self.is_0dte and self.expiry_date != self.session_date:
            raise ValueError("is_0dte requires expiry_date to equal session_date.")

    @property
    def blocks_0dte_workflow(self) -> bool:
        return not self.is_0dte or self.expiry_date != self.session_date


@dataclass(frozen=True)
class OptionChainSnapshot:
    underlying_symbol: str
    expiry: ExpirySnapshot
    source: MarketDataSource
    as_of: datetime
    freshness: QuoteFreshness
    contracts: tuple[OptionQuoteSnapshot, ...]
    is_partial: bool
    completeness_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.underlying_symbol, "underlying_symbol")
        if not isinstance(self.expiry, ExpirySnapshot):
            raise ValueError("expiry is required.")
        if not isinstance(self.source, MarketDataSource):
            raise ValueError("source is required.")
        _require_timezone_aware(self.as_of, "as_of")
        if not isinstance(self.freshness, QuoteFreshness):
            raise ValueError("freshness is required.")
        if not self.contracts:
            raise ValueError("contracts must be nonempty.")
        for quote in self.contracts:
            if not isinstance(quote, OptionQuoteSnapshot):
                raise ValueError("contracts must contain OptionQuoteSnapshot values.")
        underlyings = {quote.key.underlying for quote in self.contracts}
        if underlyings != {self.underlying_symbol}:
            raise ValueError("contracts must have one underlying.")
        expiries = {quote.key.expiry_date for quote in self.contracts}
        if expiries != {self.expiry.expiry_date}:
            raise ValueError("contracts must have one expiry.")
        keys = [quote.key for quote in self.contracts]
        if len(keys) != len(set(keys)):
            raise ValueError("contracts must have unique OptionContractKey values.")
        if self.is_partial and not self.completeness_notes:
            raise ValueError("completeness_notes are required for a partial chain.")
        for note in self.completeness_notes:
            _require_text(note, "completeness_notes")

    @property
    def is_degraded(self) -> bool:
        return self.is_partial or self.freshness is not QuoteFreshness.FRESH

    @property
    def blocks_structure_ranking(self) -> bool:
        return self.is_partial or self.freshness is not QuoteFreshness.FRESH


@dataclass(frozen=True)
class AtmStraddleSnapshot:
    underlying_symbol: str
    underlying_price: Decimal
    underlying_quote: UnderlyingQuoteSnapshot
    expiry: ExpirySnapshot
    source: MarketDataSource
    as_of: datetime
    freshness: QuoteFreshness
    call: OptionQuoteSnapshot
    put: OptionQuoteSnapshot
    width_points: Decimal
    width_percent: Decimal | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.underlying_symbol, "underlying_symbol")
        _require_positive_decimal(self.underlying_price, "underlying_price")
        if not isinstance(self.underlying_quote, UnderlyingQuoteSnapshot):
            raise ValueError("underlying_quote is required.")
        if not isinstance(self.expiry, ExpirySnapshot):
            raise ValueError("expiry is required.")
        if not isinstance(self.source, MarketDataSource):
            raise ValueError("source is required.")
        _require_timezone_aware(self.as_of, "as_of")
        if not isinstance(self.freshness, QuoteFreshness):
            raise ValueError("freshness is required.")
        if not isinstance(self.call, OptionQuoteSnapshot) or self.call.key.right != "CALL":
            raise ValueError("call must be a CALL OptionQuoteSnapshot.")
        if not isinstance(self.put, OptionQuoteSnapshot) or self.put.key.right != "PUT":
            raise ValueError("put must be a PUT OptionQuoteSnapshot.")
        if self.call.key.strike != self.put.key.strike:
            raise ValueError("call and put must share the same strike.")
        if self.call.key.expiry_date != self.put.key.expiry_date:
            raise ValueError("call and put must share the same expiry.")
        if self.call.key.expiry_date != self.expiry.expiry_date:
            raise ValueError("straddle quotes must match expiry.")
        _require_positive_decimal(self.width_points, "width_points")
        expected_width = self.call.midpoint + self.put.midpoint
        if self.width_points != expected_width:
            raise ValueError("width_points must equal call midpoint plus put midpoint.")
        if self.width_percent is not None:
            _require_positive_decimal(self.width_percent, "width_percent")
            expected_percent = self.width_points / self.underlying_price
            if self.width_percent != expected_percent:
                raise ValueError("width_percent must equal width_points / underlying_price.")
        for warning in self.warnings:
            _require_text(warning, "warnings")

    @property
    def blocks_derived_outputs(self) -> bool:
        return (
            self.freshness is not QuoteFreshness.FRESH
            or self.underlying_quote.freshness is not QuoteFreshness.FRESH
            or self.call.freshness is not QuoteFreshness.FRESH
            or self.put.freshness is not QuoteFreshness.FRESH
        )


@dataclass(frozen=True)
class MarketDataHealth:
    status: Literal["OK", "DEGRADED", "BLOCKED"]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    missing_fields: tuple[str, ...] = ()
    stale_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"OK", "DEGRADED", "BLOCKED"}:
            raise ValueError("status must be OK, DEGRADED, or BLOCKED.")
        for field_name in ("blockers", "warnings", "missing_fields", "stale_fields"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple):
                raise ValueError(f"{field_name} must be a tuple.")
            for value in values:
                _require_text(value, field_name)
        if self.blockers and self.status != "BLOCKED":
            raise ValueError("BLOCKED status is required when blockers exist.")
        if self.status == "OK" and (self.warnings or self.missing_fields or self.stale_fields):
            raise ValueError("OK status requires no warnings, missing_fields, or stale_fields.")
