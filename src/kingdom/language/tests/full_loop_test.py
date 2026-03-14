from pathlib import Path
import argparse
import random
import sys



from kingdom.language.lexicon import Lexicon, lex
from kingdom.language.parser import parse
from kingdom.language.interpreter import interpret
from kingdom.language.executor import execute   
from kingdom.model.game_init import  get_game, setup_world
from kingdom.model.noun_model import Player, World
from kingdom.verbs.verb_registration import register_verbs


def run_full_loop_test():
        ROOT = Path(__file__).resolve().parents[4]   
        sys.path.insert(0, str(ROOT))

        data_path = ROOT / "data" / "initial_state.json"

        world = World.get_instance()
        setup_world(world, data_path)

        current_room = world.rooms[world.start_room_name]

        player_name = "Dave"
        player = Player(player_name)

        save_path = ROOT / "saves" / f"{player_name}.json"

        get_game().init_session(world=world, current_player=player, initial_room=current_room, player_name=player_name, save_path=save_path)  # initialize the global action state and prefs
        game = get_game()  # retrieve the initialized game state

        register_verbs()

        lexicon = lex()  # build lexicon for parser access

        while True:
            text = input("Enter command for full loop test> ")

            parsed = parse(text, lexicon)

            interpreted = interpret(parsed, world, lexicon)

            for cmd in interpreted:
                outcome = execute(cmd, world, lexicon)
                print(outcome.message)
