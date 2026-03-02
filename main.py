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

from kingdom.terminal_style import TERMINAL_MODE_TRS80, TERMINAL_MODE_MODERN
from kingdom.models import Game, Player, Room, build_dispatch_context
from kingdom.models import QuitGame, GameOver, SaveGame, LoadGame
from kingdom.renderer import render_current_room

from kingdom.models import DIRECTIONS, DirectionNoun, DispatchContext


from kingdom.actions import build_verbs
import kingdom.item_behaviors as item_behaviors


from kingdom.parser import parse_command, resolve_command
from kingdom.utilities import SessionLogger, init_terminal_mode, ensure_terminal_session

from kingdom.UI import UI 
import kingdom.terminal_style as terminal_style

from kingdom.models import GameActionState, init_session , get_action_state, get_prefs

# new imports from main refactor - should all be temporary
from kingdom.resolver import  _resolve_target_noun, iter_known_noun_names, _iter_local_target_candidates


#------------------ Design Note: Main Refactor (v2) ------------------
def init_game_state() -> tuple[Game | None, DispatchContext | None]:
    """
    Welcome player, initialize game world and return tuple(game: Game, dispatch context: DispatchContext).
    """
    
    try:

        base_dir = Path(__file__).resolve().parent
        data_path = base_dir / "data" / "initial_state.json"

        # Build the game
        game = Game.get_instance()
        game.setup_world(data_path)

        if game.rooms: current_room = game.rooms[game.start_room_name]
        else: raise ValueError("No rooms found in game data.")    


        ui = UI(game)
        ui.print("Welcome to Kingdom.","\n", bold=True)

        player_name = ui.prompt("Enter hero name: ").strip() or "Hero"
        player = Player(player_name)
        game.set_current_player(player)

        ui.print(f"Welcome {player_name}!","\n")
        
        save_path = base_dir / "saves" / f"{player_name}.json"

        init_session(game=game, current_player=player, initial_room=current_room, player_name=player_name, save_path=save_path)  # initialize the global action state and prefs
        action_state = get_action_state()  # retrieve the initialized action state
         
        dispatch_context = build_dispatch_context(game=game, state=action_state)

        #------------------------------------------------------------

        # Build verbs for parser access
        game.verbs = build_verbs()
        
        # in future, Render will not display, so will need to follow this with a call to the UI
        lines = render_current_room(action_state, display=False)
        ui.render_room(lines, clear=False)

    except Exception as e:
        print(f"Critical error during game initialization: {e}")
        return None, None
    
    return game, dispatch_context   # initialization successful

def handle_game_over(
    game_over: GameOver,
    game: Game,
    start_room: Room,
) -> tuple[bool, bool]:
    """
    Handle GameOver exception: show message, offer clone attempt, apply effects.
    
    Returns: (should_quit: bool, new_recovery_mode: bool)
    """
    ui = UI(game)
    ui.print(str(game_over))
    ui.print("It seems that you ran into a little trouble, didn't you?")
    ui.print("Well there is help. I could try to clone the remains but it will cost you points.")
    
    attempt_clone = ui.confirm(question="Shall I try? (y/n): ")

    if not attempt_clone:
        ui.print("You may load a saved game or quit.")
        return False, True  # stay in recovery mode

    # Clone attempt (30% success chance: fail if roll > 7 → 3/10 success)
    if random.randint(1, 10) > 7:
        ui.print("Oh no! It seems that there wasn't enough of you left to clone, but it was a good try.")
        ui.print("You may load a saved game or quit.","\n")
        return False, True  # fail → recovery mode

    # Success!

    ui.print("Well I'll be darned, it worked!!","\n")

    action_state = get_action_state()
    action_state.current_room = start_room
    
    # Apply penalty for being cloned
    penalty = 20
    action_state.score = max(0, int(action_state.score) - int(penalty)) 

    if action_state.current_room is not None:
        lines = render_current_room(action_state, clear=False)
        ui.render_room(lines, clear=False)
        print() 
    
    return False, False  # success → exit recovery mode

def process_command(
    command: str,
    verbs: dict,
    game: Game,
    action_state: GameActionState,
    dispatch_context,
    recovery_mode: bool,
) -> tuple[bool, bool, str | None]:
    '''
    return values: should_quit, recovery_mode, output

    should_quit — True means “break out of the main loop.”

    recovery_mode — the updated recovery mode flag.
    '''
    
    ui = UI(game)
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
        return False, recovery_mode, "You are dead. Load a saved game or quit."

    verb = verbs.get(verb_word)
    if verb is None:
        return False, recovery_mode, "I don't understand that command."

    try:
        result = verb.execute(
        dispatch_context,   # ctx
        target_noun,        # target
        args,               # words (tuple)
        )

    except LoadGame:
        path=ui.request_load()
        if path is None:
            return False, recovery_mode, "Load cancelled."

        try:
            loaded_path = game.load_game(path)
        except RuntimeError as e:
            return False, recovery_mode, f"Load failed: {e}"

        get_prefs().remember_save(loaded_path)
        ui.print(f"Game loaded from {loaded_path}.")
        ui.clear_screen()
        ui.print(f"Welcome back {get_action_state().player_name}!","\n")
        ui.render_room(render_current_room(get_action_state()), clear=False)
        return False, recovery_mode, None  # no custom message on load, just rely on room render" 
    
    except SaveGame:
        path=ui.request_save()
        if path is None:
            return False, recovery_mode, "Save cancelled."

        try:
            saved_path = game.save_game(path)
        except RuntimeError as e:
            return False, recovery_mode, f"Save failed: {e}"

        get_prefs().remember_save(saved_path)
        return False, recovery_mode, f"Game saved to {saved_path}"
    
    except QuitGame:
        if ui.request_quit(): return True, recovery_mode, "Goodbye! Thanks for playing Kingdom."
        else: return False, recovery_mode, "Quit cancelled."
        
    except GameOver as game_over:
        start_room = Room.by_name(dispatch_context.game.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            game,
            start_room,
        )
        if should_quit:
            return True, recovery_mode, "Goodbye! Thanks for playing Kingdom."
        return False, recovery_mode, None

    except TypeError as e:
        ui.print(f"TypeError: {e}")
        return False, recovery_mode, "That command needs more information."


    if recovery_mode and verb_word in {"load", "restore"} and isinstance(result, str) and result.startswith("Game loaded from"):
        recovery_mode = False

    if result:
        current_room.visited = True

    return False, recovery_mode, result

#------------------- End of Design Note: Main Refactor (v2) ------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Kingdom game")
    parser.add_argument(
        "--mode",
        choices=[TERMINAL_MODE_TRS80, TERMINAL_MODE_MODERN],
        default=TERMINAL_MODE_MODERN,
        help="Terminal presentation mode (default: modern)",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    if not ensure_terminal_session():
        return

    init_terminal_mode(args)

    base_dir = Path(__file__).parent
    logger = SessionLogger(base_dir)
    logger.start()


    try:
        
        game, dispatch_context = init_game_state()
        ui = UI(game)

        if not game or not dispatch_context:
            print(f"Failed to initialize game. Please check logfile for details.")
            return
        
        recovery_mode = False

        while True:

            ui.print("\n")  # Add spacing before prompt
            command = ui.prompt("Enter command: ")
            ui.print("\n")  # Add spacing after command input

            should_quit, recovery_mode, output = process_command(
                command=command,
                verbs=game.verbs,
                game=game,
                action_state=get_action_state(),
                dispatch_context=dispatch_context,
                recovery_mode=recovery_mode,
            )

            if should_quit:
                break

            if output:
                ui.print(output)

    finally:
        logger.stop()


if __name__ == "__main__":
    main()
