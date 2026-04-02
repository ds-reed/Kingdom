from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.interpreter import interpret
from kingdom.language.lexicon import lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Player, World


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

    local_candidates = [game.current_room]
    local_candidates.extend(game.current_room.items)
    local_candidates.extend(game.current_room.containers)
    local_candidates.extend(game.current_room.features)
    if game.current_player is not None:
        local_candidates.extend(game.current_player.sack.contents)
    local_candidate_ids = {id(obj) for obj in local_candidates}

    out_of_context_token = None
    for token, entry in lexicon.token_to_noun.items():
        if " " in token:
            continue
        if token != token.lower():
            continue
        noun_object = getattr(entry, "noun_object", None)
        if noun_object is None:
            continue
        if id(noun_object) not in local_candidate_ids:
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
