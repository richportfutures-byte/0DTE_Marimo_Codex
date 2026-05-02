from __future__ import annotations

import io
import json
import socket
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (
    MANUAL_LIVE_CONFIRM_PHRASE,
    SCHWAB_OPTION_CHAIN_ENDPOINT,
    ManualLiveSchwabOptionChainConfig,
    build_schwab_option_chain_request_spec,
    extract_access_token_from_text,
    format_live_harness_summary,
    run_manual_live_schwab_option_chain_selection,
)


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


def load_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def live_config(**overrides: object) -> ManualLiveSchwabOptionChainConfig:
    values = {"confirm_live": MANUAL_LIVE_CONFIRM_PHRASE}
    values.update(overrides)
    return ManualLiveSchwabOptionChainConfig(**values)


def successful_fetcher(request_spec: object, access_token: str) -> dict[str, object]:
    assert access_token == RAW_TOKEN
    assert repr(request_spec).find(RAW_TOKEN) == -1
    return load_payload()


def test_live_harness_refuses_without_exact_manual_confirmation_phrase() -> None:
    calls: list[object] = []

    def fetcher(request_spec: object, access_token: str) -> dict[str, object]:
        calls.append((request_spec, access_token))
        return load_payload()

    result = run_manual_live_schwab_option_chain_selection(
        config=ManualLiveSchwabOptionChainConfig(confirm_live="wrong"),
        access_token_stdin=io.StringIO(RAW_TOKEN),
        http_get_json=fetcher,
        now=NOW,
    )

    assert result.status == "unavailable"
    assert result.reason_code == "manual_live_confirmation_required"
    assert result.live_mode_used is False
    assert calls == []


def test_live_harness_refuses_without_credential_source() -> None:
    calls: list[object] = []

    def fetcher(request_spec: object, access_token: str) -> dict[str, object]:
        calls.append((request_spec, access_token))
        return load_payload()

    result = run_manual_live_schwab_option_chain_selection(
        config=live_config(),
        http_get_json=fetcher,
        now=NOW,
    )

    assert result.status == "unavailable"
    assert result.reason_code == "access_token_required"
    assert result.live_mode_used is False
    assert calls == []


def test_request_builder_uses_exact_safe_endpoint_path_and_query_names() -> None:
    request_spec = build_schwab_option_chain_request_spec(live_config())

    assert request_spec.endpoint_url == SCHWAB_OPTION_CHAIN_ENDPOINT
    assert request_spec.query == (
        ("symbol", "$SPX"),
        ("contractType", "ALL"),
        ("strategy", "SINGLE"),
        ("strikeCount", "2"),
        ("includeUnderlyingQuote", "TRUE"),
    )
    assert request_spec.url.startswith(
        "https://api.schwabapi.com/marketdata/v1/chains?"
    )
    assert "Authorization" not in repr(request_spec)


def test_request_builder_defaults_to_spx_and_include_underlying_quote() -> None:
    request_spec = build_schwab_option_chain_request_spec(
        ManualLiveSchwabOptionChainConfig()
    )

    assert ("symbol", "$SPX") in request_spec.query
    assert ("includeUnderlyingQuote", "TRUE") in request_spec.query


def test_token_json_bundle_extraction_returns_token_without_printing_it() -> None:
    token = extract_access_token_from_text(
        json.dumps({"access_token": RAW_TOKEN, "refresh_token": "refresh-secret"})
    )
    raw_token = extract_access_token_from_text(RAW_TOKEN)

    assert token == RAW_TOKEN
    assert raw_token == RAW_TOKEN


def test_http_401_400_and_timeout_errors_map_to_safe_reason_codes() -> None:
    def unauthorized(request_spec: object, access_token: str) -> dict[str, object]:
        raise urllib.error.HTTPError(
            url="https://api.schwabapi.com/marketdata/v1/chains",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b'{"access_token":"secret"}'),
        )

    def bad_request(request_spec: object, access_token: str) -> dict[str, object]:
        raise urllib.error.HTTPError(
            url="https://api.schwabapi.com/marketdata/v1/chains",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(b'{"raw":"payload"}'),
        )

    def timeout(request_spec: object, access_token: str) -> dict[str, object]:
        raise socket.timeout("timed out")

    results = [
        run_manual_live_schwab_option_chain_selection(
            config=live_config(),
            access_token_stdin=io.StringIO(RAW_TOKEN),
            http_get_json=fetcher,
            now=NOW,
        )
        for fetcher in (unauthorized, bad_request, timeout)
    ]

    assert [item.reason_code for item in results] == [
        "http_401_unauthorized",
        "http_400_bad_request",
        "http_timeout_or_connection_error",
    ]
    assert [item.live_mode_used for item in results] == [True, True, True]


def test_successful_mocked_http_response_parses_and_builds_selection_view() -> None:
    result = run_manual_live_schwab_option_chain_selection(
        config=live_config(),
        access_token_stdin=io.StringIO(RAW_TOKEN),
        http_get_json=successful_fetcher,
        now=NOW,
    )

    assert result.status == "available"
    assert result.reason_code is None
    assert result.provider_result is not None
    assert result.provider_result.snapshot is not None
    assert result.provider_result.snapshot.provider_symbol == "$SPX"
    assert result.provider_result.selection_view is not None
    assert result.provider_result.selection_view.status == "available"
    assert result.provider_result.selection_view.selected_expiration is not None


def test_successful_mocked_result_includes_freshness_context_summary() -> None:
    result = run_manual_live_schwab_option_chain_selection(
        config=live_config(),
        access_token_stdin=io.StringIO(RAW_TOKEN),
        http_get_json=successful_fetcher,
        now=NOW,
    )

    summary = format_live_harness_summary(result)

    assert result.freshness is not None
    assert result.freshness.status == "fresh"
    assert result.context_flags is not None
    assert result.context_flags.data_context == "fresh_live"
    assert "live_mode_used: yes" in summary
    assert "provider_status: available" in summary
    assert "provider_symbol: $SPX" in summary
    assert "underlying_symbol: SPX" in summary
    assert "freshness_status: fresh" in summary
    assert "data_context: fresh_live" in summary
    assert "selected_contract_count: 4" in summary


def test_output_repr_and_log_text_do_not_include_token_header_or_payload_body() -> None:
    result = run_manual_live_schwab_option_chain_selection(
        config=live_config(),
        access_token_stdin=io.StringIO(RAW_TOKEN),
        http_get_json=lambda _request, _token: load_payload()
        | {"rawPayloadMarker": RAW_PAYLOAD_MARKER},
        now=NOW,
    )
    rendered = f"{result!r} {result!s} {format_live_harness_summary(result)}"

    assert RAW_TOKEN not in rendered
    assert "Authorization" not in rendered
    assert "Bearer" not in rendered
    assert RAW_PAYLOAD_MARKER not in rendered
    assert "callExpDateMap" not in rendered
    assert "putExpDateMap" not in rendered


def test_no_network_calls_occur_when_fetcher_is_injected() -> None:
    calls: list[str] = []

    def fetcher(request_spec: object, access_token: str) -> dict[str, object]:
        calls.append("mocked")
        return load_payload()

    result = run_manual_live_schwab_option_chain_selection(
        config=live_config(),
        access_token_stdin=io.StringIO(RAW_TOKEN),
        http_get_json=fetcher,
        now=NOW,
    )

    assert result.status == "available"
    assert calls == ["mocked"]
