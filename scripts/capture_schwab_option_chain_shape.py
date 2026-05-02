#!/usr/bin/env python3
"""Manual opt-in Schwab option-chain capture sanitizer.

This script is evidence tooling for parser design only. It is intentionally
standalone and is not imported by the notebook or production app modules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TextIO
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


DEFAULT_OUTPUT_PATH = Path(
    "tests/fixtures/market_data/schwab/raw_option_chain_0dte.sanitized.json"
)
DEFAULT_CONFIRM_PHRASE = "capture-sanitized-option-chain-shape"
DEFAULT_CHAIN_URL = "https://api.schwabapi.com/marketdata/v1/chains"
SENSITIVE_REPLACEMENT = "[REDACTED]"

SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "credential",
    "authorization",
    "bearer",
    "account",
    "customer",
    "client_secret",
    "clientid",
    "client_id",
    "access_token",
    "refresh_token",
    "callback",
    "auth",
    "request_id",
    "requestid",
    "correlation",
    "correl",
    "streamerid",
)

SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(
        r"(?i)(access_token|refresh_token|client_secret|credential|authorization|callback)="
    ),
    re.compile(r"(?i)(^|/)\.state(/|$)"),
    re.compile(r"^/Users/[^/]+/"),
    re.compile(r"^[A-Za-z]:\\"),
    re.compile(r"(?i)^https?://(localhost|127\.0\.0\.1)(:|/|$)"),
)
SENSITIVE_CATEGORY_PARTS = (
    "token",
    "secret",
    "credential",
    "bearer",
    "account",
    "customer",
    "client_secret",
    "clientid",
    "client_id",
    "access_token",
    "refresh_token",
    "callback",
)


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


@dataclass(frozen=True)
class OptionChainCaptureRequest:
    """A manually authorized market-data option-chain request."""

    url: str
    symbol: str
    timeout_seconds: float
    live_credential: str
    query: tuple[tuple[str, str], ...]


def sanitize_payload(value: JsonValue) -> JsonValue:
    """Remove sensitive fields and redact sensitive-looking string values."""

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, nested in value.items():
            if _is_sensitive_key(str(key)):
                continue
            sanitized[str(key)] = sanitize_payload(nested)
        return sanitized
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _sanitize_string(value)
    return value


def compact_option_chain_sample(
    payload: JsonValue,
    *,
    max_strikes_per_side: int = 2,
) -> JsonValue:
    """Keep a small raw-shape sample while preserving call/put map structure."""

    if not isinstance(payload, dict) or max_strikes_per_side <= 0:
        return payload

    compacted = dict(payload)
    call_key = _find_option_map_key(compacted, "call")
    put_key = _find_option_map_key(compacted, "put")
    if call_key is None and put_key is None:
        return compacted

    call_map = compacted.get(call_key) if call_key is not None else None
    put_map = compacted.get(put_key) if put_key is not None else None
    shared_expiry = _first_shared_key(call_map, put_map)

    if call_key is not None:
        compacted[call_key] = _compact_side_map(
            call_map,
            peer_map=put_map,
            preferred_expiry=shared_expiry,
            max_strikes=max_strikes_per_side,
        )
    if put_key is not None:
        compacted[put_key] = _compact_side_map(
            put_map,
            peer_map=call_map,
            preferred_expiry=shared_expiry,
            max_strikes=max_strikes_per_side,
        )
    return compacted


def summarize_shape(payload: JsonValue) -> dict[str, Any]:
    """Summarize raw option-chain shape without exposing sensitive values."""

    if not isinstance(payload, dict):
        return {
            "top_level_keys": [],
            "call_map_key": None,
            "put_map_key": None,
            "call_expiry_keys": [],
            "put_expiry_keys": [],
            "call_strike_keys": [],
            "put_strike_keys": [],
            "contract_fields": [],
        }

    call_key = _find_option_map_key(payload, "call")
    put_key = _find_option_map_key(payload, "put")
    return {
        "top_level_keys": sorted(payload.keys()),
        "call_map_key": call_key,
        "put_map_key": put_key,
        "call_expiry_keys": _map_keys(payload.get(call_key)),
        "put_expiry_keys": _map_keys(payload.get(put_key)),
        "call_strike_keys": _nested_map_keys(payload.get(call_key)),
        "put_strike_keys": _nested_map_keys(payload.get(put_key)),
        "contract_fields": _contract_fields(payload),
    }


def format_shape_summary(summary: dict[str, Any]) -> str:
    """Format a shape summary for display-safe console output."""

    lines = [
        "shape_summary:",
        f"  top_level_keys: {_format_list(summary['top_level_keys'])}",
        f"  call_map_key: {summary['call_map_key'] or 'missing'}",
        f"  put_map_key: {summary['put_map_key'] or 'missing'}",
        f"  call_expiry_keys: {_format_list(summary['call_expiry_keys'])}",
        f"  put_expiry_keys: {_format_list(summary['put_expiry_keys'])}",
        f"  call_strike_keys: {_format_list(summary['call_strike_keys'])}",
        f"  put_strike_keys: {_format_list(summary['put_strike_keys'])}",
        f"  contract_fields: {_format_list(summary['contract_fields'])}",
    ]
    return "\n".join(lines)


def fetch_option_chain_payload(request: OptionChainCaptureRequest) -> JsonValue:
    """Fetch one market-data option-chain payload after manual opt-in."""

    _validate_market_data_chain_url(request.url)
    query = urlencode(request.query)
    request_url = f"{request.url}?{query}" if query else request.url
    http_request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {request.live_credential}",
        },
        method="GET",
    )
    with urlopen(http_request, timeout=request.timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture and sanitize Schwab option-chain response shape for parser "
            "design. Live capture is off unless explicitly confirmed."
        )
    )
    parser.add_argument("--input-json", type=Path, help="sanitize an existing JSON file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--shape-report", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--symbol", default="$SPX")
    parser.add_argument("--endpoint-url", default=DEFAULT_CHAIN_URL)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--access-token-file", type=Path)
    parser.add_argument("--access-token-stdin", action="store_true")
    parser.add_argument("--contract-type", default="ALL")
    parser.add_argument("--strategy", default="SINGLE")
    parser.add_argument("--strike-count", default="2")
    parser.add_argument("--include-quotes", default="TRUE")
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument("--max-strikes-per-side", type=int, default=2)
    return parser


def run(
    argv: list[str] | None = None,
    *,
    fetcher: Callable[[OptionChainCaptureRequest], JsonValue] = fetch_option_chain_payload,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    args = build_parser().parse_args(argv)

    if args.input_json and args.live:
        _print_status(
            stdout,
            live_used=False,
            payload_captured=False,
            output_path=args.output,
            reason="input_json_and_live_are_mutually_exclusive",
        )
        return 1

    if args.input_json:
        raw_payload = _read_json(args.input_json)
        return _write_sanitized_outputs(
            raw_payload,
            output_path=args.output,
            shape_report_path=args.shape_report,
            max_strikes_per_side=args.max_strikes_per_side,
            live_used=False,
            payload_captured=False,
            stdout=stdout,
        )

    if not args.live:
        _print_status(
            stdout,
            live_used=False,
            payload_captured=False,
            output_path=args.output,
            reason="dry_run_no_live_request",
        )
        stdout.write("manual_opt_in_required: pass --live and --confirm-live with the required phrase\n")
        stdout.write(f"confirm_phrase: {DEFAULT_CONFIRM_PHRASE}\n")
        return 1

    if args.confirm_live != DEFAULT_CONFIRM_PHRASE:
        _print_status(
            stdout,
            live_used=False,
            payload_captured=False,
            output_path=args.output,
            reason="live_capture_not_confirmed",
        )
        return 1

    live_credential = _load_live_credential(args, stdin=stdin)
    if not live_credential:
        _print_status(
            stdout,
            live_used=False,
            payload_captured=False,
            output_path=args.output,
            reason="live_credential_unavailable",
        )
        return 1

    try:
        raw_payload = fetcher(_capture_request(args, live_credential=live_credential))
    except Exception as exc:  # pragma: no cover - exercised manually.
        _print_status(
            stdout,
            live_used=True,
            payload_captured=False,
            output_path=args.output,
            reason=_capture_failure_reason(exc),
        )
        return 1

    return _write_sanitized_outputs(
        raw_payload,
        output_path=args.output,
        shape_report_path=args.shape_report,
        max_strikes_per_side=args.max_strikes_per_side,
        live_used=True,
        payload_captured=True,
        stdout=stdout,
    )


def _write_sanitized_outputs(
    raw_payload: JsonValue,
    *,
    output_path: Path,
    shape_report_path: Path | None,
    max_strikes_per_side: int,
    live_used: bool,
    payload_captured: bool,
    stdout: TextIO,
) -> int:
    sanitized = compact_option_chain_sample(
        sanitize_payload(raw_payload),
        max_strikes_per_side=max_strikes_per_side,
    )
    summary = summarize_shape(sanitized)
    _write_json(output_path, sanitized)
    if shape_report_path is not None:
        _write_text(shape_report_path, _shape_report_text(summary))

    _print_status(
        stdout,
        live_used=live_used,
        payload_captured=payload_captured,
        output_path=output_path,
        reason="sanitized_output_written",
    )
    stdout.write("warning: output is sanitized and for parser design only\n")
    stdout.write(format_shape_summary(summary))
    stdout.write("\n")
    return 0


def _capture_request(args: argparse.Namespace, *, live_credential: str) -> OptionChainCaptureRequest:
    query = [
        ("symbol", args.symbol),
        ("contractType", args.contract_type),
        ("strategy", args.strategy),
        ("strikeCount", args.strike_count),
        ("includeUnderlyingQuote", args.include_quotes),
    ]
    if args.from_date:
        query.append(("fromDate", args.from_date))
    if args.to_date:
        query.append(("toDate", args.to_date))
    return OptionChainCaptureRequest(
        url=args.endpoint_url,
        symbol=args.symbol,
        timeout_seconds=args.timeout_seconds,
        live_credential=live_credential,
        query=tuple(query),
    )


def _load_live_credential(args: argparse.Namespace, *, stdin: TextIO) -> str | None:
    if args.access_token_stdin and args.access_token_file is not None:
        raise ValueError("Choose either stdin or file credential input, not both.")
    if args.access_token_stdin:
        return stdin.read().strip() or None
    if args.access_token_file is not None:
        return args.access_token_file.read_text(encoding="utf-8").strip() or None
    return None


def _validate_market_data_chain_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ValueError("live capture endpoint must use https")
    if "schwabapi.com" not in parsed.netloc:
        raise ValueError("live capture endpoint must be a Schwab API host")
    path = parsed.path.lower()
    if "marketdata" not in path or "chains" not in path:
        raise ValueError("live capture endpoint must be market-data option-chain only")
    if parsed.query and any(_is_sensitive_key(part) for part in parsed.query.split("&")):
        raise ValueError("live capture endpoint must not contain sensitive query material")


def _read_json(path: Path) -> JsonValue:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _shape_report_text(summary: dict[str, Any]) -> str:
    return (
        "# Sanitized Schwab Option-Chain Shape\n\n"
        "Sanitized fixture; not live; not broker data after sanitization; "
        "for parser design only.\n\n"
        f"```text\n{format_shape_summary(summary)}\n```\n"
    )


def _print_status(
    stdout: TextIO,
    *,
    live_used: bool,
    payload_captured: bool,
    output_path: Path,
    reason: str,
) -> None:
    stdout.write(f"live_mode_used: {'yes' if live_used else 'no'}\n")
    stdout.write(f"payload_captured: {'yes' if payload_captured else 'no'}\n")
    stdout.write(f"sanitized_output_path: {output_path}\n")
    stdout.write(f"status: {reason}\n")


def _capture_failure_reason(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        parts = ["capture_failed:HTTPError", f"http_status={exc.code}"]
        reason = _safe_http_text(getattr(exc, "reason", None))
        if reason:
            parts.append(f"reason={reason}")
        category = _safe_http_error_category(exc)
        if category:
            parts.append(f"error_category={category}")
        return ":".join(parts)
    return f"capture_failed:{type(exc).__name__}"


def _safe_http_error_category(exc: urllib.error.HTTPError) -> str | None:
    body = _read_http_error_body(exc)
    if not body:
        return None
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    for key in ("error", "errorCode", "code"):
        value = parsed.get(key)
        if isinstance(value, str):
            safe_value = _safe_http_text(value)
            if safe_value:
                return safe_value
    return None


def _read_http_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read(4096)
    except Exception:
        return ""
    if not body:
        return ""
    return body.decode("utf-8", errors="replace")


def _safe_http_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or len(stripped) > 80:
        return None
    normalized = stripped.lower().replace("-", "_")
    collapsed = normalized.replace("_", "")
    if any(part in normalized or part in collapsed for part in SENSITIVE_CATEGORY_PARTS):
        return None
    if _sanitize_string(stripped) == SENSITIVE_REPLACEMENT:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.: -]+", stripped):
        return None
    return stripped


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    collapsed = normalized.replace("_", "")
    return any(part in normalized or part in collapsed for part in SENSITIVE_KEY_PARTS)


def _sanitize_string(value: str) -> str:
    if any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
        return SENSITIVE_REPLACEMENT
    return value


def _find_option_map_key(payload: object, side: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    side_lower = side.lower()
    for key in payload:
        lowered = str(key).lower()
        if side_lower in lowered and "map" in lowered:
            return str(key)
    for key in payload:
        if side_lower in str(key).lower():
            nested = payload[key]
            if isinstance(nested, dict):
                return str(key)
    return None


def _map_keys(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key in value.keys())[:8]


def _nested_map_keys(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    keys: set[str] = set()
    for nested in value.values():
        if isinstance(nested, dict):
            keys.update(str(key) for key in nested.keys())
    return sorted(keys)[:12]


def _contract_fields(payload: object) -> list[str]:
    fields: set[str] = set()
    for value in _walk(payload):
        if isinstance(value, dict) and _looks_like_contract(value):
            fields.update(str(key) for key in value.keys())
    return sorted(fields)


def _walk(value: object) -> list[object]:
    values = [value]
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_walk(nested))
    return values


def _looks_like_contract(value: dict[str, Any]) -> bool:
    keys = {str(key).lower() for key in value.keys()}
    quote_keys = {"bid", "ask", "last", "mark"}
    contract_keys = {"symbol", "putcall", "put_call", "delta", "gamma", "theta", "vega"}
    return bool(keys & quote_keys) and bool(keys & contract_keys)


def _first_shared_key(left: object, right: object) -> str | None:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return None
    shared = sorted(set(left.keys()) & set(right.keys()))
    return str(shared[0]) if shared else None


def _compact_side_map(
    side_map: object,
    *,
    peer_map: object,
    preferred_expiry: str | None,
    max_strikes: int,
) -> object:
    if not isinstance(side_map, dict):
        return side_map
    expiry_keys = [preferred_expiry] if preferred_expiry in side_map else sorted(side_map.keys())[:1]
    compacted: dict[str, object] = {}
    for expiry_key in expiry_keys:
        strikes = side_map.get(expiry_key)
        peer_strikes = peer_map.get(expiry_key) if isinstance(peer_map, dict) else None
        compacted[str(expiry_key)] = _compact_strikes(
            strikes,
            peer_strikes=peer_strikes,
            max_strikes=max_strikes,
        )
    return compacted


def _compact_strikes(
    strikes: object,
    *,
    peer_strikes: object,
    max_strikes: int,
) -> object:
    if not isinstance(strikes, dict):
        return strikes
    preferred: list[object] = []
    if isinstance(peer_strikes, dict):
        preferred.extend(sorted(set(strikes.keys()) & set(peer_strikes.keys())))
    for key in sorted(strikes.keys()):
        if key not in preferred:
            preferred.append(key)
    return {str(key): strikes[key] for key in preferred[:max_strikes]}


def _format_list(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "[]"
    return "[" + ", ".join(str(value) for value in values) + "]"


if __name__ == "__main__":
    raise SystemExit(run())
