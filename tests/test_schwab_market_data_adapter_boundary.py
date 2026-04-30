import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "market_data" / "schwab"
SCHWAB_TEST_FILES = (
    ROOT / "tests" / "test_schwab_market_data_fixture_mapper.py",
    ROOT / "tests" / "test_schwab_market_data_adapter_boundary.py",
)
CORE_MARKET_DATA_PATH = ROOT / "src" / "spx_inventory_playbook" / "market_data.py"
FORBIDDEN_FIXTURE_TEXT = (
    "account" + "_id",
    "account" + "Number",
    "app" + "_key",
    "client" + "_secret",
    "access" + "_token",
    "refresh" + "_token",
    "bearer ",
    "authorization",
    "credential",
    "wss://",
    "https://",
)
FORBIDDEN_TEST_MODULES = {
    "http.client",
    "httpx",
    "requests",
    "socket",
    "urllib",
    "urllib.request",
    "websocket",
}
ORDER_ROUTING_TERMS = (
    "place" + "_order",
    "route" + "_order",
    "submit" + "_order",
    "execute" + "_trade",
    "automated" + "_trading",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def fixture_payloads() -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for path in sorted(FIXTURES.glob("*.json")):
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


def test_sanitized_schwab_fixture_directory_contains_expected_payloads() -> None:
    names = {path.name for path in FIXTURES.glob("*.json")}

    assert names == {
        "underlying_quote.valid.json",
        "option_chain_0dte.valid.json",
        "option_chain_0dte.partial.json",
        "option_chain_0dte.crossed_quote.json",
        "option_chain_0dte.locked_quote.json",
        "option_chain_0dte.missing_greeks.json",
        "option_chain_0dte.mismatched_expiry.json",
        "option_chain_0dte.mark_only_underlying.json",
    }


def test_sanitized_schwab_fixtures_are_marked_as_fixtures() -> None:
    for payload in fixture_payloads():
        assert payload["fixture"] is True
        assert payload["provider"] == "schwab"
        assert payload["request_id"] == "fixture-request-id"


def test_sanitized_schwab_fixtures_do_not_contain_sensitive_values() -> None:
    for path in FIXTURES.glob("*.json"):
        text = path.read_text(encoding="utf-8").lower()
        assert not any(value.lower() in text for value in FORBIDDEN_FIXTURE_TEXT)


def test_sanitized_schwab_fixture_numbers_are_decimal_compatible_strings() -> None:
    numeric_keys = {
        "bid",
        "ask",
        "last",
        "mark",
        "strike",
        "delta",
        "gamma",
        "theta",
        "vega",
        "iv",
        "bid_size",
        "ask_size",
        "volume",
        "open_interest",
        "dte",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in numeric_keys and nested is not None:
                    assert isinstance(nested, str), f"{key} must be a string"
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    for payload in fixture_payloads():
        walk(payload)


def test_schwab_fixture_mapper_tests_do_not_import_network_modules() -> None:
    for path in SCHWAB_TEST_FILES:
        assert imported_modules(path).isdisjoint(FORBIDDEN_TEST_MODULES)


def test_schwab_fixture_mapper_tests_do_not_reference_local_auth_paths() -> None:
    forbidden_path_patterns = (
        "Path" + ".home(",
        ".expand" + "user(",
        "." + "env",
        "." + "state",
        "auth" + "_state",
        "credentials" + ".json",
        "token" + ".json",
    )

    for path in SCHWAB_TEST_FILES:
        text = path.read_text(encoding="utf-8")
        assert not any(pattern in text for pattern in forbidden_path_patterns)


def test_core_market_data_contracts_remain_free_of_schwab_specific_terms() -> None:
    text = CORE_MARKET_DATA_PATH.read_text(encoding="utf-8").lower()

    assert "schwab" not in text
    assert "tdameritrade" not in text
    assert "thinkorswim" not in text


def test_schwab_fixture_mapper_tests_do_not_introduce_order_routing_language() -> None:
    for path in SCHWAB_TEST_FILES:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in ORDER_ROUTING_TERMS)
