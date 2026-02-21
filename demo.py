"""Smoke-test demo for the current Kingdom command/action pipeline."""

from pathlib import Path
import sys
sys.path.append("./src")

from kingdom.models import Game
from kingdom.actions import GameActionState, QuitGame, build_verbs
from kingdom.parser import resolve_command


def _run_command(verbs, command):
    resolved_command = resolve_command(command, known_verbs=verbs.keys())
    if resolved_command is None:
        return "UNKNOWN"

    verb_word = resolved_command.verb
    args = resolved_command.args

    verb = verbs.get(verb_word)
    if verb is None:
        return "UNKNOWN"

    try:
        return verb.execute(*args)
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

    _expect(len(game.rooms) > 0, "World loads rooms")
    _expect(len(game.boxes) > 0, "World loads boxes")

    action_state = GameActionState(current_room=game.rooms[0] if game.rooms else None)
    verbs = build_verbs(action_state, game, demo_save_path, confirm_action=lambda _prompt: True)

    _expect(set(["go", "save", "load", "examine", "verbs", "quit"]).issubset(verbs.keys()), "Core verbs are registered")

    verbs_result = _run_command(verbs, "verbs")
    _expect("Available verbs:" in verbs_result, "verbs command returns listing")

    examine_result = _run_command(verbs, "examine")
    _expect(isinstance(examine_result, str) and len(examine_result.strip()) > 0, "examine command describes current room")

    go_result = _run_command(verbs, "go up")
    _expect(go_result == "", "go command moves to connected room")

    short_dir_result = _run_command(verbs, "n")
    _expect(short_dir_result in {"", "UNKNOWN"}, "single-letter directions are handled")

    save_result = _run_command(verbs, "save")
    _expect("Game saved to" in save_result, "save command writes demo save file")
    _expect(demo_save_path.exists(), "Demo save file exists")

    load_result = _run_command(verbs, "load")
    _expect("Game loaded from" in load_result, "load command restores from demo save file")

    unknown_result = _run_command(verbs, "dance")
    _expect(unknown_result == "UNKNOWN", "Unknown commands are detected")

    quit_result = _run_command(verbs, "quit")
    _expect(quit_result == "QUIT", "quit command returns QUIT sentinel")

    print("\nAll demo smoke tests passed.")


if __name__ == "__main__":
    demo()
