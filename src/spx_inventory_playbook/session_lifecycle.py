"""Deterministic session lifecycle contract for the local workstation."""

from dataclasses import dataclass
from enum import Enum


class SessionLifecycleState(Enum):
    """High-level local session states for personal workstation operation."""

    NOT_STARTED = "not_started"
    READY_CHECK = "ready_check"
    DATA_LOADED = "data_loaded"
    INVENTORY_LOADED = "inventory_loaded"
    AUTHORIZED = "authorized"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    SESSION_CLOSED = "session_closed"


class SessionLifecycleAction(Enum):
    """Explicit operator/system lifecycle actions."""

    START_READY_CHECK = "start_ready_check"
    LOAD_DATA = "load_data"
    LOAD_INVENTORY = "load_inventory"
    AUTHORIZE = "authorize"
    RESTRICT = "restrict"
    BLOCK = "block"
    CLOSE_SESSION = "close_session"
    RESET_SESSION = "reset_session"


@dataclass(frozen=True)
class SessionLifecycleTransition:
    """A deterministic state transition with structured reason codes."""

    from_state: SessionLifecycleState
    action: SessionLifecycleAction
    to_state: SessionLifecycleState
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class SessionLifecycleDecision:
    """Decision outcome for a requested session lifecycle transition."""

    transition: SessionLifecycleTransition
    allowed: bool

    @property
    def current_state(self) -> SessionLifecycleState:
        return self.transition.from_state

    @property
    def action(self) -> SessionLifecycleAction:
        return self.transition.action

    @property
    def next_state(self) -> SessionLifecycleState:
        return self.transition.to_state

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return self.transition.reason_codes


_AUTHORIZED_PREREQUISITE_STATES = {SessionLifecycleState.INVENTORY_LOADED}
_RESTRICTABLE_STATES = {
    SessionLifecycleState.READY_CHECK,
    SessionLifecycleState.DATA_LOADED,
    SessionLifecycleState.INVENTORY_LOADED,
    SessionLifecycleState.AUTHORIZED,
    SessionLifecycleState.RESTRICTED,
}


def evaluate_session_lifecycle_transition(
    current_state: SessionLifecycleState,
    action: SessionLifecycleAction,
) -> SessionLifecycleDecision:
    """Evaluate a pure, fail-closed session lifecycle transition."""

    if current_state is SessionLifecycleState.SESSION_CLOSED:
        return _blocked(
            current_state,
            action,
            "SESSION_CLOSED_TERMINAL",
        )

    if action is SessionLifecycleAction.CLOSE_SESSION:
        return _allowed(
            current_state,
            action,
            SessionLifecycleState.SESSION_CLOSED,
            "SESSION_CLOSED",
        )

    if action is SessionLifecycleAction.RESET_SESSION:
        return _allowed(
            current_state,
            action,
            SessionLifecycleState.NOT_STARTED,
            "SESSION_RESET",
        )

    if action is SessionLifecycleAction.BLOCK:
        return _allowed(
            current_state,
            action,
            SessionLifecycleState.BLOCKED,
            "SAFETY_BLOCK_APPLIED",
        )

    if action is SessionLifecycleAction.RESTRICT:
        if current_state in _RESTRICTABLE_STATES:
            return _allowed(
                current_state,
                action,
                SessionLifecycleState.RESTRICTED,
                "SAFETY_RESTRICTION_APPLIED",
            )
        return _blocked(current_state, action, "RESTRICT_REQUIRES_ACTIVE_SESSION")

    if action is SessionLifecycleAction.AUTHORIZE:
        if current_state in _AUTHORIZED_PREREQUISITE_STATES:
            return _allowed(
                current_state,
                action,
                SessionLifecycleState.AUTHORIZED,
                "INVENTORY_LOADED_AUTHORIZATION_ALLOWED",
            )
        return _blocked(current_state, action, "AUTHORIZE_REQUIRES_INVENTORY_LOADED")

    forward_transitions = {
        (
            SessionLifecycleState.NOT_STARTED,
            SessionLifecycleAction.START_READY_CHECK,
        ): (
            SessionLifecycleState.READY_CHECK,
            "READY_CHECK_STARTED",
        ),
        (
            SessionLifecycleState.READY_CHECK,
            SessionLifecycleAction.LOAD_DATA,
        ): (
            SessionLifecycleState.DATA_LOADED,
            "DATA_LOADED",
        ),
        (
            SessionLifecycleState.DATA_LOADED,
            SessionLifecycleAction.LOAD_INVENTORY,
        ): (
            SessionLifecycleState.INVENTORY_LOADED,
            "INVENTORY_LOADED",
        ),
    }
    next_state_and_code = forward_transitions.get((current_state, action))
    if next_state_and_code is None:
        return _blocked(current_state, action, "INVALID_LIFECYCLE_TRANSITION")

    next_state, reason_code = next_state_and_code
    return _allowed(current_state, action, next_state, reason_code)


def _allowed(
    current_state: SessionLifecycleState,
    action: SessionLifecycleAction,
    next_state: SessionLifecycleState,
    reason_code: str,
) -> SessionLifecycleDecision:
    return SessionLifecycleDecision(
        transition=SessionLifecycleTransition(
            from_state=current_state,
            action=action,
            to_state=next_state,
            reason_codes=(reason_code,),
        ),
        allowed=True,
    )


def _blocked(
    current_state: SessionLifecycleState,
    action: SessionLifecycleAction,
    reason_code: str,
) -> SessionLifecycleDecision:
    return SessionLifecycleDecision(
        transition=SessionLifecycleTransition(
            from_state=current_state,
            action=action,
            to_state=current_state,
            reason_codes=(reason_code,),
        ),
        allowed=False,
    )
