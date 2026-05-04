from __future__ import annotations

import json
from pathlib import Path

import pytest

from spx_inventory_playbook.daily_export import (
    EXPORT_FILE_NAMES,
    EXPORT_SCHEMA_VERSION,
    DailyExportBundleInput,
    MarketDataExportSummary,
    build_daily_export_from_state,
    main,
    redact_export_payload,
    write_daily_export_bundle,
)
from spx_inventory_playbook.inventory_ledger import (
    InventoryEventType,
    InventoryLedgerEvent,
    InventoryLedgerSnapshot,
    InventoryLedgerStore,
    InventoryLegRecord,
    InventoryRecord,
    InventoryRecordKind,
    InventoryRecordStatus,
)
from spx_inventory_playbook.local_state import (
    LocalStateStore,
    SessionEvent,
    SessionMetadata,
    build_local_state_paths,
)
from spx_inventory_playbook.operator_inputs import OperatorInputAuditRecord
from spx_inventory_playbook.operator_inputs import (
    OperatorInputAuditDataKind,
    OperatorInputAuditEventType,
    OperatorInputSourceKind,
)


CREATED_AT = "2026-05-04T09:45:00-04:00"


def session_metadata(**overrides: object) -> SessionMetadata:
    values: dict[str, object] = {
        "session_id": "spx-2026-05-04",
        "trading_date": "2026-05-04",
        "lifecycle_state": "authorized",
        "created_at": "2026-05-04T09:00:00-04:00",
        "updated_at": "2026-05-04T09:45:00-04:00",
        "data_mode": "fixture",
        "notes": "operator note",
    }
    values.update(overrides)
    return SessionMetadata(**values)


def session_event(**overrides: object) -> SessionEvent:
    values: dict[str, object] = {
        "event_id": "event-001",
        "session_id": "spx-2026-05-04",
        "created_at": "2026-05-04T09:01:00-04:00",
        "event_type": "lifecycle_transition",
        "lifecycle_state": "ready_check",
        "reason_codes": ("READY_CHECK_STARTED",),
        "summary": "ready check",
    }
    values.update(overrides)
    return SessionEvent(**values)


def inventory_record(**overrides: object) -> InventoryRecord:
    values: dict[str, object] = {
        "record_id": "record-001",
        "session_id": "spx-2026-05-04",
        "kind": InventoryRecordKind.PAPER_INTENT.value,
        "status": InventoryRecordStatus.PLANNED.value,
        "strategy_label": "paper observation",
        "thesis": "observe abstract setup",
        "invalidation": "stop observing if context is invalid",
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "legs": (
            InventoryLegRecord(
                leg_id="leg-001",
                side="CALL",
                instrument_type="option",
                provider_symbol="SPXW abstract call",
                expiration="2026-05-04",
                strike="abstract-strike",
                quantity="1",
                reference_mark="1.25",
            ),
        ),
        "option_chain_source_label": "fixture: sanitized capture",
        "option_chain_source_type": "fixture",
        "option_chain_freshness_status": "static_fixture",
        "option_chain_data_context": "static_fixture",
        "option_chain_reason_codes": ("static_fixture_not_live",),
        "notes": "paper only",
        "operator_acknowledged_context": True,
    }
    values.update(overrides)
    return InventoryRecord(**values)


def ledger_event(**overrides: object) -> InventoryLedgerEvent:
    values: dict[str, object] = {
        "event_id": "ledger-event-001",
        "session_id": "spx-2026-05-04",
        "record_id": "record-001",
        "created_at": CREATED_AT,
        "event_type": InventoryEventType.PAPER_INTENT_CREATED.value,
        "resulting_status": InventoryRecordStatus.PLANNED.value,
        "reason_codes": ("PAPER_INTENT_RECORDED",),
        "summary": "paper intent recorded",
    }
    values.update(overrides)
    return InventoryLedgerEvent(**values)


def audit_record(**overrides: object) -> OperatorInputAuditRecord:
    values: dict[str, object] = {
        "audit_id": "audit-001",
        "session_id": "spx-2026-05-04",
        "created_at": CREATED_AT,
        "event_type": OperatorInputAuditEventType.INPUTS_EVALUATED,
        "input_source": OperatorInputSourceKind.OPERATOR_ENTERED,
        "data_kinds": (
            OperatorInputAuditDataKind.OPERATOR_ENTERED,
            OperatorInputAuditDataKind.OBSERVED_MARKET_DATA,
            OperatorInputAuditDataKind.CALCULATED_NORMALIZATION,
            OperatorInputAuditDataKind.RULE_DECISION,
        ),
        "validation_reason_codes": (),
        "rule_reasons": ("No rule blockers detected.",),
        "required_confirmations": (),
        "action_status": "authorized",
        "market_data_state": "live_fresh",
        "data_source_classification": "live",
        "can_act": True,
        "summary": "operator inputs evaluated",
    }
    values.update(overrides)
    return OperatorInputAuditRecord(**values)


def bundle_input(**overrides: object) -> DailyExportBundleInput:
    values: dict[str, object] = {
        "session": session_metadata(),
        "created_at": CREATED_AT,
        "market_data_summary": MarketDataExportSummary(
            provider_state="fixture",
            source_type="fixture",
            source_label="fixture: sanitized capture",
            status="available",
            data_source_classification="fixture_simulation",
        ),
        "session_events": (session_event(),),
        "inventory_snapshot": InventoryLedgerSnapshot(
            session_id="spx-2026-05-04",
            records=(inventory_record(),),
            events=(ledger_event(),),
        ),
        "authorization_records": (audit_record(),),
        "structured_operator_inputs": (
            {"time_window": "morning_945_1030", "dealer_regime": "positive_gex"},
        ),
        "operator_notes": "operator note",
        "app_version": None,
    }
    values.update(overrides)
    return DailyExportBundleInput(**values)


def read_json(bundle_dir: Path, file_name: str) -> dict[str, object]:
    return json.loads((bundle_dir / file_name).read_text(encoding="utf-8"))


def test_daily_export_writes_required_files_and_sections(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")

    result = write_daily_export_bundle(bundle_input(), paths=paths)

    assert result.bundle_dir == (
        tmp_path / ".state" / "exports" / "daily" / "2026-05-04" / "spx-2026-05-04"
    )
    assert {path.name for path in result.files} == set(EXPORT_FILE_NAMES)
    for file_name in EXPORT_FILE_NAMES:
        assert (result.bundle_dir / file_name).is_file()

    manifest = read_json(result.bundle_dir, "manifest.json")
    assert manifest["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert manifest["session_id"] == "spx-2026-05-04"
    assert manifest["trading_date"] == "2026-05-04"
    assert manifest["data_source_classification"] == "fixture_simulation"

    assert read_json(result.bundle_dir, "session.json")["metadata"]["data_mode"] == "fixture"
    assert read_json(result.bundle_dir, "event_ledger.json")["events"][0]["event_id"] == (
        "event-001"
    )
    assert read_json(result.bundle_dir, "inventory_snapshot.json")["records"][0][
        "record_id"
    ] == "record-001"
    assert read_json(result.bundle_dir, "paper_intents.json")["paper_intents"][0][
        "kind"
    ] == "paper_intent"
    assert read_json(result.bundle_dir, "authorization_snapshot.json")["records"][0][
        "action_status"
    ] == "authorized"


def test_missing_optional_data_is_explicit_empty_and_safe(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    result = write_daily_export_bundle(
        bundle_input(
            session_events=(),
            inventory_snapshot=None,
            authorization_records=(),
            structured_operator_inputs=(),
            operator_notes="",
        ),
        paths=paths,
    )

    assert read_json(result.bundle_dir, "event_ledger.json")["events"] == []
    assert read_json(result.bundle_dir, "inventory_snapshot.json")["records"] == []
    assert read_json(result.bundle_dir, "inventory_snapshot.json")["events"] == []
    assert read_json(result.bundle_dir, "paper_intents.json")["paper_intents"] == []
    assert read_json(result.bundle_dir, "authorization_snapshot.json")["missing"] is True
    assert read_json(result.bundle_dir, "operator_inputs.json")["missing"] is True


@pytest.mark.parametrize(
    "provider_state",
    [
        "fixture",
        "live_fresh",
        "live_stale",
        "live_unavailable",
        "live_parse_error",
        "missing",
    ],
)
def test_market_data_provenance_states_are_preserved(
    tmp_path: Path,
    provider_state: str,
) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    result = write_daily_export_bundle(
        bundle_input(
            market_data_summary=MarketDataExportSummary(
                provider_state=provider_state,
                source_type="live" if provider_state.startswith("live_") else "unknown",
                source_label="abstract source",
                status="unavailable" if provider_state == "live_unavailable" else None,
                reason_code="abstract_reason" if provider_state != "fixture" else None,
            )
        ),
        paths=paths,
    )

    market = read_json(result.bundle_dir, "market_data_summary.json")
    assert market["summary"]["provider_state"] == provider_state
    assert market["missing"] is (provider_state == "missing")
    assert read_json(result.bundle_dir, "manifest.json")["market_data_state"] == (
        provider_state
    )


def test_export_redacts_secret_like_fields_and_strings(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    result = write_daily_export_bundle(
        bundle_input(
            session=session_metadata(
                notes="access_token=abc123 Authorization: Bearer live-secret"
            ),
            structured_operator_inputs=(
                {
                    "access_token": "abc123",
                    "live_token_file_path": "/Users/stu/.state/schwab/token.json",
                    "note": "client_secret=super-secret",
                },
            ),
            operator_notes="refresh_token=refresh-secret",
        ),
        paths=paths,
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.files
        if path.suffix in {".json", ".md"}
    )
    assert "abc123" not in combined
    assert "live-secret" not in combined
    assert "super-secret" not in combined
    assert "refresh-secret" not in combined
    assert "/Users/stu/.state/schwab/token.json" not in combined
    assert "[REDACTED]" in combined


def test_redaction_helper_recurses_without_dropping_non_secret_fields() -> None:
    payload = {
        "source_label": "fixture",
        "nested": {"api_key": "secret", "note": "token=value"},
    }

    redacted = redact_export_payload(payload)

    assert redacted == {
        "source_label": "fixture",
        "nested": {"api_key": "[REDACTED]", "note": "token=[REDACTED]"},
    }


def test_state_export_reads_local_state_without_live_dependencies(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    state_store = LocalStateStore(paths)
    ledger_store = InventoryLedgerStore(paths)
    state_store.initialize()
    state_store.write_session_metadata(session_metadata())
    state_store.append_session_event(session_event())
    ledger_store.append_record(inventory_record())
    ledger_store.append_event(ledger_event())

    bundle = build_daily_export_from_state(
        paths=paths,
        session_id="spx-2026-05-04",
        created_at=CREATED_AT,
        market_data_summary=MarketDataExportSummary(
            provider_state="fixture",
            source_type="fixture",
        ),
    )
    result = write_daily_export_bundle(bundle, paths=paths)

    assert read_json(result.bundle_dir, "session.json")["metadata"]["session_id"] == (
        "spx-2026-05-04"
    )
    assert read_json(result.bundle_dir, "paper_intents.json")["paper_intents"][0][
        "record_id"
    ] == "record-001"


def test_state_export_fails_closed_when_required_session_state_is_missing(
    tmp_path: Path,
) -> None:
    paths = build_local_state_paths(tmp_path / ".state")

    with pytest.raises(ValueError, match="session metadata file was not found"):
        build_daily_export_from_state(
            paths=paths,
            session_id="missing-session",
            created_at=CREATED_AT,
            market_data_summary=MarketDataExportSummary(
                provider_state="fixture",
                source_type="fixture",
            ),
        )


def test_fixture_default_cli_writes_repo_owned_export_without_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_root = tmp_path / ".state"
    monkeypatch.setenv("SPX_OPTION_CHAIN_LIVE_TOKEN_FILE", "/not/read/token.json")

    exit_code = main(
        [
            "--state-root",
            str(state_root),
            "--session-id",
            "fixture-session",
            "--trading-date",
            "2026-05-04",
            "--created-at",
            CREATED_AT,
            "--fixture-default",
        ]
    )

    assert exit_code == 0
    bundle_dir = state_root / "exports" / "daily" / "2026-05-04" / "fixture-session"
    assert read_json(bundle_dir, "manifest.json")["market_data_state"] == "fixture"
    assert read_json(bundle_dir, "paper_intents.json")["paper_intents"] == []
