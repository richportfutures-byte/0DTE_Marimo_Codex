from spx_inventory_playbook.prompts import get_session_prompt_templates


EXPECTED_TEMPLATE_NAMES = {
    "Pre-session regime synthesis",
    "Dealer-flow interpretation",
    "One adjustment drill",
    "Strategy audit",
    "Edge hypothesis stress test",
    "Post-session review",
}


def test_get_session_prompt_templates_returns_exactly_six_templates() -> None:
    assert len(get_session_prompt_templates()) == 6


def test_template_names_are_unique() -> None:
    names = [template.name for template in get_session_prompt_templates()]

    assert len(names) == len(set(names))


def test_expected_template_names_are_present() -> None:
    names = {template.name for template in get_session_prompt_templates()}

    assert names == EXPECTED_TEMPLATE_NAMES


def test_templates_have_non_empty_core_fields() -> None:
    for template in get_session_prompt_templates():
        assert template.name.strip()
        assert template.purpose.strip()
        assert template.required_inputs
        assert template.template.strip()


def test_required_input_lists_are_non_empty() -> None:
    for template in get_session_prompt_templates():
        assert all(required_input.strip() for required_input in template.required_inputs)


def test_each_template_includes_no_fabrication_constraint() -> None:
    for template in get_session_prompt_templates():
        normalized = template.template.lower()

        assert "do not invent fake data" in normalized


def test_each_template_includes_missing_data_unknown_constraint() -> None:
    for template in get_session_prompt_templates():
        normalized = template.template.lower()

        assert "missing, stale, partial, or unverifiable fields unknown" in normalized


def test_each_template_allows_approved_adapter_data() -> None:
    for template in get_session_prompt_templates():
        normalized = template.template.lower()

        assert "user-supplied data or approved adapter data" in normalized
        assert "source, timestamp, and freshness status" in normalized


def test_each_template_blocks_automated_order_execution() -> None:
    for template in get_session_prompt_templates():
        normalized = template.template.lower()

        assert "bounded decision support only" in normalized
        assert "do not place, route, or imply automated order execution" in normalized


def test_adjustment_drill_template_is_one_scenario_only() -> None:
    adjustment_template = next(
        template
        for template in get_session_prompt_templates()
        if template.name == "One adjustment drill"
    )

    assert "one scenario only" in adjustment_template.template.lower()


def test_no_template_exceeds_four_thousand_characters() -> None:
    for template in get_session_prompt_templates():
        assert len(template.template) <= 4000
