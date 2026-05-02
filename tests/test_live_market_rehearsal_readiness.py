from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from spx_inventory_playbook.live_market_rehearsal_readiness import (
    DEFAULT_APP_OPTION_CHAIN_FIXTURE_PATH,
    RehearsalReadinessResult,
    evaluate_live_market_rehearsal_readiness,
)


NOW = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)


def check(result: RehearsalReadinessResult, name: str) -> str:
    matches = [item for item in result.checks if item.name == name]
    assert len(matches) == 1
    return matches[0].status


def test_readiness_check_passes_in_current_fixture_backed_state() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert result.overall_status == "ready_for_fixture_rehearsal"
    assert result.reason_codes == ()
    assert all(item.status == "passed" for item in result.checks)


def test_readiness_check_verifies_fixture_provider_availability() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert result.fixture_path == DEFAULT_APP_OPTION_CHAIN_FIXTURE_PATH
    assert result.provider_name == "schwab_fixture"
    assert result.source_label == "fixture: app-owned sanitized Schwab option-chain capture"
    assert result.source_type == "fixture"
    assert check(result, "fixture_provider_loads") == "passed"
    assert check(result, "parser_returns_snapshot") == "passed"
    assert check(result, "selection_view_safe") == "passed"


def test_readiness_check_verifies_static_fixture_freshness() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert check(result, "fixture_freshness_static") == "passed"


def test_readiness_check_verifies_display_only_context_flags() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert check(result, "context_flags_display_only") == "passed"


def test_readiness_check_verifies_acknowledged_static_fixture_paper_intent() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert check(result, "paper_ledger_accepts_acknowledged_static_context") == "passed"


def test_readiness_check_verifies_unacknowledged_static_fixture_rejection() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert check(result, "paper_ledger_rejects_unacknowledged_static_context") == "passed"


def test_readiness_check_verifies_live_provider_placeholder_fail_closed() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    assert check(result, "no_live_provider_active") == "passed"
    assert check(result, "live_provider_placeholder_fail_closed") == "passed"


def test_missing_fixture_blocks_readiness_with_sanitized_reason(tmp_path: Path) -> None:
    result = evaluate_live_market_rehearsal_readiness(
        fixture_path=tmp_path / "missing.json",
        now=NOW,
    )

    assert result.overall_status == "blocked"
    assert "fixture_not_found" in result.reason_codes
    assert check(result, "fixture_provider_loads") == "failed"


def test_readiness_result_repr_does_not_include_raw_payload_bodies() -> None:
    result = evaluate_live_market_rehearsal_readiness(now=NOW)

    rendered = f"{result!r} {result!s}"

    assert "callExpDateMap" not in rendered
    assert "putExpDateMap" not in rendered
    assert "SPXW  " not in rendered
    assert "Fixture rehearsal paper intent" not in rendered
