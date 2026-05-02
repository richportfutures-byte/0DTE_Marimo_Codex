"""Pure SPX option-chain selection logic for app-ready views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from spx_inventory_playbook.adapters.schwab_option_chain import (
    SchwabOptionChainSnapshot,
    SchwabOptionContract,
    SchwabOptionExpiration,
)


SelectionStatus = Literal["available", "unavailable", "blocked"]
SpreadState = Literal["acceptable", "wide", "unavailable"]


@dataclass(frozen=True)
class LiquidityDiagnostic:
    spread: float | None
    midpoint: float | None
    volume: int | None
    open_interest: int | None
    spread_state: SpreadState


@dataclass(frozen=True)
class SelectedContractView:
    contract: SchwabOptionContract
    liquidity: LiquidityDiagnostic


@dataclass(frozen=True)
class AtmStraddleEstimate:
    status: SelectionStatus
    value: float | None
    call_value: float | None
    put_value: float | None
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelectedExpirationView:
    expiration_date: date
    days_to_expiration: int | None
    reference_underlying_price: float
    atm_strike: float
    contracts: tuple[SelectedContractView, ...]
    atm_straddle: AtmStraddleEstimate


@dataclass(frozen=True)
class OptionChainSelectionView:
    status: SelectionStatus
    reason_codes: tuple[str, ...]
    provider_symbol: str
    underlying_symbol: str
    selected_expiration: SelectedExpirationView | None


def build_spx_0dte_selection_view(
    snapshot: SchwabOptionChainSnapshot,
    *,
    strikes_below: int = 2,
    strikes_above: int = 2,
    wide_spread_threshold: float = 1.0,
) -> OptionChainSelectionView:
    """Build a bounded, deterministic SPX option-chain view for later display."""

    expiration = _nearest_expiration(snapshot.expirations)
    if expiration is None:
        return _unavailable(snapshot, "expiration_unavailable")

    reference_price = _reference_underlying_price(snapshot)
    if reference_price is None:
        return _unavailable(snapshot, "underlying_reference_price_unavailable")

    strikes = sorted({contract.strike for contract in expiration.contracts})
    if not strikes:
        return _unavailable(snapshot, "strike_unavailable")

    atm_strike = min(strikes, key=lambda strike: (abs(strike - reference_price), strike))
    window_strikes = set(_strike_window(strikes, atm_strike, strikes_below, strikes_above))
    selected_contracts = tuple(
        SelectedContractView(
            contract=contract,
            liquidity=liquidity_diagnostic(
                contract,
                wide_spread_threshold=wide_spread_threshold,
            ),
        )
        for contract in expiration.contracts
        if contract.strike in window_strikes
    )

    return OptionChainSelectionView(
        status="available",
        reason_codes=(),
        provider_symbol=snapshot.provider_symbol,
        underlying_symbol=snapshot.underlying_symbol,
        selected_expiration=SelectedExpirationView(
            expiration_date=expiration.expiration_date,
            days_to_expiration=expiration.days_to_expiration,
            reference_underlying_price=reference_price,
            atm_strike=atm_strike,
            contracts=selected_contracts,
            atm_straddle=_atm_straddle_estimate(expiration.contracts, atm_strike),
        ),
    )


def liquidity_diagnostic(
    contract: SchwabOptionContract,
    *,
    wide_spread_threshold: float = 1.0,
) -> LiquidityDiagnostic:
    """Compute simple deterministic liquidity fields for one option contract."""

    spread: float | None = None
    midpoint: float | None = None
    spread_state: SpreadState = "unavailable"
    if contract.bid is not None and contract.ask is not None and contract.ask >= contract.bid:
        spread = contract.ask - contract.bid
        midpoint = (contract.bid + contract.ask) / 2
        spread_state = "wide" if spread > wide_spread_threshold else "acceptable"

    return LiquidityDiagnostic(
        spread=spread,
        midpoint=midpoint,
        volume=contract.volume,
        open_interest=contract.open_interest,
        spread_state=spread_state,
    )


def _nearest_expiration(
    expirations: tuple[SchwabOptionExpiration, ...],
) -> SchwabOptionExpiration | None:
    if not expirations:
        return None
    return min(
        expirations,
        key=lambda expiration: (
            0
            if expiration.days_to_expiration is not None
            and expiration.days_to_expiration >= 0
            else 1,
            expiration.days_to_expiration
            if expiration.days_to_expiration is not None
            and expiration.days_to_expiration >= 0
            else 10**9,
            expiration.expiration_date,
        ),
    )


def _reference_underlying_price(snapshot: SchwabOptionChainSnapshot) -> float | None:
    underlying = snapshot.underlying
    if underlying is None:
        return None
    if underlying.mark is not None:
        return underlying.mark
    if underlying.last is not None:
        return underlying.last
    if underlying.bid is not None and underlying.ask is not None and underlying.ask >= underlying.bid:
        return (underlying.bid + underlying.ask) / 2
    return None


def _strike_window(
    strikes: list[float],
    atm_strike: float,
    strikes_below: int,
    strikes_above: int,
) -> tuple[float, ...]:
    atm_index = strikes.index(atm_strike)
    start = max(0, atm_index - max(0, strikes_below))
    stop = min(len(strikes), atm_index + max(0, strikes_above) + 1)
    return tuple(strikes[start:stop])


def _atm_straddle_estimate(
    contracts: tuple[SchwabOptionContract, ...],
    atm_strike: float,
) -> AtmStraddleEstimate:
    call = _contract_at_strike(contracts, atm_strike, "CALL")
    put = _contract_at_strike(contracts, atm_strike, "PUT")
    if call is None or put is None:
        return AtmStraddleEstimate(
            status="unavailable",
            value=None,
            call_value=None,
            put_value=None,
            reason_codes=("atm_leg_unavailable",),
        )

    call_value = _contract_price_estimate(call)
    put_value = _contract_price_estimate(put)
    if call_value is None or put_value is None:
        return AtmStraddleEstimate(
            status="unavailable",
            value=None,
            call_value=call_value,
            put_value=put_value,
            reason_codes=("atm_leg_price_unavailable",),
        )
    return AtmStraddleEstimate(
        status="available",
        value=call_value + put_value,
        call_value=call_value,
        put_value=put_value,
    )


def _contract_at_strike(
    contracts: tuple[SchwabOptionContract, ...],
    strike: float,
    side: Literal["CALL", "PUT"],
) -> SchwabOptionContract | None:
    for contract in contracts:
        if contract.strike == strike and contract.side == side:
            return contract
    return None


def _contract_price_estimate(contract: SchwabOptionContract) -> float | None:
    if contract.mark is not None:
        return contract.mark
    if contract.bid is not None and contract.ask is not None and contract.ask >= contract.bid:
        return (contract.bid + contract.ask) / 2
    return None


def _unavailable(
    snapshot: SchwabOptionChainSnapshot,
    reason_code: str,
) -> OptionChainSelectionView:
    return OptionChainSelectionView(
        status="unavailable",
        reason_codes=(reason_code,),
        provider_symbol=snapshot.provider_symbol,
        underlying_symbol=snapshot.underlying_symbol,
        selected_expiration=None,
    )


__all__ = [
    "AtmStraddleEstimate",
    "LiquidityDiagnostic",
    "OptionChainSelectionView",
    "SelectedContractView",
    "SelectedExpirationView",
    "SelectionStatus",
    "SpreadState",
    "build_spx_0dte_selection_view",
    "liquidity_diagnostic",
]
