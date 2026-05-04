"""Deterministic local daily export bundle for workstation review."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Mapping, Sequence

from spx_inventory_playbook.adapters.option_chain_provider import MarketDataProviderState
from spx_inventory_playbook.inventory_ledger import (
    InventoryLedgerSnapshot,
    InventoryLedgerStore,
    InventoryRecordKind,
    inventory_record_to_json_dict,
    inventory_snapshot_to_json_dict,
)
from spx_inventory_playbook.local_state import (
    LocalStatePaths,
    LocalStateStore,
    SessionEvent,
    SessionMetadata,
    _contained_path,
    _validate_path_safe_id,
    build_local_state_paths,
    ensure_local_state_dirs,
    redact_sensitive_text,
    session_event_to_json_dict,
    session_metadata_to_json_dict,
)
from spx_inventory_playbook.operator_inputs import (
    OperatorInputAuditRecord,
    operator_input_audit_record_to_json_dict,
)


EXPORT_SCHEMA_VERSION = "daily-export-v1"
EXPORT_PACKAGE_NAME = "codex-0dte-notebook"
EXPORT_FILE_NAMES = (
    "manifest.json",
    "daily_summary.md",
    "session.json",
    "event_ledger.json",
    "inventory_snapshot.json",
    "paper_intents.json",
    "market_data_summary.json",
    "authorization_snapshot.json",
    "operator_inputs.json",
)
MARKET_DATA_EXPORT_STATES = frozenset(
    {
        "fixture",
        "live_fresh",
        "live_stale",
        "live_unavailable",
        "live_parse_error",
        "missing",
    }
)
_SECRET_KEY_PARTS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "auth_header",
    "bearer",
    "api_key",
    "token_file",
    "token_path",
    "credential_path",
    "credential_file",
)


@dataclass(frozen=True)
class MarketDataExportSummary:
    provider_state: str
    source_type: str
    source_label: str | None = None
    status: str | None = None
    reason_code: str | None = None
    loaded_at: str | None = None
    data_source_classification: str | None = None

    def __post_init__(self) -> None:
        if self.provider_state not in MARKET_DATA_EXPORT_STATES:
            raise ValueError("provider_state must be a supported export state.")
        _require_non_empty_string(self.source_type, "source_type")
        _optional_string(self.source_label, "source_label")
        _optional_string(self.status, "status")
        _optional_string(self.reason_code, "reason_code")
        _optional_string(self.loaded_at, "loaded_at")
        _optional_string(
            self.data_source_classification,
            "data_source_classification",
        )


@dataclass(frozen=True)
class DailyExportBundleInput:
    session: SessionMetadata
    created_at: str
    market_data_summary: MarketDataExportSummary
    session_events: tuple[SessionEvent, ...] = ()
    inventory_snapshot: InventoryLedgerSnapshot | None = None
    authorization_records: tuple[OperatorInputAuditRecord, ...] = ()
    structured_operator_inputs: tuple[Mapping[str, object], ...] = ()
    operator_notes: str = ""
    app_version: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.created_at, "created_at")
        if not isinstance(self.session, SessionMetadata):
            raise ValueError("session must be SessionMetadata.")
        if not isinstance(self.market_data_summary, MarketDataExportSummary):
            raise ValueError("market_data_summary must be MarketDataExportSummary.")
        if not isinstance(self.session_events, tuple):
            raise ValueError("session_events must be a tuple.")
        if not all(isinstance(event, SessionEvent) for event in self.session_events):
            raise ValueError("session_events must contain SessionEvent values.")
        if self.inventory_snapshot is not None and not isinstance(
            self.inventory_snapshot,
            InventoryLedgerSnapshot,
        ):
            raise ValueError("inventory_snapshot must be InventoryLedgerSnapshot.")
        if not isinstance(self.authorization_records, tuple):
            raise ValueError("authorization_records must be a tuple.")
        if not all(
            isinstance(record, OperatorInputAuditRecord)
            for record in self.authorization_records
        ):
            raise ValueError(
                "authorization_records must contain OperatorInputAuditRecord values."
            )
        if not isinstance(self.structured_operator_inputs, tuple):
            raise ValueError("structured_operator_inputs must be a tuple.")
        if not all(
            isinstance(item, Mapping) for item in self.structured_operator_inputs
        ):
            raise ValueError("structured_operator_inputs must contain mappings.")
        _require_string(self.operator_notes, "operator_notes")
        _optional_string(self.app_version, "app_version")


@dataclass(frozen=True)
class DailyExportResult:
    bundle_dir: Path
    files: tuple[Path, ...]


def write_daily_export_bundle(
    bundle: DailyExportBundleInput,
    *,
    paths: LocalStatePaths,
) -> DailyExportResult:
    """Write deterministic JSON/markdown daily export files under state exports."""

    _validate_path_safe_id(bundle.session.session_id, "session_id")
    _require_path_safe_segment(bundle.session.trading_date, "trading_date")
    ensure_local_state_dirs(paths)
    bundle_dir = _contained_path(
        paths.exports_dir
        / "daily"
        / bundle.session.trading_date
        / bundle.session.session_id,
        root=paths.root,
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    payloads = build_daily_export_payloads(bundle)
    written: list[Path] = []
    for file_name in EXPORT_FILE_NAMES:
        target = _contained_path(bundle_dir / file_name, root=paths.root)
        content = payloads[file_name]
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_text(_json_text(content), encoding="utf-8")
        written.append(target)
    return DailyExportResult(bundle_dir=bundle_dir, files=tuple(written))


def build_daily_export_payloads(
    bundle: DailyExportBundleInput,
) -> dict[str, Mapping[str, object] | str]:
    inventory_snapshot = bundle.inventory_snapshot or InventoryLedgerSnapshot(
        session_id=bundle.session.session_id,
        records=(),
        events=(),
    )
    if inventory_snapshot.session_id != bundle.session.session_id:
        raise ValueError("inventory snapshot session_id must match session metadata.")

    paper_intents = tuple(
        record
        for record in inventory_snapshot.records
        if record.kind == InventoryRecordKind.PAPER_INTENT.value
    )
    manifest = _manifest_payload(bundle, paper_intents=paper_intents)
    session_payload = {
        "metadata": session_metadata_to_json_dict(bundle.session),
        "missing": False,
    }
    event_payload = {
        "events": [session_event_to_json_dict(event) for event in bundle.session_events],
        "missing": False,
    }
    inventory_payload = inventory_snapshot_to_json_dict(inventory_snapshot) | {
        "missing": False
    }
    paper_intents_payload = {
        "paper_intents": [inventory_record_to_json_dict(record) for record in paper_intents],
        "missing": False,
    }
    market_payload = {
        "missing": bundle.market_data_summary.provider_state == "missing",
        "summary": market_data_summary_to_json_dict(bundle.market_data_summary),
    }
    authorization_payload = {
        "missing": not bundle.authorization_records,
        "records": [
            operator_input_audit_record_to_json_dict(record)
            for record in bundle.authorization_records
        ],
    }
    operator_inputs_payload = {
        "missing": not bundle.structured_operator_inputs and not bundle.operator_notes,
        "notes": redact_sensitive_text(bundle.operator_notes),
        "structured_operator_inputs": list(bundle.structured_operator_inputs),
    }

    payloads: dict[str, Mapping[str, object] | str] = {
        "manifest.json": manifest,
        "daily_summary.md": _daily_summary_markdown(
            bundle,
            event_count=len(bundle.session_events),
            inventory_record_count=len(inventory_snapshot.records),
            paper_intent_count=len(paper_intents),
            authorization_record_count=len(bundle.authorization_records),
        ),
        "session.json": session_payload,
        "event_ledger.json": event_payload,
        "inventory_snapshot.json": inventory_payload,
        "paper_intents.json": paper_intents_payload,
        "market_data_summary.json": market_payload,
        "authorization_snapshot.json": authorization_payload,
        "operator_inputs.json": operator_inputs_payload,
    }
    return {name: redact_export_payload(payload) for name, payload in payloads.items()}


def build_daily_export_from_state(
    *,
    paths: LocalStatePaths,
    session_id: str,
    created_at: str,
    market_data_summary: MarketDataExportSummary,
    app_version: str | None = None,
) -> DailyExportBundleInput:
    """Build an export bundle from existing local state, failing closed on session loss."""

    state_store = LocalStateStore(paths)
    ledger_store = InventoryLedgerStore(paths)
    session = state_store.read_session_metadata(session_id)
    return DailyExportBundleInput(
        session=session,
        created_at=created_at,
        market_data_summary=market_data_summary,
        session_events=state_store.read_session_events(session_id),
        inventory_snapshot=ledger_store.read_snapshot(session_id),
        operator_notes=session.notes,
        app_version=app_version,
    )


def build_fixture_default_export(
    *,
    session_id: str,
    trading_date: str,
    created_at: str,
    market_data_state: str = MarketDataProviderState.FIXTURE.value,
    app_version: str | None = None,
) -> DailyExportBundleInput:
    """Build an explicit empty fixture/default export without live dependencies."""

    session = SessionMetadata(
        session_id=session_id,
        trading_date=trading_date,
        lifecycle_state="not_started",
        created_at=created_at,
        updated_at=created_at,
        data_mode="fixture" if market_data_state == "fixture" else "unknown",
        notes="fixture/default export; no live data or credentials used",
    )
    return DailyExportBundleInput(
        session=session,
        created_at=created_at,
        market_data_summary=MarketDataExportSummary(
            provider_state=market_data_state,
            source_type="fixture" if market_data_state == "fixture" else "unknown",
            source_label="fixture/default export",
            status="available" if market_data_state == "fixture" else None,
            data_source_classification=(
                "fixture_simulation" if market_data_state == "fixture" else "unknown"
            ),
        ),
        operator_notes=session.notes,
        app_version=app_version,
    )


def market_data_summary_to_json_dict(
    summary: MarketDataExportSummary,
) -> dict[str, object]:
    return {
        "data_source_classification": summary.data_source_classification,
        "loaded_at": summary.loaded_at,
        "provider_state": summary.provider_state,
        "reason_code": summary.reason_code,
        "source_label": summary.source_label,
        "source_type": summary.source_type,
        "status": summary.status,
    }


def redact_export_payload(payload: object) -> object:
    """Redact secret-like strings and credential-bearing fields recursively."""

    if isinstance(payload, Mapping):
        redacted: dict[str, object] = {}
        for key, value in payload.items():
            key_text = str(key)
            if _is_secret_key(key_text):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = redact_export_payload(value)
        return redacted
    if isinstance(payload, list):
        return [redact_export_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return [redact_export_payload(item) for item in payload]
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    return payload


def _manifest_payload(
    bundle: DailyExportBundleInput,
    *,
    paper_intents: Sequence[object],
) -> dict[str, object]:
    source_classification = bundle.market_data_summary.data_source_classification
    if source_classification is None:
        source_classification = _classification_from_market_state(
            bundle.market_data_summary.provider_state
        )
    return {
        "app_version": bundle.app_version,
        "created_at": bundle.created_at,
        "data_source_classification": source_classification,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "files": list(EXPORT_FILE_NAMES),
        "market_data_state": bundle.market_data_summary.provider_state,
        "paper_intent_count": len(paper_intents),
        "session_id": bundle.session.session_id,
        "source_provenance": {
            "provider_state": bundle.market_data_summary.provider_state,
            "source_label": bundle.market_data_summary.source_label,
            "source_type": bundle.market_data_summary.source_type,
        },
        "trading_date": bundle.session.trading_date,
    }


def _daily_summary_markdown(
    bundle: DailyExportBundleInput,
    *,
    event_count: int,
    inventory_record_count: int,
    paper_intent_count: int,
    authorization_record_count: int,
) -> str:
    return "\n".join(
        [
            "# Daily Export Summary",
            "",
            f"- Export schema: {EXPORT_SCHEMA_VERSION}",
            f"- Created at: {bundle.created_at}",
            f"- Trading date: {bundle.session.trading_date}",
            f"- Session id: {bundle.session.session_id}",
            f"- Lifecycle state: {bundle.session.lifecycle_state}",
            f"- Market data state: {bundle.market_data_summary.provider_state}",
            f"- Source type: {bundle.market_data_summary.source_type}",
            f"- Session events: {event_count}",
            f"- Inventory records: {inventory_record_count}",
            f"- Paper intents: {paper_intent_count}",
            f"- Authorization records: {authorization_record_count}",
            "",
        ]
    )


def _classification_from_market_state(provider_state: str) -> str:
    if provider_state == "fixture":
        return "fixture_simulation"
    if provider_state.startswith("live_"):
        return "live"
    return "unknown"


def _installed_app_version() -> str | None:
    try:
        return version(EXPORT_PACKAGE_NAME)
    except PackageNotFoundError:
        return None


def _json_text(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
    ) + "\n"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SECRET_KEY_PARTS)


def _require_path_safe_segment(value: object, field_name: str) -> str:
    text = _require_non_empty_string(value, field_name)
    if text != text.strip() or "/" in text or "\\" in text or "\x00" in text:
        raise ValueError(f"{field_name} must be path-safe.")
    if ".." in text:
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


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, field_name)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a deterministic local daily export bundle.",
    )
    parser.add_argument("--state-root", default=".state")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--trading-date", required=True)
    parser.add_argument("--created-at", default=None)
    parser.add_argument(
        "--market-data-state",
        choices=sorted(MARKET_DATA_EXPORT_STATES),
        default=MarketDataProviderState.FIXTURE.value,
    )
    parser.add_argument(
        "--fixture-default",
        action="store_true",
        help="Create an explicit empty fixture/default export without reading session state.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    created_at = args.created_at or _utc_timestamp()
    paths = build_local_state_paths(Path(args.state_root))
    app_version = _installed_app_version()
    market_summary = MarketDataExportSummary(
        provider_state=args.market_data_state,
        source_type="fixture" if args.market_data_state == "fixture" else "unknown",
        source_label="cli export",
        data_source_classification=_classification_from_market_state(
            args.market_data_state
        ),
    )
    if args.fixture_default:
        bundle = build_fixture_default_export(
            session_id=args.session_id,
            trading_date=args.trading_date,
            created_at=created_at,
            market_data_state=args.market_data_state,
            app_version=app_version,
        )
    else:
        bundle = build_daily_export_from_state(
            paths=paths,
            session_id=args.session_id,
            created_at=created_at,
            market_data_summary=market_summary,
            app_version=app_version,
        )
    result = write_daily_export_bundle(bundle, paths=paths)
    print(result.bundle_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
