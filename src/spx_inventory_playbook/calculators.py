"""Small pure calculation helpers for future rule logic."""

from dataclasses import dataclass
from math import isfinite


SPX_OPTION_MULTIPLIER = 100.0
ES_DOLLARS_PER_POINT = 50.0
MES_DOLLARS_PER_POINT = 5.0


@dataclass(frozen=True)
class HedgeCalculation:
    option_delta: float
    contracts: int
    hedge_percent: float
    dollar_delta_per_point: float
    target_hedge_dollars_per_point: float
    mes_equivalent: float
    mes_rounded: int
    es_equivalent: float
    es_rounded: int


@dataclass(frozen=True)
class CostCalculation:
    contracts: int
    legs: int
    commission_per_contract: float
    fees_per_contract: float
    entry_spread_crossing_per_contract: float
    exit_spread_crossing_per_contract: float
    gross_target_dollars: float
    roundtrip_contract_count: int
    commission_and_fees: float
    spread_crossing_cost: float
    total_friction: float
    target_after_friction: float
    friction_percent_of_target: float
    friction_warning: bool


def midpoint(bid: float, ask: float) -> float:
    """Return the midpoint for explicit user-supplied bid and ask values."""
    if bid < 0 or ask < 0:
        raise ValueError("Bid and ask must be non-negative.")
    if ask < bid:
        raise ValueError("Ask must be greater than or equal to bid.")
    return (bid + ask) / 2


def _require_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")


def _require_number(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError(f"{field_name} must be a finite number.")


def _require_non_negative_number(value: float, field_name: str) -> None:
    _require_number(value, field_name)
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")


def calculate_futures_hedge(
    option_delta: float,
    contracts: int,
    hedge_percent: float = 1.0,
) -> HedgeCalculation:
    """Calculate ES/MES hedge equivalents from user-supplied option delta."""
    _require_number(option_delta, "option_delta")
    _require_positive_int(contracts, "contracts")
    _require_number(hedge_percent, "hedge_percent")
    if hedge_percent < 0 or hedge_percent > 1:
        raise ValueError("hedge_percent must be between 0 and 1 inclusive.")

    dollar_delta_per_point = option_delta * SPX_OPTION_MULTIPLIER * contracts
    target_hedge_dollars_per_point = abs(dollar_delta_per_point) * hedge_percent
    mes_equivalent = target_hedge_dollars_per_point / MES_DOLLARS_PER_POINT
    es_equivalent = target_hedge_dollars_per_point / ES_DOLLARS_PER_POINT

    return HedgeCalculation(
        option_delta=option_delta,
        contracts=contracts,
        hedge_percent=hedge_percent,
        dollar_delta_per_point=dollar_delta_per_point,
        target_hedge_dollars_per_point=target_hedge_dollars_per_point,
        mes_equivalent=mes_equivalent,
        mes_rounded=int(round(mes_equivalent)),
        es_equivalent=es_equivalent,
        es_rounded=int(round(es_equivalent)),
    )


def calculate_trade_friction(
    contracts: int,
    legs: int,
    commission_per_contract: float,
    fees_per_contract: float,
    entry_spread_crossing_per_contract: float,
    exit_spread_crossing_per_contract: float,
    gross_target_dollars: float,
) -> CostCalculation:
    """Calculate mechanical round-trip friction from user-supplied cost inputs."""
    _require_positive_int(contracts, "contracts")
    _require_positive_int(legs, "legs")
    _require_non_negative_number(commission_per_contract, "commission_per_contract")
    _require_non_negative_number(fees_per_contract, "fees_per_contract")
    _require_non_negative_number(
        entry_spread_crossing_per_contract,
        "entry_spread_crossing_per_contract",
    )
    _require_non_negative_number(
        exit_spread_crossing_per_contract,
        "exit_spread_crossing_per_contract",
    )
    _require_number(gross_target_dollars, "gross_target_dollars")
    if gross_target_dollars <= 0:
        raise ValueError("gross_target_dollars must be positive.")

    roundtrip_contract_count = contracts * legs * 2
    commission_and_fees = roundtrip_contract_count * (
        commission_per_contract + fees_per_contract
    )
    spread_crossing_cost = contracts * legs * (
        entry_spread_crossing_per_contract + exit_spread_crossing_per_contract
    )
    total_friction = commission_and_fees + spread_crossing_cost
    target_after_friction = gross_target_dollars - total_friction
    friction_percent_of_target = total_friction / gross_target_dollars

    return CostCalculation(
        contracts=contracts,
        legs=legs,
        commission_per_contract=commission_per_contract,
        fees_per_contract=fees_per_contract,
        entry_spread_crossing_per_contract=entry_spread_crossing_per_contract,
        exit_spread_crossing_per_contract=exit_spread_crossing_per_contract,
        gross_target_dollars=gross_target_dollars,
        roundtrip_contract_count=roundtrip_contract_count,
        commission_and_fees=commission_and_fees,
        spread_crossing_cost=spread_crossing_cost,
        total_friction=total_friction,
        target_after_friction=target_after_friction,
        friction_percent_of_target=friction_percent_of_target,
        friction_warning=friction_percent_of_target >= 0.25,
    )
