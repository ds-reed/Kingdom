"""Pytest smoke tests for the current Kingdom command/action pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from kingdom.verbs.verb_registration import register_verbs
from kingdom.model.verb_model import Verb
from kingdom.model.game_init import (
    GameActionState,
    GameOver,
    LoadGame,
    QuitGame,
    SaveGame,
    get_action_state,
    init_session,
    reset_all_state,
    setup_world,
)
from kingdom.model.game_persistence import load_game, save_game
from kingdom.model.noun_model import DirectionNoun, Player, World
from kingdom.parser import resolve_command


def _iter_known_noun_names(game: World):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.display_name()
        yield noun.obj_handle()


def _iter_local_target_candidates(game: World, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for container in state.current_room.containers:
            yield container
            if not container.is_openable or container.is_open:
                for item in container.contents:
                    yield item

    player = game.require_player(return_error=True)
    if not isinstance(player, str):
        for item in player.sack.contents:
            yield item


def _resolve_target_noun(game: World, state: GameActionState, resolved_command) -> object | None:
    noun_matches = resolved_command.parse.nouns
    if not noun_matches:
        return None

    local_candidates = list(_iter_local_target_candidates(game, state))
    for noun_match in noun_matches:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                return candidate

    return None


def _run_command(game: World, state: GameActionState, verbs, command, demo_save_path: Path | None = None):
    resolved_command = resolve_command(
        command,
        known_verbs=verbs.keys(),
        known_nouns=_iter_known_noun_names(game),
    )
    if resolved_command is None:
        return "UNKNOWN"

    verb_word = resolved_command.verb
    args = tuple(resolved_command.args)
    target_noun = _resolve_target_noun(game, state, resolved_command)

    verb = verbs.get(verb_word)
    if verb is None:
        return "UNKNOWN"

    try:
        return verb.execute(target_noun, args)
    except SaveGame:
        if demo_save_path is None:
            return "SAVE_ERROR"
        saved_path = save_game(game, demo_save_path)
        return f"Game saved to {saved_path}"
    except LoadGame:
        if demo_save_path is None:
            return "LOAD_ERROR"
        loaded_path = load_game(game, demo_save_path)
        return f"Game loaded from {loaded_path}"
    except QuitGame:
        return "QUIT"
    except GameOver as error:
        return f"GAME_OVER: {error}"
    except TypeError:
        return "ARG_ERROR"


def _expect_contains(result: object, needle: str):
    assert isinstance(result, str)
    assert needle.lower() in result.lower()


@pytest.fixture
def smoke_context(tmp_path: Path):
    reset_all_state()

    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    demo_save_path = tmp_path / "working_state.demo.json"

    game = World.get_instance()
    setup_world(game, data_path)
    player = Player("DemoHero")

    assert len(game.rooms) > 0
    assert any(len(room.containers) > 0 for room in game.rooms.values())

    start_room = game.rooms.get(game.start_room_name) if isinstance(game.rooms, dict) else None
    assert start_room is not None

    init_session(
        world=game,
        current_player=player,
        initial_room=start_room,
        player_name="DemoHero",
        save_path=demo_save_path,
    )
    action_state = get_action_state()
    register_verbs()
    verbs = Verb.registry
    covered_verbs: set[str] = set()

    def run(command: str):
        resolved = resolve_command(
            command,
            known_verbs=verbs.keys(),
            known_nouns=_iter_known_noun_names(game),
        )
        result = _run_command(game, action_state, verbs, command, demo_save_path=demo_save_path)
        if resolved is not None:
            canonical = verbs[resolved.verb].name
            covered_verbs.add(canonical)
        return result

    return {
        "game": game,
        "action_state": action_state,
        "verbs": verbs,
        "run": run,
        "covered_verbs": covered_verbs,
        "demo_save_path": demo_save_path,
    }


def test_demo_smoke(smoke_context):
    run = smoke_context["run"]
    verbs = smoke_context["verbs"]
    action_state: GameActionState = smoke_context["action_state"]
    demo_save_path: Path = smoke_context["demo_save_path"]

    assert set(["go", "save", "load", "look", "help", "quit", "inventory", "score"]).issubset(verbs.keys())

    help_result = run("help")
    assert isinstance(help_result, str) and "You can try commands like:" in help_result

    help_commands_result = run("help commands")
    assert isinstance(help_commands_result, str) and "Available commands:" in help_commands_result

    look_result = run("look")
    assert isinstance(look_result, str) and len(look_result.strip()) > 0

    score_result = run("score")
    assert isinstance(score_result, str) and "Your current score is:" in score_result

    inventory_result = run("inventory")
    assert isinstance(inventory_result, str) and "don't have anything" in inventory_result.lower()

    _expect_contains(run("open bean"), "you reached me")

    _expect_contains(run("open lunch bag"), "open")
    look_in_bag_result = run("look in lunch bag")
    assert isinstance(look_in_bag_result, str)
    assert "inside" in look_in_bag_result.lower()
    assert "lunch bag" in look_in_bag_result.lower()

    _expect_contains(run("take fish"), "you take")
    _expect_contains(run("take key"), "you take")
    _expect_contains(run("take lamp"), "you take")
    _expect_contains(run("take lighter"), "you take")
    _expect_contains(run("take torch"), "you take")
    _expect_contains(run("close lunch bag"), "close")
    _expect_contains(run("drop torch"), "you drop")
    _expect_contains(run("take torch"), "you take")

    _expect_contains(run("light torch"), "you light")
    _expect_contains(run("extinguish torch"), "you extinguish")
    _expect_contains(run("say hello"), "wind")
    _expect_contains(run("eat fish"), "vomit")

    _expect_contains(run("unlock trapdoor"), "you unlock")
    _expect_contains(run("open trapdoor"), "passage leading down")

    _expect_contains(run("go down"), "you go down")
    assert action_state.current_room.name == "Blank Chamber"

    _expect_contains(run("rub lamp"), "imposing djinni")
    _expect_contains(run("make wish"), "places a doorway in the west wall")

    _expect_contains(run("west"), "you go west")
    assert action_state.current_room.name == "Colossal Cave"

    _expect_contains(run("swim west"), "you swim west")
    assert action_state.current_room.name == "Pool Ledge"

    _expect_contains(run("teleport Demo Landing"), "you teleport")
    assert action_state.current_room.name == "Demo Landing"

    save_result = run("save")
    assert isinstance(save_result, str)
    assert "Game saved to" in save_result
    assert demo_save_path.exists()

    load_result = run("load")
    assert isinstance(load_result, str)
    assert "Game loaded from" in load_result

    debug_result = run("debug room")
    assert debug_result is None or isinstance(debug_result, str)

    die_result = run("die")
    assert isinstance(die_result, str) and die_result.startswith("GAME_OVER:")

    assert run("dance") == "UNKNOWN"
    assert run("quit") == "QUIT"

    expected_canonical_verbs = {
        "go", "swim", "teleport",
        "light", "extinguish", "open", "close", "unlock", "eat", "rub", "say", "make", "look",
        "help", "score", "load", "save", "quit", "die", "debug",
        "inventory", "take", "drop",
    }
    missing = sorted(expected_canonical_verbs - smoke_context["covered_verbs"])
    assert not missing, f"All canonical verbs were exercised (missing: {missing})"
