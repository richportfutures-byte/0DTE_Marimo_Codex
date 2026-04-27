import pytest

from spx_inventory_playbook.calculators import (
    calculate_futures_hedge,
    calculate_trade_friction,
    midpoint,
)


def test_midpoint_returns_average() -> None:
    assert midpoint(1.0, 3.0) == 2.0


def test_midpoint_rejects_crossed_market() -> None:
    with pytest.raises(ValueError, match="Ask"):
        midpoint(3.0, 1.0)


def test_futures_hedge_calculates_mes_and_es_equivalents() -> None:
    result = calculate_futures_hedge(option_delta=0.30, contracts=1)

    assert result.dollar_delta_per_point == pytest.approx(30.0)
    assert result.target_hedge_dollars_per_point == pytest.approx(30.0)
    assert result.mes_equivalent == pytest.approx(6.0)
    assert result.mes_rounded == 6
    assert result.es_equivalent == pytest.approx(0.6)
    assert result.es_rounded == 1


def test_futures_hedge_preserves_signed_delta_but_positive_hedge_equivalent() -> None:
    result = calculate_futures_hedge(option_delta=-0.30, contracts=1)

    assert result.dollar_delta_per_point == pytest.approx(-30.0)
    assert result.target_hedge_dollars_per_point == pytest.approx(30.0)
    assert result.mes_equivalent == pytest.approx(6.0)
    assert result.es_equivalent == pytest.approx(0.6)


def test_futures_hedge_percent_scales_target() -> None:
    result = calculate_futures_hedge(option_delta=0.30, contracts=1, hedge_percent=0.5)

    assert result.dollar_delta_per_point == pytest.approx(30.0)
    assert result.target_hedge_dollars_per_point == pytest.approx(15.0)
    assert result.mes_equivalent == pytest.approx(3.0)
    assert result.es_equivalent == pytest.approx(0.3)


@pytest.mark.parametrize("contracts", [0, -1, 1.5, True])
def test_futures_hedge_rejects_invalid_contracts(contracts: object) -> None:
    with pytest.raises(ValueError, match="contracts"):
        calculate_futures_hedge(option_delta=0.30, contracts=contracts)  # type: ignore[arg-type]


@pytest.mark.parametrize("hedge_percent", [-0.1, 1.1, True])
def test_futures_hedge_rejects_invalid_hedge_percent(hedge_percent: object) -> None:
    with pytest.raises(ValueError, match="hedge_percent"):
        calculate_futures_hedge(
            option_delta=0.30,
            contracts=1,
            hedge_percent=hedge_percent,  # type: ignore[arg-type]
        )


def test_trade_friction_calculates_roundtrip_costs() -> None:
    result = calculate_trade_friction(
        contracts=2,
        legs=3,
        commission_per_contract=1.0,
        fees_per_contract=0.5,
        entry_spread_crossing_per_contract=2.0,
        exit_spread_crossing_per_contract=3.0,
        gross_target_dollars=100.0,
    )

    assert result.roundtrip_contract_count == 12
    assert result.commission_and_fees == pytest.approx(18.0)
    assert result.spread_crossing_cost == pytest.approx(30.0)
    assert result.total_friction == pytest.approx(48.0)
    assert result.target_after_friction == pytest.approx(52.0)
    assert result.friction_percent_of_target == pytest.approx(0.48)


def test_trade_friction_warns_at_or_above_twenty_five_percent() -> None:
    result = calculate_trade_friction(
        contracts=1,
        legs=1,
        commission_per_contract=5.0,
        fees_per_contract=0.0,
        entry_spread_crossing_per_contract=7.5,
        exit_spread_crossing_per_contract=7.5,
        gross_target_dollars=100.0,
    )

    assert result.total_friction == pytest.approx(25.0)
    assert result.friction_warning is True


def test_trade_friction_does_not_warn_below_twenty_five_percent() -> None:
    result = calculate_trade_friction(
        contracts=1,
        legs=1,
        commission_per_contract=1.0,
        fees_per_contract=0.0,
        entry_spread_crossing_per_contract=1.0,
        exit_spread_crossing_per_contract=1.0,
        gross_target_dollars=100.0,
    )

    assert result.total_friction == pytest.approx(4.0)
    assert result.friction_warning is False


@pytest.mark.parametrize(
    "kwargs, error_field",
    [
        ({"contracts": 0}, "contracts"),
        ({"contracts": -1}, "contracts"),
        ({"contracts": 1.5}, "contracts"),
        ({"legs": 0}, "legs"),
        ({"legs": -1}, "legs"),
        ({"legs": 1.5}, "legs"),
        ({"commission_per_contract": -0.01}, "commission_per_contract"),
        ({"fees_per_contract": -0.01}, "fees_per_contract"),
        (
            {"entry_spread_crossing_per_contract": -0.01},
            "entry_spread_crossing_per_contract",
        ),
        (
            {"exit_spread_crossing_per_contract": -0.01},
            "exit_spread_crossing_per_contract",
        ),
        ({"gross_target_dollars": 0.0}, "gross_target_dollars"),
        ({"gross_target_dollars": -1.0}, "gross_target_dollars"),
    ],
)
def test_trade_friction_rejects_invalid_inputs(
    kwargs: dict[str, object],
    error_field: str,
) -> None:
    params = {
        "contracts": 1,
        "legs": 1,
        "commission_per_contract": 1.0,
        "fees_per_contract": 0.5,
        "entry_spread_crossing_per_contract": 1.0,
        "exit_spread_crossing_per_contract": 1.0,
        "gross_target_dollars": 100.0,
    }
    params.update(kwargs)

    with pytest.raises(ValueError, match=error_field):
        calculate_trade_friction(**params)  # type: ignore[arg-type]
