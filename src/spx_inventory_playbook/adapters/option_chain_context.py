"""Display-only context flags derived from option-chain selection data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from spx_inventory_playbook.adapters.option_chain_freshness import (
    OptionChainFreshness,
)
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    OptionChainSelectionView,
)


DataContext = Literal[
    "static_fixture",
    "fresh_live",
    "aging_live",
    "stale_live",
    "invalid",
    "unavailable",
]
StraddleContext = Literal["available", "unavailable"]
LiquidityContext = Literal["acceptable", "mixed", "wide", "unavailable"]
GreekContext = Literal["available", "partial", "unavailable"]
OperatorWarningLevel = Literal["info", "caution", "blocked"]


@dataclass(frozen=True)
class OptionChainContextFlags:
    data_context: DataContext
    straddle_context: StraddleContext
    liquidity_context: LiquidityContext
    greek_context: GreekContext
    operator_warning_level: OperatorWarningLevel
    reason_codes: tuple[str, ...] = ()


def build_option_chain_context_flags(
    selection_view: OptionChainSelectionView | None,
    freshness: OptionChainFreshness,
) -> OptionChainContextFlags:
    """Build conservative display-only context flags for operator awareness."""

    reason_codes: list[str] = []
    data_context = _data_context(freshness)
    if data_context == "static_fixture":
        reason_codes.append("static_fixture_not_live")
    elif data_context in {"stale_live", "invalid", "unavailable"}:
        reason_codes.append(f"data_{data_context}")

    if selection_view is None or selection_view.status != "available":
        reason_codes.append("selection_unavailable")
        return OptionChainContextFlags(
            data_context=data_context,
            straddle_context="unavailable",
            liquidity_context="unavailable",
            greek_context="unavailable",
            operator_warning_level=_warning_level(data_context, reason_codes),
            reason_codes=tuple(reason_codes),
        )

    expiration = selection_view.selected_expiration
    if expiration is None:
        reason_codes.append("selected_expiration_unavailable")
        return OptionChainContextFlags(
            data_context=data_context,
            straddle_context="unavailable",
            liquidity_context="unavailable",
            greek_context="unavailable",
            operator_warning_level=_warning_level(data_context, reason_codes),
            reason_codes=tuple(reason_codes),
        )

    straddle_context: StraddleContext = (
        "available" if expiration.atm_straddle.status == "available" else "unavailable"
    )
    if straddle_context == "unavailable":
        reason_codes.append("atm_straddle_unavailable")

    liquidity_context = _liquidity_context(selection_view)
    if liquidity_context in {"wide", "mixed", "unavailable"}:
        reason_codes.append(f"liquidity_{liquidity_context}")

    greek_context = _greek_context(selection_view)
    if greek_context in {"partial", "unavailable"}:
        reason_codes.append(f"greeks_{greek_context}")

    return OptionChainContextFlags(
        data_context=data_context,
        straddle_context=straddle_context,
        liquidity_context=liquidity_context,
        greek_context=greek_context,
        operator_warning_level=_warning_level(data_context, reason_codes),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def _data_context(freshness: OptionChainFreshness) -> DataContext:
    if freshness.status == "static_fixture":
        return "static_fixture"
    if freshness.status == "fresh":
        return "fresh_live"
    if freshness.status == "aging":
        return "aging_live"
    if freshness.status == "stale":
        return "stale_live"
    if freshness.status == "invalid":
        return "invalid"
    return "unavailable"


def _liquidity_context(selection_view: OptionChainSelectionView) -> LiquidityContext:
    expiration = selection_view.selected_expiration
    if expiration is None or not expiration.contracts:
        return "unavailable"

    states = {item.liquidity.spread_state for item in expiration.contracts}
    if states == {"acceptable"}:
        return "acceptable"
    if states == {"wide"}:
        return "wide"
    if states == {"unavailable"}:
        return "unavailable"
    return "mixed"


def _greek_context(selection_view: OptionChainSelectionView) -> GreekContext:
    expiration = selection_view.selected_expiration
    if expiration is None or not expiration.contracts:
        return "unavailable"

    availability = [
        all(
            value is not None
            for value in (
                item.contract.delta,
                item.contract.gamma,
                item.contract.theta,
                item.contract.vega,
                item.contract.implied_volatility,
            )
        )
        for item in expiration.contracts
    ]
    if all(availability):
        return "available"
    if any(availability):
        return "partial"
    return "unavailable"


def _warning_level(
    data_context: DataContext,
    reason_codes: list[str],
) -> OperatorWarningLevel:
    if data_context in {"invalid", "unavailable"}:
        return "blocked"
    if data_context in {"static_fixture", "stale_live"}:
        return "caution"
    if any(
        code.startswith(("liquidity_", "greeks_", "atm_straddle_"))
        for code in reason_codes
    ):
        return "caution"
    return "info"


__all__ = [
    "DataContext",
    "GreekContext",
    "LiquidityContext",
    "OperatorWarningLevel",
    "OptionChainContextFlags",
    "StraddleContext",
    "build_option_chain_context_flags",
]
