from __future__ import annotations

import base64
import json
import stat
import urllib.error
from pathlib import Path

import pytest

from spx_inventory_playbook.adapters.schwab_token_manager import (
    SchwabTokenManagerError,
    build_refresh_request,
    load_access_token_with_refresh_if_needed,
    load_token_json,
)


NOW = 1_800_000_000.0
OLD_ACCESS = "old-secret-access-token"
OLD_REFRESH = "old-secret-refresh-token"
NEW_ACCESS = "new-secret-access-token"
NEW_REFRESH = "new-secret-refresh-token"
APP_SECRET = "dummy-secret-value"
RAW_BODY = "raw-token-endpoint-body-with-secret"


class Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> Response:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def write_token(path: Path, token_data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(token_data), encoding="utf-8")


def token_path(tmp_path: Path) -> Path:
    return tmp_path / "external" / "schwab-token.json"


def base_token(**overrides: object) -> dict[str, object]:
    token = {
        "access_token": OLD_ACCESS,
        "refresh_token": OLD_REFRESH,
        "_spx_expires_at_epoch": NOW + 3600,
    }
    token.update(overrides)
    return token


def successful_urlopen(body: bytes) -> object:
    def _urlopen(request: object, timeout: int) -> Response:
        return Response(body)

    return _urlopen


def test_valid_fresh_token_does_not_refresh(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token())
    calls: list[str] = []

    access_token = load_access_token_with_refresh_if_needed(
        path,
        app_key="key",
        app_secret=APP_SECRET,
        now_epoch=NOW,
        urlopen_func=lambda request, timeout: calls.append("refresh") or Response(b"{}"),
    )

    assert access_token == OLD_ACCESS
    assert calls == []
    assert json.loads(path.read_text(encoding="utf-8"))["access_token"] == OLD_ACCESS


def test_expired_token_refreshes_and_rewrites_atomically(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token(_spx_expires_at_epoch=NOW - 1))

    access_token = load_access_token_with_refresh_if_needed(
        path,
        app_key="key",
        app_secret=APP_SECRET,
        now_epoch=NOW,
        urlopen_func=successful_urlopen(
            json.dumps(
                {
                    "access_token": NEW_ACCESS,
                    "refresh_token": NEW_REFRESH,
                    "expires_in": 1800,
                }
            ).encode("utf-8")
        ),
    )
    on_disk = json.loads(path.read_text(encoding="utf-8"))

    assert access_token == NEW_ACCESS
    assert on_disk["access_token"] == NEW_ACCESS
    assert on_disk["refresh_token"] == NEW_REFRESH
    assert on_disk["_spx_obtained_at_epoch"] == NOW
    assert on_disk["_spx_expires_at_epoch"] == NOW + 1800
    if hasattr(stat, "S_IMODE"):
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0


def test_near_expired_token_refreshes(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token(_spx_expires_at_epoch=NOW + 60))

    access_token = load_access_token_with_refresh_if_needed(
        path,
        app_key="key",
        app_secret=APP_SECRET,
        now_epoch=NOW,
        refresh_skew_seconds=120,
        urlopen_func=successful_urlopen(
            json.dumps({"access_token": NEW_ACCESS, "expires_in": 1800}).encode(
                "utf-8"
            )
        ),
    )

    assert access_token == NEW_ACCESS


def test_malformed_token_file_fails_closed(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{not-json " + OLD_ACCESS, encoding="utf-8")

    with pytest.raises(SchwabTokenManagerError) as exc_info:
        load_token_json(path)

    assert exc_info.value.reason_code == "token_file_malformed"
    assert OLD_ACCESS not in repr(exc_info.value)


def test_missing_access_token_fails_closed(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, {"refresh_token": OLD_REFRESH})

    with pytest.raises(SchwabTokenManagerError) as exc_info:
        load_access_token_with_refresh_if_needed(
            path,
            app_key="key",
            app_secret=APP_SECRET,
            now_epoch=NOW,
        )

    assert exc_info.value.reason_code == "access_token_required"


def test_missing_refresh_token_fails_closed(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, {"access_token": OLD_ACCESS})

    with pytest.raises(SchwabTokenManagerError) as exc_info:
        load_access_token_with_refresh_if_needed(
            path,
            app_key="key",
            app_secret=APP_SECRET,
            now_epoch=NOW,
        )

    assert exc_info.value.reason_code == "refresh_token_required"


@pytest.mark.parametrize("status_code", [401, 403, 429, 500])
def test_refresh_http_failures_fail_closed_without_rewriting(
    tmp_path: Path,
    status_code: int,
) -> None:
    path = token_path(tmp_path)
    original = base_token(_spx_expires_at_epoch=NOW - 1)
    write_token(path, original)

    def failing_urlopen(request: object, timeout: int) -> object:
        raise urllib.error.HTTPError(
            "https://api.schwabapi.com/v1/oauth/token",
            status_code,
            "Denied",
            None,
            None,
        )

    with pytest.raises(SchwabTokenManagerError) as exc_info:
        load_access_token_with_refresh_if_needed(
            path,
            app_key="key",
            app_secret=APP_SECRET,
            now_epoch=NOW,
            urlopen_func=failing_urlopen,
        )

    assert exc_info.value.reason_code == "token_refresh_failed"
    assert exc_info.value.http_status == status_code
    assert json.loads(path.read_text(encoding="utf-8")) == original


def test_refresh_response_without_refresh_token_preserves_existing_refresh_token(
    tmp_path: Path,
) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token(_spx_expires_at_epoch=NOW - 1))

    load_access_token_with_refresh_if_needed(
        path,
        app_key="key",
        app_secret=APP_SECRET,
        now_epoch=NOW,
        urlopen_func=successful_urlopen(
            json.dumps({"access_token": NEW_ACCESS, "expires_in": 1800}).encode(
                "utf-8"
            )
        ),
    )

    assert json.loads(path.read_text(encoding="utf-8"))["refresh_token"] == OLD_REFRESH


def test_refresh_response_records_expiry_metadata(tmp_path: Path) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token(_spx_expires_at_epoch=NOW - 1))

    load_access_token_with_refresh_if_needed(
        path,
        app_key="key",
        app_secret=APP_SECRET,
        now_epoch=NOW,
        urlopen_func=successful_urlopen(
            json.dumps({"access_token": NEW_ACCESS, "expires_in": "900"}).encode(
                "utf-8"
            )
        ),
    )

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["_spx_obtained_at_epoch"] == NOW
    assert on_disk["_spx_expires_at_epoch"] == NOW + 900


def test_refresh_request_shape_uses_basic_auth_without_repr_leaking_values() -> None:
    request = build_refresh_request(
        token_url="https://api.schwabapi.com/v1/oauth/token",
        app_key="dummy-key",
        app_secret=APP_SECRET,
        refresh_token=OLD_REFRESH,
    )
    decoded = base64.b64decode(
        request.get_header("Authorization").removeprefix("Basic ")
    ).decode("utf-8")

    assert request.get_method() == "POST"
    assert decoded == f"dummy-key:{APP_SECRET}"
    assert APP_SECRET not in repr(request.headers)
    assert OLD_REFRESH not in repr(request.headers)


def test_exception_repr_does_not_leak_secret_values_or_raw_response_body(
    tmp_path: Path,
) -> None:
    path = token_path(tmp_path)
    write_token(path, base_token(_spx_expires_at_epoch=NOW - 1))

    def failing_urlopen(request: object, timeout: int) -> object:
        raise urllib.error.HTTPError(
            "https://api.schwabapi.com/v1/oauth/token",
            401,
            f"Denied {OLD_REFRESH} {RAW_BODY}",
            None,
            None,
        )

    with pytest.raises(SchwabTokenManagerError) as exc_info:
        load_access_token_with_refresh_if_needed(
            path,
            app_key="key",
            app_secret=APP_SECRET,
            now_epoch=NOW,
            urlopen_func=failing_urlopen,
        )

    rendered = f"{exc_info.value!r} {exc_info.value!s}"
    assert OLD_ACCESS not in rendered
    assert OLD_REFRESH not in rendered
    assert APP_SECRET not in rendered
    assert "Authorization" not in rendered
    assert "Bearer" not in rendered
    assert RAW_BODY not in rendered
