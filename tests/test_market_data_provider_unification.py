from __future__ import annotations

import io
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (
    MANUAL_LIVE_CONFIRM_PHRASE,
    read_access_token,
)
from spx_inventory_playbook.adapters.option_chain_freshness import (
    OptionChainFreshnessThresholds,
    classify_market_data_provider_state,
    classify_option_chain_freshness,
)
from spx_inventory_playbook.adapters.option_chain_provider import (
    FixtureOptionChainProvider,
    MarketDataProviderState,
    OptionChainProviderRequest,
    OptionChainProviderResult,
    evaluate_live_provider_gate,
    summarize_provider_state,
)
from spx_inventory_playbook.marimo_option_chain_toggle import (
    FIXTURE_OPTION_CHAIN_MODE_LABEL,
    LIVE_OPTION_CHAIN_MODE_LABEL,
    build_marimo_option_chain_toggle_result,
    load_marimo_option_chain_provider,
    should_preserve_last_successful_option_chain_result,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)
NOW = datetime(2026, 5, 4, 13, 0, tzinfo=timezone.utc)
RAW_TOKEN = "secret-token-value"
RAW_PAYLOAD_MARKER = "raw-secret-payload-marker"


def load_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def token_file_path(tmp_path: Path) -> Path:
    path = tmp_path / "token.json"
    path.write_text("this-file-must-not-be-read", encoding="utf-8")
    return path


def live_provider_result(
    *,
    status: str = "available",
    loaded_at: datetime | None = NOW,
    reason_code: str | None = None,
) -> OptionChainProviderResult:
    return OptionChainProviderResult(
        provider_name="sample_live",
        source_label="manual_live_schwab_option_chain",
        source_type="live",
        status=status,
        reason_code=reason_code,
        loaded_at=loaded_at,
        is_static_source=False,
    )


def test_fixture_is_default_provider_state() -> None:
    calls: list[str] = []

    result = load_marimo_option_chain_provider(
        selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=None,
        http_get_json=lambda _request, _token: calls.append("live") or load_payload(),
        now=NOW,
    )

    assert calls == []
    assert result.provider_result.source_type == "fixture"
    assert result.provider_state is MarketDataProviderState.FIXTURE


def test_live_mode_blocked_without_confirmation_phrase(tmp_path: Path) -> None:
    gate = evaluate_live_provider_gate(
        OptionChainProviderRequest(
            requested_source_type="live",
            confirm_live="wrong",
            live_token_file_path=token_file_path(tmp_path),
            required_confirmation_phrase=MANUAL_LIVE_CONFIRM_PHRASE,
        )
    )

    assert gate.allowed is False
    assert gate.reason_code == "manual_live_confirmation_required"
    assert "token.json" not in repr(gate)


def test_live_mode_blocked_without_token_file_path() -> None:
    gate = evaluate_live_provider_gate(
        OptionChainProviderRequest(
            requested_source_type="live",
            confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
            live_token_file_path=None,
            required_confirmation_phrase=MANUAL_LIVE_CONFIRM_PHRASE,
        )
    )

    assert gate.allowed is False
    assert gate.reason_code == "access_token_required"


def test_token_file_contents_are_not_read_when_in_memory_token_is_supplied(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    def fetcher(_request: object, access_token: str) -> dict[str, object]:
        calls.append(access_token)
        return load_payload()

    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=token_file_path(tmp_path),
        http_get_json=fetcher,
        access_token_text=RAW_TOKEN,
        now=NOW,
    )

    assert calls == [RAW_TOKEN]
    assert result.provider_state is MarketDataProviderState.LIVE_FRESH


def test_no_live_network_call_occurs_in_fixture_default() -> None:
    calls: list[str] = []

    load_marimo_option_chain_provider(
        selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
        confirm_live="",
        fixture_path=FIXTURE_PATH,
        live_token_file_path=None,
        http_get_json=lambda _request, _token: calls.append("live") or load_payload(),
        now=NOW,
    )

    assert calls == []


def test_stale_live_result_maps_to_live_stale() -> None:
    provider_result = live_provider_result(loaded_at=NOW - timedelta(seconds=90))
    freshness = classify_option_chain_freshness(
        provider_result,
        now=NOW,
        thresholds=OptionChainFreshnessThresholds(fresh_seconds=15, aging_seconds=60),
    )

    assert freshness.status == "stale"
    assert (
        classify_market_data_provider_state(provider_result, freshness)
        is MarketDataProviderState.LIVE_STALE
    )


def test_stale_live_result_is_not_retained_as_last_successful_context() -> None:
    provider_result = live_provider_result(loaded_at=NOW - timedelta(seconds=90))
    toggle_result = build_marimo_option_chain_toggle_result(
        control_state=load_marimo_option_chain_provider(
            selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
            confirm_live="",
            fixture_path=FIXTURE_PATH,
            live_token_file_path=None,
            now=NOW,
        ).control_state,
        provider_result=provider_result,
        now=NOW,
    )

    assert toggle_result.provider_state is MarketDataProviderState.LIVE_STALE
    assert should_preserve_last_successful_option_chain_result(toggle_result) is False


def test_fresh_live_result_maps_to_live_fresh() -> None:
    provider_result = live_provider_result(loaded_at=NOW)
    freshness = classify_option_chain_freshness(provider_result, now=NOW)

    assert freshness.status == "fresh"
    assert (
        classify_market_data_provider_state(provider_result, freshness)
        is MarketDataProviderState.LIVE_FRESH
    )


def test_malformed_live_payload_maps_to_live_parse_error(tmp_path: Path) -> None:
    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=token_file_path(tmp_path),
        http_get_json=lambda _request, _token: {"callExpDateMap": RAW_PAYLOAD_MARKER},
        access_token_text=RAW_TOKEN,
        now=NOW,
    )
    rendered = f"{result!r} {result.provider_result!r}"

    assert result.provider_result.status == "error"
    assert result.provider_result.reason_code == "response_parse_error"
    assert result.provider_state is MarketDataProviderState.LIVE_PARSE_ERROR
    assert RAW_PAYLOAD_MARKER not in rendered
    assert RAW_TOKEN not in rendered


def test_unavailable_live_provider_maps_to_live_unavailable(tmp_path: Path) -> None:
    def unavailable_fetcher(_request: object, access_token: str) -> dict[str, object]:
        raise urllib.error.HTTPError(
            url="https://api.schwabapi.com/marketdata/v1/chains",
            code=401,
            msg="Unauthorized",
            hdrs={"Authorization": f"Bearer {access_token}"},
            fp=io.BytesIO(b"secret body"),
        )

    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=token_file_path(tmp_path),
        http_get_json=unavailable_fetcher,
        access_token_text=RAW_TOKEN,
        now=NOW,
    )
    rendered = f"{result!r} {result.provider_result!r}"

    assert result.provider_state is MarketDataProviderState.LIVE_UNAVAILABLE
    assert result.provider_result.reason_code == "http_401_unauthorized"
    assert "Authorization" not in rendered
    assert "Bearer" not in rendered
    assert RAW_TOKEN not in rendered


def test_no_silent_fallback_from_live_failure_to_fixture(tmp_path: Path) -> None:
    result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live="wrong",
        fixture_path=FIXTURE_PATH,
        live_token_file_path=token_file_path(tmp_path),
        now=NOW,
    )

    assert result.provider_result.source_type == "live"
    assert result.provider_state is MarketDataProviderState.LIVE_UNAVAILABLE
    assert result.provider_result.snapshot is None
    assert result.provider_result.selection_view is None


def test_provider_state_summary_is_safe_and_non_secret() -> None:
    provider_result = live_provider_result(reason_code="http_401_unauthorized")
    freshness = classify_option_chain_freshness(provider_result, now=NOW)
    provider_state = classify_market_data_provider_state(provider_result, freshness)

    summary = summarize_provider_state(provider_result, provider_state)
    rendered = repr(summary)

    assert summary.provider_state is MarketDataProviderState.LIVE_FRESH
    assert "token" not in rendered.lower()
    assert "authorization" not in rendered.lower()
    assert "bearer" not in rendered.lower()
    assert "raw" not in rendered.lower()


def test_read_access_token_can_be_exercised_without_token_file_access() -> None:
    assert read_access_token(access_token_stdin=io.StringIO(RAW_TOKEN)) == RAW_TOKEN


def test_build_toggle_result_surfaces_provider_state_for_downstream_code() -> None:
    fixture_result = FixtureOptionChainProvider(
        FIXTURE_PATH,
        clock=lambda: NOW,
    ).get_spx_0dte_selection()

    result = build_marimo_option_chain_toggle_result(
        control_state=load_marimo_option_chain_provider(
            selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
            confirm_live="",
            fixture_path=FIXTURE_PATH,
            live_token_file_path=None,
            now=NOW,
        ).control_state,
        provider_result=fixture_result,
        now=NOW,
    )

    assert result.provider_state is MarketDataProviderState.FIXTURE
