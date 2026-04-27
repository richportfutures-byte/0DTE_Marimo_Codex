from spx_inventory_playbook.validators import (
    BehaviorContext,
    DealerRegime,
    InventoryState,
    MarketContext,
    PositionContext,
    PositionStructure,
    TimeWindow,
    ValidationMessage,
    ValidationResult,
    ValidationSeverity,
    validate_inventory_state,
)


def make_state(
    *,
    behavior_authorized: bool = True,
    daily_lockout_active: bool = False,
    weekly_lockout_active: bool = False,
    trying_to_avoid_loss_realization: bool = False,
    rule_violation_occurred: bool = False,
    accepted_beyond_invalidation: bool = False,
    liquidity_acceptable: bool = True,
    time_window: TimeWindow = TimeWindow.MORNING_945_1030,
    position_size_exceeds_plan: bool = False,
) -> InventoryState:
    return InventoryState(
        market=MarketContext(
            dealer_regime=DealerRegime.UNCLEAR,
            time_window=time_window,
            spot_relative_to_flip=None,
            event_pending=False,
            liquidity_acceptable=liquidity_acceptable,
        ),
        position=PositionContext(
            structure=PositionStructure.OTHER,
            thesis_valid=True,
            accepted_beyond_invalidation=accepted_beyond_invalidation,
            current_loss_inside_plan=True,
            gamma_manageable=True,
            delta_intentional=True,
            position_size_exceeds_plan=position_size_exceeds_plan,
        ),
        behavior=BehaviorContext(
            behavior_authorized=behavior_authorized,
            daily_lockout_active=daily_lockout_active,
            weekly_lockout_active=weekly_lockout_active,
            trying_to_avoid_loss_realization=trying_to_avoid_loss_realization,
            rule_violation_occurred=rule_violation_occurred,
        ),
    )


def messages_by_code(result: ValidationResult) -> dict[str, ValidationMessage]:
    return {message.code: message for message in result.messages}


def test_validation_result_has_blockers() -> None:
    warning_only = ValidationResult(
        messages=[
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                code="WARNING_ONLY",
                message="test warning",
            )
        ]
    )
    blocker = ValidationResult(
        messages=[
            ValidationMessage(
                severity=ValidationSeverity.BLOCKER,
                code="BLOCKER",
                message="test blocker",
            )
        ]
    )

    assert not warning_only.has_blockers()
    assert blocker.has_blockers()


def test_daily_lockout_creates_blocker() -> None:
    result = validate_inventory_state(make_state(daily_lockout_active=True))

    message = messages_by_code(result)["LOCKOUT_ACTIVE"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_behavior_not_authorized_creates_blocker() -> None:
    result = validate_inventory_state(make_state(behavior_authorized=False))

    message = messages_by_code(result)["BEHAVIOR_NOT_AUTHORIZED"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_accepted_beyond_invalidation_creates_blocker() -> None:
    result = validate_inventory_state(make_state(accepted_beyond_invalidation=True))

    message = messages_by_code(result)["THESIS_INVALIDATED"]
    assert message.severity is ValidationSeverity.BLOCKER
    assert result.has_blockers()


def test_poor_liquidity_creates_warning_not_blocker() -> None:
    result = validate_inventory_state(make_state(liquidity_acceptable=False))

    message = messages_by_code(result)["LIQUIDITY_POOR"]
    assert message.severity is ValidationSeverity.WARNING
    assert not result.has_blockers()


def test_final_five_minutes_creates_warning_not_blocker() -> None:
    result = validate_inventory_state(make_state(time_window=TimeWindow.FINAL_5_1555_1600))

    message = messages_by_code(result)["FINAL_5_MINUTES"]
    assert message.severity is ValidationSeverity.WARNING
    assert not result.has_blockers()
