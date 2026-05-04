from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib import util
from pathlib import Path

import marimo
import pytest

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (
    MANUAL_LIVE_CONFIRM_PHRASE,
)
from spx_inventory_playbook.adapters.option_chain_provider import MarketDataProviderState
from spx_inventory_playbook.daily_export import (
    EXPORT_FILE_NAMES,
    DailyExportBundleInput,
    MarketDataExportSummary,
    build_daily_export_from_state,
    write_daily_export_bundle,
)
from spx_inventory_playbook.inventory_ledger import (
    InventoryEventType,
    InventoryLedgerEvent,
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
from spx_inventory_playbook.marimo_option_chain_toggle import (
    FIXTURE_OPTION_CHAIN_MODE_LABEL,
    LIVE_OPTION_CHAIN_MODE_LABEL,
    load_marimo_option_chain_provider,
)
from spx_inventory_playbook.operator_inputs import (
    OperatorBehaviorAuthorization,
    OperatorContinuationState,
    OperatorDeltaContext,
    OperatorFoundationState,
    OperatorGammaRegime,
    OperatorInputState,
    OperatorLiquidity,
    OperatorLockoutState,
    OperatorLossAvoidanceRisk,
    OperatorPositionSize,
    OperatorRuleViolationState,
    OperatorSetup,
    OperatorThesisValidity,
    operator_input_audit_record_from_json_dict,
    operator_input_audit_record_to_json_dict,
)
from spx_inventory_playbook.rules import (
    ActionStatus,
    DataSourceClassification,
    evaluate_operator_input_authorization_with_audit,
)
from spx_inventory_playbook.session_lifecycle import (
    SessionLifecycleAction,
    SessionLifecycleState,
    evaluate_session_lifecycle_transition,
)
from spx_inventory_playbook.validators import Action, DealerRegime, TimeWindow


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)
CREATED_AT = "2026-05-04T09:45:00-04:00"


def load_notebook_module():
    spec = util.spec_from_file_location("spx_inventory_app_r9_smoke", NOTEBOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_operator_input(**overrides: object) -> OperatorInputState:
    values = {
        "time_window": TimeWindow.MORNING_945_1030,
        "dealer_regime": DealerRegime.POSITIVE_GEX,
        "liquidity": OperatorLiquidity.ACCEPTABLE,
        "thesis_validity": OperatorThesisValidity.VALID,
        "gamma_regime": OperatorGammaRegime.MANAGEABLE,
        "delta_context": OperatorDeltaContext.INTENTIONAL,
        "position_size": OperatorPositionSize.INSIDE_PLAN,
        "lockout_state": OperatorLockoutState.NONE,
        "behavior_authorization": OperatorBehaviorAuthorization.AUTHORIZED,
        "rule_violations": OperatorRuleViolationState.NONE,
        "loss_avoidance_risk": OperatorLossAvoidanceRisk.ABSENT,
        "foundation_state": OperatorFoundationState.ESTABLISHED,
        "setup": OperatorSetup.NONE,
        "continuation_state": OperatorContinuationState.INTACT,
    }
    values.update(overrides)
    return OperatorInputState(**values)


def session_metadata(**overrides: object) -> SessionMetadata:
    values: dict[str, object] = {
        "session_id": "spx-2026-05-04",
        "trading_date": "2026-05-04",
        "lifecycle_state": SessionLifecycleState.AUTHORIZED.value,
        "created_at": "2026-05-04T09:00:00-04:00",
        "updated_at": CREATED_AT,
        "data_mode": "fixture",
        "notes": "fixture app-level regression",
    }
    values.update(overrides)
    return SessionMetadata(**values)


def lifecycle_event(**overrides: object) -> SessionEvent:
    values: dict[str, object] = {
        "event_id": "event-001",
        "session_id": "spx-2026-05-04",
        "created_at": "2026-05-04T09:01:00-04:00",
        "event_type": "lifecycle_transition",
        "lifecycle_state": SessionLifecycleState.READY_CHECK.value,
        "reason_codes": ("READY_CHECK_STARTED",),
        "summary": "ready check started",
    }
    values.update(overrides)
    return SessionEvent(**values)


def inventory_record(**overrides: object) -> InventoryRecord:
    values: dict[str, object] = {
        "record_id": "record-001",
        "session_id": "spx-2026-05-04",
        "kind": InventoryRecordKind.PAPER_INTENT.value,
        "status": InventoryRecordStatus.PLANNED.value,
        "strategy_label": "abstract paper observation",
        "thesis": "observe fixture-only app regression",
        "invalidation": "stop if context is invalid",
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


def read_json(bundle_dir: Path, file_name: str) -> dict[str, object]:
    return json.loads((bundle_dir / file_name).read_text(encoding="utf-8"))


def test_notebook_import_and_script_smoke_do_not_require_live_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPX_OPTION_CHAIN_LIVE_TOKEN_FILE", "/abstract/not-read-token.json")
    module = load_notebook_module()

    assert isinstance(module.app, marimo.App)
    assert len(list(module.app._cell_manager.valid_cells())) > 0

    env = os.environ.copy()
    env["SPX_OPTION_CHAIN_LIVE_TOKEN_FILE"] = "/abstract/not-read-token.json"
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, str(NOTEBOOK_PATH)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "not-read-token" not in result.stdout
    assert "not-read-token" not in result.stderr


def test_session_lifecycle_persists_stable_metadata_and_exports_after_restart(
    tmp_path: Path,
) -> None:
    ready = evaluate_session_lifecycle_transition(
        SessionLifecycleState.NOT_STARTED,
        SessionLifecycleAction.START_READY_CHECK,
    )
    data_loaded = evaluate_session_lifecycle_transition(
        ready.next_state,
        SessionLifecycleAction.LOAD_DATA,
    )
    inventory_loaded = evaluate_session_lifecycle_transition(
        data_loaded.next_state,
        SessionLifecycleAction.LOAD_INVENTORY,
    )
    authorized = evaluate_session_lifecycle_transition(
        inventory_loaded.next_state,
        SessionLifecycleAction.AUTHORIZE,
    )
    closed = evaluate_session_lifecycle_transition(
        authorized.next_state,
        SessionLifecycleAction.CLOSE_SESSION,
    )
    invalid = evaluate_session_lifecycle_transition(
        SessionLifecycleState.READY_CHECK,
        SessionLifecycleAction.AUTHORIZE,
    )

    assert authorized.allowed is True
    assert closed.next_state is SessionLifecycleState.SESSION_CLOSED
    assert invalid.allowed is False
    assert invalid.reason_codes == ("AUTHORIZE_REQUIRES_INVENTORY_LOADED",)

    paths = build_local_state_paths(tmp_path / ".state")
    state_store = LocalStateStore(paths)
    ledger_store = InventoryLedgerStore(paths)
    state_store.initialize()
    state_store.write_session_metadata(session_metadata())
    state_store.append_session_event(lifecycle_event())
    ledger_store.append_record(inventory_record())
    ledger_store.append_event(ledger_event())

    restarted_state_store = LocalStateStore(paths)
    restarted_ledger_store = InventoryLedgerStore(paths)
    restored_metadata = restarted_state_store.read_session_metadata("spx-2026-05-04")
    restored_snapshot = restarted_ledger_store.read_snapshot("spx-2026-05-04")

    assert restored_metadata.session_id == "spx-2026-05-04"
    assert restored_metadata.trading_date == "2026-05-04"
    assert restored_snapshot.records[0].record_id == "record-001"

    bundle = build_daily_export_from_state(
        paths=paths,
        session_id="spx-2026-05-04",
        created_at=CREATED_AT,
        market_data_summary=MarketDataExportSummary(
            provider_state="fixture",
            source_type="fixture",
            data_source_classification="fixture_simulation",
        ),
    )
    result = write_daily_export_bundle(bundle, paths=paths)

    assert read_json(result.bundle_dir, "manifest.json")["session_id"] == (
        "spx-2026-05-04"
    )
    assert read_json(result.bundle_dir, "paper_intents.json")["paper_intents"][0][
        "record_id"
    ] == "record-001"


def test_corrupted_or_missing_required_state_fails_explicitly(tmp_path: Path) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    state_store = LocalStateStore(paths)
    state_store.initialize()

    with pytest.raises(ValueError, match="session metadata file was not found"):
        state_store.read_session_metadata("missing-session")

    corrupt_path = paths.sessions_dir / "spx-2026-05-04.json"
    corrupt_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="session metadata JSON is corrupt"):
        state_store.read_session_metadata("spx-2026-05-04")


def test_live_gate_regression_keeps_fixture_default_and_live_failures_distinct(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    fixture_result = load_marimo_option_chain_provider(
        selected_mode=FIXTURE_OPTION_CHAIN_MODE_LABEL,
        confirm_live=MANUAL_LIVE_CONFIRM_PHRASE,
        fixture_path=FIXTURE_PATH,
        live_token_file_path=tmp_path / "abstract-token-file.json",
        http_get_json=lambda _request, _token: calls.append("live") or {},
    )

    blocked_live_result = load_marimo_option_chain_provider(
        selected_mode=LIVE_OPTION_CHAIN_MODE_LABEL,
        confirm_live="wrong phrase",
        fixture_path=FIXTURE_PATH,
        live_token_file_path=tmp_path / "abstract-token-file.json",
        http_get_json=lambda _request, _token: calls.append("live") or {},
    )

    assert calls == []
    assert fixture_result.provider_result.source_type == "fixture"
    assert fixture_result.provider_state is MarketDataProviderState.FIXTURE
    assert blocked_live_result.provider_result.source_type == "live"
    assert blocked_live_result.provider_state is MarketDataProviderState.LIVE_UNAVAILABLE
    assert blocked_live_result.provider_result.reason_code == (
        "manual_live_confirmation_required"
    )

    for provider_state in (
        MarketDataProviderState.LIVE_STALE,
        MarketDataProviderState.LIVE_UNAVAILABLE,
        MarketDataProviderState.LIVE_PARSE_ERROR,
    ):
        decision, _, audit = evaluate_operator_input_authorization_with_audit(
            valid_operator_input(),
            audit_id=f"audit-{provider_state.value}",
            session_id="spx-2026-05-04",
            created_at=CREATED_AT,
            market_data_state=provider_state,
        )
        assert decision.can_act is False
        assert audit.market_data_state == provider_state.value


def test_rule_engine_remains_primary_operator_authorization_and_audit_layer() -> None:
    missing_decision, missing_validation, missing_audit = (
        evaluate_operator_input_authorization_with_audit(
            valid_operator_input(dealer_regime=None),
            audit_id="audit-missing-input",
            session_id="spx-2026-05-04",
            created_at=CREATED_AT,
            market_data_state=MarketDataProviderState.LIVE_FRESH,
        )
    )
    lockout_decision, _, lockout_audit = evaluate_operator_input_authorization_with_audit(
        valid_operator_input(lockout_state=OperatorLockoutState.DAILY),
        audit_id="audit-lockout",
        session_id="spx-2026-05-04",
        created_at=CREATED_AT,
        market_data_state=MarketDataProviderState.LIVE_FRESH,
    )
    stale_decision, _, stale_audit = evaluate_operator_input_authorization_with_audit(
        valid_operator_input(),
        audit_id="audit-stale-data",
        session_id="spx-2026-05-04",
        created_at=CREATED_AT,
        market_data_state=MarketDataProviderState.LIVE_STALE,
    )

    assert missing_decision.action_status is ActionStatus.BLOCKED
    assert missing_validation.reason_codes == ("DEALER_REGIME_MISSING",)
    assert missing_audit.validation_reason_codes == ("DEALER_REGIME_MISSING",)
    assert "resolve_operator_input_defects" in missing_audit.required_confirmations

    assert lockout_decision.action_status is ActionStatus.BLOCKED
    assert Action.CONVERT_RESTRUCTURE in lockout_decision.blocked_actions
    assert lockout_audit.action_status == ActionStatus.BLOCKED.value

    assert stale_decision.action_status is ActionStatus.RESTRICTED
    assert stale_audit.market_data_state == MarketDataProviderState.LIVE_STALE.value
    assert stale_audit.data_source_classification == DataSourceClassification.LIVE.value

    restored = operator_input_audit_record_from_json_dict(
        operator_input_audit_record_to_json_dict(stale_audit)
    )
    assert restored == stale_audit

    source = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "evaluate_operator_input_authorization" in source
    assert "rule_decision.action_status.value" in source
    assert "evaluate_inventory_rules" not in source


def test_export_bundle_regression_preserves_sections_provenance_and_redaction(
    tmp_path: Path,
) -> None:
    paths = build_local_state_paths(tmp_path / ".state")
    decision, _, audit = evaluate_operator_input_authorization_with_audit(
        valid_operator_input(),
        audit_id="audit-export",
        session_id="spx-2026-05-04",
        created_at=CREATED_AT,
        market_data_state=MarketDataProviderState.FIXTURE,
    )
    bundle = DailyExportBundleInput(
        session=session_metadata(notes="Authorization: Bearer placeholder-auth"),
        created_at=CREATED_AT,
        market_data_summary=MarketDataExportSummary(
            provider_state="fixture",
            source_type="fixture",
            source_label="fixture source access_token=placeholder-token",
            data_source_classification="fixture_simulation",
        ),
        session_events=(),
        inventory_snapshot=None,
        authorization_records=(audit,),
        structured_operator_inputs=(
            {
                "api_key": "placeholder-api-key",
                "token_file_path": "/abstract/token/path.json",
            },
        ),
        operator_notes="refresh_token=placeholder-refresh",
        app_version=None,
    )

    result = write_daily_export_bundle(bundle, paths=paths)

    assert decision.action_status is ActionStatus.SIMULATION_ONLY
    assert {path.name for path in result.files} == set(EXPORT_FILE_NAMES)
    assert read_json(result.bundle_dir, "manifest.json")[
        "data_source_classification"
    ] == "fixture_simulation"
    assert read_json(result.bundle_dir, "market_data_summary.json")["summary"][
        "provider_state"
    ] == "fixture"
    assert read_json(result.bundle_dir, "authorization_snapshot.json")["records"][0][
        "action_status"
    ] == "simulation_only"

    rendered_bundle = "\n".join(path.read_text(encoding="utf-8") for path in result.files)
    assert "placeholder-token" not in rendered_bundle
    assert "placeholder-auth" not in rendered_bundle
    assert "placeholder-api-key" not in rendered_bundle
    assert "placeholder-refresh" not in rendered_bundle
    assert "/abstract/token/path.json" not in rendered_bundle
    assert "[REDACTED]" in rendered_bundle
