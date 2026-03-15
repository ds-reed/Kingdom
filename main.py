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
from kingdom.model.noun_model import World, Player, Room
from kingdom.model.game_model import Game, QuitGame, GameOver, SaveGame, LoadGame, get_game

from kingdom.rendering.descriptions import render_current_room
from kingdom.rendering.command_results import exit_message

from kingdom.verbs.verb_registration import register_verbs

# language modules
from kingdom.language.lexicon import Lexicon
from kingdom.language.parser import parse
from kingdom.language.interpreter import interpret
from kingdom.language.executor import execute  


#------------------ Design Note: Main Refactor (v2) ------------------
def init_game_state() -> Game | None:
    """
    Welcome player and initialize game world.
    """

    ui.print("Welcome to Kingdom.","\n", bold=True)
    player_name = ui.prompt("Player name> ").strip() or "ralf"
    ui.print(f"Welcome {player_name}!","\n")
    
    base_dir = Path(__file__).resolve().parent
    save_path = base_dir / "saves" / f"{player_name}.json"
    data_path = base_dir / "data" / "initial_state.json"
    
    try:

        #-----------------------setup a new game ---------------------

        register_verbs()
        
        game = get_game()                   # create fresh game instance (resets all state)
        game.world = World.get_instance()   # ensure world is initialized before setup_world
        game.setup_world(data_path)         # populate world with initial state from JSON file
        player = Player(player_name)        # create player instance

        game.init_session(                  # initialize the global game state and prefs  
                world= game.world, 
                current_player=player, 
                player_name=player_name, 
                save_path=save_path
                )
          
        #------------------------------------------------------------

    except Exception as e:
        print(f"Critical error during game initialization: {e}")
        return None
    
    ui.render_room(render_current_room(game.current_room))
    
    return game   # initialization successful

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
        if ui.request_quit(): return True, recovery_mode, exit_message(get_game())
        else: return False, recovery_mode, "Quit cancelled."
        
    except GameOver as game_over:
        start_room = Room.by_name(world.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            world,
            start_room,
        )
        if should_quit:
            return True, recovery_mode, exit_message(get_game())
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
        
        game =init_game_state()
        
        recovery_mode = False

        while True:

            command = ui.prompt("\n> ")
            ui.print()

            should_quit, recovery_mode, output = process_command(
                raw_command=command,
                world=game.world,
                lexicon=game.lexicon,
                recovery_mode=recovery_mode,
            )
            
            ui.print(output) if output else None
            if should_quit:
                break



    finally:
        logger.stop()


if __name__ == "__main__":
    main()
