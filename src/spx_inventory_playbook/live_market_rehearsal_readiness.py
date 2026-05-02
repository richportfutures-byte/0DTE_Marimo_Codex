"""Fixture-only readiness checks for a future live-market paper rehearsal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from spx_inventory_playbook.adapters.option_chain_context import (
    OptionChainContextFlags,
    build_option_chain_context_flags,
)
from spx_inventory_playbook.adapters.option_chain_freshness import (
    OptionChainFreshness,
    classify_option_chain_freshness,
)
from spx_inventory_playbook.adapters.option_chain_provider import (
    FixtureOptionChainProvider,
    LiveSchwabOptionChainProvider,
    OptionChainProviderResult,
)
from spx_inventory_playbook.paper_trades import (
    PaperTradeIntent,
    PaperTradeLedger,
    PaperTradeLeg,
    create_paper_trade_intent,
)


ReadinessOverallStatus = Literal["ready_for_fixture_rehearsal", "blocked"]
ReadinessCheckStatus = Literal["passed", "failed"]

DEFAULT_APP_OPTION_CHAIN_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fixtures"
    / "market_data"
    / "schwab"
    / "raw_option_chain_0dte.sanitized.json"
)


@dataclass(frozen=True)
class RehearsalReadinessCheck:
    name: str
    status: ReadinessCheckStatus
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RehearsalReadinessResult:
    overall_status: ReadinessOverallStatus
    checks: tuple[RehearsalReadinessCheck, ...]
    reason_codes: tuple[str, ...]
    fixture_path: Path
    provider_name: str | None = None
    source_label: str | None = None
    source_type: str | None = None

    def __repr__(self) -> str:
        return (
            "RehearsalReadinessResult("
            f"overall_status={self.overall_status!r}, "
            f"checks={len(self.checks)!r}, "
            f"reason_codes={self.reason_codes!r}, "
            f"fixture_path={str(self.fixture_path)!r}, "
            f"provider_name={self.provider_name!r}, "
            f"source_label={self.source_label!r}, "
            f"source_type={self.source_type!r})"
        )

    __str__ = __repr__


def evaluate_live_market_rehearsal_readiness(
    *,
    fixture_path: Path = DEFAULT_APP_OPTION_CHAIN_FIXTURE_PATH,
    now: datetime | None = None,
) -> RehearsalReadinessResult:
    """Evaluate local fixture-only readiness without activating live data paths."""

    now_value = now or datetime.now(timezone.utc)
    provider_result = FixtureOptionChainProvider(
        fixture_path=fixture_path,
        source_label="fixture: app-owned sanitized Schwab option-chain capture",
        clock=lambda: now_value,
    ).get_spx_0dte_selection()
    freshness = classify_option_chain_freshness(provider_result, now=now_value)
    context_flags = build_option_chain_context_flags(
        provider_result.selection_view,
        freshness,
    )
    acknowledged_ledger, acknowledged_validation = PaperTradeLedger().append(
        _sample_paper_intent(
            created_at=now_value,
            provider_result=provider_result,
            freshness=freshness,
            context_flags=context_flags,
            operator_acknowledged_context=True,
        ),
    )
    unacknowledged_ledger, unacknowledged_validation = PaperTradeLedger().append(
        _sample_paper_intent(
            created_at=now_value,
            provider_result=provider_result,
            freshness=freshness,
            context_flags=context_flags,
            operator_acknowledged_context=False,
        ),
    )
    live_provider_result = LiveSchwabOptionChainProvider().get_spx_0dte_selection()

    checks = (
        _check(
            "fixture_provider_loads",
            provider_result.status == "available",
            provider_result.reason_code or "fixture_provider_unavailable",
        ),
        _check(
            "parser_returns_snapshot",
            provider_result.snapshot is not None,
            "snapshot_unavailable",
        ),
        _check(
            "selection_view_safe",
            provider_result.selection_view is not None
            and provider_result.selection_view.status in {"available", "unavailable"},
            "selection_view_unavailable",
        ),
        _check(
            "fixture_freshness_static",
            freshness.status == "static_fixture",
            freshness.reason_code or "freshness_not_static_fixture",
        ),
        _check(
            "context_flags_display_only",
            context_flags.data_context == "static_fixture"
            and context_flags.operator_warning_level in {"caution", "blocked"}
            and "static_fixture_not_live" in context_flags.reason_codes,
            "context_flags_not_static_fixture_display_warning",
        ),
        _check(
            "paper_ledger_accepts_acknowledged_static_context",
            acknowledged_validation.is_valid
            and len(acknowledged_ledger.records) == 1,
            "acknowledged_paper_intent_rejected",
        ),
        _check(
            "paper_ledger_rejects_unacknowledged_static_context",
            not unacknowledged_validation.is_valid
            and unacknowledged_validation.reason_codes
            == ("option_chain_context_acknowledgement_required",)
            and len(unacknowledged_ledger.records) == 0,
            "unacknowledged_paper_intent_not_rejected",
        ),
        _check(
            "no_live_provider_active",
            provider_result.source_type == "fixture"
            and provider_result.is_static_source
            and live_provider_result.status == "unavailable",
            "live_provider_may_be_active",
        ),
        _check(
            "live_provider_placeholder_fail_closed",
            live_provider_result.status == "unavailable"
            and live_provider_result.reason_code == "live_provider_not_implemented"
            and live_provider_result.snapshot is None
            and live_provider_result.selection_view is None,
            "live_provider_not_fail_closed",
        ),
    )
    reason_codes = tuple(
        code
        for check in checks
        if check.status == "failed"
        for code in check.reason_codes
    )
    return RehearsalReadinessResult(
        overall_status=(
            "ready_for_fixture_rehearsal" if not reason_codes else "blocked"
        ),
        checks=checks,
        reason_codes=reason_codes,
        fixture_path=fixture_path,
        provider_name=provider_result.provider_name,
        source_label=provider_result.source_label,
        source_type=provider_result.source_type,
    )


def _check(
    name: str,
    condition: bool,
    reason_code: str,
) -> RehearsalReadinessCheck:
    if condition:
        return RehearsalReadinessCheck(name=name, status="passed")
    return RehearsalReadinessCheck(
        name=name,
        status="failed",
        reason_codes=(reason_code,),
    )


def _sample_paper_intent(
    *,
    created_at: datetime,
    provider_result: OptionChainProviderResult,
    freshness: OptionChainFreshness,
    context_flags: OptionChainContextFlags,
    operator_acknowledged_context: bool,
) -> PaperTradeIntent:
    selected_contracts = ()
    if (
        provider_result.selection_view is not None
        and provider_result.selection_view.selected_expiration is not None
    ):
        selected_contracts = provider_result.selection_view.selected_expiration.contracts

    return create_paper_trade_intent(
        created_at=created_at,
        strategy_label="Fixture rehearsal paper intent",
        thesis="Verify local paper intent workflow using fixture option-chain context.",
        invalidation="Stop rehearsal if fixture context is confused with live data.",
        notes="Readiness harness sample; no broker submission.",
        legs=tuple(
            PaperTradeLeg(
                provider_symbol=item.contract.provider_symbol,
                side=item.contract.side,
                expiration=item.contract.expiration,
                strike=item.contract.strike,
                reference_mark=item.contract.mark,
            )
            for item in selected_contracts[:2]
        ),
        option_chain_source_label=provider_result.source_label,
        option_chain_freshness_status=freshness.status,
        option_chain_data_context=context_flags.data_context,
        option_chain_warning_level=context_flags.operator_warning_level,
        option_chain_reason_codes=context_flags.reason_codes,
        playbook_status_label="readiness_harness_fixture_only",
        playbook_allowed_actions=(),
        operator_acknowledged_context=operator_acknowledged_context,
    )


__all__ = [
    "DEFAULT_APP_OPTION_CHAIN_FIXTURE_PATH",
    "ReadinessCheckStatus",
    "ReadinessOverallStatus",
    "RehearsalReadinessCheck",
    "RehearsalReadinessResult",
    "evaluate_live_market_rehearsal_readiness",
]
