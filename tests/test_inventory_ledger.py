from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from spx_inventory_playbook.inventory_ledger import (
    InventoryEventType,
    InventoryLedgerEvent,
    InventoryLedgerSnapshot,
    InventoryLedgerStore,
    InventoryLegRecord,
    InventoryRecord,
    InventoryRecordKind,
    InventoryRecordStatus,
    inventory_event_from_json_dict,
    inventory_event_to_json_dict,
    inventory_leg_from_json_dict,
    inventory_leg_to_json_dict,
    inventory_record_from_json_dict,
    inventory_record_from_paper_trade_intent,
    inventory_record_to_json_dict,
    inventory_snapshot_from_json_dict,
    inventory_snapshot_to_json_dict,
)
from spx_inventory_playbook.local_state import build_local_state_paths
from spx_inventory_playbook.paper_trades import PaperTradeLeg, create_paper_trade_intent


CREATED_AT = "2026-05-04T09:40:00-04:00"


def leg(**overrides: object) -> InventoryLegRecord:
    values: dict[str, object] = {
        "leg_id": "leg-001",
        "side": "CALL",
        "instrument_type": "option",
        "provider_symbol": "SPXW abstract call",
        "expiration": "2026-05-04",
        "strike": "abstract-strike",
        "quantity": "1",
        "reference_mark": "1.25",
    }
    values.update(overrides)
    return InventoryLegRecord(**values)


def record(**overrides: object) -> InventoryRecord:
    values: dict[str, object] = {
        "record_id": "record-001",
        "session_id": "session-001",
        "kind": InventoryRecordKind.PAPER_INTENT.value,
        "status": InventoryRecordStatus.PLANNED.value,
        "strategy_label": "paper observation",
        "thesis": "observe whether the setup remains educationally valid",
        "invalidation": "stop observing if context is misunderstood",
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "legs": (leg(),),
        "entry_reference": "1.25",
        "option_chain_source_label": "fixture: sanitized capture",
        "option_chain_source_type": "fixture",
        "option_chain_freshness_status": "static_fixture",
        "option_chain_data_context": "static_fixture",
        "option_chain_warning_level": "caution",
        "option_chain_reason_codes": ("static_fixture_not_live",),
        "playbook_status_label": "normal",
        "playbook_allowed_actions": ("hold", "reduce"),
        "notes": "local paper note",
        "operator_acknowledged_context": True,
    }
    values.update(overrides)
    return InventoryRecord(**values)


def ledger_event(**overrides: object) -> InventoryLedgerEvent:
    values: dict[str, object] = {
        "event_id": "event-001",
        "session_id": "session-001",
        "record_id": "record-001",
        "created_at": CREATED_AT,
        "event_type": InventoryEventType.PAPER_INTENT_CREATED.value,
        "resulting_status": InventoryRecordStatus.PLANNED.value,
        "reason_codes": ("PAPER_INTENT_RECORDED",),
        "summary": "paper intent recorded",
    }
    values.update(overrides)
    return InventoryLedgerEvent(**values)


def test_leg_serialization_roundtrip() -> None:
    original = leg()

    payload = inventory_leg_to_json_dict(original)
    restored = inventory_leg_from_json_dict(payload)

    assert restored == original
    assert payload["reference_mark"] == "1.25"


def test_record_serialization_roundtrip() -> None:
    original = record()

    payload = inventory_record_to_json_dict(original)
    restored = inventory_record_from_json_dict(payload)

    assert restored == original
    assert payload["legs"] == [inventory_leg_to_json_dict(leg())]
    assert payload["playbook_allowed_actions"] == ["hold", "reduce"]


def test_event_serialization_roundtrip() -> None:
    original = ledger_event()

    payload = inventory_event_to_json_dict(original)
    restored = inventory_event_from_json_dict(payload)

    assert restored == original
    assert payload["reason_codes"] == ["PAPER_INTENT_RECORDED"]


def test_snapshot_serialization_roundtrip() -> None:
    original = InventoryLedgerSnapshot(
        session_id="session-001",
        records=(record(),),
        events=(ledger_event(),),
    )

    payload = inventory_snapshot_to_json_dict(original)
    restored = inventory_snapshot_from_json_dict(payload)

    assert restored == original


def test_extra_json_fields_are_ignored() -> None:
    leg_payload = inventory_leg_to_json_dict(leg())
    record_payload = inventory_record_to_json_dict(record())
    event_payload = inventory_event_to_json_dict(ledger_event())
    snapshot_payload = inventory_snapshot_to_json_dict(
        InventoryLedgerSnapshot("session-001", (record(),), (ledger_event(),))
    )
    for payload in (leg_payload, record_payload, event_payload, snapshot_payload):
        payload["ignored"] = "extra"

    assert inventory_leg_from_json_dict(leg_payload) == leg()
    assert inventory_record_from_json_dict(record_payload) == record()
    assert inventory_event_from_json_dict(event_payload) == ledger_event()
    assert inventory_snapshot_from_json_dict(snapshot_payload) == InventoryLedgerSnapshot(
        "session-001",
        (record(),),
        (ledger_event(),),
    )


@pytest.mark.parametrize(
    ("builder", "field_name"),
    [
        (inventory_leg_to_json_dict, "leg_id"),
        (inventory_record_to_json_dict, "record_id"),
        (inventory_event_to_json_dict, "event_id"),
    ],
)
def test_missing_required_fields_fail(builder, field_name: str) -> None:
    source = {
        inventory_leg_to_json_dict: leg(),
        inventory_record_to_json_dict: record(),
        inventory_event_to_json_dict: ledger_event(),
    }[builder]
    payload = builder(source)
    del payload[field_name]

    parser = {
        inventory_leg_to_json_dict: inventory_leg_from_json_dict,
        inventory_record_to_json_dict: inventory_record_from_json_dict,
        inventory_event_to_json_dict: inventory_event_from_json_dict,
    }[builder]
    with pytest.raises(ValueError, match=f"{field_name} is required"):
        parser(payload)


@pytest.mark.parametrize(
    ("payload_builder", "parser", "field_name", "bad_value"),
    [
        (inventory_leg_to_json_dict, inventory_leg_from_json_dict, "strike", 1.25),
        (inventory_record_to_json_dict, inventory_record_from_json_dict, "legs", "bad"),
        (inventory_record_to_json_dict, inventory_record_from_json_dict, "is_paper_only", "yes"),
        (inventory_event_to_json_dict, inventory_event_from_json_dict, "reason_codes", "bad"),
    ],
)
def test_malformed_field_types_fail(
    payload_builder,
    parser,
    field_name: str,
    bad_value: object,
) -> None:
    source = {
        inventory_leg_to_json_dict: leg(),
        inventory_record_to_json_dict: record(),
        inventory_event_to_json_dict: ledger_event(),
    }[payload_builder]
    payload = payload_builder(source)
    payload[field_name] = bad_value

    with pytest.raises(ValueError):
        parser(payload)


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (leg, "leg_id"),
        (record, "record_id"),
        (record, "session_id"),
        (ledger_event, "event_id"),
        (ledger_event, "record_id"),
    ],
)
def test_invalid_ids_are_rejected(factory, field_name: str) -> None:
    with pytest.raises(ValueError):
        factory(**{field_name: "../escape"})


def test_invalid_kind_status_and_event_type_are_rejected() -> None:
    with pytest.raises(ValueError, match="kind"):
        record(kind="unknown")
    with pytest.raises(ValueError, match="status"):
        record(status="unknown")
    with pytest.raises(ValueError, match="event_type"):
        ledger_event(event_type="unknown")


def test_thesis_required() -> None:
    with pytest.raises(ValueError, match="thesis"):
        record(thesis="")


def test_invalidation_required() -> None:
    with pytest.raises(ValueError, match="invalidation"):
        record(invalidation="")


def test_rejected_record_may_omit_thesis_and_invalidation() -> None:
    rejected = record(
        status=InventoryRecordStatus.REJECTED.value,
        thesis="",
        invalidation="",
    )

    assert rejected.status == InventoryRecordStatus.REJECTED.value


def test_broker_submitted_true_is_rejected() -> None:
    with pytest.raises(ValueError, match="broker_submitted"):
        record(broker_submitted=True)


def test_is_paper_only_false_is_rejected() -> None:
    with pytest.raises(ValueError, match="is_paper_only"):
        record(is_paper_only=False)


def test_static_fixture_paper_intent_requires_operator_acknowledgement() -> None:
    with pytest.raises(ValueError, match="acknowledgement"):
        record(operator_acknowledged_context=False)


@pytest.mark.parametrize(
    "context",
    ["stale_live", "unavailable", "invalid", "unknown"],
)
def test_degraded_contexts_require_operator_acknowledgement(context: str) -> None:
    with pytest.raises(ValueError, match="acknowledgement"):
        record(
            option_chain_source_type="live",
            option_chain_freshness_status=context,
            option_chain_data_context=context,
            operator_acknowledged_context=False,
        )


def test_acknowledged_fixture_or_stale_context_is_accepted_for_paper_only_recordkeeping() -> None:
    fixture_record = record(operator_acknowledged_context=True)
    stale_record = record(
        option_chain_source_type="live",
        option_chain_freshness_status="stale_live",
        option_chain_data_context="stale_live",
        operator_acknowledged_context=True,
    )

    assert fixture_record.is_paper_only is True
    assert stale_record.is_paper_only is True


def test_notes_and_summaries_are_redacted() -> None:
    secret_record = record(notes="note access_token=hidden")
    secret_event = ledger_event(summary="summary token=hidden")

    assert secret_record.notes == "note access_token=[REDACTED]"
    assert secret_event.summary == "summary token=[REDACTED]"
    assert "hidden" not in inventory_record_to_json_dict(secret_record)["notes"]
    assert "hidden" not in inventory_event_to_json_dict(secret_event)["summary"]


def test_append_read_records_preserves_order(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    first = record(record_id="record-001", notes="first")
    second = record(record_id="record-002", notes="second")

    path = store.append_record(first)
    store.append_record(second)

    assert path == tmp_path / ".state" / "sessions" / "session-001.inventory.records.jsonl"
    assert store.read_records("session-001") == (first, second)


def test_append_read_events_preserves_order(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    first = ledger_event(event_id="event-001", summary="first")
    second = ledger_event(event_id="event-002", summary="second")

    path = store.append_event(first)
    store.append_event(second)

    assert path == tmp_path / ".state" / "sessions" / "session-001.inventory.events.jsonl"
    assert store.read_events("session-001") == (first, second)


def test_snapshot_returns_both_records_and_events(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    store.append_record(record())
    store.append_event(ledger_event())

    snapshot = store.read_snapshot("session-001")

    assert snapshot == InventoryLedgerSnapshot(
        session_id="session-001",
        records=(record(),),
        events=(ledger_event(),),
    )


def test_corrupt_records_jsonl_raises_safe_value_error(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    target = tmp_path / ".state" / "sessions" / "session-001.inventory.records.jsonl"
    target.write_text("{not json access_token=hidden}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="inventory record JSONL record 1 is corrupt") as exc_info:
        store.read_records("session-001")

    assert "hidden" not in str(exc_info.value)


def test_corrupt_events_jsonl_raises_safe_value_error(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()
    target = tmp_path / ".state" / "sessions" / "session-001.inventory.events.jsonl"
    target.write_text("{not json token=hidden}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="inventory event JSONL record 1 is corrupt") as exc_info:
        store.read_events("session-001")

    assert "hidden" not in str(exc_info.value)


def test_path_traversal_cannot_escape_root(tmp_path: Path) -> None:
    store = InventoryLedgerStore(build_local_state_paths(tmp_path / ".state"))
    store.initialize()

    with pytest.raises(ValueError):
        store.read_records("../escape")
    with pytest.raises(ValueError):
        store.read_events("../escape")

    assert not (tmp_path / "escape.inventory.records.jsonl").exists()


def test_helper_maps_paper_trade_intent_into_inventory_record() -> None:
    intent = create_paper_trade_intent(
        created_at=datetime(2026, 5, 4, 13, 30, tzinfo=timezone.utc),
        strategy_label="paper spread observation",
        thesis="observe paper-only spread behavior",
        invalidation="stop if stale fixture context is misunderstood",
        notes="manual note token=hidden",
        legs=(
            PaperTradeLeg(
                provider_symbol="SPXW abstract put",
                side="PUT",
                expiration=date(2026, 5, 4),
                strike=1.25,
                reference_mark=0.75,
            ),
        ),
        entry_reference=1.0,
        option_chain_source_label="fixture: sanitized capture",
        option_chain_source_type="fixture",
        option_chain_freshness_status="static_fixture",
        option_chain_data_context="static_fixture",
        option_chain_warning_level="caution",
        option_chain_reason_codes=("static_fixture_not_live",),
        playbook_status_label="normal",
        playbook_allowed_actions=("hold", "reduce"),
        operator_acknowledged_context=True,
    )

    mapped = inventory_record_from_paper_trade_intent(
        "session-001",
        "record-001",
        intent,
    )

    assert mapped.kind == InventoryRecordKind.PAPER_INTENT.value
    assert mapped.status == InventoryRecordStatus.PLANNED.value
    assert mapped.is_paper_only is True
    assert mapped.broker_submitted is False
    assert mapped.strategy_label == intent.strategy_label
    assert mapped.thesis == intent.thesis
    assert mapped.invalidation == intent.invalidation
    assert mapped.entry_reference == "1.0"
    assert mapped.option_chain_reason_codes == ("static_fixture_not_live",)
    assert mapped.playbook_allowed_actions == ("hold", "reduce")
    assert mapped.notes == "manual note token=[REDACTED]"
    assert mapped.legs == (
        InventoryLegRecord(
            leg_id="record-001-leg-1",
            side="PUT",
            instrument_type="option",
            provider_symbol="SPXW abstract put",
            expiration="2026-05-04",
            strike="1.25",
            reference_mark="0.75",
        ),
    )


def test_no_marimo_import_required() -> None:
    import spx_inventory_playbook.inventory_ledger as inventory_ledger

    assert "marimo" not in inventory_ledger.__dict__


def test_no_live_api_or_token_file_access_performed() -> None:
    source = Path("src/spx_inventory_playbook/inventory_ledger.py").read_text(
        encoding="utf-8"
    )

    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    assert "Path.home" not in source
    assert "expanduser" not in source
    assert "token_file" not in source
