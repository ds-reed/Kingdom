from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.interpreter import _resolve_target_noun, interpret
from kingdom.language.lexicon import add_noun_to_lexicon, lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Item, Player, World


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def interpreter_context(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    world = World.get_instance()
    game.world = world
    game.setup_world(data_path)

    player = Player("Phase1Tester")
    game.init_session(
        world=world,
        current_player=player,
        player_name="Phase1Tester",
        save_path=tmp_path / "phase1.tmp.json",
    )

    register_verbs()
    lexicon = lex()

    return {
        "game": game,
        "lexicon": lexicon,
    }


def _interpret_one(command: str, ctx: dict):
    parsed = parse(command, ctx["lexicon"])
    interpreted = interpret(parsed, ctx["game"], ctx["lexicon"])
    assert len(interpreted) == 1
    return interpreted[0]


def test_interpreter_contract_direct_object_resolves_from_context(interpreter_context):
    cmd = _interpret_one("look bag", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.token_head == "bag"
    assert cmd.direct.noun_object is not None
    assert cmd.direct.noun_object.obj_handle() == "bag"


def test_interpreter_contract_unresolved_direct_object_stays_safe(interpreter_context):
    cmd = _interpret_one("look unicorn", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.token_head == "unicorn"
    assert cmd.direct.noun_object is None


def test_interpreter_contract_prep_phrase_out_of_context_target_stays_unresolved(interpreter_context):
    game = interpreter_context["game"]
    lexicon = interpreter_context["lexicon"]

    out_of_context_token = None
    for token in lexicon.noun_tokens:
        if " " in token:
            continue
        if token != token.lower():
            continue
        if _resolve_target_noun(game.current_room, token) is None:
            out_of_context_token = token
            break

    assert out_of_context_token is not None, "Expected at least one noun token outside local context"

    input_token = out_of_context_token
    cmd = _interpret_one(f"put bag in {input_token}", interpreter_context)

    assert len(cmd.prep_phrases) == 1
    prep = cmd.prep_phrases[0]
    target = prep["object"]

    assert prep["prep"] == "in"
    assert target.token_head == input_token
    assert target.noun_object is None


def test_interpreter_contract_prep_phrase_local_target_resolves_from_context(interpreter_context):
    cmd = _interpret_one("put bag in bag", interpreter_context)

    assert len(cmd.prep_phrases) == 1
    prep = cmd.prep_phrases[0]
    target = prep["object"]

    assert prep["prep"] == "in"
    assert target.token_head == "bag"
    assert target.noun_object is not None
    assert target.noun_object.obj_handle() == "bag"


def test_interpreter_contract_direction_only_maps_to_implicit_go(interpreter_context):
    cmd = _interpret_one("west", interpreter_context)

    assert cmd.verb is not None
    assert cmd.verb.canonical_name() == "go"
    assert cmd.verb_source == "implicit"
    assert cmd.direction == "west"
    assert cmd.all_tokens == ["west"]


def test_interpreter_contract_single_noun_without_verb_stays_verbless(interpreter_context):
    cmd = _interpret_one("bag", interpreter_context)

    assert cmd.verb is None
    assert cmd.verb_source == "implicit"
    assert cmd.direct is not None
    assert cmd.direct.token_head == "bag"
    assert cmd.direct.noun_object is not None
    assert cmd.direct.noun_object.obj_handle() == "bag"


def test_interpreter_contract_unknown_word_is_safe_without_verb(interpreter_context):
    cmd = _interpret_one("dance", interpreter_context)

    assert cmd.verb is None
    assert cmd.verb_source == "unknown"
    assert cmd.verb_token == "dance"
    assert cmd.direct is not None
    assert cmd.direct.token_head == "dance"
    assert cmd.direct.noun_object is None


def test_interpreter_contract_adjective_disambiguates_same_head_nouns(interpreter_context):
    game = interpreter_context["game"]
    lexicon = interpreter_context["lexicon"]

    first = Item("testgem", description="a small test gem", handle="testgem", adjectives=["small"])
    second = Item("testgem", description="a large test gem", handle="testgem", adjectives=["large"])
    game.current_room.items.extend([first, second])
    add_noun_to_lexicon(first, lexicon)
    add_noun_to_lexicon(second, lexicon)

    cmd = _interpret_one("look large testgem", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.token_head == "testgem"
    assert cmd.direct.noun_object is second


def test_interpreter_contract_same_head_no_adjective_uses_first_match(interpreter_context):
    game = interpreter_context["game"]
    lexicon = interpreter_context["lexicon"]

    first = Item("testcoin", description="a small test coin", handle="testcoin", adjectives=["small"])
    second = Item("testcoin", description="a large test coin", handle="testcoin", adjectives=["large"])
    game.current_room.items.extend([first, second])
    add_noun_to_lexicon(first, lexicon)
    add_noun_to_lexicon(second, lexicon)

    cmd = _interpret_one("look testcoin", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.noun_object is first


def test_interpreter_contract_unknown_adjective_falls_back_to_first_match(interpreter_context):
    game = interpreter_context["game"]
    lexicon = interpreter_context["lexicon"]

    first = Item("testring", description="a plain test ring", handle="testring", adjectives=["plain"])
    second = Item("testring", description="a ornate test ring", handle="testring", adjectives=["ornate"])
    game.current_room.items.extend([first, second])
    add_noun_to_lexicon(first, lexicon)
    add_noun_to_lexicon(second, lexicon)

    cmd = _interpret_one("look shiny testring", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.noun_object is first


def test_interpreter_contract_single_match_ignores_extra_adjective_noise(interpreter_context):
    game = interpreter_context["game"]
    lexicon = interpreter_context["lexicon"]

    only = Item("testidol", description="an ancient idol", handle="testidol", adjectives=["ancient"])
    game.current_room.items.append(only)
    add_noun_to_lexicon(only, lexicon)

    cmd = _interpret_one("look gleaming testidol", interpreter_context)

    assert cmd.direct is not None
    assert cmd.direct.noun_object is only
