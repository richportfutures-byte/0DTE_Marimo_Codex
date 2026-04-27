import pytest

from spx_inventory_playbook.calculators import midpoint


def test_midpoint_returns_average() -> None:
    assert midpoint(1.0, 3.0) == 2.0


def test_midpoint_rejects_crossed_market() -> None:
    with pytest.raises(ValueError, match="Ask"):
        midpoint(3.0, 1.0)
