from __future__ import annotations

import ast
from datetime import date, datetime, timezone
from pathlib import Path

from spx_inventory_playbook.paper_trades import (
    PaperTradeIntent,
    PaperTradeLedger,
    PaperTradeLeg,
    create_paper_trade_intent,
    validate_paper_trade_intent,
)


ROOT = Path(__file__).resolve().parents[1]
PAPER_MODULE_PATH = ROOT / "src/spx_inventory_playbook/paper_trades.py"
CREATED_AT = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)


def valid_intent(**overrides: object) -> PaperTradeIntent:
    values = {
        "created_at": CREATED_AT,
        "strategy_label": "ATM paper straddle observation",
        "thesis": "Practice observing ATM quote width and liquidity state.",
        "invalidation": "Stop paper observation if fixture context is misunderstood.",
        "operator_acknowledged_context": True,
    }
    values.update(overrides)
    return create_paper_trade_intent(**values)


def test_paper_intent_validates_with_required_fields() -> None:
    validation = validate_paper_trade_intent(valid_intent())

    assert validation.is_valid is True
    assert validation.reason_codes == ()


def test_empty_strategy_thesis_or_invalidation_fail_validation() -> None:
    intent = valid_intent(strategy_label="", thesis="", invalidation="")

    validation = validate_paper_trade_intent(intent)

    assert validation.is_valid is False
    assert validation.reason_codes == (
        "strategy_label_required",
        "thesis_required",
        "invalidation_required",
    )


def test_intent_records_paper_only_not_broker_submitted_metadata() -> None:
    intent = valid_intent()

    assert intent.is_paper_only is True
    assert intent.broker_submitted is False
    assert intent.paper_disclaimer == "local_paper_intent_only_no_broker_submission"


def test_intent_can_include_option_chain_context_and_leg_metadata() -> None:
    leg = PaperTradeLeg(
        provider_symbol="SPXW  260504C07230000",
        side="CALL",
        expiration=date(2026, 5, 4),
        strike=7230.0,
        reference_mark=17.0,
    )
    intent = valid_intent(
        legs=(leg,),
        entry_reference=43.25,
        option_chain_source_label="fixture: sanitized Schwab option-chain capture",
        option_chain_freshness_status="static_fixture",
        option_chain_data_context="static_fixture",
        option_chain_warning_level="caution",
        option_chain_reason_codes=("static_fixture_not_live",),
        playbook_status_label="normal",
        playbook_allowed_actions=("hold", "reduce"),
    )

    assert intent.legs == (leg,)
    assert intent.entry_reference == 43.25
    assert intent.option_chain_source_label == "fixture: sanitized Schwab option-chain capture"
    assert intent.option_chain_freshness_status == "static_fixture"
    assert intent.option_chain_data_context == "static_fixture"
    assert intent.option_chain_warning_level == "caution"
    assert intent.option_chain_reason_codes == ("static_fixture_not_live",)
    assert intent.playbook_status_label == "normal"
    assert intent.playbook_allowed_actions == ("hold", "reduce")


def test_ledger_append_adds_immutable_records_without_mutating_previous_entries() -> None:
    ledger = PaperTradeLedger()
    first = valid_intent(strategy_label="first")
    second = valid_intent(strategy_label="second")

    ledger_after_first, first_validation = ledger.append(first)
    ledger_after_second, second_validation = ledger_after_first.append(second)

    assert first_validation.is_valid is True
    assert second_validation.is_valid is True
    assert ledger.records == ()
    assert ledger_after_first.records == (first,)
    assert ledger_after_second.records == (first, second)


def test_ledger_rejects_invalid_records_without_mutating() -> None:
    ledger = PaperTradeLedger()
    invalid = valid_intent(strategy_label="")

    next_ledger, validation = ledger.append(invalid)

    assert validation.is_valid is False
    assert validation.reason_codes == ("strategy_label_required",)
    assert next_ledger is ledger
    assert next_ledger.records == ()


def test_static_or_stale_context_requires_operator_acknowledgement() -> None:
    static_intent = valid_intent(
        option_chain_data_context="static_fixture",
        operator_acknowledged_context=False,
    )
    stale_intent = valid_intent(
        option_chain_data_context="stale_live",
        operator_acknowledged_context=False,
    )

    assert validate_paper_trade_intent(static_intent).reason_codes == (
        "option_chain_context_acknowledgement_required",
    )
    assert validate_paper_trade_intent(stale_intent).reason_codes == (
        "option_chain_context_acknowledgement_required",
    )


def test_paper_module_does_not_import_broker_or_authorization_modules() -> None:
    tree = ast.parse(PAPER_MODULE_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden_terms = (
        "schwab",
        "broker",
        "account",
        "order",
        "position",
        "fill",
        "pnl",
        "playbook",
        "rules",
        "validators",
    )
    assert all(
        not any(term in module.lower() for term in forbidden_terms)
        for module in imported
    )
