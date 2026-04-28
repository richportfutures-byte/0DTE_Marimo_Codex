from dataclasses import fields

from spx_inventory_playbook.reference import ReferenceCard, get_reference_cards

# Fields that contain long-form educational content (exempt from 220-char limit)
LONG_FORM_FIELDS = frozenset({"deep_dive", "mental_model", "key_mechanics"})


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


def card_strings(card, *, exclude: frozenset[str] = frozenset()) -> list[str]:
    values: list[str] = []
    for field in fields(card):
        if field.name in exclude:
            continue
        value = getattr(card, field.name)
        if isinstance(value, str):
            values.append(value)
        else:
            values.extend(value)
    return values


def compact_strings(card) -> list[str]:
    """Return only the compact fields subject to the 220-char limit."""
    return card_strings(card, exclude=LONG_FORM_FIELDS)


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


def test_no_compact_field_exceeds_two_hundred_twenty_characters() -> None:
    for card in get_reference_cards():
        for value in compact_strings(card):
            assert len(value) <= 220


def test_every_card_has_verification_inputs() -> None:
    for card in get_reference_cards():
        assert card.verification_inputs
        assert all(value.strip() for value in card.verification_inputs)


def test_reference_cards_do_not_contain_fake_market_markers() -> None:
    for card in get_reference_cards():
        joined = " ".join(compact_strings(card))
        for marker in FORBIDDEN_MARKERS:
            assert marker not in joined


def test_reference_cards_do_not_contain_recommendation_phrases() -> None:
    for card in get_reference_cards():
        joined = " ".join(compact_strings(card)).lower()
        for phrase in FORBIDDEN_RECOMMENDATION_PHRASES:
            assert phrase not in joined


def test_dealer_level_language_does_not_imply_support_or_resistance() -> None:
    allowed_phrases = (
        "dealer levels are not support/resistance",
        "dealer levels are not support or resistance",
        "this is not a support or resistance level",
    )

    for card in get_reference_cards():
        joined = " ".join(compact_strings(card)).lower()
        contains_forbidden_word = "support" in joined or "resistance" in joined
        explicitly_rejects_level_language = any(phrase in joined for phrase in allowed_phrases)

        assert not contains_forbidden_word or explicitly_rejects_level_language


def test_reference_cards_do_not_say_vix_alone_is_sufficient() -> None:
    forbidden_phrases = (
        "vix alone is sufficient",
        "vix alone is enough",
        "vix is sufficient",
    )

    for card in get_reference_cards():
        joined = " ".join(card_strings(card)).lower()
        for phrase in forbidden_phrases:
            assert phrase not in joined


def test_futures_hedging_is_not_described_as_a_second_trade() -> None:
    forbidden_phrases = (
        "second trade",
        "second directional trade",
        "separate directional trade",
    )

    for card in get_reference_cards():
        joined = " ".join(card_strings(card)).lower()
        for phrase in forbidden_phrases:
            assert phrase not in joined


# ── Deep-dive content quality tests ──


def test_every_card_has_deep_dive_content() -> None:
    for card in get_reference_cards():
        assert card.deep_dive.strip(), f"{card.topic} is missing deep_dive"
        assert len(card.deep_dive) >= 400, f"{card.topic} deep_dive is too short"


def test_every_card_has_mental_model() -> None:
    for card in get_reference_cards():
        assert card.mental_model.strip(), f"{card.topic} is missing mental_model"
        assert len(card.mental_model) >= 100, f"{card.topic} mental_model is too short"


def test_every_card_has_key_mechanics() -> None:
    for card in get_reference_cards():
        assert len(card.key_mechanics) >= 3, f"{card.topic} needs at least 3 key mechanics"
        for mech in card.key_mechanics:
            assert mech.strip(), f"{card.topic} has empty key mechanic"


def test_deep_dive_does_not_contain_recommendation_imperatives() -> None:
    """Deep-dive content may use words like 'buy' educationally but must not
    contain imperative recommendation patterns."""
    imperative_patterns = (
        "you should buy",
        "you should sell",
        "take the trade",
        "trade this",
        "enter the position",
        "i recommend",
    )
    for card in get_reference_cards():
        text = (card.deep_dive + " " + card.mental_model).lower()
        for pattern in imperative_patterns:
            assert pattern not in text, f"{card.topic} deep_dive contains '{pattern}'"


def test_deep_dive_does_not_fabricate_price_levels() -> None:
    """Deep-dive must not contain fabricated specific price levels."""
    price_markers = ("6125", "6100", "6200")
    for card in get_reference_cards():
        text = card.deep_dive + " " + card.mental_model
        for marker in price_markers:
            assert marker not in text, f"{card.topic} deep_dive contains '{marker}'"
