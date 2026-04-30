import ast
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from spx_inventory_playbook.market_data import (
    AtmStraddleSnapshot,
    ExpirySnapshot,
    MarketDataSource,
    OptionChainSnapshot,
    OptionContractKey,
    OptionQuoteSnapshot,
    QuoteFreshness,
    UnderlyingQuoteSnapshot,
)
from spx_inventory_playbook.market_data_facade import (
    MarketDataFacadeResult,
    evaluate_market_data_facade,
)


NOW = datetime(2026, 4, 30, 10, 0, tzinfo=ZoneInfo("America/New_York"))
ROOT = Path(__file__).resolve().parents[1]
FACADE_PATH = ROOT / "src" / "spx_inventory_playbook" / "market_data_facade.py"
TEST_PATH = ROOT / "tests" / "test_market_data_facade.py"


def source_fixture() -> MarketDataSource:
    return MarketDataSource(
        provider="fixture",
        adapter="canonical_fixture",
        retrieved_at=NOW,
    )


def expiry_fixture() -> ExpirySnapshot:
    return ExpirySnapshot(
        expiry_date=NOW.date(),
        session_date=NOW.date(),
        dte=0,
        is_0dte=True,
        settlement="PM",
        source=source_fixture(),
    )


def key_fixture(**overrides: object) -> OptionContractKey:
    values = {
        "underlying": "SPX",
        "expiry_date": NOW.date(),
        "strike": Decimal("5000"),
        "right": "CALL",
        "product": "SPXW",
        "provider_symbol": "fixture-symbol",
    }
    values.update(overrides)
    return OptionContractKey(**values)


def quote_fixture(**overrides: object) -> OptionQuoteSnapshot:
    values = {
        "key": key_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("10.00"),
        "ask": Decimal("10.40"),
        "delta": Decimal("0.50"),
        "gamma": Decimal("0.010"),
        "theta": Decimal("-0.40"),
        "vega": Decimal("0.08"),
        "iv": Decimal("0.18"),
    }
    values.update(overrides)
    return OptionQuoteSnapshot(**values)


def put_quote_fixture(**overrides: object) -> OptionQuoteSnapshot:
    values = {
        "key": key_fixture(right="PUT", provider_symbol="fixture-put"),
        "bid": Decimal("9.80"),
        "ask": Decimal("10.20"),
        "delta": Decimal("-0.50"),
    }
    values.update(overrides)
    return quote_fixture(**values)


def underlying_fixture(**overrides: object) -> UnderlyingQuoteSnapshot:
    values = {
        "symbol": "SPX",
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "bid": Decimal("4999.00"),
        "ask": Decimal("5001.00"),
    }
    values.update(overrides)
    return UnderlyingQuoteSnapshot(**values)


def chain_fixture(**overrides: object) -> OptionChainSnapshot:
    values = {
        "underlying_symbol": "SPX",
        "expiry": expiry_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "contracts": (
            quote_fixture(key=key_fixture(right="CALL", provider_symbol="fixture-call")),
            put_quote_fixture(),
        ),
        "is_partial": False,
        "completeness_notes": (),
    }
    values.update(overrides)
    return OptionChainSnapshot(**values)


def straddle_fixture(**overrides: object) -> AtmStraddleSnapshot:
    call = quote_fixture(
        key=key_fixture(right="CALL", provider_symbol="fixture-call"),
        bid=Decimal("10.00"),
        ask=Decimal("10.40"),
    )
    put = put_quote_fixture()
    values = {
        "underlying_symbol": "SPX",
        "underlying_price": Decimal("5000"),
        "underlying_quote": underlying_fixture(),
        "expiry": expiry_fixture(),
        "source": source_fixture(),
        "as_of": NOW,
        "freshness": QuoteFreshness.FRESH,
        "call": call,
        "put": put,
        "width_points": Decimal("20.20"),
        "width_percent": Decimal("0.00404"),
    }
    values.update(overrides)
    return AtmStraddleSnapshot(**values)


def test_missing_underlying_blocks_derived_outputs() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=None,
        option_chain=chain_fixture(),
        atm_straddle=None,
    )

    assert result.health.status == "BLOCKED"
    assert "underlying_quote" in result.health.missing_fields
    assert result.underlying_usable is False
    assert result.chain_derived_outputs_usable is False
    assert result.atm_straddle_usable is False
    assert result.api_outputs_usable is False


def test_stale_underlying_requires_manual_confirmation() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(freshness=QuoteFreshness.STALE),
        option_chain=chain_fixture(),
        atm_straddle=straddle_fixture(freshness=QuoteFreshness.STALE),
    )

    assert result.health.status == "BLOCKED"
    assert "underlying_quote" in result.health.stale_fields
    assert result.underlying_usable is False
    assert result.manual_confirmation_required is True


def test_missing_chain_blocks_option_workflow() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=None,
        atm_straddle=None,
    )

    assert result.health.status == "BLOCKED"
    assert result.underlying_usable is True
    assert result.option_chain_usable is False
    assert "option_chain" in result.health.missing_fields


def test_partial_chain_degrades_health_and_preserves_completeness_notes() -> None:
    partial_chain = chain_fixture(
        is_partial=True,
        completeness_notes=("ATM neighborhood is incomplete.",),
    )

    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=partial_chain,
        atm_straddle=straddle_fixture(),
    )

    assert result.health.status == "DEGRADED"
    assert result.option_chain_usable is False
    assert "ATM neighborhood is incomplete." in result.health.warnings
    assert result.api_outputs_usable is False


def test_locked_quote_degrades_liquidity_if_detectable() -> None:
    locked_call = quote_fixture(bid=Decimal("10.00"), ask=Decimal("10.00"))
    chain = chain_fixture(
        contracts=(locked_call, put_quote_fixture()),
    )

    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=chain,
        atm_straddle=None,
    )

    assert result.health.status == "DEGRADED"
    assert result.option_chain_usable is False
    assert any("Locked option quote" in warning for warning in result.health.warnings)


def test_missing_greeks_are_allowed_but_greek_checks_are_unavailable() -> None:
    call = quote_fixture(delta=None, gamma=None, theta=None, vega=None, iv=None)
    put = put_quote_fixture(delta=None, gamma=None, theta=None, vega=None, iv=None)

    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=chain_fixture(contracts=(call, put)),
        atm_straddle=straddle_fixture(call=call, put=put),
    )

    assert result.option_chain_usable is True
    assert result.greek_checks_available is False
    assert any("Greeks unavailable" in warning for warning in result.health.warnings)


def test_missing_atm_straddle_blocks_straddle_outputs() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=chain_fixture(),
        atm_straddle=None,
    )

    assert result.health.status == "DEGRADED"
    assert "atm_straddle" in result.health.missing_fields
    assert result.atm_straddle_usable is False
    assert result.api_outputs_usable is False


def test_stale_atm_straddle_blocks_straddle_outputs() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=chain_fixture(),
        atm_straddle=straddle_fixture(freshness=QuoteFreshness.STALE),
    )

    assert result.health.status == "DEGRADED"
    assert "atm_straddle" in result.health.stale_fields
    assert result.atm_straddle_usable is False


def test_healthy_inputs_return_usable_data_status() -> None:
    result = evaluate_market_data_facade(
        underlying_quote=underlying_fixture(),
        option_chain=chain_fixture(),
        atm_straddle=straddle_fixture(),
    )

    assert isinstance(result, MarketDataFacadeResult)
    assert result.health.status == "OK"
    assert result.underlying_usable is True
    assert result.option_chain_usable is True
    assert result.atm_straddle_usable is True
    assert result.api_outputs_usable is True
    assert result.manual_confirmation_required is False


def test_facade_has_no_provider_specific_imports() -> None:
    tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert f"spx_inventory_playbook.adap{'ters'}" not in modules


def test_facade_exposes_only_broker_neutral_names() -> None:
    text = FACADE_PATH.read_text(encoding="utf-8").lower()
    avoided_terms = (f"sch{'wab'}", "thinkorswim", "tdameritrade")

    assert not any(term in text for term in avoided_terms)


def test_facade_does_not_use_external_io_sources() -> None:
    tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    blocked_modules = {
        "os",
        "pathlib",
        f"urll{'ib'}",
        f"requ{'ests'}",
        f"htt{'px'}",
        f"sock{'et'}",
        f"websock{'et'}",
    }
    assert imported.isdisjoint(blocked_modules)


def test_facade_avoids_action_language() -> None:
    terms = (
        f"ord{'er'}",
        f"rou{'te'}",
        f"execu{'tion'}",
        f"fi{'ll'}",
        f"acc{'ount'}",
        f"posi{'tion'}",
    )

    for path in (FACADE_PATH, TEST_PATH):
        text = path.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in terms)
