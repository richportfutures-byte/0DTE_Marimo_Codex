from spx_inventory_playbook.session_lifecycle import (
    SessionLifecycleAction,
    SessionLifecycleDecision,
    SessionLifecycleState,
    SessionLifecycleTransition,
    evaluate_session_lifecycle_transition,
)


def evaluate(
    state: SessionLifecycleState,
    action: SessionLifecycleAction,
) -> SessionLifecycleDecision:
    return evaluate_session_lifecycle_transition(state, action)


def assert_allowed(
    decision: SessionLifecycleDecision,
    *,
    current_state: SessionLifecycleState,
    action: SessionLifecycleAction,
    next_state: SessionLifecycleState,
    reason_code: str,
) -> None:
    assert decision.allowed is True
    assert decision.current_state is current_state
    assert decision.action is action
    assert decision.next_state is next_state
    assert decision.reason_codes == (reason_code,)
    assert isinstance(decision.transition, SessionLifecycleTransition)


def assert_blocked(
    decision: SessionLifecycleDecision,
    *,
    current_state: SessionLifecycleState,
    action: SessionLifecycleAction,
    reason_code: str,
) -> None:
    assert decision.allowed is False
    assert decision.current_state is current_state
    assert decision.action is action
    assert decision.next_state is current_state
    assert decision.reason_codes == (reason_code,)


def test_initial_ready_check_transition() -> None:
    decision = evaluate(
        SessionLifecycleState.NOT_STARTED,
        SessionLifecycleAction.START_READY_CHECK,
    )

    assert_allowed(
        decision,
        current_state=SessionLifecycleState.NOT_STARTED,
        action=SessionLifecycleAction.START_READY_CHECK,
        next_state=SessionLifecycleState.READY_CHECK,
        reason_code="READY_CHECK_STARTED",
    )


def test_data_load_transition() -> None:
    decision = evaluate(SessionLifecycleState.READY_CHECK, SessionLifecycleAction.LOAD_DATA)

    assert_allowed(
        decision,
        current_state=SessionLifecycleState.READY_CHECK,
        action=SessionLifecycleAction.LOAD_DATA,
        next_state=SessionLifecycleState.DATA_LOADED,
        reason_code="DATA_LOADED",
    )


def test_inventory_load_transition() -> None:
    decision = evaluate(SessionLifecycleState.DATA_LOADED, SessionLifecycleAction.LOAD_INVENTORY)

    assert_allowed(
        decision,
        current_state=SessionLifecycleState.DATA_LOADED,
        action=SessionLifecycleAction.LOAD_INVENTORY,
        next_state=SessionLifecycleState.INVENTORY_LOADED,
        reason_code="INVENTORY_LOADED",
    )


def test_authorization_only_after_inventory_load() -> None:
    decision = evaluate(SessionLifecycleState.INVENTORY_LOADED, SessionLifecycleAction.AUTHORIZE)

    assert_allowed(
        decision,
        current_state=SessionLifecycleState.INVENTORY_LOADED,
        action=SessionLifecycleAction.AUTHORIZE,
        next_state=SessionLifecycleState.AUTHORIZED,
        reason_code="INVENTORY_LOADED_AUTHORIZATION_ALLOWED",
    )


def test_direct_authorization_from_not_started_is_blocked() -> None:
    decision = evaluate(SessionLifecycleState.NOT_STARTED, SessionLifecycleAction.AUTHORIZE)

    assert_blocked(
        decision,
        current_state=SessionLifecycleState.NOT_STARTED,
        action=SessionLifecycleAction.AUTHORIZE,
        reason_code="AUTHORIZE_REQUIRES_INVENTORY_LOADED",
    )


def test_direct_authorization_from_ready_check_is_blocked() -> None:
    decision = evaluate(SessionLifecycleState.READY_CHECK, SessionLifecycleAction.AUTHORIZE)

    assert_blocked(
        decision,
        current_state=SessionLifecycleState.READY_CHECK,
        action=SessionLifecycleAction.AUTHORIZE,
        reason_code="AUTHORIZE_REQUIRES_INVENTORY_LOADED",
    )


def test_direct_authorization_from_data_loaded_is_blocked() -> None:
    decision = evaluate(SessionLifecycleState.DATA_LOADED, SessionLifecycleAction.AUTHORIZE)

    assert_blocked(
        decision,
        current_state=SessionLifecycleState.DATA_LOADED,
        action=SessionLifecycleAction.AUTHORIZE,
        reason_code="AUTHORIZE_REQUIRES_INVENTORY_LOADED",
    )


def test_restricted_transition_from_inventory_loaded_is_allowed() -> None:
    decision = evaluate(SessionLifecycleState.INVENTORY_LOADED, SessionLifecycleAction.RESTRICT)

    assert_allowed(
        decision,
        current_state=SessionLifecycleState.INVENTORY_LOADED,
        action=SessionLifecycleAction.RESTRICT,
        next_state=SessionLifecycleState.RESTRICTED,
        reason_code="SAFETY_RESTRICTION_APPLIED",
    )


def test_blocked_transition_from_any_active_pre_closed_state_is_allowed() -> None:
    active_pre_closed_states = set(SessionLifecycleState) - {
        SessionLifecycleState.SESSION_CLOSED
    }

    for state in active_pre_closed_states:
        decision = evaluate(state, SessionLifecycleAction.BLOCK)
        assert_allowed(
            decision,
            current_state=state,
            action=SessionLifecycleAction.BLOCK,
            next_state=SessionLifecycleState.BLOCKED,
            reason_code="SAFETY_BLOCK_APPLIED",
        )


def test_close_session_is_allowed_from_active_states() -> None:
    active_pre_closed_states = set(SessionLifecycleState) - {
        SessionLifecycleState.SESSION_CLOSED
    }

    for state in active_pre_closed_states:
        decision = evaluate(state, SessionLifecycleAction.CLOSE_SESSION)
        assert_allowed(
            decision,
            current_state=state,
            action=SessionLifecycleAction.CLOSE_SESSION,
            next_state=SessionLifecycleState.SESSION_CLOSED,
            reason_code="SESSION_CLOSED",
        )


def test_closed_session_is_terminal() -> None:
    for action in SessionLifecycleAction:
        decision = evaluate(SessionLifecycleState.SESSION_CLOSED, action)
        assert_blocked(
            decision,
            current_state=SessionLifecycleState.SESSION_CLOSED,
            action=action,
            reason_code="SESSION_CLOSED_TERMINAL",
        )


def test_invalid_transition_returns_same_state_and_reason_code() -> None:
    decision = evaluate(SessionLifecycleState.READY_CHECK, SessionLifecycleAction.LOAD_INVENTORY)

    assert_blocked(
        decision,
        current_state=SessionLifecycleState.READY_CHECK,
        action=SessionLifecycleAction.LOAD_INVENTORY,
        reason_code="INVALID_LIFECYCLE_TRANSITION",
    )


def test_reset_returns_to_not_started_before_close() -> None:
    for state in set(SessionLifecycleState) - {SessionLifecycleState.SESSION_CLOSED}:
        decision = evaluate(state, SessionLifecycleAction.RESET_SESSION)
        assert_allowed(
            decision,
            current_state=state,
            action=SessionLifecycleAction.RESET_SESSION,
            next_state=SessionLifecycleState.NOT_STARTED,
            reason_code="SESSION_RESET",
        )


def test_reset_after_close_is_blocked_by_terminal_session_rule() -> None:
    decision = evaluate(
        SessionLifecycleState.SESSION_CLOSED,
        SessionLifecycleAction.RESET_SESSION,
    )

    assert_blocked(
        decision,
        current_state=SessionLifecycleState.SESSION_CLOSED,
        action=SessionLifecycleAction.RESET_SESSION,
        reason_code="SESSION_CLOSED_TERMINAL",
    )


def test_all_decisions_are_deterministic_and_contain_structured_reason_codes() -> None:
    for state in SessionLifecycleState:
        for action in SessionLifecycleAction:
            first_decision = evaluate(state, action)
            second_decision = evaluate(state, action)

            assert first_decision == second_decision
            assert isinstance(first_decision.reason_codes, tuple)
            assert first_decision.reason_codes
            assert all(isinstance(code, str) and code for code in first_decision.reason_codes)
