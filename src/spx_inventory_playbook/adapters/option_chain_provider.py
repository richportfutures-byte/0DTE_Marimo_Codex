"""Provider boundary for app-ready option-chain selection views."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

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


class OptionChainProvider(Protocol):
    """Boundary later app code can call without knowing the backing source."""

    def get_spx_0dte_selection(self) -> "OptionChainProviderResult":
        """Return a bounded SPX option-chain selection view."""


@dataclass(frozen=True)
class OptionChainProviderResult:
    provider_name: str
    source_label: str
    status: ProviderStatus
    reason_code: str | None = None
    fixture_path: Path | None = None
    snapshot: SchwabOptionChainSnapshot | None = None
    selection_view: OptionChainSelectionView | None = None

    def __repr__(self) -> str:
        return (
            "OptionChainProviderResult("
            f"provider_name={self.provider_name!r}, "
            f"source_label={self.source_label!r}, "
            f"status={self.status!r}, "
            f"reason_code={self.reason_code!r}, "
            f"fixture_path={str(self.fixture_path)!r}, "
            f"has_snapshot={self.snapshot is not None!r}, "
            f"has_selection_view={self.selection_view is not None!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class FixtureOptionChainProvider:
    fixture_path: Path
    provider_name: str = "schwab_fixture"
    source_label: str = "fixture"

    def get_spx_0dte_selection(self) -> OptionChainProviderResult:
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self._result("error", "fixture_not_found")
        except OSError:
            return self._result("error", "fixture_read_error")
        except json.JSONDecodeError:
            return self._result("error", "fixture_json_malformed")

        try:
            snapshot = parse_schwab_option_chain(payload)
            selection_view = build_spx_0dte_selection_view(snapshot)
        except SchwabOptionChainParserError:
            return self._result("error", "fixture_parse_error")

        if selection_view.status != "available":
            reason_code = (
                selection_view.reason_codes[0]
                if selection_view.reason_codes
                else "selection_unavailable"
            )
            return self._result(
                "unavailable",
                reason_code,
                snapshot=snapshot,
                selection_view=selection_view,
            )

        return self._result(
            "available",
            None,
            snapshot=snapshot,
            selection_view=selection_view,
        )

    def _result(
        self,
        status: ProviderStatus,
        reason_code: str | None,
        *,
        snapshot: SchwabOptionChainSnapshot | None = None,
        selection_view: OptionChainSelectionView | None = None,
    ) -> OptionChainProviderResult:
        return OptionChainProviderResult(
            provider_name=self.provider_name,
            source_label=self.source_label,
            status=status,
            reason_code=reason_code,
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
            status="unavailable",
            reason_code="live_provider_not_implemented",
        )


__all__ = [
    "FixtureOptionChainProvider",
    "LiveSchwabOptionChainProvider",
    "OptionChainProvider",
    "OptionChainProviderResult",
    "ProviderStatus",
]
