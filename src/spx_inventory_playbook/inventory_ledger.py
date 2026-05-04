"""Append-only inventory ledger foundation for local paper workstation records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError
from pathlib import Path
from typing import Mapping

from spx_inventory_playbook.local_state import (
    LocalStatePaths,
    _contained_path,
    _json_line,
    _validate_path_safe_id,
    ensure_local_state_dirs,
    redact_sensitive_text,
)
from spx_inventory_playbook.paper_trades import PaperTradeIntent, PaperTradeLeg


class InventoryRecordKind(Enum):
    POSITION = "position"
    PAPER_INTENT = "paper_intent"


class InventoryRecordStatus(Enum):
    PLANNED = "planned"
    OPEN = "open"
    ADJUSTED = "adjusted"
    REDUCED = "reduced"
    CLOSED = "closed"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    REJECTED = "rejected"


class InventoryEventType(Enum):
    POSITION_CREATED = "position_created"
    POSITION_UPDATED = "position_updated"
    POSITION_CLOSED = "position_closed"
    POSITION_INVALIDATED = "position_invalidated"
    PAPER_INTENT_CREATED = "paper_intent_created"
    PAPER_INTENT_REJECTED = "paper_intent_rejected"
    PAPER_INTENT_ACKNOWLEDGED = "paper_intent_acknowledged"
    LEDGER_NOTE_ADDED = "ledger_note_added"


_RECORD_KIND_VALUES = {kind.value for kind in InventoryRecordKind}
_RECORD_STATUS_VALUES = {status.value for status in InventoryRecordStatus}
_EVENT_TYPE_VALUES = {event_type.value for event_type in InventoryEventType}
_ACK_REQUIRED_CONTEXT_VALUES = {
    "static_fixture",
    "stale",
    "stale_live",
    "unavailable",
    "invalid",
    "unknown",
}


@dataclass(frozen=True)
class InventoryLegRecord:
    leg_id: str
    side: str
    instrument_type: str
    provider_symbol: str | None = None
    expiration: str | None = None
    strike: str | None = None
    quantity: str | None = None
    reference_mark: str | None = None

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.leg_id, "leg_id")
        _require_non_empty_string(self.side, "side")
        _require_non_empty_string(self.instrument_type, "instrument_type")
        _optional_string(self.provider_symbol, "provider_symbol")
        _optional_string(self.expiration, "expiration")
        _optional_string(self.strike, "strike")
        _optional_string(self.quantity, "quantity")
        _optional_string(self.reference_mark, "reference_mark")


@dataclass(frozen=True)
class InventoryRecord:
    record_id: str
    session_id: str
    kind: str
    status: str
    strategy_label: str
    thesis: str
    invalidation: str
    created_at: str
    updated_at: str
    legs: tuple[InventoryLegRecord, ...] = ()
    entry_reference: str | None = None
    current_reference: str | None = None
    option_chain_source_label: str | None = None
    option_chain_source_type: str | None = None
    option_chain_freshness_status: str | None = None
    option_chain_data_context: str | None = None
    option_chain_warning_level: str | None = None
    option_chain_reason_codes: tuple[str, ...] = ()
    playbook_status_label: str | None = None
    playbook_allowed_actions: tuple[str, ...] = ()
    linked_rule_decision_id: str | None = None
    linked_market_snapshot_id: str | None = None
    notes: str = ""
    is_paper_only: bool = True
    broker_submitted: bool = False
    operator_acknowledged_context: bool = False

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.record_id, "record_id")
        _validate_path_safe_id(self.session_id, "session_id")
        _validate_enum_value(self.kind, _RECORD_KIND_VALUES, "kind")
        _validate_enum_value(self.status, _RECORD_STATUS_VALUES, "status")
        _require_non_empty_string(self.strategy_label, "strategy_label")
        _require_non_empty_string(self.created_at, "created_at")
        _require_non_empty_string(self.updated_at, "updated_at")
        _validate_record_thesis_fields(self)
        _validate_record_tuples(self)
        _validate_record_optional_strings(self)
        if not isinstance(self.is_paper_only, bool):
            raise ValueError("is_paper_only must be a boolean.")
        if not self.is_paper_only:
            raise ValueError("is_paper_only must remain True.")
        if not isinstance(self.broker_submitted, bool):
            raise ValueError("broker_submitted must be a boolean.")
        if self.broker_submitted:
            raise ValueError("broker_submitted must remain False.")
        if not isinstance(self.operator_acknowledged_context, bool):
            raise ValueError("operator_acknowledged_context must be a boolean.")
        if _paper_intent_context_requires_acknowledgement(self):
            raise ValueError("operator acknowledgement is required for degraded context.")
        object.__setattr__(self, "notes", redact_sensitive_text(self.notes))


@dataclass(frozen=True)
class InventoryLedgerEvent:
    event_id: str
    session_id: str
    record_id: str
    created_at: str
    event_type: str
    resulting_status: str
    reason_codes: tuple[str, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.event_id, "event_id")
        _validate_path_safe_id(self.session_id, "session_id")
        _validate_path_safe_id(self.record_id, "record_id")
        _require_non_empty_string(self.created_at, "created_at")
        _validate_enum_value(self.event_type, _EVENT_TYPE_VALUES, "event_type")
        _validate_enum_value(self.resulting_status, _RECORD_STATUS_VALUES, "resulting_status")
        _require_string_tuple(self.reason_codes, "reason_codes")
        summary = _require_string(self.summary, "summary")
        object.__setattr__(self, "summary", redact_sensitive_text(summary))


@dataclass(frozen=True)
class InventoryLedgerSnapshot:
    session_id: str
    records: tuple[InventoryRecord, ...]
    events: tuple[InventoryLedgerEvent, ...]

    def __post_init__(self) -> None:
        _validate_path_safe_id(self.session_id, "session_id")
        if not isinstance(self.records, tuple):
            raise ValueError("records must be a tuple.")
        if not all(isinstance(record, InventoryRecord) for record in self.records):
            raise ValueError("records must contain InventoryRecord values.")
        if not isinstance(self.events, tuple):
            raise ValueError("events must be a tuple.")
        if not all(isinstance(event, InventoryLedgerEvent) for event in self.events):
            raise ValueError("events must contain InventoryLedgerEvent values.")


class InventoryLedgerStore:
    """Append-only local inventory ledger store under the R3 state root."""

    def __init__(self, paths: LocalStatePaths) -> None:
        self.paths = paths

    def initialize(self) -> None:
        ensure_local_state_dirs(self.paths)

    def append_record(self, record: InventoryRecord) -> Path:
        target = self._records_path(record.session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(_json_line(inventory_record_to_json_dict(record)) + "\n")
        return target

    def append_event(self, event: InventoryLedgerEvent) -> Path:
        target = self._events_path(event.session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(_json_line(inventory_event_to_json_dict(event)) + "\n")
        return target

    def read_records(self, session_id: str) -> tuple[InventoryRecord, ...]:
        return tuple(
            inventory_record_from_json_dict(payload)
            for payload in _read_jsonl_objects(self._records_path(session_id), "inventory record")
        )

    def read_events(self, session_id: str) -> tuple[InventoryLedgerEvent, ...]:
        return tuple(
            inventory_event_from_json_dict(payload)
            for payload in _read_jsonl_objects(self._events_path(session_id), "inventory event")
        )

    def read_snapshot(self, session_id: str) -> InventoryLedgerSnapshot:
        return InventoryLedgerSnapshot(
            session_id=session_id,
            records=self.read_records(session_id),
            events=self.read_events(session_id),
        )

    def _records_path(self, session_id: str) -> Path:
        _validate_path_safe_id(session_id, "session_id")
        return _contained_path(
            self.paths.sessions_dir / f"{session_id}.inventory.records.jsonl",
            root=self.paths.root,
        )

    def _events_path(self, session_id: str) -> Path:
        _validate_path_safe_id(session_id, "session_id")
        return _contained_path(
            self.paths.sessions_dir / f"{session_id}.inventory.events.jsonl",
            root=self.paths.root,
        )


def inventory_leg_to_json_dict(leg: InventoryLegRecord) -> dict[str, object]:
    return {
        "expiration": leg.expiration,
        "instrument_type": leg.instrument_type,
        "leg_id": leg.leg_id,
        "provider_symbol": leg.provider_symbol,
        "quantity": leg.quantity,
        "reference_mark": leg.reference_mark,
        "side": leg.side,
        "strike": leg.strike,
    }


def inventory_leg_from_json_dict(payload: Mapping[str, object]) -> InventoryLegRecord:
    return InventoryLegRecord(
        leg_id=_required_json_string(payload, "leg_id"),
        side=_required_json_string(payload, "side"),
        instrument_type=_required_json_string(payload, "instrument_type"),
        provider_symbol=_optional_json_string(payload, "provider_symbol"),
        expiration=_optional_json_string(payload, "expiration"),
        strike=_optional_json_string(payload, "strike"),
        quantity=_optional_json_string(payload, "quantity"),
        reference_mark=_optional_json_string(payload, "reference_mark"),
    )


def inventory_record_to_json_dict(record: InventoryRecord) -> dict[str, object]:
    return {
        "broker_submitted": record.broker_submitted,
        "created_at": record.created_at,
        "current_reference": record.current_reference,
        "entry_reference": record.entry_reference,
        "invalidation": record.invalidation,
        "is_paper_only": record.is_paper_only,
        "kind": record.kind,
        "legs": [inventory_leg_to_json_dict(leg) for leg in record.legs],
        "linked_market_snapshot_id": record.linked_market_snapshot_id,
        "linked_rule_decision_id": record.linked_rule_decision_id,
        "notes": redact_sensitive_text(record.notes),
        "operator_acknowledged_context": record.operator_acknowledged_context,
        "option_chain_data_context": record.option_chain_data_context,
        "option_chain_freshness_status": record.option_chain_freshness_status,
        "option_chain_reason_codes": list(record.option_chain_reason_codes),
        "option_chain_source_label": record.option_chain_source_label,
        "option_chain_source_type": record.option_chain_source_type,
        "option_chain_warning_level": record.option_chain_warning_level,
        "playbook_allowed_actions": list(record.playbook_allowed_actions),
        "playbook_status_label": record.playbook_status_label,
        "record_id": record.record_id,
        "session_id": record.session_id,
        "status": record.status,
        "strategy_label": record.strategy_label,
        "thesis": record.thesis,
        "updated_at": record.updated_at,
    }


def inventory_record_from_json_dict(payload: Mapping[str, object]) -> InventoryRecord:
    return InventoryRecord(
        record_id=_required_json_string(payload, "record_id"),
        session_id=_required_json_string(payload, "session_id"),
        kind=_required_json_string(payload, "kind"),
        status=_required_json_string(payload, "status"),
        strategy_label=_required_json_string(payload, "strategy_label"),
        thesis=_required_json_string(payload, "thesis"),
        invalidation=_required_json_string(payload, "invalidation"),
        created_at=_required_json_string(payload, "created_at"),
        updated_at=_required_json_string(payload, "updated_at"),
        legs=_optional_json_leg_tuple(payload, "legs"),
        entry_reference=_optional_json_string(payload, "entry_reference"),
        current_reference=_optional_json_string(payload, "current_reference"),
        option_chain_source_label=_optional_json_string(payload, "option_chain_source_label"),
        option_chain_source_type=_optional_json_string(payload, "option_chain_source_type"),
        option_chain_freshness_status=_optional_json_string(
            payload,
            "option_chain_freshness_status",
        ),
        option_chain_data_context=_optional_json_string(payload, "option_chain_data_context"),
        option_chain_warning_level=_optional_json_string(payload, "option_chain_warning_level"),
        option_chain_reason_codes=_optional_json_string_tuple(
            payload,
            "option_chain_reason_codes",
        ),
        playbook_status_label=_optional_json_string(payload, "playbook_status_label"),
        playbook_allowed_actions=_optional_json_string_tuple(
            payload,
            "playbook_allowed_actions",
        ),
        linked_rule_decision_id=_optional_json_string(payload, "linked_rule_decision_id"),
        linked_market_snapshot_id=_optional_json_string(payload, "linked_market_snapshot_id"),
        notes=_optional_json_string(payload, "notes", default=""),
        is_paper_only=_optional_json_bool(payload, "is_paper_only", default=True),
        broker_submitted=_optional_json_bool(payload, "broker_submitted", default=False),
        operator_acknowledged_context=_optional_json_bool(
            payload,
            "operator_acknowledged_context",
            default=False,
        ),
    )


def inventory_event_to_json_dict(event: InventoryLedgerEvent) -> dict[str, object]:
    return {
        "created_at": event.created_at,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "reason_codes": list(event.reason_codes),
        "record_id": event.record_id,
        "resulting_status": event.resulting_status,
        "session_id": event.session_id,
        "summary": redact_sensitive_text(event.summary),
    }


def inventory_event_from_json_dict(payload: Mapping[str, object]) -> InventoryLedgerEvent:
    return InventoryLedgerEvent(
        event_id=_required_json_string(payload, "event_id"),
        session_id=_required_json_string(payload, "session_id"),
        record_id=_required_json_string(payload, "record_id"),
        created_at=_required_json_string(payload, "created_at"),
        event_type=_required_json_string(payload, "event_type"),
        resulting_status=_required_json_string(payload, "resulting_status"),
        reason_codes=_optional_json_string_tuple(payload, "reason_codes"),
        summary=_optional_json_string(payload, "summary", default=""),
    )


def inventory_snapshot_to_json_dict(snapshot: InventoryLedgerSnapshot) -> dict[str, object]:
    return {
        "events": [inventory_event_to_json_dict(event) for event in snapshot.events],
        "records": [inventory_record_to_json_dict(record) for record in snapshot.records],
        "session_id": snapshot.session_id,
    }


def inventory_snapshot_from_json_dict(payload: Mapping[str, object]) -> InventoryLedgerSnapshot:
    return InventoryLedgerSnapshot(
        session_id=_required_json_string(payload, "session_id"),
        records=_required_record_tuple(payload, "records"),
        events=_required_event_tuple(payload, "events"),
    )


def inventory_record_from_paper_trade_intent(
    session_id: str,
    record_id: str,
    intent: PaperTradeIntent,
) -> InventoryRecord:
    return InventoryRecord(
        record_id=record_id,
        session_id=session_id,
        kind=InventoryRecordKind.PAPER_INTENT.value,
        status=InventoryRecordStatus.PLANNED.value,
        strategy_label=intent.strategy_label,
        thesis=intent.thesis,
        invalidation=intent.invalidation,
        created_at=intent.created_at.isoformat(),
        updated_at=intent.created_at.isoformat(),
        legs=tuple(
            _inventory_leg_from_paper_trade_leg(
                record_id=record_id,
                leg_number=leg_number,
                leg=leg,
            )
            for leg_number, leg in enumerate(intent.legs, start=1)
        ),
        entry_reference=_string_or_none(intent.entry_reference),
        option_chain_source_label=intent.option_chain_source_label,
        option_chain_source_type=intent.option_chain_source_type,
        option_chain_freshness_status=intent.option_chain_freshness_status,
        option_chain_data_context=intent.option_chain_data_context,
        option_chain_warning_level=intent.option_chain_warning_level,
        option_chain_reason_codes=tuple(intent.option_chain_reason_codes),
        playbook_status_label=intent.playbook_status_label,
        playbook_allowed_actions=tuple(intent.playbook_allowed_actions),
        notes=intent.notes,
        is_paper_only=intent.is_paper_only,
        broker_submitted=intent.broker_submitted,
        operator_acknowledged_context=intent.operator_acknowledged_context,
    )


def _inventory_leg_from_paper_trade_leg(
    *,
    record_id: str,
    leg_number: int,
    leg: PaperTradeLeg,
) -> InventoryLegRecord:
    return InventoryLegRecord(
        leg_id=f"{record_id}-leg-{leg_number}",
        side=leg.side or "unknown",
        instrument_type="option",
        provider_symbol=leg.provider_symbol,
        expiration=leg.expiration.isoformat() if leg.expiration else None,
        strike=_string_or_none(leg.strike),
        reference_mark=_string_or_none(leg.reference_mark),
    )


def _read_jsonl_objects(path: Path, record_label: str) -> tuple[Mapping[str, object], ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ()

    payloads: list[Mapping[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except JSONDecodeError as exc:
            raise ValueError(f"{record_label} JSONL record {line_number} is corrupt.") from exc
        if not isinstance(payload, Mapping):
            raise ValueError(f"{record_label} JSONL record {line_number} must be an object.")
        payloads.append(payload)
    return tuple(payloads)


def _validate_record_thesis_fields(record: InventoryRecord) -> None:
    if record.status == InventoryRecordStatus.REJECTED.value:
        _require_string(record.thesis, "thesis")
        _require_string(record.invalidation, "invalidation")
        return
    if record.kind in {InventoryRecordKind.POSITION.value, InventoryRecordKind.PAPER_INTENT.value}:
        _require_non_empty_string(record.thesis, "thesis")
        _require_non_empty_string(record.invalidation, "invalidation")


def _validate_record_tuples(record: InventoryRecord) -> None:
    if not isinstance(record.legs, tuple):
        raise ValueError("legs must be a tuple.")
    if not all(isinstance(leg, InventoryLegRecord) for leg in record.legs):
        raise ValueError("legs must contain InventoryLegRecord values.")
    _require_string_tuple(record.option_chain_reason_codes, "option_chain_reason_codes")
    _require_string_tuple(record.playbook_allowed_actions, "playbook_allowed_actions")


def _validate_record_optional_strings(record: InventoryRecord) -> None:
    _optional_string(record.entry_reference, "entry_reference")
    _optional_string(record.current_reference, "current_reference")
    _optional_string(record.option_chain_source_label, "option_chain_source_label")
    _optional_string(record.option_chain_source_type, "option_chain_source_type")
    _optional_string(record.option_chain_freshness_status, "option_chain_freshness_status")
    _optional_string(record.option_chain_data_context, "option_chain_data_context")
    _optional_string(record.option_chain_warning_level, "option_chain_warning_level")
    _optional_string(record.playbook_status_label, "playbook_status_label")
    _optional_string(record.linked_rule_decision_id, "linked_rule_decision_id")
    _optional_string(record.linked_market_snapshot_id, "linked_market_snapshot_id")
    notes = _require_string(record.notes, "notes")
    object.__setattr__(record, "notes", notes)


def _paper_intent_context_requires_acknowledgement(record: InventoryRecord) -> bool:
    if record.kind != InventoryRecordKind.PAPER_INTENT.value:
        return False
    context_values = {
        record.option_chain_source_type,
        record.option_chain_freshness_status,
        record.option_chain_data_context,
    }
    normalized_values = {
        value.lower()
        for value in context_values
        if isinstance(value, str) and value.strip()
    }
    return (
        bool(normalized_values & _ACK_REQUIRED_CONTEXT_VALUES)
        and not record.operator_acknowledged_context
    )


def _validate_enum_value(value: object, allowed_values: set[str], field_name: str) -> str:
    text = _require_non_empty_string(value, field_name)
    if text not in allowed_values:
        raise ValueError(f"{field_name} must be a known inventory ledger value.")
    return text


def _required_json_string(payload: Mapping[str, object], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required.")
    return _require_string(payload[field_name], field_name)


def _optional_json_string(
    payload: Mapping[str, object],
    field_name: str,
    *,
    default: str | None = None,
) -> str | None:
    if field_name not in payload or payload[field_name] is None:
        return default
    return _require_string(payload[field_name], field_name)


def _optional_json_bool(
    payload: Mapping[str, object],
    field_name: str,
    *,
    default: bool,
) -> bool:
    if field_name not in payload:
        return default
    value = payload[field_name]
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean.")
    return value


def _optional_json_string_tuple(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[str, ...]:
    if field_name not in payload:
        return ()
    value = payload[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings.")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings.")
    return tuple(value)


def _optional_json_leg_tuple(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[InventoryLegRecord, ...]:
    if field_name not in payload:
        return ()
    value = payload[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of leg records.")
    legs: list[InventoryLegRecord] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must be a list of leg records.")
        legs.append(inventory_leg_from_json_dict(item))
    return tuple(legs)


def _required_record_tuple(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[InventoryRecord, ...]:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required.")
    value = payload[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of inventory records.")
    records: list[InventoryRecord] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must be a list of inventory records.")
        records.append(inventory_record_from_json_dict(item))
    return tuple(records)


def _required_event_tuple(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[InventoryLedgerEvent, ...]:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required.")
    value = payload[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of inventory events.")
    events: list[InventoryLedgerEvent] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must be a list of inventory events.")
        events.append(inventory_event_from_json_dict(item))
    return tuple(events)


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


def _require_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple of strings.")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a tuple of strings.")
    return value


def _string_or_none(value: object) -> str | None:
    return None if value is None else str(value)
