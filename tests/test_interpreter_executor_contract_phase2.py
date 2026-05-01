from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.interpreter import InterpretedTarget, interpret
from kingdom.language.lexicon import lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Player, World


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def context(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    world = World.get_instance()
    game.world = world
    game.setup_world(PROJECT_ROOT / "data" / "initial_state.json")

    player = Player("Phase2Tester")
    game.init_session(
        world=world,
        current_player=player,
        player_name="Phase2Tester",
        save_path=tmp_path / "phase2.tmp.json",
    )

    register_verbs()
    lexicon = lex()

    return {"game": game, "lexicon": lexicon}


def _interpret(command: str, ctx: dict):
    parsed = parse(command, ctx["lexicon"])
    interpreted = interpret(parsed, ctx["game"], ctx["lexicon"])
    assert len(interpreted) == 1
    return interpreted[0]


def test_executor_contract_explicit_command_fields(context):
    cmd = _interpret("put bag in bag", context)

    assert cmd.verb is not None
    assert cmd.verb_token == "put"
    assert cmd.verb_source == "explicit"
    assert cmd.direct_object_token == "bag"
    assert cmd.direction is None
    assert isinstance(cmd.prep_phrases, list)
    assert len(cmd.prep_phrases) == 1

    prep = cmd.prep_phrases[0]
    assert prep["prep"] == "in"
    assert isinstance(prep["object"], InterpretedTarget)
    assert prep["object"].token_head == "bag"


def test_executor_contract_direction_only_fields(context):
    cmd = _interpret("west", context)

    assert cmd.verb is not None
    assert cmd.verb.canonical_name() == "go"
    assert cmd.verb_source == "implicit"
    assert cmd.verb_token is None
    assert cmd.direction == "west"
    assert cmd.direct is None
    assert cmd.direct_object_token is None
    assert cmd.prep_phrases == []


def test_executor_contract_unknown_input_fields(context):
    cmd = _interpret("dance", context)

    assert cmd.verb is None
    assert cmd.verb_source == "unknown"
    assert cmd.verb_token == "dance"
    assert cmd.direction is None
    assert cmd.prep_phrases == []
    assert cmd.direct is not None
    assert cmd.direct.token_head == "dance"
    assert cmd.direct_object_token == "dance"


def test_executor_contract_out_of_context_prep_target_is_unresolved(context):
    cmd = _interpret("put bag in narnia", context)

    assert len(cmd.prep_phrases) == 1
    prep = cmd.prep_phrases[0]
    assert prep["prep"] == "in"
    assert prep["object"].token_head == "narnia"
    assert prep["object"].noun_object is None
