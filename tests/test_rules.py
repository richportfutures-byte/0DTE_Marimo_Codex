from spx_inventory_playbook.rules import list_valid_actions


def test_valid_actions_are_planned_inventory_actions() -> None:
    assert list_valid_actions() == ("hold", "reduce", "hedge", "convert", "close", "stop")
