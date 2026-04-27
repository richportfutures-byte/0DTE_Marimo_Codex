"""Abstract inventory-state fixtures for tests and future UI wiring."""

from dataclasses import replace

from .validators import (
    BehaviorContext,
    DealerRegime,
    InventoryState,
    MarketContext,
    PositionContext,
    PositionStructure,
    TimeWindow,
)


_ALLOWED_OVERRIDE_FIELDS = {
    "market": {
        "dealer_regime",
        "time_window",
        "spot_relative_to_flip",
        "event_pending",
        "liquidity_acceptable",
    },
    "position": {
        "structure",
        "thesis_valid",
        "accepted_beyond_invalidation",
        "current_loss_inside_plan",
        "gamma_manageable",
        "delta_intentional",
        "position_size_exceeds_plan",
    },
    "behavior": {
        "behavior_authorized",
        "daily_lockout_active",
        "weekly_lockout_active",
        "trying_to_avoid_loss_realization",
        "rule_violation_occurred",
    },
}


def clean_state() -> InventoryState:
    """Return an abstract state with no validation blockers or warnings."""
    return InventoryState(
        market=MarketContext(
            dealer_regime=DealerRegime.UNCLEAR,
            time_window=TimeWindow.MORNING_945_1030,
            spot_relative_to_flip=None,
            event_pending=False,
            liquidity_acceptable=True,
        ),
        position=PositionContext(
            structure=PositionStructure.OTHER,
            thesis_valid=True,
            accepted_beyond_invalidation=False,
            current_loss_inside_plan=True,
            gamma_manageable=True,
            delta_intentional=True,
            position_size_exceeds_plan=False,
        ),
        behavior=BehaviorContext(
            behavior_authorized=True,
            daily_lockout_active=False,
            weekly_lockout_active=False,
            trying_to_avoid_loss_realization=False,
            rule_violation_occurred=False,
        ),
    )


def state_with_overrides(base: InventoryState, **overrides: object) -> InventoryState:
    """Return a copy of a state with dotted nested-field overrides applied."""
    updates: dict[str, dict[str, object]] = {"market": {}, "position": {}, "behavior": {}}

    for key, value in overrides.items():
        parts = key.split(".")
        if len(parts) != 2:
            raise ValueError(f"Unsupported override key: {key}")

        section, field_name = parts
        if field_name not in _ALLOWED_OVERRIDE_FIELDS.get(section, set()):
            raise ValueError(f"Unsupported override key: {key}")

        updates[section][field_name] = value

    market = replace(base.market, **updates["market"]) if updates["market"] else base.market
    position = (
        replace(base.position, **updates["position"]) if updates["position"] else base.position
    )
    behavior = (
        replace(base.behavior, **updates["behavior"]) if updates["behavior"] else base.behavior
    )

    return replace(base, market=market, position=position, behavior=behavior)


def lockout_state() -> InventoryState:
    """Return an abstract daily-lockout state."""
    return state_with_overrides(clean_state(), **{"behavior.daily_lockout_active": True})


def behavior_not_authorized_state() -> InventoryState:
    """Return an abstract state where discretionary behavior is not authorized."""
    return state_with_overrides(clean_state(), **{"behavior.behavior_authorized": False})


def rule_violation_state() -> InventoryState:
    """Return an abstract state where a rule violation has occurred."""
    return state_with_overrides(clean_state(), **{"behavior.rule_violation_occurred": True})


def thesis_invalidated_state() -> InventoryState:
    """Return an abstract state accepted beyond thesis invalidation."""
    return state_with_overrides(
        clean_state(),
        **{
            "position.thesis_valid": False,
            "position.accepted_beyond_invalidation": True,
        },
    )


def poor_liquidity_state() -> InventoryState:
    """Return an abstract state where option-side liquidity is unacceptable."""
    return state_with_overrides(clean_state(), **{"market.liquidity_acceptable": False})


def final_five_minutes_state() -> InventoryState:
    """Return an abstract final-five-minute state."""
    return state_with_overrides(
        clean_state(),
        **{"market.time_window": TimeWindow.FINAL_5_1555_1600},
    )


def size_exceeds_plan_state() -> InventoryState:
    """Return an abstract state where position size exceeds plan."""
    return state_with_overrides(clean_state(), **{"position.position_size_exceeds_plan": True})


def loss_avoidance_state() -> InventoryState:
    """Return an abstract state where loss-avoidance behavior risk is present."""
    return state_with_overrides(
        clean_state(),
        **{"behavior.trying_to_avoid_loss_realization": True},
    )


def negative_gex_credit_spread_state() -> InventoryState:
    """Return an abstract negative-GEX credit-spread state."""
    return state_with_overrides(
        clean_state(),
        **{
            "market.dealer_regime": DealerRegime.NEGATIVE_GEX,
            "position.structure": PositionStructure.CREDIT_SPREAD,
        },
    )


def near_flip_unclear_state() -> InventoryState:
    """Return an abstract near-flip state with unclear spot relation."""
    return state_with_overrides(
        clean_state(),
        **{
            "market.dealer_regime": DealerRegime.NEAR_FLIP,
            "market.spot_relative_to_flip": "unclear",
        },
    )
