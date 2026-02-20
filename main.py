"""
Kingdom Game World Simulator - Core API
Uses Game model methods for setup, save, and load functionality.
See demo.py for gameplay examples.
"""

from pathlib import Path
import argparse
import os
import subprocess
import sys
sys.path.append("./src")

from kingdom.models import Game, Player, ensure_direction_nouns, get_direction_nouns_for_available_exits
from kingdom.actions import (
    build_dispatch_context,
    GameActionState,
    build_verbs,
    QuitGame,
)
from kingdom.parser import parse_command, resolve_command
from kingdom.utilities import start_session_logging, stop_session_logging
from kingdom.terminal_style import (
    clear_screen,
    trs80_clear_and_show_room,
    trs80_print,
    trs80_prompt,
    TRS80_WHITE,
    TERMINAL_MODE_TRS80,
    TERMINAL_MODE_MODERN,
)
import kingdom.terminal_style as terminal_style


def iter_known_noun_names(game: Game):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.get_descriptive_phrase()
        yield noun.get_noun_name()


def _iter_local_target_candidates(game: Game, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for box in state.current_room.boxes:
            yield box
            for item in box.contents:
                yield item

    player = game.current_player
    if player is not None:
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


def _try_implicit_noun_action(game: Game, state: GameActionState, raw_command: str) -> str | None:
    parse_result = parse_command(raw_command, known_verbs=[], known_nouns=iter_known_noun_names(game))
    if not parse_result.nouns:
        return None

    dispatch_context = build_dispatch_context(state, game)

    local_candidates = list(_iter_local_target_candidates(game, state))
    for noun_match in parse_result.nouns:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                can_handle, refusal_message = candidate.can_handle_verb(
                    "",
                    dispatch_context=dispatch_context,
                )
                if not can_handle:
                    return refusal_message or "I don't understand that command."

                handled_result = candidate.handle_verb(
                    "",
                    dispatch_context=dispatch_context,
                )
                if handled_result is not None:
                    return handled_result
    return None


def ensure_terminal_session() -> bool:
    """Ensure game runs in a real terminal window on Windows.

    Returns True when execution should continue in this process.
    Returns False when a new terminal session is spawned and this process should exit.
    """
    if os.name != "nt":
        return True

    streams = (sys.stdin, sys.stdout, sys.stderr)
    has_tty = all(getattr(stream, "isatty", lambda: False)() for stream in streams)
    if has_tty:
        return True

    if os.environ.get("KINGDOM_TERMINAL_RELAUNCHED") == "1":
        return True

    base_dir = Path(__file__).resolve().parent
    script_path = Path(__file__).resolve()

    python_exe = Path(sys.executable)
    if python_exe.name.lower() == "pythonw.exe":
        python_exe = python_exe.with_name("python.exe")

    working_dir = str(base_dir).replace("'", "''")
    python_cmd = str(python_exe).replace("'", "''")
    script_cmd = str(script_path).replace("'", "''")
    ps_command = (
        "$env:KINGDOM_TERMINAL_RELAUNCHED='1'; "
        f"Set-Location -LiteralPath '{working_dir}'; "
        f"& '{python_cmd}' '{script_cmd}'"
    )

    subprocess.Popen(
        [
            "cmd",
            "/c",
            "start",
            '"Kingdom TRS-80"',
            "powershell",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_command,
        ]
    )
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Kingdom game")
    parser.add_argument(
        "--mode",
        choices=[TERMINAL_MODE_TRS80, TERMINAL_MODE_MODERN],
        default=TERMINAL_MODE_TRS80,
        help="Terminal presentation mode (default: trs80)",
    )
    return parser.parse_args()


def main(args: argparse.Namespace | None = None):
    """Run a minimal verb-based load/save flow with input loop."""
    if args is None:
        args = parse_args()

    terminal_style.ACTIVE_TERMINAL_MODE = args.mode

    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "initial_state.json"
    save_path = base_dir / "data" / "working_state.json"
    log_file, log_path, original_stdout, original_stderr = start_session_logging(base_dir)

    try:
        trs80_print(f"Logging to {log_path}", style=TRS80_WHITE)
        trs80_print("Welcome to Kingdom.", style=TRS80_WHITE, bold=True)

        game = Game.get_instance()

        game.setup_world(data_path)
        ensure_direction_nouns()

        hero_name = trs80_prompt("Enter hero name: ").strip() or "Hero"
        game.set_current_player(Player(hero_name))
        trs80_print(f"Welcome, {hero_name}.", style=TRS80_WHITE)

        def confirm_action(prompt_text: str) -> bool:
            reply = trs80_prompt(f"{prompt_text} (y/n): ").strip().lower()
            return reply in {"y", "yes"}

        if game.rooms:
            clear_screen()
            current_room = game.rooms[0]
            trs80_clear_and_show_room(current_room, hero_name=hero_name)
            print()
        else:
            current_room = None
        action_state = GameActionState(current_room=current_room, hero_name=hero_name)

        verbs = build_verbs(
            action_state,
            game,
            save_path,
            confirm_action=confirm_action,
            prompt_action=trs80_prompt,
        )

        while True:
            command = trs80_prompt("Enter command: ")
            if not command:
                continue

            resolved_command = resolve_command(
                command,
                known_verbs=verbs.keys(),
                known_nouns=iter_known_noun_names(game),
            )
            if resolved_command is None:
                implicit_result = _try_implicit_noun_action(game, action_state, command)
                if implicit_result:
                    trs80_print(implicit_result, style=TRS80_WHITE)
                    continue
                trs80_print("I don't understand that command.", style=TRS80_WHITE)
                continue

            verb_word = resolved_command.verb
            args = resolved_command.args
            target_noun = _resolve_target_noun(game, action_state, resolved_command)

            verb = verbs.get(verb_word)
            if verb is None:
                trs80_print("I don't understand that command.", style=TRS80_WHITE)
                continue

            try:
                result = verb.execute(
                    *args,
                    target=target_noun,
                    dispatch_context=build_dispatch_context(action_state, game),
                )
            except QuitGame:
                trs80_print("Goodbye!", style=TRS80_WHITE)
                break
            except TypeError:
                trs80_print("That command needs more information.", style=TRS80_WHITE)
                continue

            if result:
                trs80_print(result, style=TRS80_WHITE)
    finally:
        stop_session_logging(log_file, original_stdout, original_stderr)


if __name__ == "__main__":
    if ensure_terminal_session():
        main(parse_args())
