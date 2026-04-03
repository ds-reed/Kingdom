from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.executor import CommandStatus, execute
from kingdom.language.interpreter import interpret
from kingdom.language.lexicon import lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Player, World


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo_context(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    data_path = PROJECT_ROOT / "data" / "demo_castle.json"
    world = World.get_instance()
    game.world = world
    game.setup_world(data_path)

    player = Player("SynonymTester")
    game.init_session(
        world=world,
        current_player=player,
        player_name="SynonymTester",
        save_path=tmp_path / "guard-synonym.tmp.json",
    )
    game.debug_mode = True

    register_verbs()
    lexicon = lex()

    return {
        "game": game,
        "lexicon": lexicon,
    }


def _execute_one(command: str, ctx: dict):
    parsed = parse(command, ctx["lexicon"])
    interpreted = interpret(parsed, ctx["game"], ctx["lexicon"])
    assert len(interpreted) == 1
    return execute(interpreted[0], ctx["game"], command)


def _run_to_antechamber(ctx: dict) -> None:
    _execute_one("open door", ctx)
    _execute_one("go east", ctx)


def _execute_sequence(commands: list[str], ctx: dict):
    outcome = None
    for command in commands:
        outcome = _execute_one(command, ctx)
    return outcome


@pytest.mark.parametrize("command", ["loot guard", "take all from guard"])
def test_guard_synonym_targets_body_container_for_loot_commands(demo_context, command: str):
    _run_to_antechamber(demo_context)

    outcome = _execute_one(command, demo_context)

    assert outcome.status == CommandStatus.SUCCESS
    assert "rusty iron trapdoor" not in (outcome.message or "").lower()
    assert "can't" not in (outcome.message or "").lower()
    assert any(
        phrase in (outcome.message or "").lower()
        for phrase in ("cigarettes", "lighter", "small brass key")
    )


def test_trade_banana_to_mermaid_for_vase_uses_two_prep_phrases(demo_context):
    _execute_one("take banana", demo_context)
    demo_context["game"].current_room = demo_context["game"].world.rooms["Pool Ledge"]

    outcome = _execute_one("trade banana to mermaid for vase", demo_context)

    assert outcome is not None
    assert outcome.status == CommandStatus.SUCCESS
    assert "receive" in (outcome.message or "").lower()
    assert "vase" in (outcome.message or "").lower()
