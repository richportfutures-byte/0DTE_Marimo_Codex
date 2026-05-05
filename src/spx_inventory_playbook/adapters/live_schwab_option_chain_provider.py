"""Manual-gated live Schwab option-chain selection harness.

This module is intentionally outside the Marimo app. It performs one manually
confirmed market-data option-chain request, then reuses the parser, selection,
freshness, and display-only context flag path.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, TextIO

from spx_inventory_playbook.adapters.option_chain_context import (
    OptionChainContextFlags,
    build_option_chain_context_flags,
)
from spx_inventory_playbook.adapters.option_chain_freshness import (
    OptionChainFreshness,
    classify_option_chain_freshness,
)
from spx_inventory_playbook.adapters.option_chain_provider import (
    OptionChainProviderResult,
)
from spx_inventory_playbook.adapters.schwab_option_chain import (
    SchwabOptionChainParserError,
    parse_schwab_option_chain,
)
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    build_spx_0dte_selection_view,
)
from spx_inventory_playbook.adapters.schwab_token_manager import (
    DEFAULT_SCHWAB_TOKEN_URL,
    SchwabTokenManagerError,
    load_access_token_with_refresh_if_needed,
)


MANUAL_LIVE_CONFIRM_PHRASE = "capture-live-option-chain-selection"
SCHWAB_OPTION_CHAIN_ENDPOINT = "https://api.schwabapi.com/marketdata/v1/chains"
SCHWAB_APP_KEY_ENV_VAR = "SCHWAB_APP_KEY"
SCHWAB_APP_SECRET_ENV_VAR = "SCHWAB_APP_SECRET"
SCHWAB_OAUTH_TOKEN_URL_ENV_VAR = "SCHWAB_OAUTH_TOKEN_URL"

LiveHarnessStatus = Literal["available", "unavailable", "error"]
JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ManualLiveSchwabOptionChainConfig:
    confirm_live: str = ""
    symbol: str = "$SPX"
    contract_type: str = "ALL"
    strategy: str = "SINGLE"
    strike_count: int = 2
    include_underlying_quote: bool = True
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class SchwabOptionChainRequestSpec:
    endpoint_url: str
    query: tuple[tuple[str, str], ...]
    timeout_seconds: float

    @property
    def url(self) -> str:
        return f"{self.endpoint_url}?{urllib.parse.urlencode(self.query)}"

    def __repr__(self) -> str:
        return (
            "SchwabOptionChainRequestSpec("
            f"endpoint_url={self.endpoint_url!r}, "
            f"query={self.query!r}, "
            f"timeout_seconds={self.timeout_seconds!r})"
        )


@dataclass(frozen=True)
class LiveSchwabOptionChainHarnessResult:
    status: LiveHarnessStatus
    reason_code: str | None
    live_mode_used: bool
    provider_result: OptionChainProviderResult | None = None
    freshness: OptionChainFreshness | None = None
    context_flags: OptionChainContextFlags | None = None
    http_status: int | None = None
    http_reason: str | None = None

    def __repr__(self) -> str:
        return (
            "LiveSchwabOptionChainHarnessResult("
            f"status={self.status!r}, "
            f"reason_code={self.reason_code!r}, "
            f"live_mode_used={self.live_mode_used!r}, "
            f"http_status={self.http_status!r}, "
            f"http_reason={self.http_reason!r}, "
            f"provider_status={self.provider_result.status if self.provider_result else None!r}, "
            f"freshness_status={self.freshness.status if self.freshness else None!r}, "
            f"data_context={self.context_flags.data_context if self.context_flags else None!r})"
        )

    __str__ = __repr__


def build_schwab_option_chain_request_spec(
    config: ManualLiveSchwabOptionChainConfig,
) -> SchwabOptionChainRequestSpec:
    """Build the only Schwab market-data request this harness is allowed to make."""

    if config.symbol != "$SPX":
        raise ValueError("manual live option-chain harness currently allows only $SPX")
    if config.contract_type != "ALL":
        raise ValueError("contractType must be ALL")
    if config.strategy != "SINGLE":
        raise ValueError("strategy must be SINGLE")
    if config.strike_count < 1 or config.strike_count > 20:
        raise ValueError("strikeCount must be between 1 and 20")
    if not config.include_underlying_quote:
        raise ValueError("includeUnderlyingQuote must be enabled")

    return SchwabOptionChainRequestSpec(
        endpoint_url=SCHWAB_OPTION_CHAIN_ENDPOINT,
        query=(
            ("symbol", config.symbol),
            ("contractType", config.contract_type),
            ("strategy", config.strategy),
            ("strikeCount", str(config.strike_count)),
            ("includeUnderlyingQuote", "TRUE"),
        ),
        timeout_seconds=config.timeout_seconds,
    )


def extract_access_token_from_text(value: str) -> str | None:
    """Extract an access token from raw stdin text or a local JSON token bundle."""

    stripped = value.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if isinstance(parsed, dict):
        token = parsed.get("access_token")
        if isinstance(token, str) and token.strip():
            return token.strip()
    return None


def read_access_token(
    *,
    access_token_file: Path | None = None,
    access_token_stdin: TextIO | None = None,
) -> str | None:
    """Read one local credential source without printing or logging it."""

    if access_token_file is not None and access_token_stdin is not None:
        raise ValueError("choose either access token file or stdin, not both")
    if access_token_file is not None:
        return extract_access_token_from_text(
            access_token_file.read_text(encoding="utf-8")
        )
    if access_token_stdin is not None:
        return extract_access_token_from_text(access_token_stdin.read())
    return None


def run_manual_live_schwab_option_chain_selection(
    *,
    config: ManualLiveSchwabOptionChainConfig,
    access_token_file: Path | None = None,
    access_token_stdin: TextIO | None = None,
    http_get_json: Callable[[SchwabOptionChainRequestSpec, str], JsonObject]
    | None = None,
    app_key: str | None = None,
    app_secret: str | None = None,
    token_url: str | None = None,
    token_refresh_urlopen: Callable[..., object] = urllib.request.urlopen,
    now: datetime | None = None,
) -> LiveSchwabOptionChainHarnessResult:
    """Run one manually gated live selection capture and return safe metadata."""

    if config.confirm_live != MANUAL_LIVE_CONFIRM_PHRASE:
        return LiveSchwabOptionChainHarnessResult(
            status="unavailable",
            reason_code="manual_live_confirmation_required",
            live_mode_used=False,
        )

    token_result = _load_live_access_token(
        access_token_file=access_token_file,
        access_token_stdin=access_token_stdin,
        app_key=app_key,
        app_secret=app_secret,
        token_url=token_url,
        token_refresh_urlopen=token_refresh_urlopen,
    )
    if isinstance(token_result, LiveSchwabOptionChainHarnessResult):
        return token_result
    access_token = token_result

    try:
        request_spec = build_schwab_option_chain_request_spec(config)
        fetcher = http_get_json or _urlopen_json
        payload = fetcher(request_spec, access_token)
        snapshot = parse_schwab_option_chain(payload)
        selection_view = build_spx_0dte_selection_view(snapshot)
    except urllib.error.HTTPError as exc:
        return _http_error_result(exc)
    except (TimeoutError, socket.timeout, urllib.error.URLError):
        return LiveSchwabOptionChainHarnessResult(
            status="error",
            reason_code="http_timeout_or_connection_error",
            live_mode_used=True,
        )
    except SchwabOptionChainParserError:
        return LiveSchwabOptionChainHarnessResult(
            status="error",
            reason_code="response_parse_error",
            live_mode_used=True,
        )
    except (ValueError, OSError, json.JSONDecodeError):
        return LiveSchwabOptionChainHarnessResult(
            status="error",
            reason_code="live_harness_error",
            live_mode_used=True,
        )

    loaded_at = now or datetime.now(timezone.utc)
    provider_result = OptionChainProviderResult(
        provider_name="schwab_manual_live",
        source_label="manual_live_schwab_option_chain",
        source_type="live",
        status=selection_view.status if selection_view.status == "available" else "unavailable",
        reason_code=(
            None
            if selection_view.status == "available"
            else selection_view.reason_codes[0]
            if selection_view.reason_codes
            else "selection_unavailable"
        ),
        loaded_at=loaded_at,
        is_static_source=False,
        snapshot=snapshot,
        selection_view=selection_view,
    )
    freshness = classify_option_chain_freshness(provider_result, now=loaded_at)
    context_flags = build_option_chain_context_flags(selection_view, freshness)
    return LiveSchwabOptionChainHarnessResult(
        status=provider_result.status,
        reason_code=provider_result.reason_code,
        live_mode_used=True,
        provider_result=provider_result,
        freshness=freshness,
        context_flags=context_flags,
    )


def format_live_harness_summary(result: LiveSchwabOptionChainHarnessResult) -> str:
    """Format only sanitized summary diagnostics for terminal output."""

    lines = [
        f"live_mode_used: {'yes' if result.live_mode_used else 'no'}",
        f"provider_status: {result.status}",
    ]
    if result.reason_code:
        lines.append(f"reason_code: {result.reason_code}")
    if result.http_status is not None:
        lines.append(f"http_status: {result.http_status}")
    if result.http_reason:
        lines.append(f"http_reason: {result.http_reason}")

    provider_result = result.provider_result
    selection_view = provider_result.selection_view if provider_result else None
    if provider_result and provider_result.snapshot:
        lines.append(f"provider_symbol: {provider_result.snapshot.provider_symbol}")
        lines.append(f"underlying_symbol: {provider_result.snapshot.underlying_symbol}")
    if selection_view and selection_view.selected_expiration:
        expiration = selection_view.selected_expiration
        lines.append(f"selected_expiration: {expiration.expiration_date.isoformat()}")
        lines.append(f"selected_dte: {expiration.days_to_expiration}")
        lines.append(f"atm_strike: {expiration.atm_strike}")
        lines.append(f"atm_straddle_status: {expiration.atm_straddle.status}")
        if expiration.atm_straddle.value is not None:
            lines.append(f"atm_straddle_value: {expiration.atm_straddle.value}")
        lines.append(f"selected_contract_count: {len(expiration.contracts)}")
    if result.freshness:
        lines.append(f"freshness_status: {result.freshness.status}")
    if result.context_flags:
        lines.append(f"data_context: {result.context_flags.data_context}")
        lines.append(f"operator_warning_level: {result.context_flags.operator_warning_level}")
        if result.context_flags.reason_codes:
            lines.append(
                "context_reason_codes: "
                + ", ".join(result.context_flags.reason_codes)
            )
    return "\n".join(lines) + "\n"


def _urlopen_json(
    request_spec: SchwabOptionChainRequestSpec,
    access_token: str,
) -> JsonObject:
    request = urllib.request.Request(
        request_spec.url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=request_spec.timeout_seconds) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Schwab option-chain response must be a JSON object")
    return parsed


def _load_live_access_token(
    *,
    access_token_file: Path | None,
    access_token_stdin: TextIO | None,
    app_key: str | None,
    app_secret: str | None,
    token_url: str | None,
    token_refresh_urlopen: Callable[..., object],
) -> str | LiveSchwabOptionChainHarnessResult:
    if access_token_file is not None and access_token_stdin is not None:
        return LiveSchwabOptionChainHarnessResult(
            status="unavailable",
            reason_code="access_token_source_conflict",
            live_mode_used=False,
        )
    if access_token_file is not None:
        try:
            return load_access_token_with_refresh_if_needed(
                access_token_file,
                app_key=_resolve_app_key(app_key),
                app_secret=_resolve_app_secret(app_secret),
                token_url=_resolve_token_url(token_url),
                urlopen_func=token_refresh_urlopen,
            )
        except SchwabTokenManagerError as exc:
            return LiveSchwabOptionChainHarnessResult(
                status="error",
                reason_code=exc.reason_code,
                live_mode_used=True,
                http_status=exc.http_status,
            )
    try:
        access_token = read_access_token(access_token_stdin=access_token_stdin)
    except (ValueError, OSError, json.JSONDecodeError):
        access_token = None
    if not access_token:
        return LiveSchwabOptionChainHarnessResult(
            status="unavailable",
            reason_code="access_token_required",
            live_mode_used=False,
        )
    return access_token


def _resolve_app_key(value: str | None) -> str:
    return (value if value is not None else os.environ.get(SCHWAB_APP_KEY_ENV_VAR, "")).strip()


def _resolve_app_secret(value: str | None) -> str:
    return (
        value
        if value is not None
        else os.environ.get(SCHWAB_APP_SECRET_ENV_VAR, "")
    ).strip()


def _resolve_token_url(value: str | None) -> str:
    resolved = (
        value
        if value is not None
        else os.environ.get(SCHWAB_OAUTH_TOKEN_URL_ENV_VAR, "")
    ).strip()
    return resolved or DEFAULT_SCHWAB_TOKEN_URL


def _http_error_result(exc: urllib.error.HTTPError) -> LiveSchwabOptionChainHarnessResult:
    return LiveSchwabOptionChainHarnessResult(
        status="error",
        reason_code=_http_reason_code(exc.code),
        live_mode_used=True,
        http_status=exc.code,
        http_reason=_safe_http_reason(getattr(exc, "reason", None)),
    )


def _http_reason_code(status_code: int) -> str:
    if status_code == 400:
        return "http_400_bad_request"
    if status_code == 401:
        return "http_401_unauthorized"
    return f"http_{status_code}_error"


def _safe_http_reason(reason: object) -> str | None:
    if not isinstance(reason, str):
        return None
    stripped = reason.strip()
    if not stripped or len(stripped) > 80:
        return None
    if not all(char.isalnum() or char in " ._-" for char in stripped):
        return None
    lowered = stripped.lower()
    if any(part in lowered for part in ("token", "secret", "authorization", "bearer")):
        return None
    return stripped


__all__ = [
    "MANUAL_LIVE_CONFIRM_PHRASE",
    "SCHWAB_OPTION_CHAIN_ENDPOINT",
    "SCHWAB_APP_KEY_ENV_VAR",
    "SCHWAB_APP_SECRET_ENV_VAR",
    "SCHWAB_OAUTH_TOKEN_URL_ENV_VAR",
    "LiveSchwabOptionChainHarnessResult",
    "ManualLiveSchwabOptionChainConfig",
    "SchwabOptionChainRequestSpec",
    "build_schwab_option_chain_request_spec",
    "extract_access_token_from_text",
    "format_live_harness_summary",
    "read_access_token",
    "run_manual_live_schwab_option_chain_selection",
]
