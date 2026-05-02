from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from spx_inventory_playbook.adapters.option_chain_context import (
    build_option_chain_context_flags,
)
from spx_inventory_playbook.adapters.option_chain_freshness import OptionChainFreshness
from spx_inventory_playbook.adapters.schwab_option_chain import (
    parse_schwab_option_chain,
)
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    build_spx_0dte_selection_view,
)


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "src/spx_inventory_playbook/adapters/option_chain_context.py"
FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)
NOW = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)


def selection_view():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return build_spx_0dte_selection_view(parse_schwab_option_chain(payload))


def freshness(status: str, *, source_type: str = "live") -> OptionChainFreshness:
    return OptionChainFreshness(
        status=status,
        source_type=source_type,
        loaded_at=NOW,
        age_seconds=None,
        reason_code=None,
    )


def test_static_fixture_data_produces_static_fixture_context_and_caution() -> None:
    flags = build_option_chain_context_flags(
        selection_view(),
        freshness("static_fixture", source_type="fixture"),
    )

    assert flags.data_context == "static_fixture"
    assert flags.operator_warning_level == "caution"
    assert "static_fixture_not_live" in flags.reason_codes


def test_fresh_non_static_sample_classifies_as_fresh_live() -> None:
    flags = build_option_chain_context_flags(selection_view(), freshness("fresh"))

    assert flags.data_context == "fresh_live"
    assert flags.operator_warning_level == "info"
    assert flags.straddle_context == "available"


def test_stale_non_static_sample_classifies_as_stale_live_with_warning() -> None:
    flags = build_option_chain_context_flags(selection_view(), freshness("stale"))

    assert flags.data_context == "stale_live"
    assert flags.operator_warning_level == "caution"
    assert "data_stale_live" in flags.reason_codes


def test_missing_straddle_adds_reason_code() -> None:
    view = selection_view()
    assert view.selected_expiration is not None
    straddle = replace(
        view.selected_expiration.atm_straddle,
        status="unavailable",
        value=None,
        reason_codes=("atm_leg_unavailable",),
    )
    expiration = replace(view.selected_expiration, atm_straddle=straddle)
    mutated = replace(view, selected_expiration=expiration)

    flags = build_option_chain_context_flags(mutated, freshness("fresh"))

    assert flags.straddle_context == "unavailable"
    assert flags.operator_warning_level == "caution"
    assert "atm_straddle_unavailable" in flags.reason_codes


def test_wide_or_unavailable_liquidity_adds_reason_code() -> None:
    view = selection_view()
    assert view.selected_expiration is not None
    first_item = view.selected_expiration.contracts[0]
    wide_liquidity = replace(first_item.liquidity, spread_state="wide")
    contracts = (
        replace(first_item, liquidity=wide_liquidity),
        *view.selected_expiration.contracts[1:],
    )
    mutated = replace(
        view,
        selected_expiration=replace(view.selected_expiration, contracts=contracts),
    )

    flags = build_option_chain_context_flags(mutated, freshness("fresh"))

    assert flags.liquidity_context == "mixed"
    assert flags.operator_warning_level == "caution"
    assert "liquidity_mixed" in flags.reason_codes


def test_missing_or_partial_greeks_add_reason_code() -> None:
    view = selection_view()
    assert view.selected_expiration is not None
    first_item = view.selected_expiration.contracts[0]
    contract = replace(first_item.contract, delta=None, gamma=None, theta=None)
    contracts = (
        replace(first_item, contract=contract),
        *view.selected_expiration.contracts[1:],
    )
    mutated = replace(
        view,
        selected_expiration=replace(view.selected_expiration, contracts=contracts),
    )

    flags = build_option_chain_context_flags(mutated, freshness("fresh"))

    assert flags.greek_context == "partial"
    assert flags.operator_warning_level == "caution"
    assert "greeks_partial" in flags.reason_codes


def test_context_flags_do_not_include_directional_bias_or_trade_recommendations() -> None:
    flags = build_option_chain_context_flags(selection_view(), freshness("static_fixture"))
    rendered = repr(flags).lower()

    forbidden_terms = (
        "bullish",
        "bearish",
        "long",
        "short",
        "buy",
        "sell",
        "recommend",
        "authorize",
        "permission",
    )
    assert all(term not in rendered for term in forbidden_terms)


def test_context_module_does_not_import_playbook_authorization_modules() -> None:
    tree = ast.parse(CONTEXT_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = {
        "spx_inventory_playbook.playbook",
        "spx_inventory_playbook.rules",
        "spx_inventory_playbook.validators",
        "spx_inventory_playbook.positions",
    }
    assert imported.isdisjoint(forbidden)
