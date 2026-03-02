"""Smoke-test demo for the current Kingdom command/action pipeline."""

from pathlib import Path
import sys
sys.path.append("./src")

from kingdom.models import Game, Player, QuitGame, build_dispatch_context, DirectionNoun
from kingdom.session import GameActionState, init_session, get_action_state
from kingdom.actions import build_verbs
from kingdom.parser import resolve_command
from kingdom.UI import UI


def _iter_known_noun_names(game: Game):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.get_descriptive_phrase()
        yield noun.get_noun_name()


def _iter_local_target_candidates(game: Game, state: GameActionState):
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


def _resolve_target_noun(game: Game, state: GameActionState, resolved_command) -> object | None:
    noun_matches = resolved_command.parse.nouns
    if not noun_matches:
        return None

    local_candidates = list(_iter_local_target_candidates(game, state))
    for noun_match in noun_matches:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                return candidate

    return None


def _run_command(game: Game, state: GameActionState, verbs, command, dispatch_context=None):
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
        return verb.execute(dispatch_context, target_noun, args)
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
    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "initial_state.json"
    demo_save_path = base_dir / "data" / "working_state.demo.json"

    game = Game.get_instance()
    game.setup_world(data_path)
    game.set_current_player(Player("DemoHero"))

    _expect(len(game.rooms) > 0, "World loads rooms")
    _expect(len(game.boxes) > 0, "World loads boxes")

    start_room = game.rooms.get(game.start_room_name) if isinstance(game.rooms, dict) else None
    _expect(start_room is not None, "Start room resolves from world data")

    init_session(initial_room=start_room, player_name="DemoHero", save_dir=demo_save_path.parent)
    action_state = get_action_state()

    ui = UI(
        confirm=lambda _prompt: True,
        prompt=lambda _prompt: "",
        save_path=demo_save_path,
        load_path=demo_save_path,
        game=game,
    )

    dispatch_context = build_dispatch_context(state=action_state, game=game)
    dispatch_context.ui = ui

    verbs = build_verbs(action_state, game, demo_save_path, confirm_action=lambda _prompt: True)

    _expect(
        set(["go", "save", "load", "look", "help", "quit", "inventory", "score"]).issubset(verbs.keys()),
        "Core verbs are registered",
    )

    help_result = _run_command(game, action_state, verbs, "help", dispatch_context=dispatch_context)
    _expect(isinstance(help_result, str) and "You can try commands like:" in help_result, "help command returns default help text")

    help_commands_result = _run_command(game, action_state, verbs, "help commands", dispatch_context=dispatch_context)
    _expect(isinstance(help_commands_result, str) and "Available commands:" in help_commands_result, "help commands returns command listing")

    look_result = _run_command(game, action_state, verbs, "look", dispatch_context=dispatch_context)
    _expect(isinstance(look_result, str) and len(look_result.strip()) > 0, "look command describes current room")

    score_result = _run_command(game, action_state, verbs, "score", dispatch_context=dispatch_context)
    _expect(isinstance(score_result, str) and "Your current score is:" in score_result, "score command returns score text")

    inventory_result = _run_command(game, action_state, verbs, "inventory", dispatch_context=dispatch_context)
    _expect(isinstance(inventory_result, str) and "don't have anything" in inventory_result.lower(), "inventory reports empty inventory")

    exits = action_state.current_room.available_directions(visible_only=True)
    _expect(len(exits) > 0, "Start room has at least one visible exit for movement test")
    original_room = action_state.current_room
    move_result = _run_command(game, action_state, verbs, exits[0], dispatch_context=dispatch_context)
    _expect(isinstance(move_result, str) and "You go" in move_result, "Implicit direction command resolves to movement")
    _expect(action_state.current_room is not original_room, "Movement changes current room")

    save_result = _run_command(game, action_state, verbs, "save", dispatch_context=dispatch_context)
    _expect("Game saved to" in save_result, "save command writes demo save file")
    _expect(demo_save_path.exists(), "Demo save file exists")

    load_result = _run_command(game, action_state, verbs, "load", dispatch_context=dispatch_context)
    _expect("Game loaded from" in load_result, "load command restores from demo save file")

    unknown_result = _run_command(game, action_state, verbs, "dance", dispatch_context=dispatch_context)
    _expect(unknown_result == "UNKNOWN", "Unknown commands are detected")

    quit_result = _run_command(game, action_state, verbs, "quit", dispatch_context=dispatch_context)
    _expect(quit_result == "QUIT", "quit command returns QUIT sentinel")

    print("\nAll demo smoke tests passed.")


if __name__ == "__main__":
    demo()
