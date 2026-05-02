from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from spx_inventory_playbook.adapters.schwab_option_chain import (
    SchwabOptionChainSnapshot,
    SchwabOptionContract,
    SchwabOptionExpiration,
    parse_schwab_option_chain,
)
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    build_spx_0dte_selection_view,
    liquidity_diagnostic,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)


def parsed_snapshot() -> SchwabOptionChainSnapshot:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return parse_schwab_option_chain(payload)


def selected_view():
    return build_spx_0dte_selection_view(parsed_snapshot())


def selected_expiration():
    expiration = selected_view().selected_expiration
    assert expiration is not None
    return expiration


def contract_at(
    contracts: tuple[SchwabOptionContract, ...],
    *,
    side: str,
    strike: float,
) -> SchwabOptionContract:
    return next(contract for contract in contracts if contract.side == side and contract.strike == strike)


def test_captured_fixture_parses_then_selection_view_builds_successfully() -> None:
    view = selected_view()

    assert view.status == "available"
    assert view.reason_codes == ()
    assert view.provider_symbol == "$SPX"
    assert view.underlying_symbol == "SPX"
    assert view.selected_expiration is not None


def test_nearest_expiration_is_selected_by_lowest_nonnegative_dte() -> None:
    snapshot = parsed_snapshot()
    selected = snapshot.expirations[0]
    later = SchwabOptionExpiration(
        expiration_date=date(2026, 5, 5),
        days_to_expiration=3,
        contracts=selected.contracts,
    )
    same_dte_later_date = SchwabOptionExpiration(
        expiration_date=date(2026, 5, 6),
        days_to_expiration=2,
        contracts=selected.contracts,
    )
    mutated = replace(
        snapshot,
        expirations=(later, same_dte_later_date, selected),
    )

    view = build_spx_0dte_selection_view(mutated)

    assert view.selected_expiration is not None
    assert view.selected_expiration.expiration_date == date(2026, 5, 4)
    assert view.selected_expiration.days_to_expiration == 2


def test_atm_strike_is_closest_to_underlying_reference_price() -> None:
    expiration = selected_expiration()

    assert expiration.reference_underlying_price == pytest.approx(7230.12)
    assert expiration.atm_strike == 7230.0


def test_window_around_atm_includes_calls_and_puts_where_available() -> None:
    snapshot = parsed_snapshot()
    view = build_spx_0dte_selection_view(snapshot, strikes_below=0, strikes_above=0)

    assert view.selected_expiration is not None
    selected_contracts = tuple(item.contract for item in view.selected_expiration.contracts)
    assert {contract.strike for contract in selected_contracts} == {7230.0}
    assert {contract.side for contract in selected_contracts} == {"CALL", "PUT"}


def test_atm_straddle_uses_mark_values_when_present() -> None:
    expiration = selected_expiration()

    assert expiration.atm_straddle.status == "available"
    assert expiration.atm_straddle.call_value == pytest.approx(17.0)
    assert expiration.atm_straddle.put_value == pytest.approx(26.25)
    assert expiration.atm_straddle.value == pytest.approx(43.25)


def test_atm_straddle_falls_back_to_bid_ask_midpoint_when_mark_is_missing() -> None:
    snapshot = parsed_snapshot()
    expiration = snapshot.expirations[0]
    contracts = tuple(
        replace(contract, mark=None)
        if contract.strike == 7230.0 and contract.side in {"CALL", "PUT"}
        else contract
        for contract in expiration.contracts
    )
    mutated = replace(snapshot, expirations=(replace(expiration, contracts=contracts),))

    view = build_spx_0dte_selection_view(mutated)

    assert view.selected_expiration is not None
    straddle = view.selected_expiration.atm_straddle
    assert straddle.status == "available"
    assert straddle.call_value == pytest.approx(17.0)
    assert straddle.put_value == pytest.approx(26.25)
    assert straddle.value == pytest.approx(43.25)


def test_missing_one_atm_leg_makes_straddle_unavailable_without_crashing() -> None:
    snapshot = parsed_snapshot()
    expiration = snapshot.expirations[0]
    contracts = tuple(
        contract
        for contract in expiration.contracts
        if not (contract.strike == 7230.0 and contract.side == "PUT")
    )
    mutated = replace(snapshot, expirations=(replace(expiration, contracts=contracts),))

    view = build_spx_0dte_selection_view(mutated)

    assert view.status == "available"
    assert view.selected_expiration is not None
    assert view.selected_expiration.atm_straddle.status == "unavailable"
    assert view.selected_expiration.atm_straddle.reason_codes == ("atm_leg_unavailable",)


def test_missing_underlying_price_makes_selection_unavailable() -> None:
    snapshot = parsed_snapshot()
    assert snapshot.underlying is not None
    underlying = replace(snapshot.underlying, mark=None, last=None, bid=None, ask=None)
    mutated = replace(snapshot, underlying=underlying)

    view = build_spx_0dte_selection_view(mutated)

    assert view.status == "unavailable"
    assert view.reason_codes == ("underlying_reference_price_unavailable",)
    assert view.selected_expiration is None


def test_empty_expiration_set_makes_selection_unavailable() -> None:
    snapshot = replace(parsed_snapshot(), expirations=())

    view = build_spx_0dte_selection_view(snapshot)

    assert view.status == "unavailable"
    assert view.reason_codes == ("expiration_unavailable",)
    assert view.selected_expiration is None


def test_liquidity_diagnostics_compute_spread_and_midpoint() -> None:
    contracts = selected_expiration().contracts
    diagnostic = next(item.liquidity for item in contracts if item.contract.side == "CALL")

    assert diagnostic.spread == pytest.approx(0.4)
    assert diagnostic.midpoint == pytest.approx(17.0)
    assert diagnostic.volume == 2587
    assert diagnostic.open_interest == 0
    assert diagnostic.spread_state == "acceptable"


def test_wide_and_unavailable_spread_classification_is_deterministic() -> None:
    snapshot = parsed_snapshot()
    contract = contract_at(snapshot.expirations[0].contracts, side="CALL", strike=7230.0)

    wide = liquidity_diagnostic(
        replace(contract, bid=10.0, ask=12.0),
        wide_spread_threshold=1.0,
    )
    unavailable = liquidity_diagnostic(replace(contract, bid=None, ask=12.0))

    assert wide.spread == pytest.approx(2.0)
    assert wide.midpoint == pytest.approx(11.0)
    assert wide.spread_state == "wide"
    assert unavailable.spread is None
    assert unavailable.midpoint is None
    assert unavailable.spread_state == "unavailable"


def test_status_output_does_not_include_raw_payload_bodies() -> None:
    snapshot = replace(parsed_snapshot(), expirations=())

    view = build_spx_0dte_selection_view(snapshot)
    rendered = f"{view!r} {view.status} {view.reason_codes}"

    assert "raw-payload-body" not in rendered
    assert "secret-token-value" not in rendered
