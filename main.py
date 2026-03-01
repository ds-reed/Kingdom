"""
Kingdom Game World Simulator - Core API
Uses Game model methods for setup, save, and load functionality.
See demo.py for gameplay examples.
"""

from pathlib import Path
import argparse
import os
import random
import subprocess
import sys
sys.path.append("./src")

from kingdom.models import Game, Player, Room, GameOver, QuitGame, GameActionState, build_dispatch_context
from kingdom.renderer import render_current_room

from kingdom.models import DIRECTIONS, DirectionNoun, DispatchContext


from kingdom.actions import build_verbs
import kingdom.item_behaviors as item_behaviors


from kingdom.parser import parse_command, resolve_command
from kingdom.utilities import start_session_logging, stop_session_logging
from kingdom.terminal_style import (
    clear_screen,
    trs80_print,
    trs80_prompt,
    TRS80_WHITE,
    TERMINAL_MODE_TRS80,
    TERMINAL_MODE_MODERN,
)
from kingdom.UI import UI
import kingdom.terminal_style as terminal_style

from kingdom.actions import build_verbs

# new imports from main refactor - should all be temporary
import random
from kingdom.resolver import  _resolve_target_noun, iter_known_noun_names, _iter_local_target_candidates


#------------------ Design Note: Main Refactor (v2) ------------------
def init_game_state() -> tuple[Game | None, DispatchContext | None]:
    """
    Initialize game state and return True if successful, False if there was a critical error.
    """
    
    try:
        trs80_print("Welcome to Kingdom.", style=TRS80_WHITE, bold=True)

        base_dir = Path(__file__).resolve().parent
        data_path = base_dir / "data" / "initial_state.json"

        # Build the game
        game = Game.get_instance()
        game.setup_world(data_path)

        print()
        hero_name = trs80_prompt("Enter hero name: ").strip() or "Hero"
        game.set_current_player(Player(hero_name))
        print()
        trs80_print(f"Welcome {hero_name}!", style=TRS80_WHITE)
        print()

        if game.rooms:
            current_room = game.rooms[game.start_room_name]
        else:
            raise ValueError("No rooms found in game data.")    
        
        action_state = GameActionState(current_room=current_room, hero_name=hero_name)
        game.state = action_state    # give the world a pointer to action state  

        #----- will get cleaned up when UI is decoupled from verbs -------------
        save_path = base_dir / "data" / f"{hero_name}-save.json"
        load_path = base_dir / "data" / f"{hero_name}-save.json"      

        def confirm_action(prompt_text: str, *args, **kwargs) -> bool:
            reply = trs80_prompt(f"{prompt_text} (y/n): ").strip().lower()
            return reply in {"y", "yes"}     
        def prompt_callback(prompt_text: str, *args, **kwargs) -> str:
            return trs80_prompt(prompt_text)
        
        dispatch_context = build_dispatch_context(game=game, state=game.state)
        ui = UI(
            confirm=confirm_action,
            prompt=prompt_callback,
            save_path=save_path,
            load_path=load_path,
            game=game,
        )
        dispatch_context.ui = ui
        #-----------------------------------------------------------------------


        # Build verbs for parser access
        game.verbs = build_verbs(
            action_state,
            game,
            save_path,
            confirm_action=confirm_action,
            prompt_action=trs80_prompt,
        )
        
        # in future, Render will not display, so will need to follow this with a call to the UI
        render_current_room(action_state, clear=False)


    except Exception as e:
        trs80_print(f"Critical error during game initialization: {e}", style=TRS80_WHITE)
        return None, None
    return game, dispatch_context   # initialization successful

def handle_game_over(
    game_over: GameOver,
    game: Game,
    action_state: GameActionState,
    start_room: Room,
    trs80_print,
    trs80_prompt,
    render_current_room,
) -> tuple[bool, bool]:
    """
    Handle GameOver exception: show message, offer clone attempt, apply effects.
    
    Returns: (should_quit: bool, new_recovery_mode: bool)
    """

    trs80_print(str(game_over), style=TRS80_WHITE)
    trs80_print("It seems that you ran into a little trouble, didn't you?", style=TRS80_WHITE)
    trs80_print("Well there is help. I could try to clone the remains but it will cost you points.", style=TRS80_WHITE)
    
    attempt_clone = trs80_prompt("Shall I try? (y/n): ").strip().lower() in {"y", "yes"}

    if not attempt_clone:
        trs80_print("You may load a saved game or quit.", style=TRS80_WHITE)
        return False, True  # stay in recovery mode

    # Clone attempt (30% success chance: fail if roll > 7 → 3/10 success)
    if random.randint(1, 10) > 7:
        trs80_print("It seems that there wasn't enough to clone, but it was a good try.", style=TRS80_WHITE)
        trs80_print("You may load a saved game or quit.", style=TRS80_WHITE)
        return False, True  # fail → recovery mode

    # Success!
    trs80_print("Well I'll be darned, it worked!!", style=TRS80_WHITE)
    action_state.current_room = start_room
    
    # Apply penalty for being cloned
    penalty = 20
    game.score = max(0, int(game.score) - int(penalty)) 

    if action_state.current_room is not None:
        render_current_room(action_state, clear=False)
        print() 
    
    return False, False  # success → exit recovery mode

def process_command(
    command: str,
    verbs: dict,
    game: Game,
    action_state: GameActionState,
    dispatch_context,
    recovery_mode: bool,
    trs80_print,
    trs80_prompt,
    render_current_room,
) -> tuple[bool, bool, str | None]:
    '''
    return values: should_quit, recovery_mode, output

    should_quit — True means “break out of the main loop.”

    recovery_mode — the updated recovery mode flag.
    '''
    recovery_allowed_verbs = {"load", "restore", "quit", "q", "exit", "help", "commands"}

    current_room = action_state.current_room
    if not command:
        return False, recovery_mode, None

    resolved_command = resolve_command(
        command,
        known_verbs=verbs.keys(),
        known_nouns=iter_known_noun_names(game),
    )

    if resolved_command is None:
        return False, recovery_mode, "I don't understand that command."

    verb_word = resolved_command.verb
    args = resolved_command.args
    target_noun = _resolve_target_noun(game, action_state, resolved_command)

    if recovery_mode and verb_word not in recovery_allowed_verbs:
        trs80_print("You are dead. Load a saved game or quit.", style=TRS80_WHITE)
        return False, recovery_mode, "You are dead. Load a saved game or quit."

    verb = verbs.get(verb_word)
    if verb is None:
        trs80_print("I don't understand that command.", style=TRS80_WHITE)
        return False, recovery_mode, "I don't understand that command."

    try:
        result = verb.execute(
        dispatch_context,   # ctx
        target_noun,        # target
        args,               # words (tuple)
        )

    except QuitGame:
        trs80_print("Goodbye!", style=TRS80_WHITE)
        return True, recovery_mode, "Goodbye! Thanks for playing Kingdom."
    except GameOver as game_over:
        start_room = Room.by_name(dispatch_context.game.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            game,
            action_state,
            start_room,
            trs80_print,
            trs80_prompt,
            render_current_room,
        )
        if should_quit:
            return True, recovery_mode, "Goodbye! Thanks for playing Kingdom."
        return False, recovery_mode, None

    except TypeError as e:
        trs80_print(f"TypeError: {e}", style=TRS80_WHITE)
        return False, recovery_mode, "That command needs more information."


    if recovery_mode and verb_word in {"load", "restore"} and isinstance(result, str) and result.startswith("Game loaded from"):
        recovery_mode = False

    if result:
        current_room.visited = True

    return False, recovery_mode, result



#------------------- End of Design Note: Main Refactor (v2) ------------------

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
        default=TERMINAL_MODE_MODERN,
        help="Terminal presentation mode (default: modern)",
    )
    return parser.parse_args()

def main(args: argparse.Namespace | None = None):
    """Run a minimal verb-based load/save flow with input loop."""


    if args is None:
        args = parse_args()

    terminal_style.ACTIVE_TERMINAL_MODE = args.mode

    base_dir = Path(__file__).parent
    log_file, log_path, original_stdout, original_stderr = start_session_logging(base_dir)

    try:

        game, dispatch_context = init_game_state()

        if not game or not dispatch_context:
            trs80_print(f"Failed to initialize game. Please check {log_path} for details.", style=TRS80_WHITE)
            return
        
        recovery_mode = False

        while True:
            print()
            command = trs80_prompt("Enter command: ")
            print()

            should_quit, recovery_mode, output = process_command(
                command=command,
                verbs=game.verbs,
                game=game,
                action_state=game.state,
                dispatch_context=dispatch_context,
                recovery_mode=recovery_mode,
                trs80_print=trs80_print,
                trs80_prompt=trs80_prompt,
                render_current_room=render_current_room,
            )

            if should_quit:
                break

            if output:
                trs80_print(output, style=TRS80_WHITE)

    finally:
        stop_session_logging(log_file, original_stdout, original_stderr)


if __name__ == "__main__":
    if ensure_terminal_session():
        main(parse_args())
