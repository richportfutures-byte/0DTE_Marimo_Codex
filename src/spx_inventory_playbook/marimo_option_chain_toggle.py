"""Fail-closed Marimo option-chain source selection.

This module owns only market-data provider selection for the notebook. It does
not import playbook authorization, state-machine, broker, account, order,
position, fill, or P&L code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (
    MANUAL_LIVE_CONFIRM_PHRASE,
    ManualLiveSchwabOptionChainConfig,
    SchwabOptionChainRequestSpec,
    run_manual_live_schwab_option_chain_selection,
)
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
    OptionChainProviderResult,
    ProviderSourceType,
)


FIXTURE_OPTION_CHAIN_MODE_LABEL = "Fixture/static option chain"
LIVE_OPTION_CHAIN_MODE_LABEL = "Live Schwab option chain"
LIVE_TOKEN_FILE_ENV_VAR = "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE"
FALLBACK_LIVE_TOKEN_FILE_ENV_VAR = "SCHWAB_TOKEN_PATH"

JsonObject = dict[str, object]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MarimoOptionChainControlState:
    selected_mode: str
    requested_source_type: ProviderSourceType
    live_mode_selected: bool
    manual_confirmation_valid: bool
    credential_source_configured: bool
    credential_source_label: str
    manual_refresh_only: bool = True

    @property
    def live_activation_ready(self) -> bool:
        return (
            self.live_mode_selected
            and self.manual_confirmation_valid
            and self.credential_source_configured
        )

    def __repr__(self) -> str:
        return (
            "MarimoOptionChainControlState("
            f"selected_mode={self.selected_mode!r}, "
            f"requested_source_type={self.requested_source_type!r}, "
            f"live_mode_selected={self.live_mode_selected!r}, "
            f"manual_confirmation_valid={self.manual_confirmation_valid!r}, "
            f"credential_source_configured={self.credential_source_configured!r}, "
            f"credential_source_label={self.credential_source_label!r}, "
            f"manual_refresh_only={self.manual_refresh_only!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class MarimoOptionChainToggleResult:
    control_state: MarimoOptionChainControlState
    provider_result: OptionChainProviderResult
    freshness: OptionChainFreshness
    context_flags: OptionChainContextFlags

    def __repr__(self) -> str:
        return (
            "MarimoOptionChainToggleResult("
            f"control_state={self.control_state!r}, "
            f"provider_result={self.provider_result!r}, "
            f"freshness_status={self.freshness.status!r}, "
            f"data_context={self.context_flags.data_context!r})"
        )

    __str__ = __repr__


def resolve_live_token_file_path(
    environ: Mapping[str, str] | None = None,
) -> Path | None:
    """Resolve a local token-file path without reading or displaying contents."""

    env = os.environ if environ is None else environ
    value = (env.get(LIVE_TOKEN_FILE_ENV_VAR) or "").strip()
    if not value:
        value = (env.get(FALLBACK_LIVE_TOKEN_FILE_ENV_VAR) or "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def build_marimo_option_chain_control_state(
    *,
    selected_mode: str,
    confirm_live: str,
    live_token_file_path: Path | None,
) -> MarimoOptionChainControlState:
    """Describe operator activation state without touching credential contents."""

    live_mode_selected = selected_mode == LIVE_OPTION_CHAIN_MODE_LABEL
    return MarimoOptionChainControlState(
        selected_mode=selected_mode,
        requested_source_type="live" if live_mode_selected else "fixture",
        live_mode_selected=live_mode_selected,
        manual_confirmation_valid=confirm_live == MANUAL_LIVE_CONFIRM_PHRASE,
        credential_source_configured=live_token_file_path is not None,
        credential_source_label=(
            "local token file configured"
            if live_token_file_path is not None
            else "local token file missing"
        ),
    )


def load_marimo_option_chain_provider(
    *,
    selected_mode: str,
    confirm_live: str,
    fixture_path: Path,
    live_token_file_path: Path | None,
    http_get_json: Callable[[SchwabOptionChainRequestSpec, str], JsonObject]
    | None = None,
    now: datetime | None = None,
) -> MarimoOptionChainToggleResult:
    """Load one option-chain provider result according to fail-closed controls."""

    loaded_at = now or _utc_now()
    control_state = build_marimo_option_chain_control_state(
        selected_mode=selected_mode,
        confirm_live=confirm_live,
        live_token_file_path=live_token_file_path,
    )
    if not control_state.live_mode_selected:
        provider_result = FixtureOptionChainProvider(
            fixture_path,
            source_label="fixture: sanitized Schwab option-chain capture",
            clock=lambda: loaded_at,
        ).get_spx_0dte_selection()
        return _toggle_result(control_state, provider_result, now=loaded_at)

    if not control_state.manual_confirmation_valid:
        provider_result = _blocked_live_provider_result(
            reason_code="manual_live_confirmation_required",
            loaded_at=loaded_at,
        )
        return _toggle_result(control_state, provider_result, now=loaded_at)

    if live_token_file_path is None:
        provider_result = _blocked_live_provider_result(
            reason_code="access_token_required",
            loaded_at=loaded_at,
        )
        return _toggle_result(control_state, provider_result, now=loaded_at)

    harness_result = run_manual_live_schwab_option_chain_selection(
        config=ManualLiveSchwabOptionChainConfig(confirm_live=confirm_live),
        access_token_file=live_token_file_path,
        http_get_json=http_get_json,
        now=loaded_at,
    )
    provider_result = harness_result.provider_result or _blocked_live_provider_result(
        status=harness_result.status,
        reason_code=harness_result.reason_code or "live_provider_unavailable",
        loaded_at=loaded_at,
    )
    return build_marimo_option_chain_toggle_result(
        control_state=control_state,
        provider_result=provider_result,
        now=loaded_at,
    )


def build_marimo_option_chain_toggle_result(
    *,
    control_state: MarimoOptionChainControlState,
    provider_result: OptionChainProviderResult,
    now: datetime | None = None,
) -> MarimoOptionChainToggleResult:
    """Attach freshness and display-only context to an existing provider result."""

    evaluated_at = now or _utc_now()
    freshness = classify_option_chain_freshness(provider_result, now=evaluated_at)
    context_flags = build_option_chain_context_flags(
        provider_result.selection_view,
        freshness,
    )
    return MarimoOptionChainToggleResult(
        control_state=control_state,
        provider_result=provider_result,
        freshness=freshness,
        context_flags=context_flags,
    )


def _toggle_result(
    control_state: MarimoOptionChainControlState,
    provider_result: OptionChainProviderResult,
    *,
    now: datetime,
) -> MarimoOptionChainToggleResult:
    return build_marimo_option_chain_toggle_result(
        control_state=control_state,
        provider_result=provider_result,
        now=now,
    )


def _blocked_live_provider_result(
    *,
    reason_code: str,
    loaded_at: datetime,
    status: str = "unavailable",
) -> OptionChainProviderResult:
    return OptionChainProviderResult(
        provider_name="schwab_manual_live",
        source_label="live: manual Schwab option-chain market data",
        source_type="live",
        status=status,
        reason_code=reason_code,
        loaded_at=loaded_at,
        is_static_source=False,
    )


__all__ = [
    "FALLBACK_LIVE_TOKEN_FILE_ENV_VAR",
    "FIXTURE_OPTION_CHAIN_MODE_LABEL",
    "LIVE_OPTION_CHAIN_MODE_LABEL",
    "LIVE_TOKEN_FILE_ENV_VAR",
    "MarimoOptionChainControlState",
    "MarimoOptionChainToggleResult",
    "build_marimo_option_chain_control_state",
    "build_marimo_option_chain_toggle_result",
    "load_marimo_option_chain_provider",
    "resolve_live_token_file_path",
]
