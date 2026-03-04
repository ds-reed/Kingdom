"""Smoke-test demo for the current Kingdom command/action pipeline."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from kingdom.model.noun_model import World, Player, DirectionNoun
from kingdom.model.game_init import QuitGame, SaveGame, LoadGame
from kingdom.model.game_init import GameActionState, init_session, get_action_state
from kingdom.model.game_persistence import save_game, load_game
from kingdom.language.lexicon.verbs.verb_registry import build_verb_registry
from kingdom.parser import resolve_command
from kingdom.UI import UI


def _iter_known_noun_names(game: World):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.get_descriptive_phrase()
        yield noun.get_noun_name()


def _iter_local_target_candidates(game: World, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for box in state.current_room.boxes:
            yield box
            if not box.is_openable or box.is_open:
                for item in box.contents:
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
    except TypeError:
        return "ARG_ERROR"


def _expect(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def demo():
    """Run deterministic smoke tests for core gameplay flows."""
    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    demo_save_path = PROJECT_ROOT / "data" / "working_state.demo.json"

    game = World.get_instance()
    game.setup_world(data_path)
    player = Player("DemoHero")

    _expect(len(game.rooms) > 0, "World loads rooms")
    _expect(len(game.boxes) > 0, "World loads boxes")

    start_room = game.rooms.get(game.start_room_name) if isinstance(game.rooms, dict) else None
    _expect(start_room is not None, "Start room resolves from world data")

    init_session(world=game, current_player=player, initial_room=start_room, player_name="DemoHero", save_path=demo_save_path)
    action_state = get_action_state()

    ui = UI()

    verbs = build_verb_registry()

    _expect(
        set(["go", "save", "load", "look", "help", "quit", "inventory", "score"]).issubset(verbs.keys()),
        "Core verbs are registered",
    )

    help_result = _run_command(game, action_state, verbs, "help")
    _expect(isinstance(help_result, str) and "You can try commands like:" in help_result, "help command returns default help text")

    help_commands_result = _run_command(game, action_state, verbs, "help commands")
    _expect(isinstance(help_commands_result, str) and "Available commands:" in help_commands_result, "help commands returns command listing")

    look_result = _run_command(game, action_state, verbs, "look")
    _expect(isinstance(look_result, str) and len(look_result.strip()) > 0, "look command describes current room")

    score_result = _run_command(game, action_state, verbs, "score")
    _expect(isinstance(score_result, str) and "Your current score is:" in score_result, "score command returns score text")

    inventory_result = _run_command(game, action_state, verbs, "inventory")
    _expect(isinstance(inventory_result, str) and "don't have anything" in inventory_result.lower(), "inventory reports empty inventory")

    exits = action_state.current_room.available_directions(visible_only=True)
    _expect(len(exits) > 0, "Start room has at least one visible exit for movement test")
    original_room = action_state.current_room
    move_result = _run_command(game, action_state, verbs, exits[0])
    _expect(isinstance(move_result, str) and "You go" in move_result, "Implicit direction command resolves to movement")
    _expect(action_state.current_room is not original_room, "Movement changes current room")

    save_result = _run_command(game, action_state, verbs, "save", demo_save_path=demo_save_path)
    _expect("Game saved to" in save_result, "save command writes demo save file")
    _expect(demo_save_path.exists(), "Demo save file exists")

    load_result = _run_command(game, action_state, verbs, "load", demo_save_path=demo_save_path)
    _expect("Game loaded from" in load_result, "load command restores from demo save file")

    unknown_result = _run_command(game, action_state, verbs, "dance")
    _expect(unknown_result == "UNKNOWN", "Unknown commands are detected")

    quit_result = _run_command(game, action_state, verbs, "quit")
    _expect(quit_result == "QUIT", "quit command returns QUIT sentinel")

    print("\nAll demo smoke tests passed.")


if __name__ == "__main__":
    demo()
