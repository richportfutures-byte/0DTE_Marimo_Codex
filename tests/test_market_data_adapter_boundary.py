import ast
import os
from pathlib import Path

import pytest

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


ROOT = Path(__file__).resolve().parents[1]
CORE_MARKET_DATA_PATH = ROOT / "src/spx_inventory_playbook/market_data.py"
CONTRACT_TEST_FILES = (
    ROOT / "tests/test_market_data_contracts.py",
    ROOT / "tests/test_market_data_freshness.py",
    ROOT / "tests/test_option_chain_snapshot.py",
    ROOT / "tests/test_atm_straddle_snapshot.py",
    ROOT / "tests/test_market_data_health.py",
    ROOT / "tests/test_market_data_adapter_boundary.py",
)
CANONICAL_CONTRACT_NAMES = {
    "MarketDataSource",
    "QuoteFreshness",
    "UnderlyingQuoteSnapshot",
    "OptionContractKey",
    "OptionQuoteSnapshot",
    "ExpirySnapshot",
    "OptionChainSnapshot",
    "AtmStraddleSnapshot",
    "MarketDataHealth",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_core_market_data_module_does_not_import_schwab_adapter() -> None:
    modules = imported_modules(CORE_MARKET_DATA_PATH)

    assert not any("schwab" in module.lower() for module in modules)
    assert not any("adapter" in module.lower() for module in modules)


def test_schwab_specific_names_do_not_leak_into_core_contracts() -> None:
    source = CORE_MARKET_DATA_PATH.read_text().lower()

    assert "schwab" not in source
    assert "tdameritrade" not in source
    assert "thinkorswim" not in source


def test_future_adapter_boundary_returns_canonical_contract_names() -> None:
    exported = {
        MarketDataSource.__name__,
        QuoteFreshness.__name__,
        UnderlyingQuoteSnapshot.__name__,
        OptionContractKey.__name__,
        OptionQuoteSnapshot.__name__,
        ExpirySnapshot.__name__,
        OptionChainSnapshot.__name__,
        AtmStraddleSnapshot.__name__,
        MarketDataHealth.__name__,
    }

    assert exported == CANONICAL_CONTRACT_NAMES


def test_contract_tests_do_not_require_schwab_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in ("SCHWAB_CLIENT_ID", "SCHWAB_CLIENT_SECRET", "SCHWAB_REFRESH_TOKEN"):
        monkeypatch.delenv(key, raising=False)

    assert "SCHWAB_CLIENT_ID" not in os.environ


def test_contract_tests_do_not_read_token_or_auth_paths() -> None:
    forbidden_path_patterns = (
        "Path.home(",
        ".expanduser(",
        ".env",
        "auth_state",
        "credentials.json",
        "token.json",
    )

    for path in CONTRACT_TEST_FILES:
        text = path.read_text()
        assert not any(pattern in text for pattern in forbidden_path_patterns)


def test_no_network_modules_used_by_contract_tests() -> None:
    forbidden_modules = {
        "http.client",
        "httpx",
        "requests",
        "socket",
        "urllib",
        "urllib.request",
        "websocket",
    }

    for path in CONTRACT_TEST_FILES:
        assert imported_modules(path).isdisjoint(forbidden_modules)


def test_order_routing_terms_are_absent_from_market_data_contracts() -> None:
    text = CORE_MARKET_DATA_PATH.read_text().lower()

    for term in ("place_order", "route_order", "submit_order", "execute_trade"):
        assert term not in text
