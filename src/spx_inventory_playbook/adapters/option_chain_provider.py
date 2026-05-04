"""Provider boundary for app-ready option-chain selection views."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Protocol

from spx_inventory_playbook.adapters.schwab_option_chain import (
    SchwabOptionChainParserError,
    SchwabOptionChainSnapshot,
    parse_schwab_option_chain,
)
from spx_inventory_playbook.adapters.schwab_option_chain_selection import (
    OptionChainSelectionView,
    build_spx_0dte_selection_view,
)


ProviderStatus = Literal["available", "unavailable", "error"]
ProviderSourceType = Literal["fixture", "live", "unknown"]


class MarketDataProviderState(Enum):
    """Unified operator-facing state for market-data provider results."""

    FIXTURE = "fixture"
    LIVE_FRESH = "live_fresh"
    LIVE_STALE = "live_stale"
    LIVE_UNAVAILABLE = "live_unavailable"
    LIVE_PARSE_ERROR = "live_parse_error"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OptionChainProvider(Protocol):
    """Boundary later app code can call without knowing the backing source."""

    def get_spx_0dte_selection(self) -> "OptionChainProviderResult":
        """Return a bounded SPX option-chain selection view."""


@dataclass(frozen=True)
class OptionChainProviderRequest:
    """Typed provider request/gate input that never exposes credential contents."""

    requested_source_type: ProviderSourceType = "fixture"
    confirm_live: str = ""
    live_token_file_path: Path | None = None
    required_confirmation_phrase: str = ""

    @property
    def live_requested(self) -> bool:
        return self.requested_source_type == "live"


@dataclass(frozen=True)
class LiveProviderGateDecision:
    """Fail-closed live-provider activation decision."""

    live_requested: bool
    allowed: bool
    reason_code: str | None
    token_file_path_provided: bool

    def __repr__(self) -> str:
        return (
            "LiveProviderGateDecision("
            f"live_requested={self.live_requested!r}, "
            f"allowed={self.allowed!r}, "
            f"reason_code={self.reason_code!r}, "
            f"token_file_path_provided={self.token_file_path_provided!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class OptionChainProviderResult:
    provider_name: str
    source_label: str
    source_type: ProviderSourceType
    status: ProviderStatus
    reason_code: str | None = None
    loaded_at: datetime | None = None
    is_static_source: bool = False
    fixture_path: Path | None = None
    snapshot: SchwabOptionChainSnapshot | None = None
    selection_view: OptionChainSelectionView | None = None

    def __repr__(self) -> str:
        return (
            "OptionChainProviderResult("
            f"provider_name={self.provider_name!r}, "
            f"source_label={self.source_label!r}, "
            f"source_type={self.source_type!r}, "
            f"status={self.status!r}, "
            f"reason_code={self.reason_code!r}, "
            f"loaded_at={self.loaded_at.isoformat() if self.loaded_at else None!r}, "
            f"is_static_source={self.is_static_source!r}, "
            f"fixture_path={str(self.fixture_path)!r}, "
            f"has_snapshot={self.snapshot is not None!r}, "
            f"has_selection_view={self.selection_view is not None!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class MarketDataProviderStateSummary:
    """Safe, persistable provider-state summary without paths or raw payloads."""

    provider_state: MarketDataProviderState
    provider_name: str
    source_label: str
    source_type: ProviderSourceType
    status: ProviderStatus
    reason_code: str | None
    loaded_at: datetime | None


def evaluate_live_provider_gate(
    request: OptionChainProviderRequest,
) -> LiveProviderGateDecision:
    """Evaluate live activation without reading token files or displaying paths."""

    if not request.live_requested:
        return LiveProviderGateDecision(
            live_requested=False,
            allowed=False,
            reason_code="fixture_mode_default",
            token_file_path_provided=request.live_token_file_path is not None,
        )
    if request.confirm_live != request.required_confirmation_phrase:
        return LiveProviderGateDecision(
            live_requested=True,
            allowed=False,
            reason_code="manual_live_confirmation_required",
            token_file_path_provided=request.live_token_file_path is not None,
        )
    if request.live_token_file_path is None:
        return LiveProviderGateDecision(
            live_requested=True,
            allowed=False,
            reason_code="access_token_required",
            token_file_path_provided=False,
        )
    return LiveProviderGateDecision(
        live_requested=True,
        allowed=True,
        reason_code=None,
        token_file_path_provided=True,
    )


def summarize_provider_state(
    result: OptionChainProviderResult,
    provider_state: MarketDataProviderState,
) -> MarketDataProviderStateSummary:
    """Build a safe provider-state summary for downstream persistence/display."""

    return MarketDataProviderStateSummary(
        provider_state=provider_state,
        provider_name=result.provider_name,
        source_label=result.source_label,
        source_type=result.source_type,
        status=result.status,
        reason_code=result.reason_code,
        loaded_at=result.loaded_at,
    )


@dataclass(frozen=True)
class FixtureOptionChainProvider:
    fixture_path: Path
    provider_name: str = "schwab_fixture"
    source_label: str = "fixture"
    clock: Callable[[], datetime] = _utc_now

    def get_spx_0dte_selection(self) -> OptionChainProviderResult:
        loaded_at = self.clock()
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self._result("error", "fixture_not_found", loaded_at=loaded_at)
        except OSError:
            return self._result("error", "fixture_read_error", loaded_at=loaded_at)
        except json.JSONDecodeError:
            return self._result("error", "fixture_json_malformed", loaded_at=loaded_at)

        try:
            snapshot = parse_schwab_option_chain(payload)
            selection_view = build_spx_0dte_selection_view(snapshot)
        except SchwabOptionChainParserError:
            return self._result("error", "fixture_parse_error", loaded_at=loaded_at)

        if selection_view.status != "available":
            reason_code = (
                selection_view.reason_codes[0]
                if selection_view.reason_codes
                else "selection_unavailable"
            )
            return self._result(
                "unavailable",
                reason_code,
                loaded_at=loaded_at,
                snapshot=snapshot,
                selection_view=selection_view,
            )

        return self._result(
            "available",
            None,
            loaded_at=loaded_at,
            snapshot=snapshot,
            selection_view=selection_view,
        )

    def _result(
        self,
        status: ProviderStatus,
        reason_code: str | None,
        *,
        loaded_at: datetime,
        snapshot: SchwabOptionChainSnapshot | None = None,
        selection_view: OptionChainSelectionView | None = None,
    ) -> OptionChainProviderResult:
        return OptionChainProviderResult(
            provider_name=self.provider_name,
            source_label=self.source_label,
            source_type="fixture",
            status=status,
            reason_code=reason_code,
            loaded_at=loaded_at,
            is_static_source=True,
            fixture_path=self.fixture_path,
            snapshot=snapshot,
            selection_view=selection_view,
        )


@dataclass(frozen=True)
class LiveSchwabOptionChainProvider:
    provider_name: str = "schwab_live"
    source_label: str = "live"

    def get_spx_0dte_selection(self) -> OptionChainProviderResult:
        return OptionChainProviderResult(
            provider_name=self.provider_name,
            source_label=self.source_label,
            source_type="live",
            status="unavailable",
            reason_code="live_provider_not_implemented",
            loaded_at=None,
            is_static_source=False,
        )


__all__ = [
    "FixtureOptionChainProvider",
    "LiveSchwabOptionChainProvider",
    "LiveProviderGateDecision",
    "MarketDataProviderState",
    "MarketDataProviderStateSummary",
    "OptionChainProvider",
    "OptionChainProviderRequest",
    "OptionChainProviderResult",
    "ProviderSourceType",
    "ProviderStatus",
    "evaluate_live_provider_gate",
    "summarize_provider_state",
]
