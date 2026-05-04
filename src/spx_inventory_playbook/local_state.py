"""Durable local-state foundation for personal workstation sessions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Mapping


DATA_MODES = frozenset({"none", "fixture", "live", "mixed", "unknown"})
_SENSITIVE_PATTERNS = (
    re.compile(r"(access_token=)[^\s&;]+", re.IGNORECASE),
    re.compile(r"(refresh_token=)[^\s&;]+", re.IGNORECASE),
    re.compile(r"(client_secret=)[^\s&;]+", re.IGNORECASE),
    re.compile(r"(api_key=)[^\s&;]+", re.IGNORECASE),
    re.compile(r"(token=)[^\s&;]+", re.IGNORECASE),
    re.compile(r"(authorization:\s*)[^\r\n]+", re.IGNORECASE),
    re.compile(r"(bearer\s+)[^\s,;]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class LocalStatePaths:
    root: Path
    sessions_dir: Path
    events_dir: Path
    snapshots_dir: Path
    exports_dir: Path


@dataclass(frozen=True)
class SessionMetadata:
    session_id: str
    trading_date: str
    lifecycle_state: str
    created_at: str
    updated_at: str
    data_mode: str = "none"
    notes: str = ""

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.session_id, "session_id")
        _require_non_empty_string(self.trading_date, "trading_date")
        _require_non_empty_string(self.lifecycle_state, "lifecycle_state")
        _require_non_empty_string(self.created_at, "created_at")
        _require_non_empty_string(self.updated_at, "updated_at")
        data_mode = _require_string(self.data_mode, "data_mode")
        if data_mode not in DATA_MODES:
            raise ValueError("data_mode must be one of the supported local state modes.")
        notes = _require_string(self.notes, "notes")
        object.__setattr__(self, "notes", redact_sensitive_text(notes))


@dataclass(frozen=True)
class SessionEvent:
    event_id: str
    session_id: str
    created_at: str
    event_type: str
    lifecycle_state: str
    reason_codes: tuple[str, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.event_id, "event_id")
        _validate_path_safe_id(self.session_id, "session_id")
        _require_non_empty_string(self.created_at, "created_at")
        _require_non_empty_string(self.event_type, "event_type")
        _require_non_empty_string(self.lifecycle_state, "lifecycle_state")
        if not isinstance(self.reason_codes, tuple):
            raise ValueError("reason_codes must be a tuple of strings.")
        if not all(isinstance(code, str) for code in self.reason_codes):
            raise ValueError("reason_codes must be a tuple of strings.")
        summary = _require_string(self.summary, "summary")
        object.__setattr__(self, "summary", redact_sensitive_text(summary))


class LocalStateStore:
    """Small file-backed store for session metadata and lifecycle events."""

    def __init__(self, paths: LocalStatePaths) -> None:
        self.paths = paths

    def initialize(self) -> None:
        ensure_local_state_dirs(self.paths)

    def write_session_metadata(self, metadata: SessionMetadata) -> Path:
        target = self._session_metadata_path(metadata.session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target.with_name(f".{target.name}.tmp")
        payload = session_metadata_to_json_dict(metadata)
        temp_path.write_text(_json_line(payload), encoding="utf-8")
        temp_path.replace(target)
        return target

    def read_session_metadata(self, session_id: str) -> SessionMetadata:
        target = self._session_metadata_path(session_id)
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError("session metadata file was not found.") from exc
        except JSONDecodeError as exc:
            raise ValueError("session metadata JSON is corrupt.") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("session metadata JSON must be an object.")
        return session_metadata_from_json_dict(payload)

    def append_session_event(self, event: SessionEvent) -> Path:
        target = self._session_events_path(event.session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = session_event_to_json_dict(event)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(_json_line(payload) + "\n")
        return target

    def read_session_events(self, session_id: str) -> tuple[SessionEvent, ...]:
        target = self._session_events_path(session_id)
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return ()

        events: list[SessionEvent] = []
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except JSONDecodeError as exc:
                raise ValueError(f"session event JSONL record {line_number} is corrupt.") from exc
            if not isinstance(payload, Mapping):
                raise ValueError(f"session event JSONL record {line_number} must be an object.")
            events.append(session_event_from_json_dict(payload))
        return tuple(events)

    def _session_metadata_path(self, session_id: str) -> Path:
        _validate_path_safe_id(session_id, "session_id")
        return _contained_path(
            self.paths.sessions_dir / f"{session_id}.json",
            root=self.paths.root,
        )

    def _session_events_path(self, session_id: str) -> Path:
        _validate_path_safe_id(session_id, "session_id")
        return _contained_path(
            self.paths.events_dir / f"{session_id}.events.jsonl",
            root=self.paths.root,
        )


def build_local_state_paths(root: Path) -> LocalStatePaths:
    """Compute local state paths without creating directories."""
    return LocalStatePaths(
        root=root,
        sessions_dir=root / "sessions",
        events_dir=root / "events",
        snapshots_dir=root / "snapshots",
        exports_dir=root / "exports",
    )


def ensure_local_state_dirs(paths: LocalStatePaths) -> None:
    """Create the local state directory tree."""
    for directory in (
        paths.root,
        paths.sessions_dir,
        paths.events_dir,
        paths.snapshots_dir,
        paths.exports_dir,
    ):
        _contained_path(directory, root=paths.root).mkdir(parents=True, exist_ok=True)


def session_metadata_to_json_dict(metadata: SessionMetadata) -> dict[str, object]:
    return {
        "created_at": metadata.created_at,
        "data_mode": metadata.data_mode,
        "lifecycle_state": metadata.lifecycle_state,
        "notes": redact_sensitive_text(metadata.notes),
        "session_id": metadata.session_id,
        "trading_date": metadata.trading_date,
        "updated_at": metadata.updated_at,
    }


def session_metadata_from_json_dict(payload: Mapping[str, object]) -> SessionMetadata:
    return SessionMetadata(
        session_id=_required_json_string(payload, "session_id"),
        trading_date=_required_json_string(payload, "trading_date"),
        lifecycle_state=_required_json_string(payload, "lifecycle_state"),
        created_at=_required_json_string(payload, "created_at"),
        updated_at=_required_json_string(payload, "updated_at"),
        data_mode=_optional_json_string(payload, "data_mode", default="none"),
        notes=_optional_json_string(payload, "notes", default=""),
    )


def session_event_to_json_dict(event: SessionEvent) -> dict[str, object]:
    return {
        "created_at": event.created_at,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "lifecycle_state": event.lifecycle_state,
        "reason_codes": list(event.reason_codes),
        "session_id": event.session_id,
        "summary": redact_sensitive_text(event.summary),
    }


def session_event_from_json_dict(payload: Mapping[str, object]) -> SessionEvent:
    return SessionEvent(
        event_id=_required_json_string(payload, "event_id"),
        session_id=_required_json_string(payload, "session_id"),
        created_at=_required_json_string(payload, "created_at"),
        event_type=_required_json_string(payload, "event_type"),
        lifecycle_state=_required_json_string(payload, "lifecycle_state"),
        reason_codes=_optional_json_string_tuple(payload, "reason_codes", default=()),
        summary=_optional_json_string(payload, "summary", default=""),
    )


def redact_sensitive_text(value: str) -> str:
    """Redact obvious credential-like substrings from local persisted text."""
    redacted = value
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


def _json_line(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _contained_path(path: Path, *, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise ValueError("local state path must remain inside the configured root.")
    return path


def _validate_path_safe_id(value: object, field_name: str) -> str:
    text = _require_non_empty_string(value, field_name)
    if text != text.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace.")
    if "/" in text or "\\" in text or ".." in text or "\x00" in text:
        raise ValueError(f"{field_name} must be path-safe.")
    return text


def _require_non_empty_string(value: object, field_name: str) -> str:
    text = _require_string(value, field_name)
    if not text:
        raise ValueError(f"{field_name} must be non-empty.")
    return text


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    return value


def _required_json_string(payload: Mapping[str, object], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required.")
    return _require_string(payload[field_name], field_name)


def _optional_json_string(
    payload: Mapping[str, object],
    field_name: str,
    *,
    default: str,
) -> str:
    if field_name not in payload:
        return default
    return _require_string(payload[field_name], field_name)


def _optional_json_string_tuple(
    payload: Mapping[str, object],
    field_name: str,
    *,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    if field_name not in payload:
        return default
    value = payload[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings.")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings.")
    return tuple(value)
