#exception_handling.py
'''
functions that require handling exceptions that are relevant to the main game loop
includes initialization, game over handling, save, quit and load
'''

import sys
from pathlib import Path
sys.path.append("./src")
import random

from kingdom.GUI.UI import ui
from kingdom.rendering.command_results import exit_message, format_command_outcome
from kingdom.rendering.descriptions import render_current_room
from kingdom.model.game_model import Game, Player, GameOver, LoadGame, SaveGame, QuitGame, WinGame, get_game
from kingdom.model.noun_model import Room, World

from kingdom.engine.verbs.verb_registration import register_verbs

from kingdom.language.lexicon import Lexicon
from kingdom.language.parser import parse 
from kingdom.language.interpreter import interpret
from kingdom.language.executor import execute


#------------------ Design Note: Main Refactor (v2) ------------------
def init_game_state(world_file) -> Game | None:
    """
    Welcome player and initialize game world.
    """

    ui.print("Welcome to Kingdom.","\n")
    player_name = ui.prompt("Player name> ").strip() or "ralf"
    ui.print(f"Welcome {player_name}!","\n")
    
    # exception_handling.py lives under src/kingdom/engine; project root is 3 levels up.
    project_root = Path(__file__).resolve().parents[3]
    save_path = project_root / "saves" / f"{player_name}.json"

    requested_world = Path(world_file).expanduser()
    if requested_world.is_absolute():
        data_path = requested_world
    else:
        # Prefer data/ for short names (e.g., demo_castle.json), but allow repo-relative paths too.
        data_candidate = project_root / "data" / requested_world
        repo_candidate = project_root / requested_world
        data_path = data_candidate if data_candidate.exists() else repo_candidate
    
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
            rendered_output = format_command_outcome(outcome)
            ui.print(rendered_output if outcome else "Command executed.")
            game = get_game()   
            if game.current_room == world.end_room:
                if not game.continue_after_win:
                    raise WinGame()

    except LoadGame:
        path=ui.request_load()
        if path is None:
            return False, recovery_mode, "Load cancelled."

        try:
            game = get_game()
            loaded_path = game.load_game(path)
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
            game = get_game()
            saved_path = game.save_game(path)
        except RuntimeError as e:
            return False, recovery_mode, f"Save failed: {e}"

        get_game().prefs.remember_save(saved_path)
        return False, recovery_mode, f"Game saved to {saved_path}"
    
    except QuitGame:
        if ui.request_quit(): return True, recovery_mode, exit_message(get_game())
        else: return False, recovery_mode, "Quit cancelled."
        
    except GameOver as game_over:
        start_room = world.start_room or world.rooms.get(world.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            world,
            start_room,
        )
        if should_quit:
            return True, recovery_mode, exit_message(get_game())
        return False, recovery_mode, None
    
    except WinGame:
        ui.print(f"Congratulations!! You have reached the end of the game!")
        ui.print("You can quit now or keep exploring if you like.")
        if ui.request_quit(): 
            return True, recovery_mode, exit_message(get_game())
        else: 
            get_game().continue_after_win = True
            return False, recovery_mode, "Quit cancelled."


    except TypeError as e:
        ui.print(f"TypeError: {e}")
        return False, recovery_mode, "That command needs more information."


    if recovery_mode and verb_word in {"load", "restore"} and isinstance(result, str) and result.startswith("Game loaded from"):
        recovery_mode = False

    if result:
        current_room_before_command.found = True    #fix: this should happen in the move verb

    return False, recovery_mode, result

#------------------- End of Design Note: Main Refactor (v2) ------------------