from __future__ import annotations

import ast
import io
import json
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (
    MANUAL_LIVE_CONFIRM_PHRASE,
)
from spx_inventory_playbook.marimo_option_chain_toggle import (
    FALLBACK_LIVE_TOKEN_FILE_ENV_VAR,
    FIXTURE_OPTION_CHAIN_MODE_LABEL,
    LIVE_OPTION_CHAIN_MODE_LABEL,
    LIVE_TOKEN_FILE_ENV_VAR,
    build_marimo_option_chain_control_state,
    load_marimo_option_chain_provider,
    resolve_live_token_file_path,
)


ROOT = Path(__file__).resolve().parents[1]
TOGGLE_MODULE_PATH = ROOT / "src/spx_inventory_playbook/marimo_option_chain_toggle.py"
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"
FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)
NOW = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
RAW_TOKEN = "secret-access-token-value"
RAW_PAYLOAD_MARKER = "raw-payload-body-marker"


def write_token_file(tmp_path: Path) -> Path:
    token_file = tmp_path / "schwab-token.json"
    token_file.write_text(
        json.dumps({"access_token": "token-file-contents-must-not-be-read"}),
        encoding="utf-8",
    )
    return token_file


def load_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def successful_fetcher(request_spec: object, access_token: str) -> dict[str, object]:
    assert access_token == RAW_TOKEN
    assert "Authorization" not in repr(request_spec)
    return load_payload()


def test_app_defaults_to_fixture_mode_without_live_call(tmp_path: Path) -> None:
    calls: list[str] = []

    result = load_marimo_option_chain_provider(
        selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=write_token_file(tmp_path),
        http_get_json=lambda _request, _token: calls.append("live") or load_payload(),
        now=NOW,
    )

    assert calls == []
    assert result.control_state.live_mode_selected is False
    assert result.provider_result.source_type == "fixture"
    assert result.provider_result.provider_name == "schwab_fixture"
    assert result.freshness.status == "static_fixture"
    assert result.context_flags.data_context == "static_fixture"


def test_live_mode_blocked_without_explicit_mode_selection(tmp_path: Path) -> None:
    control = build_marimo_option_chain_control_state(
        selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        live_token_file_path=write_token_file(tmp_path),
    )

    assert control.live_mode_selected is False
    assert control.live_activation_ready is False
    assert control.requested_source_type == "fixture"


def test_live_mode_blocked_without_exact_confirmation_phrase(tmp_path: Path) -> None:
    calls: list[str] = []

    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live="wrong",
        fixture_path=FIXTURE_PATH,
        live_token_file_path=write_token_file(tmp_path),
        http_get_json=lambda _request, _token: calls.append("live") or load_payload(),
        now=NOW,
    )

    assert calls == []
    assert result.provider_result.source_type == "live"
    assert result.provider_result.status == "unavailable"
    assert result.provider_result.reason_code == "manual_live_confirmation_required"
    assert result.freshness.status == "unavailable"
    assert result.context_flags.data_context == "unavailable"


def test_live_mode_blocked_without_credential_source() -> None:
    calls: list[str] = []

    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=None,
        http_get_json=lambda _request, _token: calls.append("live") or load_payload(),
        now=NOW,
    )

    assert calls == []
    assert result.control_state.credential_source_configured is False
    assert result.provider_result.source_type == "live"
    assert result.provider_result.status == "unavailable"
    assert result.provider_result.reason_code == "access_token_required"


def test_mocked_live_success_renders_live_schwab_provider_not_fixture(
    tmp_path: Path,
) -> None:
    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=write_token_file(tmp_path),
        http_get_json=successful_fetcher,
        access_token_text=RAW_TOKEN,
        now=NOW,
    )

    assert result.control_state.live_activation_ready is True
    assert result.provider_result.source_type == "live"
    assert result.provider_result.provider_name == "schwab_manual_live"
    assert result.provider_result.source_label == "manual_live_schwab_option_chain"
    assert result.provider_result.status == "available"
    assert result.freshness.status == "fresh"
    assert result.provider_state.value == "live_fresh"
    assert result.context_flags.data_context == "fresh_live"


def test_mocked_live_failure_has_safe_reason_without_payload_token_or_header(
    tmp_path: Path,
) -> None:
    def failing_fetcher(request_spec: object, access_token: str) -> dict[str, object]:
        raise urllib.error.HTTPError(
            url="https://api.schwabapi.com/marketdata/v1/chains",
            code=401,
            msg="Unauthorized",
            hdrs={"Authorization": f"Bearer {access_token}"},
            fp=io.BytesIO(
                json.dumps(
                    {
                        "access_token": RAW_TOKEN,
                        "rawPayloadMarker": RAW_PAYLOAD_MARKER,
                    }
                ).encode("utf-8")
            ),
        )

    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=write_token_file(tmp_path),
        http_get_json=failing_fetcher,
        access_token_text=RAW_TOKEN,
        now=NOW,
    )
    rendered = f"{result!r} {result.provider_result!r} {result.context_flags!r}"

    assert result.provider_result.status == "error"
    assert result.provider_result.reason_code == "http_401_unauthorized"
    assert result.provider_state.value == "live_unavailable"
    assert RAW_TOKEN not in rendered
    assert RAW_PAYLOAD_MARKER not in rendered
    assert "Authorization" not in rendered
    assert "Bearer" not in rendered
    assert "callExpDateMap" not in rendered
    assert "putExpDateMap" not in rendered


def test_token_file_path_resolution_uses_env_without_exposing_contents() -> None:
    path = resolve_live_token_file_path({LIVE_TOKEN_FILE_ENV_VAR: "/tmp/token.json"})
    fallback = resolve_live_token_file_path(
        {FALLBACK_LIVE_TOKEN_FILE_ENV_VAR: "/tmp/fallback-token.json"}
    )
    missing = resolve_live_token_file_path({})
    control = build_marimo_option_chain_control_state(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        live_token_file_path=path,
    )

    assert path == Path("/tmp/token.json")
    assert fallback == Path("/tmp/fallback-token.json")
    assert missing is None
    assert "/tmp/token.json" not in repr(control)
    assert control.credential_source_label == "local token file configured"


def test_notebook_source_includes_controlled_live_toggle_labels() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "FIXTURE_OPTION_CHAIN_MODE_LABEL" in source
    assert "LIVE_OPTION_CHAIN_MODE_LABEL" in source
    assert "Refresh Option Chain" in source
    assert "capture-live-option-chain-selection" in source
    assert "Option Chain Failed Live Request" in source
    assert "Option Chain Live Schwab View" in source
    assert "Token file path is read from environment" in source
    assert "Last successful result retained" in source
    assert "Provider state" in source


def test_live_toggle_code_does_not_import_playbook_authorization_modules() -> None:
    tree = ast.parse(TOGGLE_MODULE_PATH.read_text(encoding="utf-8"))
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
