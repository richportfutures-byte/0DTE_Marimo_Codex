from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from spx_inventory_playbook.local_state import (
    LocalStateStore,
    SessionEvent,
    SessionMetadata,
    build_local_state_paths,
    ensure_local_state_dirs,
    redact_sensitive_text,
    session_event_from_json_dict,
    session_event_to_json_dict,
    session_metadata_from_json_dict,
    session_metadata_to_json_dict,
)


def metadata(**overrides: object) -> SessionMetadata:
    values: dict[str, object] = {
        "session_id": "spx-2026-05-04",
        "trading_date": "2026-05-04",
        "lifecycle_state": "ready_check",
        "created_at": "2026-05-04T09:00:00-04:00",
        "updated_at": "2026-05-04T09:05:00-04:00",
        "data_mode": "fixture",
        "notes": "fixture rehearsal",
    }
    values.update(overrides)
    return SessionMetadata(**values)


def event(**overrides: object) -> SessionEvent:
    values: dict[str, object] = {
        "event_id": "event-001",
        "session_id": "spx-2026-05-04",
        "created_at": "2026-05-04T09:06:00-04:00",
        "event_type": "lifecycle_transition",
        "lifecycle_state": "ready_check",
        "reason_codes": ("READY_CHECK_STARTED",),
        "summary": "ready check started",
    }
    values.update(overrides)
    return SessionEvent(**values)


def test_build_local_state_paths_computes_expected_directories_without_creating_them(
    tmp_path: Path,
) -> None:
    root = tmp_path / ".state"
    paths = build_local_state_paths(root)

    assert paths.root == root
    assert paths.sessions_dir == root / "sessions"
    assert paths.events_dir == root / "events"
    assert paths.snapshots_dir == root / "snapshots"
    assert paths.exports_dir == root / "exports"
    assert not root.exists()


def test_ensure_local_state_dirs_creates_expected_directories(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")

    ensure_local_state_dirs(paths)

    for directory in (
        paths.root,
        paths.sessions_dir,
        paths.events_dir,
        paths.snapshots_dir,
        paths.exports_dir,
    ):
        assert directory.is_dir()


def test_session_metadata_roundtrip_serialization() -> None:
    original = metadata()

    payload = session_metadata_to_json_dict(original)
    restored = session_metadata_from_json_dict(payload)

    assert restored == original
    assert payload == {
        "created_at": "2026-05-04T09:00:00-04:00",
        "data_mode": "fixture",
        "lifecycle_state": "ready_check",
        "notes": "fixture rehearsal",
        "session_id": "spx-2026-05-04",
        "trading_date": "2026-05-04",
        "updated_at": "2026-05-04T09:05:00-04:00",
    }


def test_session_event_roundtrip_serialization() -> None:
    original = event()

    payload = session_event_to_json_dict(original)
    restored = session_event_from_json_dict(payload)

    assert restored == original
    assert payload["reason_codes"] == ["READY_CHECK_STARTED"]


def test_extra_json_fields_are_ignored() -> None:
    metadata_payload = session_metadata_to_json_dict(metadata())
    metadata_payload["ignored"] = "extra"
    event_payload = session_event_to_json_dict(event())
    event_payload["ignored"] = "extra"

    assert session_metadata_from_json_dict(metadata_payload) == metadata()
    assert session_event_from_json_dict(event_payload) == event()


@pytest.mark.parametrize(
    "field_name",
    ["session_id", "trading_date", "lifecycle_state", "created_at", "updated_at"],
)
def test_missing_required_metadata_fields_raise_value_error(field_name: str) -> None:
    payload = session_metadata_to_json_dict(metadata())
    del payload[field_name]

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        session_metadata_from_json_dict(payload)


@pytest.mark.parametrize(
    "field_name",
    ["event_id", "session_id", "created_at", "event_type", "lifecycle_state"],
)
def test_missing_required_event_fields_raise_value_error(field_name: str) -> None:
    payload = session_event_to_json_dict(event())
    del payload[field_name]

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        session_event_from_json_dict(payload)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("session_id", 123),
        ("trading_date", None),
        ("lifecycle_state", []),
        ("created_at", {}),
        ("updated_at", False),
        ("data_mode", 1),
        ("notes", ("not", "string")),
    ],
)
def test_malformed_metadata_field_types_raise_value_error(
    field_name: str,
    bad_value: object,
) -> None:
    payload = session_metadata_to_json_dict(metadata())
    payload[field_name] = bad_value

    with pytest.raises(ValueError):
        session_metadata_from_json_dict(payload)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("event_id", 123),
        ("session_id", None),
        ("created_at", []),
        ("event_type", {}),
        ("lifecycle_state", False),
        ("reason_codes", "not-a-list"),
        ("reason_codes", ["OK", 1]),
        ("summary", ("not", "string")),
    ],
)
def test_malformed_event_field_types_raise_value_error(
    field_name: str,
    bad_value: object,
) -> None:
    payload = session_event_to_json_dict(event())
    payload[field_name] = bad_value

    with pytest.raises(ValueError):
        session_event_from_json_dict(payload)


@pytest.mark.parametrize(
    "bad_session_id",
    ["", " ../escape", "../escape", "folder/session", r"folder\\session", "session\x00id", " id "],
)
def test_invalid_session_ids_are_rejected(bad_session_id: str) -> None:
    with pytest.raises(ValueError):
        metadata(session_id=bad_session_id)


@pytest.mark.parametrize(
    "bad_event_id",
    ["", "../event", "folder/event", r"folder\\event", "event\x00id", " event "],
)
def test_invalid_event_ids_are_rejected(bad_event_id: str) -> None:
    with pytest.raises(ValueError):
        event(event_id=bad_event_id)


def test_metadata_write_read_roundtrip(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    original = metadata()

    written_path = store.write_session_metadata(original)
    restored = store.read_session_metadata(original.session_id)

    assert written_path == tmp_path / ".state" / "sessions" / "spx-2026-05-04.json"
    assert restored == original


def test_event_append_read_roundtrip(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    original = event()

    written_path = store.append_session_event(original)
    restored = store.read_session_events(original.session_id)

    assert written_path == tmp_path / ".state" / "events" / "spx-2026-05-04.events.jsonl"
    assert restored == (original,)


def test_events_are_append_only_and_ordered(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    first = event(event_id="event-001", summary="first")
    second = event(event_id="event-002", summary="second")

    store.append_session_event(first)
    store.append_session_event(second)

    assert store.read_session_events("spx-2026-05-04") == (first, second)


@pytest.mark.parametrize(
    "bad_session_id",
    ["../escape", "folder/session", r"folder\\session", "session..escape"],
)
def test_path_traversal_cannot_escape_root(tmp_path: Path, bad_session_id: str) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()

    with pytest.raises(ValueError):
        store.read_session_metadata(bad_session_id)
    with pytest.raises(ValueError):
        store.read_session_events(bad_session_id)

    assert not (tmp_path / "escape.json").exists()


def test_store_rejects_paths_that_escape_root(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    escaped_paths = type(paths)(
        root=paths.root,
        sessions_dir=tmp_path / "outside-sessions",
        events_dir=paths.events_dir,
        snapshots_dir=paths.snapshots_dir,
        exports_dir=paths.exports_dir,
    )

    with pytest.raises(ValueError, match="inside the configured root"):
        ensure_local_state_dirs(escaped_paths)


def test_corrupt_metadata_json_raises_safe_value_error(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    target = tmp_path / ".state" / "sessions" / "spx-2026-05-04.json"
    target.write_text("{not valid json and access_token=secret}", encoding="utf-8")

    with pytest.raises(ValueError, match="session metadata JSON is corrupt") as exc_info:
        store.read_session_metadata("spx-2026-05-04")

    assert "access_token=secret" not in str(exc_info.value)


def test_corrupt_event_jsonl_raises_safe_value_error(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    target = tmp_path / ".state" / "events" / "spx-2026-05-04.events.jsonl"
    target.write_text("{not valid json and token=secret}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="session event JSONL record 1 is corrupt") as exc_info:
        store.read_session_events("spx-2026-05-04")

    assert "token=secret" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("access_token=aaa", "access_token=[REDACTED]"),
        ("refresh_token=bbb", "refresh_token=[REDACTED]"),
        ("authorization: Bearer ccc", "authorization: [REDACTED]"),
        ("bearer ddd", "bearer [REDACTED]"),
        ("client_secret=eee", "client_secret=[REDACTED]"),
        ("api_key=fff", "api_key=[REDACTED]"),
        ("token=ggg", "token=[REDACTED]"),
    ],
)
def test_redaction_catches_obvious_credential_like_substrings(
    value: str,
    expected: str,
) -> None:
    assert redact_sensitive_text(value) == expected


def test_persisted_notes_and_summaries_are_redacted(tmp_path: Path) -> None:
    store = LocalStateStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    secret_metadata = metadata(notes="operator note access_token=hidden")
    secret_event = event(summary="summary token=hidden")

    store.write_session_metadata(secret_metadata)
    store.append_session_event(secret_event)

    metadata_text = (tmp_path / ".state" / "sessions" / "spx-2026-05-04.json").read_text(
        encoding="utf-8"
    )
    event_text = (tmp_path / ".state" / "events" / "spx-2026-05-04.events.jsonl").read_text(
        encoding="utf-8"
    )
    assert "hidden" not in metadata_text
    assert "hidden" not in event_text
    assert "[REDACTED]" in metadata_text
    assert "[REDACTED]" in event_text


def test_metadata_and_events_are_frozen() -> None:
    original = metadata()
    original_event = event()

    with pytest.raises(FrozenInstanceError):
        original.notes = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        original_event.summary = "changed"  # type: ignore[misc]


def test_no_marimo_import_is_required() -> None:
    import spx_inventory_playbook.local_state as local_state

    assert "marimo" not in local_state.__dict__


def test_no_live_api_or_token_file_access_is_performed() -> None:
    source = Path("src/spx_inventory_playbook/local_state.py").read_text(encoding="utf-8")

    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    assert "Path.home" not in source
    assert "expanduser" not in source
    assert "token_file" not in source
