"""
Kingdom Game World Simulator - Core API
Uses World model methods for setup, save, and load functionality.
See demo.py for gameplay examples.
"""

from pathlib import Path
import argparse
from pydoc import text
import random
import sys
sys.path.append("./src")

from kingdom.terminal_style import TERMINAL_MODE_TRS80, TERMINAL_MODE_MODERN, set_terminal_mode
from kingdom.utilities import SessionLogger, ensure_terminal_session

from kingdom.UI import ui

#  model modules
from kingdom.model.noun_model import Noun, World, Player, Room
from kingdom.model.game_init import QuitGame, GameOver, SaveGame, LoadGame
from kingdom.model.game_persistence import save_game, load_game
from kingdom.model.game_init import GameActionState, get_game, setup_world
from kingdom.model.verb_model import Verb

from kingdom.rendering.descriptions import render_current_room

from kingdom.verbs.verb_registration import register_verbs


# language modules
from kingdom.language.lexicon import Lexicon, lex
from kingdom.language.parser import parse
from kingdom.language.interpreter import interpret
from kingdom.language.executor import execute  



#------------------ Design Note: Main Refactor (v2) ------------------
def init_game_state() -> tuple[World | None, Lexicon | None]:
    """
    Welcome player and initialize game world.
    """
    
    try:

        base_dir = Path(__file__).resolve().parent
        data_path = base_dir / "data" / "initial_state.json"

        # Initialize world and game state
        world = World.get_instance()
        setup_world(world, data_path)

        if world.rooms: current_room = world.rooms[world.start_room_name]
        else: raise ValueError("No rooms found in game data.")    


        ui.print("Welcome to Kingdom.","\n", bold=True)

        player_name = ui.prompt("Player name> ").strip() or "ralf"
        player = Player(player_name)

        ui.print(f"Welcome {player_name}!","\n")
        
        save_path = base_dir / "saves" / f"{player_name}.json"
        game = get_game()
        game.init_session(world=world, current_player=player, initial_room=current_room, player_name=player_name, save_path=save_path)  # initialize the global action state and prefs

         
        #------------------------------------------------------------

        # Build verbs for parser access
        register_verbs()
        
        lexicon = lex()  # build lexicon for parser access
        game.lexicon = lexicon  # store lexicon in action state for access during game


        lines = render_current_room(game.current_room)
        ui.render_room(lines, clear=False)

    except Exception as e:
        print(f"Critical error during game initialization: {e}")
        return None, None
    
    return world, lexicon   # initialization successful

def handle_game_over(
    game_over: GameOver,
    world: World,
    start_room: Room,
) -> tuple[bool, bool]:
    """
    Handle GameOver exception: show message, offer clone attempt, apply effects.
    
    Returns: (should_quit: bool, new_recovery_mode: bool)
    """
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

    game = get_game()
    game.current_room = start_room
    
    # Apply penalty for being cloned
    penalty = 20
    game.score = max(0, int(game.score) - int(penalty)) 

    if game.current_room is not None:
        lines = render_current_room(game.current_room, look=True)
        ui.render_room(lines, clear=False)
        print() 
    
    return False, False  # success → exit recovery mode

def process_command(
    raw_command: str,
    world: World,
    lexicon: Lexicon,
    recovery_mode: bool,
) -> tuple[bool, bool, str | None]:
    '''
    return values: should_quit, recovery_mode, output

    should_quit — True means “break out of the main loop.”

    recovery_mode — the updated recovery mode flag.
    '''
    result = None

    if not raw_command:
        return False, recovery_mode, "What would you like to do? (type help for assistance)"

    current_room_before_command = get_game().current_room  # capture current room before command execution for potential use in recovery mode logic

    parsed = parse(raw_command, lexicon)

    interpreted = interpret(parsed, world, lexicon)

    if recovery_mode:
        verb_word = interpreted[0].verb.name if interpreted[0].verb else None
        if verb_word not in {"load", "quit", "help"}:
            return False, recovery_mode, "You are dead. Load a saved game or quit."

    try:
        for cmd in interpreted:
            outcome = execute(cmd, world, raw_command)                     #pass orignal command for better error message
            ui.print(outcome.message if outcome else "Command executed.")

    except LoadGame:
        path=ui.request_load()
        if path is None:
            return False, recovery_mode, "Load cancelled."

        try:
            loaded_path = load_game(world, path)
        except RuntimeError as e:
            return False, recovery_mode, f"Load failed: {e}"

        get_game().prefs.remember_save(loaded_path)
        ui.print(f"Game loaded from {loaded_path}.")
        ui.clear_screen()
        ui.print(f"Welcome back {get_game().player_name}!","\n")
        ui.render_room(render_current_room(get_game().current_room), clear=False)
        return False, recovery_mode, None  # no custom message on load, just rely on room render" 
    
    except SaveGame:
        path=ui.request_save()
        if path is None:
            return False, recovery_mode, "Save cancelled."

        try:
            saved_path = save_game(world, path)
        except RuntimeError as e:
            return False, recovery_mode, f"Save failed: {e}"

        get_game().prefs.remember_save(saved_path)
        return False, recovery_mode, f"Game saved to {saved_path}"
    
    except QuitGame:
        if ui.request_quit(): return True, recovery_mode, "Goodbye! Thanks for playing Kingdom."
        else: return False, recovery_mode, "Quit cancelled."
        
    except GameOver as game_over:
        start_room = Room.by_name(world.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            world,
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
        current_room_before_command.found = True    #fix: this should happen in the move verb

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

    set_terminal_mode(args.mode)

    base_dir = Path(__file__).parent
    logger = SessionLogger(base_dir)
    logger.start()


    try:
        
        world, lexicon = init_game_state()
        
        recovery_mode = False

        while True:

            command = ui.prompt("\n> ")
            ui.print()

            should_quit, recovery_mode, output = process_command(
                raw_command=command,
                world=world,
                lexicon=lexicon,
                recovery_mode=recovery_mode,
            )

            if should_quit:
                break

            ui.print(output) if output else None

    finally:
        logger.stop()


if __name__ == "__main__":
    main()
