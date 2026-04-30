"""Sanitized Schwab-shaped fixture mapper for broker-neutral market data."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    ExpirySnapshot,
    MarketDataHealth,
    MarketDataSource,
    OptionChainSnapshot,
    OptionContractKey,
    OptionQuoteSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)


ADAPTER_NAME = "schwab_market_data_fixture_mapper"


class SchwabMarketDataMapper:
    """Map sanitized Schwab-shaped fixture payloads into canonical contracts."""

    def map_underlying_quote(
        self,
        payload: dict[str, Any],
        *,
        retrieved_at: datetime,
        max_age_seconds: int,
    ) -> UnderlyingQuoteSnapshot:
        source = self._source(payload, retrieved_at)
        underlying = self._require_mapping(payload.get("underlying"), "underlying")
        as_of = self._parse_datetime(underlying.get("quote_time"), "underlying.quote_time")

        return UnderlyingQuoteSnapshot(
            symbol=self._require_text(
                underlying.get("canonical_symbol"),
                "underlying.canonical_symbol",
            ),
            source=source,
            as_of=as_of,
            freshness=self._freshness(as_of, retrieved_at, max_age_seconds),
            bid=self._optional_decimal(underlying.get("bid"), "underlying.bid"),
            ask=self._optional_decimal(underlying.get("ask"), "underlying.ask"),
            last=self._optional_decimal(underlying.get("last"), "underlying.last"),
            provider_mark=self._optional_decimal(
                underlying.get("mark"),
                "underlying.mark",
            ),
            is_proxy=bool(underlying.get("is_proxy", False)),
            proxy_for=self._optional_text(underlying.get("proxy_for"), "underlying.proxy_for"),
        )

    def map_option_chain(
        self,
        payload: dict[str, Any],
        *,
        session_date: date,
        retrieved_at: datetime,
        max_age_seconds: int,
    ) -> OptionChainSnapshot:
        source = self._source(payload, retrieved_at)
        expiry_payload = self._require_mapping(payload.get("expiry"), "expiry")
        expiry_date = self._parse_date(expiry_payload.get("expiry_date"), "expiry.expiry_date")
        payload_session_date = self._parse_date(
            expiry_payload.get("session_date"),
            "expiry.session_date",
        )
        if payload_session_date != session_date:
            raise ValueError("0DTE expiry session_date does not match requested session_date.")
        if expiry_date != session_date:
            raise ValueError("0DTE option chain expiry must match session_date.")

        contracts_payload = payload.get("contracts")
        if not isinstance(contracts_payload, list):
            raise ValueError("contracts must be a list.")
        as_of = self._chain_as_of(contracts_payload)
        freshness = self._freshness(as_of, retrieved_at, max_age_seconds)
        underlying_symbol = self._require_text(
            payload.get("underlying_symbol"),
            "underlying_symbol",
        )

        expiry = ExpirySnapshot(
            expiry_date=expiry_date,
            session_date=session_date,
            dte=self._required_int(expiry_payload.get("dte"), "expiry.dte"),
            is_0dte=True,
            source=source,
            settlement=self._optional_text(expiry_payload.get("settlement"), "expiry.settlement"),
        )
        contracts = tuple(
            self._map_option_quote(
                contract,
                source=source,
                fallback_underlying=underlying_symbol,
                fallback_product=self._optional_text(payload.get("product"), "product"),
                chain_freshness=freshness,
            )
            for contract in contracts_payload
        )

        return OptionChainSnapshot(
            underlying_symbol=underlying_symbol,
            expiry=expiry,
            source=source,
            as_of=as_of,
            freshness=freshness,
            contracts=contracts,
            is_partial=bool(payload.get("is_partial", False)),
            completeness_notes=tuple(
                self._require_text(note, "completeness_notes")
                for note in self._list_value(payload.get("completeness_notes"))
            ),
        )

    def map_market_data_health(
        self,
        *,
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
        missing_fields: tuple[str, ...] = (),
        stale_fields: tuple[str, ...] = (),
    ) -> MarketDataHealth:
        if blockers:
            status = "BLOCKED"
        elif warnings or missing_fields or stale_fields:
            status = "DEGRADED"
        else:
            status = "OK"
        return MarketDataHealth(
            status=status,
            blockers=blockers,
            warnings=warnings,
            missing_fields=missing_fields,
            stale_fields=stale_fields,
        )

    def derive_atm_straddle(
        self,
        chain: OptionChainSnapshot,
        underlying_quote: UnderlyingQuoteSnapshot,
    ) -> AtmStraddleSnapshot:
        if chain.underlying_symbol != underlying_quote.symbol:
            raise ValueError("ATM straddle underlying must match option chain.")
        call, put = self._atm_call_put(chain, underlying_quote.midpoint)
        width_points = call.midpoint + put.midpoint
        underlying_price = call.key.strike

        return AtmStraddleSnapshot(
            underlying_symbol=chain.underlying_symbol,
            underlying_price=underlying_price,
            underlying_quote=underlying_quote,
            expiry=chain.expiry,
            source=chain.source,
            as_of=chain.as_of,
            freshness=self._combined_freshness(chain.freshness, underlying_quote.freshness),
            call=call,
            put=put,
            width_points=width_points,
            width_percent=width_points / underlying_price,
        )

    def _map_option_quote(
        self,
        payload: object,
        *,
        source: MarketDataSource,
        fallback_underlying: str,
        fallback_product: str | None,
        chain_freshness: QuoteFreshness,
    ) -> OptionQuoteSnapshot:
        contract = self._require_mapping(payload, "contracts[]")
        as_of = self._parse_datetime(contract.get("quote_time"), "contracts[].quote_time")
        key = OptionContractKey(
            underlying=self._optional_text(contract.get("underlying"), "contracts[].underlying")
            or fallback_underlying,
            expiry_date=self._parse_date(
                contract.get("expiry_date"),
                "contracts[].expiry_date",
            ),
            strike=self._required_decimal(contract.get("strike"), "contracts[].strike"),
            right=self._require_text(contract.get("right"), "contracts[].right"),
            provider_symbol=self._optional_text(
                contract.get("provider_symbol"),
                "contracts[].provider_symbol",
            ),
            settlement=None,
            product=self._optional_text(contract.get("product"), "contracts[].product")
            or fallback_product,
        )
        return OptionQuoteSnapshot(
            key=key,
            source=source,
            as_of=as_of,
            freshness=chain_freshness,
            bid=self._optional_decimal(contract.get("bid"), "contracts[].bid"),
            ask=self._optional_decimal(contract.get("ask"), "contracts[].ask"),
            last=self._optional_decimal(contract.get("last"), "contracts[].last"),
            provider_mark=self._optional_decimal(contract.get("mark"), "contracts[].mark"),
            bid_size=self._optional_int(contract.get("bid_size"), "contracts[].bid_size"),
            ask_size=self._optional_int(contract.get("ask_size"), "contracts[].ask_size"),
            volume=self._optional_int(contract.get("volume"), "contracts[].volume"),
            open_interest=self._optional_int(
                contract.get("open_interest"),
                "contracts[].open_interest",
            ),
            delta=self._optional_decimal(contract.get("delta"), "contracts[].delta"),
            gamma=self._optional_decimal(contract.get("gamma"), "contracts[].gamma"),
            theta=self._optional_decimal(contract.get("theta"), "contracts[].theta"),
            vega=self._optional_decimal(contract.get("vega"), "contracts[].vega"),
            iv=self._optional_decimal(contract.get("iv"), "contracts[].iv"),
        )

    def _source(self, payload: dict[str, Any], retrieved_at: datetime) -> MarketDataSource:
        return MarketDataSource(
            provider=self._require_text(payload.get("provider"), "provider"),
            adapter=ADAPTER_NAME,
            retrieved_at=retrieved_at,
            is_live=False,
            request_id=self._optional_text(payload.get("request_id"), "request_id"),
        )

    def _chain_as_of(self, contracts: list[object]) -> datetime:
        if not contracts:
            raise ValueError("contracts must be nonempty.")
        quote_times = [
            self._parse_datetime(
                self._require_mapping(contract, "contracts[]").get("quote_time"),
                "contracts[].quote_time",
            )
            for contract in contracts
        ]
        return min(quote_times)

    def _atm_call_put(
        self,
        chain: OptionChainSnapshot,
        underlying_midpoint: Decimal,
    ) -> tuple[OptionQuoteSnapshot, OptionQuoteSnapshot]:
        by_strike: dict[Decimal, dict[str, OptionQuoteSnapshot]] = {}
        for quote in chain.contracts:
            by_strike.setdefault(quote.key.strike, {})[quote.key.right] = quote

        paired_strikes = [
            strike
            for strike, quotes in by_strike.items()
            if "CALL" in quotes and "PUT" in quotes
        ]
        if not paired_strikes:
            raise ValueError("ATM straddle requires a call and put pair.")
        atm_strike = min(paired_strikes, key=lambda strike: abs(strike - underlying_midpoint))
        quotes = by_strike[atm_strike]
        return quotes["CALL"], quotes["PUT"]

    def _freshness(
        self,
        as_of: datetime,
        retrieved_at: datetime,
        max_age_seconds: int,
    ) -> QuoteFreshness:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative.")
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware.")
        age = retrieved_at - as_of
        if age < timedelta(0):
            raise ValueError("as_of cannot be after retrieved_at.")
        if age > timedelta(seconds=max_age_seconds):
            return QuoteFreshness.STALE
        return QuoteFreshness.FRESH

    def _combined_freshness(
        self,
        chain_freshness: QuoteFreshness,
        underlying_freshness: QuoteFreshness,
    ) -> QuoteFreshness:
        if chain_freshness is QuoteFreshness.FRESH and underlying_freshness is QuoteFreshness.FRESH:
            return QuoteFreshness.FRESH
        if QuoteFreshness.MISSING in {chain_freshness, underlying_freshness}:
            return QuoteFreshness.MISSING
        if QuoteFreshness.UNKNOWN in {chain_freshness, underlying_freshness}:
            return QuoteFreshness.UNKNOWN
        return QuoteFreshness.STALE

    def _required_decimal(self, value: object, field_name: str) -> Decimal:
        decimal_value = self._optional_decimal(value, field_name)
        if decimal_value is None:
            raise ValueError(f"{field_name} is required.")
        return decimal_value

    def _optional_decimal(self, value: object, field_name: str) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a decimal string.")
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be decimal-compatible.") from exc

    def _required_int(self, value: object, field_name: str) -> int:
        int_value = self._optional_int(value, field_name)
        if int_value is None:
            raise ValueError(f"{field_name} is required.")
        return int_value

    def _optional_int(self, value: object, field_name: str) -> int | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be an integer string.")
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be integer-compatible.") from exc

    def _parse_date(self, value: object, field_name: str) -> date:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO date.") from exc

    def _parse_datetime(self, value: object, field_name: str) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO datetime.") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware.")
        return parsed

    def _require_text(self, value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")
        return value

    def _optional_text(self, value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be text when provided.")
        return value

    def _require_mapping(self, value: object, field_name: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be an object.")
        return value

    def _list_value(self, value: object) -> list[object]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("completeness_notes must be a list.")
        return value
