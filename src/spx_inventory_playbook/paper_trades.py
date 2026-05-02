"""Local-only paper trade intent records for operator practice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


PaperTradeStatus = Literal["valid", "invalid"]


@dataclass(frozen=True)
class PaperTradeLeg:
    provider_symbol: str | None
    side: Literal["CALL", "PUT"] | None
    expiration: date | None
    strike: float | None
    reference_mark: float | None = None


@dataclass(frozen=True)
class PaperTradeIntent:
    created_at: datetime
    strategy_label: str
    thesis: str
    invalidation: str
    notes: str = ""
    legs: tuple[PaperTradeLeg, ...] = ()
    entry_reference: float | None = None
    option_chain_source_label: str | None = None
    option_chain_freshness_status: str | None = None
    option_chain_data_context: str | None = None
    option_chain_warning_level: str | None = None
    option_chain_reason_codes: tuple[str, ...] = ()
    playbook_status_label: str | None = None
    playbook_allowed_actions: tuple[str, ...] = ()
    is_paper_only: bool = True
    broker_submitted: bool = False
    operator_acknowledged_context: bool = False
    paper_disclaimer: str = "local_paper_intent_only_no_broker_submission"


@dataclass(frozen=True)
class PaperTradeValidationResult:
    status: PaperTradeStatus
    reason_codes: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"


@dataclass(frozen=True)
class PaperTradeLedger:
    records: tuple[PaperTradeIntent, ...] = ()

    def append(
        self,
        intent: PaperTradeIntent,
    ) -> tuple["PaperTradeLedger", PaperTradeValidationResult]:
        validation = validate_paper_trade_intent(intent)
        if not validation.is_valid:
            return self, validation
        return PaperTradeLedger(records=self.records + (intent,)), validation


def validate_paper_trade_intent(intent: PaperTradeIntent) -> PaperTradeValidationResult:
    reason_codes: list[str] = []
    if not intent.strategy_label.strip():
        reason_codes.append("strategy_label_required")
    if not intent.thesis.strip():
        reason_codes.append("thesis_required")
    if not intent.invalidation.strip():
        reason_codes.append("invalidation_required")
    if not intent.is_paper_only:
        reason_codes.append("paper_only_required")
    if intent.broker_submitted:
        reason_codes.append("broker_submission_not_allowed")
    if (
        intent.option_chain_data_context
        in {"static_fixture", "stale_live", "invalid", "unavailable"}
        and not intent.operator_acknowledged_context
    ):
        reason_codes.append("option_chain_context_acknowledgement_required")

    if reason_codes:
        return PaperTradeValidationResult(
            status="invalid",
            reason_codes=tuple(reason_codes),
        )
    return PaperTradeValidationResult(status="valid")


def create_paper_trade_intent(
    *,
    created_at: datetime,
    strategy_label: str,
    thesis: str,
    invalidation: str,
    notes: str = "",
    legs: tuple[PaperTradeLeg, ...] = (),
    entry_reference: float | None = None,
    option_chain_source_label: str | None = None,
    option_chain_freshness_status: str | None = None,
    option_chain_data_context: str | None = None,
    option_chain_warning_level: str | None = None,
    option_chain_reason_codes: tuple[str, ...] = (),
    playbook_status_label: str | None = None,
    playbook_allowed_actions: tuple[str, ...] = (),
    operator_acknowledged_context: bool = False,
) -> PaperTradeIntent:
    return PaperTradeIntent(
        created_at=created_at,
        strategy_label=strategy_label.strip(),
        thesis=thesis.strip(),
        invalidation=invalidation.strip(),
        notes=notes.strip(),
        legs=tuple(legs),
        entry_reference=entry_reference,
        option_chain_source_label=option_chain_source_label,
        option_chain_freshness_status=option_chain_freshness_status,
        option_chain_data_context=option_chain_data_context,
        option_chain_warning_level=option_chain_warning_level,
        option_chain_reason_codes=tuple(option_chain_reason_codes),
        playbook_status_label=playbook_status_label,
        playbook_allowed_actions=tuple(playbook_allowed_actions),
        is_paper_only=True,
        broker_submitted=False,
        operator_acknowledged_context=operator_acknowledged_context,
    )


__all__ = [
    "PaperTradeIntent",
    "PaperTradeLedger",
    "PaperTradeLeg",
    "PaperTradeStatus",
    "PaperTradeValidationResult",
    "create_paper_trade_intent",
    "validate_paper_trade_intent",
]
