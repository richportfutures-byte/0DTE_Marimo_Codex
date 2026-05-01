from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "capture_schwab_option_chain_shape.py"
)

spec = importlib.util.spec_from_file_location("capture_schwab_option_chain_shape", SCRIPT_PATH)
capture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["capture_schwab_option_chain_shape"] = capture
spec.loader.exec_module(capture)


def raw_payload() -> dict[str, Any]:
    return {
        "symbol": "SPX",
        "status": "SUCCESS",
        "tokenField": "raw-token-value",
        "nested": {
            "accountNumber": "123456789",
            "customerId": "customer-123",
            "authorization": "Bearer raw-secret",
            "callbackUrl": "http://localhost/callback?code=hidden",
        },
        "callExpDateMap": {
            "2026-04-30:0": {
                "5000.0": [
                    {
                        "symbol": "SPXW  260430C05000000",
                        "putCall": "CALL",
                        "bid": 10.0,
                        "ask": 10.4,
                        "last": 10.2,
                        "mark": 10.2,
                        "delta": 0.51,
                        "gamma": 0.012,
                        "theta": -0.4,
                        "vega": 0.08,
                        "volatility": 18.0,
                        "quoteTimeInLong": 1777557600000,
                    }
                ],
                "5010.0": [
                    {
                        "symbol": "SPXW  260430C05010000",
                        "putCall": "CALL",
                        "bid": 5.0,
                        "ask": 5.4,
                    }
                ],
            }
        },
        "putExpDateMap": {
            "2026-04-30:0": {
                "5000.0": [
                    {
                        "symbol": "SPXW  260430P05000000",
                        "putCall": "PUT",
                        "bid": 9.8,
                        "ask": 10.2,
                        "last": 10.0,
                        "mark": 10.0,
                        "delta": -0.49,
                        "gamma": 0.011,
                        "theta": -0.38,
                        "vega": 0.08,
                        "volatility": 19.0,
                        "quoteTimeInLong": 1777557600000,
                    }
                ]
            }
        },
    }


def assert_no_sensitive_content(value: object) -> None:
    rendered = json.dumps(value, sort_keys=True)
    assert "raw-token-value" not in rendered
    assert "123456789" not in rendered
    assert "customer-123" not in rendered
    assert "Bearer raw-secret" not in rendered
    assert "localhost" not in rendered
    assert "callback" not in rendered.lower()


def test_sanitizer_removes_token_like_fields_recursively() -> None:
    sanitized = capture.sanitize_payload(raw_payload())

    assert "tokenField" not in sanitized
    assert_no_sensitive_content(sanitized)


def test_sanitizer_removes_account_customer_auth_like_fields_recursively() -> None:
    sanitized = capture.sanitize_payload(raw_payload())

    assert sanitized["nested"] == {}
    assert_no_sensitive_content(sanitized)


def test_sanitizer_preserves_call_put_nesting_keys() -> None:
    sanitized = capture.sanitize_payload(raw_payload())

    assert "callExpDateMap" in sanitized
    assert "putExpDateMap" in sanitized
    assert "2026-04-30:0" in sanitized["callExpDateMap"]
    assert "5000.0" in sanitized["putExpDateMap"]["2026-04-30:0"]


def test_sanitizer_preserves_contract_field_names() -> None:
    sanitized = capture.sanitize_payload(raw_payload())
    call_contract = sanitized["callExpDateMap"]["2026-04-30:0"]["5000.0"][0]

    assert set(call_contract) >= {
        "symbol",
        "putCall",
        "bid",
        "ask",
        "last",
        "mark",
        "quoteTimeInLong",
    }


def test_sanitizer_preserves_bid_ask_last_mark_numeric_shape() -> None:
    sanitized = capture.sanitize_payload(raw_payload())
    call_contract = sanitized["callExpDateMap"]["2026-04-30:0"]["5000.0"][0]

    assert call_contract["bid"] == 10.0
    assert call_contract["ask"] == 10.4
    assert call_contract["last"] == 10.2
    assert call_contract["mark"] == 10.2


def test_sanitizer_preserves_greek_and_iv_field_names_if_present() -> None:
    sanitized = capture.sanitize_payload(raw_payload())
    contract_fields = capture.summarize_shape(sanitized)["contract_fields"]

    assert "delta" in contract_fields
    assert "gamma" in contract_fields
    assert "theta" in contract_fields
    assert "vega" in contract_fields
    assert "volatility" in contract_fields


def test_sanitizer_does_not_write_unsanitized_sensitive_fields(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.json"
    output_path = tmp_path / "sanitized.json"
    raw_path.write_text(json.dumps(raw_payload()), encoding="utf-8")

    exit_code = capture.run(
        ["--input-json", str(raw_path), "--output", str(output_path)],
        stdout=io.StringIO(),
    )

    assert exit_code == 0
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert_no_sensitive_content(written)
    assert "tokenField" not in written


def test_shape_summary_lists_option_chain_keys_and_contract_fields() -> None:
    sanitized = capture.sanitize_payload(raw_payload())
    summary = capture.summarize_shape(sanitized)

    assert summary["top_level_keys"] == [
        "callExpDateMap",
        "nested",
        "putExpDateMap",
        "status",
        "symbol",
    ]
    assert summary["call_map_key"] == "callExpDateMap"
    assert summary["put_map_key"] == "putExpDateMap"
    assert summary["call_expiry_keys"] == ["2026-04-30:0"]
    assert summary["put_expiry_keys"] == ["2026-04-30:0"]
    assert summary["call_strike_keys"] == ["5000.0", "5010.0"]
    assert summary["put_strike_keys"] == ["5000.0"]
    assert "putCall" in summary["contract_fields"]


def test_default_script_behavior_does_not_run_live() -> None:
    calls: list[object] = []

    def fetcher(request: object) -> dict[str, object]:
        calls.append(request)
        return {}

    output = io.StringIO()
    exit_code = capture.run([], fetcher=fetcher, stdout=output)

    assert exit_code == 1
    assert calls == []
    assert "live_mode_used: no" in output.getvalue()
    assert "dry_run_no_live_request" in output.getvalue()


def test_live_mode_requires_explicit_manual_flags(tmp_path: Path) -> None:
    calls: list[object] = []

    def fetcher(request: object) -> dict[str, object]:
        calls.append(request)
        return raw_payload()

    output = io.StringIO()
    exit_code = capture.run(
        [
            "--live",
            "--output",
            str(tmp_path / "sanitized.json"),
        ],
        fetcher=fetcher,
        stdout=output,
    )

    assert exit_code == 1
    assert calls == []
    assert "live_capture_not_confirmed" in output.getvalue()


def test_live_mode_requires_credential_input_even_when_confirmed(tmp_path: Path) -> None:
    calls: list[object] = []

    def fetcher(request: object) -> dict[str, object]:
        calls.append(request)
        return raw_payload()

    output = io.StringIO()
    exit_code = capture.run(
        [
            "--live",
            "--confirm-live",
            capture.DEFAULT_CONFIRM_PHRASE,
            "--output",
            str(tmp_path / "sanitized.json"),
        ],
        fetcher=fetcher,
        stdout=output,
    )

    assert exit_code == 1
    assert calls == []
    assert "live_credential_unavailable" in output.getvalue()


def test_confirmed_live_mode_uses_injected_fetcher_and_sanitizes_output(tmp_path: Path) -> None:
    requests: list[object] = []

    def fetcher(request: object) -> dict[str, object]:
        requests.append(request)
        return raw_payload()

    output_path = tmp_path / "sanitized.json"
    output = io.StringIO()
    exit_code = capture.run(
        [
            "--live",
            "--confirm-live",
            capture.DEFAULT_CONFIRM_PHRASE,
            "--access-token-stdin",
            "--output",
            str(output_path),
        ],
        fetcher=fetcher,
        stdin=io.StringIO("manual-live-credential"),
        stdout=output,
    )

    assert exit_code == 0
    assert len(requests) == 1
    assert requests[0].symbol == "SPX"
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert_no_sensitive_content(written)
    assert "payload_captured: yes" in output.getvalue()
