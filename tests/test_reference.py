from dataclasses import fields

from spx_inventory_playbook.reference import get_reference_cards


EXPECTED_TOPICS = {
    "Dealer gamma / GEX",
    "Zero-gamma flip",
    "Vanna and charm",
    "Skew and structure selection",
    "Variance risk premium",
    "SPX/SPXW execution microstructure",
    "PM cash settlement",
    "Futures hedging",
    "Cost realism",
    "Behavioral lockouts",
    "Modern 0DTE structural risk",
    "Source / broker verification checklist",
}

FORBIDDEN_MARKERS = ("6125", "6100", "6200", "$", "bid/ask", "P/L")
FORBIDDEN_RECOMMENDATION_PHRASES = (
    "buy",
    "sell",
    "enter",
    "take the trade",
    "trade this",
)


def card_strings(card) -> list[str]:
    values: list[str] = []
    for field in fields(card):
        value = getattr(card, field.name)
        if isinstance(value, str):
            values.append(value)
        else:
            values.extend(value)
    return values


def test_get_reference_cards_returns_exactly_twelve_cards() -> None:
    assert len(get_reference_cards()) == 12


def test_reference_card_topics_are_unique() -> None:
    topics = [card.topic for card in get_reference_cards()]

    assert len(topics) == len(set(topics))


def test_expected_reference_topics_are_present() -> None:
    topics = {card.topic for card in get_reference_cards()}

    assert topics == EXPECTED_TOPICS


def test_all_string_fields_are_non_empty() -> None:
    for card in get_reference_cards():
        for value in card_strings(card):
            assert value.strip()


def test_no_string_field_exceeds_two_hundred_twenty_characters() -> None:
    for card in get_reference_cards():
        for value in card_strings(card):
            assert len(value) <= 220


def test_every_card_has_verification_inputs() -> None:
    for card in get_reference_cards():
        assert card.verification_inputs
        assert all(value.strip() for value in card.verification_inputs)


def test_reference_cards_do_not_contain_fake_market_markers() -> None:
    for card in get_reference_cards():
        joined = " ".join(card_strings(card))
        for marker in FORBIDDEN_MARKERS:
            assert marker not in joined


def test_reference_cards_do_not_contain_recommendation_phrases() -> None:
    for card in get_reference_cards():
        joined = " ".join(card_strings(card)).lower()
        for phrase in FORBIDDEN_RECOMMENDATION_PHRASES:
            assert phrase not in joined
