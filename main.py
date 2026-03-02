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
from kingdom.models import Game, Player, Room, GameActionState, build_dispatch_context
from kingdom.models import QuitGame, GameOver, SaveGame, LoadGame
from kingdom.renderer import render_current_room

from kingdom.models import DIRECTIONS, DirectionNoun, DispatchContext


from kingdom.actions import build_verbs
import kingdom.item_behaviors as item_behaviors


from kingdom.parser import parse_command, resolve_command
from kingdom.utilities import SessionLogger, init_terminal_mode, ensure_terminal_session

from kingdom.UI import UI 
import kingdom.terminal_style as terminal_style


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


        ui = UI(game)
        ui.print("Welcome to Kingdom.", bold=True)
        ui.print()
        hero_name = ui.prompt("Enter hero name: ").strip() or "Hero"
        game.set_current_player(Player(hero_name))
        ui.print()
        ui.print(f"Welcome {hero_name}!")
        ui.print()

        if game.rooms:
            current_room = game.rooms[game.start_room_name]
        else:
            raise ValueError("No rooms found in game data.")    
        
        action_state = GameActionState(current_room=current_room, hero_name=hero_name)
        game.state = action_state    # give the world a pointer to action state  

        game.save_path = base_dir / "data" / f"{hero_name}-save.json"
        game.load_path = base_dir / "data" / f"{hero_name}-save.json"      
        
        dispatch_context = build_dispatch_context(game=game, state=game.state)

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
    action_state: GameActionState,
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
        ui.print()
        ui.print("Oh no! It seems that there wasn't enough of you left to clone, but it was a good try.")
        ui.print("You may load a saved game or quit.")
        ui.print()
        return False, True  # fail → recovery mode

    # Success!
    ui.print()
    ui.print("Well I'll be darned, it worked!!")
    ui.print()
    action_state.current_room = start_room
    
    # Apply penalty for being cloned
    penalty = 20
    game.score = max(0, int(game.score) - int(penalty)) 

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
        ui.print("You are dead. Load a saved game or quit.")
        return False, recovery_mode, "You are dead. Load a saved game or quit."

    verb = verbs.get(verb_word)
    if verb is None:
        ui.print("I don't understand that command.")
        return False, recovery_mode, "I don't understand that command."

    try:
        result = verb.execute(
        dispatch_context,   # ctx
        target_noun,        # target
        args,               # words (tuple)
        )

    except LoadGame:
        msg=ui.request_load()
        return False, recovery_mode, msg
    except SaveGame:
        msg=ui.request_save()
        return False, recovery_mode, msg
    except QuitGame:
        msg = ui.request_quit()
        if msg:
            return True, recovery_mode, msg
        else:
            return False, recovery_mode, "Quit cancelled."
    except GameOver as game_over:
        start_room = Room.by_name(dispatch_context.game.start_room_name)
        should_quit, recovery_mode = handle_game_over(
            game_over,
            game,
            action_state,
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
            ui.print()
            command = ui.prompt("Enter command: ")
            ui.print()

            should_quit, recovery_mode, output = process_command(
                command=command,
                verbs=game.verbs,
                game=game,
                action_state=game.state,
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
