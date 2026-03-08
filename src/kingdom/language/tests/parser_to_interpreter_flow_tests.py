# parser_to_interpreter_flow_tests.py

import sys
from pathlib import Path

from kingdom.model.noun_model import World

# Make sure Python can find the kingdom package
ROOT = Path(__file__).resolve().parents[3]   
sys.path.insert(0, str(ROOT))

from kingdom.language.parser import parse   
from kingdom.language.lexicon import Lexicon, VerbEntry, NounEntry
from kingdom.language.interpreter import interpret, InterpretedCommand, InterpretedTarget
from kingdom.language.parser import ParserOptions, parse


def run_p2i_flow_tests(lexicon: Lexicon, tests):
    print("\n=======================================")
    print(" RUNNING PARSER TO INTERPRETER TEST SUITE")
    print("=========================================\n")
    
    world = World.get_instance()

    for stage_name, stage_tests in tests.items():
        stage_num = int(stage_name.split("_")[1])
        print(f"--- {stage_name.upper()} ---")

        for test in stage_tests:
            phrase = test["input"]

            options = ParserOptions(stage=stage_num)
            parsed_actions = parse(phrase, lexicon, options)
            interpreted_commands = interpret(parsed_actions, world, lexicon)
            for cmd in interpreted_commands:
                verb = cmd.verb.canonical
                if cmd.direct:
                    for direct in cmd.direct:
                        noun = direct.canonical_head.canonical if direct else None
                        directions = cmd.direction
                        print(f"verb = {verb}, noun = {noun}, direction = {directions}")