"""Schwab token-file refresh support for explicitly gated live market data."""

from __future__ import annotations

import base64
import json
import os
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable


DEFAULT_SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

JsonObject = dict[str, Any]
UrlopenFunc = Callable[..., object]


class SchwabTokenManagerError(RuntimeError):
    """Safe token-manager failure with a stable non-secret reason code."""

    def __init__(
        self,
        reason_code: str,
        *,
        http_status: int | None = None,
        exception_class: str | None = None,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.http_status = http_status
        self.exception_class = exception_class

    def __repr__(self) -> str:
        return (
            "SchwabTokenManagerError("
            f"reason_code={self.reason_code!r}, "
            f"http_status={self.http_status!r}, "
            f"exception_class={self.exception_class!r})"
        )

    __str__ = __repr__


def load_access_token_with_refresh_if_needed(
    token_path: Path,
    *,
    app_key: str,
    app_secret: str,
    token_url: str = DEFAULT_SCHWAB_TOKEN_URL,
    now_epoch: float | None = None,
    refresh_skew_seconds: float = 120,
    urlopen_func: UrlopenFunc = urllib.request.urlopen,
) -> str:
    """Return a usable access token, refreshing the local token file when needed."""

    token_data = load_token_json(token_path)
    access_token_from(token_data)
    refresh_token_from(token_data)
    if token_is_expired_or_near_expiry(
        token_data,
        now_epoch=now_epoch,
        skew_seconds=refresh_skew_seconds,
    ):
        token_data = refresh_token_file(
            token_path,
            token_data=token_data,
            app_key=app_key,
            app_secret=app_secret,
            token_url=token_url,
            now_epoch=now_epoch,
            urlopen_func=urlopen_func,
        )
    return access_token_from(token_data)


def load_token_json(token_path: Path) -> JsonObject:
    """Load token JSON without echoing path contents in failures."""

    try:
        raw_text = token_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SchwabTokenManagerError("token_file_unavailable") from exc
    except OSError as exc:
        raise SchwabTokenManagerError("token_file_unavailable") from exc
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SchwabTokenManagerError("token_file_malformed") from exc
    if not isinstance(parsed, dict):
        raise SchwabTokenManagerError("token_file_malformed")
    return parsed


def access_token_from(token_data: JsonObject) -> str:
    value = token_data.get("access_token")
    if not isinstance(value, str) or not value.strip():
        raise SchwabTokenManagerError("access_token_required")
    return value.strip()


def refresh_token_from(token_data: JsonObject) -> str:
    value = token_data.get("refresh_token")
    if not isinstance(value, str) or not value.strip():
        raise SchwabTokenManagerError("refresh_token_required")
    return value.strip()


def token_is_expired_or_near_expiry(
    token_data: JsonObject,
    *,
    now_epoch: float | None = None,
    skew_seconds: float = 120,
) -> bool:
    now = time.time() if now_epoch is None else now_epoch
    explicit_expiry = _numeric_token_value(
        token_data,
        "expires_at",
        "expires_at_epoch",
        "expires_at_epoch_seconds",
        "_spx_expires_at_epoch",
    )
    if explicit_expiry is not None:
        return explicit_expiry <= now + skew_seconds

    issued_at = _numeric_token_value(
        token_data,
        "issued_at",
        "obtained_at",
        "_spx_obtained_at_epoch",
    )
    expires_in = _numeric_token_value(token_data, "expires_in")
    if issued_at is not None and expires_in is not None:
        return issued_at + expires_in <= now + skew_seconds
    return False


def build_refresh_request(
    *,
    token_url: str,
    app_key: str,
    app_secret: str,
    refresh_token: str,
) -> urllib.request.Request:
    payload = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh_token}
    ).encode("utf-8")
    basic_auth = base64.b64encode(f"{app_key}:{app_secret}".encode("utf-8")).decode(
        "ascii"
    )
    return urllib.request.Request(
        token_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Content-Length": str(len(payload)),
        },
    )


def refresh_token_file(
    token_path: Path,
    *,
    token_data: JsonObject,
    app_key: str,
    app_secret: str,
    token_url: str = DEFAULT_SCHWAB_TOKEN_URL,
    now_epoch: float | None = None,
    urlopen_func: UrlopenFunc = urllib.request.urlopen,
) -> JsonObject:
    """Refresh token JSON and atomically replace the source file."""

    if not app_key.strip() or not app_secret.strip():
        raise SchwabTokenManagerError("token_refresh_credentials_required")
    request = build_refresh_request(
        token_url=token_url,
        app_key=app_key.strip(),
        app_secret=app_secret.strip(),
        refresh_token=refresh_token_from(token_data),
    )
    try:
        with urlopen_func(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise SchwabTokenManagerError(
            "token_refresh_failed",
            http_status=exc.code,
            exception_class=exc.__class__.__name__,
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SchwabTokenManagerError(
            "token_refresh_failed",
            exception_class=exc.__class__.__name__,
        ) from exc

    try:
        refreshed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SchwabTokenManagerError("token_refresh_response_malformed") from exc
    if not isinstance(refreshed, dict):
        raise SchwabTokenManagerError("token_refresh_response_malformed")

    merged = merge_refresh_response(
        token_data,
        refreshed,
        now_epoch=time.time() if now_epoch is None else now_epoch,
    )
    write_token_json_atomic(token_path, merged)
    return merged


def merge_refresh_response(
    existing: JsonObject,
    refreshed: JsonObject,
    *,
    now_epoch: float,
) -> JsonObject:
    access_token = refreshed.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise SchwabTokenManagerError("access_token_required")

    merged = {**existing, **refreshed}
    if not isinstance(merged.get("refresh_token"), str) or not str(
        merged["refresh_token"]
    ).strip():
        merged["refresh_token"] = refresh_token_from(existing)
    merged["_spx_obtained_at_epoch"] = now_epoch
    expires_in = _numeric_token_value(merged, "expires_in")
    if expires_in is not None:
        merged["_spx_expires_at_epoch"] = now_epoch + expires_in
    return merged


def write_token_json_atomic(token_path: Path, token_data: JsonObject) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=".token.",
        suffix=".tmp",
        dir=token_path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(token_data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        _chmod_owner_only(temp_path)
        temp_path.replace(token_path)
        _chmod_owner_only(token_path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _numeric_token_value(token_data: JsonObject, *keys: str) -> float | None:
    for key in keys:
        value = token_data.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _chmod_owner_only(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


__all__ = [
    "DEFAULT_SCHWAB_TOKEN_URL",
    "SchwabTokenManagerError",
    "access_token_from",
    "build_refresh_request",
    "load_access_token_with_refresh_if_needed",
    "load_token_json",
    "merge_refresh_response",
    "refresh_token_file",
    "refresh_token_from",
    "token_is_expired_or_near_expiry",
    "write_token_json_atomic",
]
