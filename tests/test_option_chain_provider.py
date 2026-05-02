from __future__ import annotations

from pathlib import Path

from spx_inventory_playbook.adapters.option_chain_provider import (
    FixtureOptionChainProvider,
    LiveSchwabOptionChainProvider,
)
from spx_inventory_playbook.adapters.schwab_option_chain import SchwabOptionChainSnapshot
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    OptionChainSelectionView,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)


def test_fixture_provider_loads_captured_fixture_and_returns_available_result() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH).get_spx_0dte_selection()

    assert result.status == "available"
    assert result.reason_code is None
    assert result.fixture_path == FIXTURE_PATH


def test_fixture_provider_returns_parsed_snapshot_and_selection_view() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH).get_spx_0dte_selection()

    assert isinstance(result.snapshot, SchwabOptionChainSnapshot)
    assert isinstance(result.selection_view, OptionChainSelectionView)
    assert result.snapshot.provider_symbol == "$SPX"
    assert result.selection_view.status == "available"
    assert result.selection_view.selected_expiration is not None


def test_fixture_provider_result_has_provider_and_source_metadata() -> None:
    result = FixtureOptionChainProvider(
        FIXTURE_PATH,
        provider_name="fixture_provider",
        source_label="captured_schwab_fixture",
    ).get_spx_0dte_selection()

    assert result.provider_name == "fixture_provider"
    assert result.source_label == "captured_schwab_fixture"


def test_missing_fixture_path_returns_error_without_traceback_leakage(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    result = FixtureOptionChainProvider(missing_path).get_spx_0dte_selection()

    assert result.status == "error"
    assert result.reason_code == "fixture_not_found"
    assert result.snapshot is None
    assert result.selection_view is None
    rendered = repr(result)
    assert "Traceback" not in rendered
    assert "FileNotFoundError" not in rendered


def test_malformed_fixture_json_returns_error_without_raw_body_leakage(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "malformed.json"
    fixture_path.write_text("{ secret-token-value raw-payload-body", encoding="utf-8")

    result = FixtureOptionChainProvider(fixture_path).get_spx_0dte_selection()

    assert result.status == "error"
    assert result.reason_code == "fixture_json_malformed"
    assert result.snapshot is None
    assert result.selection_view is None
    rendered = repr(result)
    assert "secret-token-value" not in rendered
    assert "raw-payload-body" not in rendered


def test_structurally_malformed_fixture_returns_error_without_payload_leakage(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "bad-shape.json"
    fixture_path.write_text(
        '{"symbol":"$SPX","callExpDateMap":"secret-token-value raw-payload-body"}',
        encoding="utf-8",
    )

    result = FixtureOptionChainProvider(fixture_path).get_spx_0dte_selection()

    assert result.status == "error"
    assert result.reason_code == "fixture_parse_error"
    rendered = f"{result!r} {result!s}"
    assert "secret-token-value" not in rendered
    assert "raw-payload-body" not in rendered


def test_provider_result_repr_is_metadata_only() -> None:
    result = FixtureOptionChainProvider(FIXTURE_PATH).get_spx_0dte_selection()

    rendered = repr(result)

    assert "provider_name='schwab_fixture'" in rendered
    assert "status='available'" in rendered
    assert "has_snapshot=True" in rendered
    assert "has_selection_view=True" in rendered
    assert "callExpDateMap" not in rendered
    assert "putExpDateMap" not in rendered
    assert "SPXW  " not in rendered


def test_live_placeholder_is_fail_closed_and_non_executing() -> None:
    result = LiveSchwabOptionChainProvider().get_spx_0dte_selection()

    assert result.provider_name == "schwab_live"
    assert result.source_label == "live"
    assert result.status == "unavailable"
    assert result.reason_code == "live_provider_not_implemented"
    assert result.snapshot is None
    assert result.selection_view is None
    assert result.fixture_path is None
