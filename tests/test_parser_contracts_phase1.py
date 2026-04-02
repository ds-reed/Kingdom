from __future__ import annotations

from kingdom.language.parser import parse
from kingdom.language.tests.dummy_lexicon import build_dummy_lexicon


def _parse_one(command: str):
    lexicon = build_dummy_lexicon()
    parsed = parse(command, lexicon)
    assert len(parsed) == 1
    return parsed[0]


def test_parser_contract_primary_verb_and_source():
    action = _parse_one("stand the torch inside the bracket")

    assert action.primary_verb is not None
    assert action.primary_verb.canonical == "stand"
    assert action.primary_verb_token == "stand"
    assert action.verb_source == "explicit"


def test_parser_contract_object_phrase_shape():
    action = _parse_one("stand the torch inside the bracket")

    assert len(action.object_phrases) == 2
    first, second = action.object_phrases

    assert set(first.keys()) == {"head", "adjectives", "span"}
    assert first["head"] == "torch"
    assert first["adjectives"] == []
    assert first["span"] == (2, 3)

    assert set(second.keys()) == {"head", "adjectives", "span"}
    assert second["head"] == "bracket"
    assert second["adjectives"] == []
    assert second["span"] == (5, 6)


def test_parser_contract_preposition_shape_and_canonicalization():
    action = _parse_one("put the torch in the bag")

    assert action.prep_phrases == [{"prep": "into", "object": "bag"}]


def test_parser_contract_direction_and_modifier_tokens():
    go_action = _parse_one("go west")
    assert go_action.direction_tokens == ["west"]
    assert go_action.modifier_tokens == []

    take_action = _parse_one("take all")
    assert take_action.direction_tokens == []
    assert take_action.modifier_tokens == ["all"]


def test_parser_contract_preposition_without_object_is_preserved():
    action = _parse_one("put torch in")

    assert action.object_phrases == [{"head": "torch", "adjectives": [], "span": (1, 2)}]
    assert action.prep_phrases == [{"prep": "into", "object": None}]


def test_parser_contract_unknown_adjective_grouping_before_noun_head():
    action = _parse_one("take pearly-white knife")

    assert action.object_phrases == [
        {"head": "knife", "adjectives": ["pearly-white"], "span": (1, 3)}
    ]


def test_parser_contract_quantifier_heads_are_grouped_as_noun_phrases():
    all_action = _parse_one("take all")
    assert all_action.object_phrases == [{"head": "all", "adjectives": [], "span": (1, 2)}]

    everything_action = _parse_one("take everything")
    assert everything_action.object_phrases == [
        {"head": "everything", "adjectives": [], "span": (1, 2)}
    ]
