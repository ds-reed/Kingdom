#!/usr/bin/env python3

import sys
from pathlib import Path

# Make sure Python can find the kingdom package
ROOT = Path(__file__).resolve().parents[3]   # adjust if needed
sys.path.insert(0, str(ROOT))


from kingdom.language.tests import parser_test_harness
from kingdom.language.tests.dummy_lexicon import build_dummy_lexicon
from kingdom.language.tests.test_parser_dataset import TESTS
from kingdom.language.parser import parse   # your parser module
from kingdom.language.lexicon import Lexicon

def main():

    lexicon = build_dummy_lexicon()
    tests = TESTS

    choice = None
    while choice != "4":
        print("Select test suite:")
        print("1) Parser only")
        print("2) Parser + Interpreter flow")
        print("3) Full loop (Parser + Interpreter + Executor)")
        print("4) Exit ")
        choice = input("> ").strip()

        if choice == "1":
            from kingdom.language.tests.parser_test_harness import run_parser_tests
            run_parser_tests(lexicon, tests)

        elif choice == "2":
            from kingdom.language.tests.parser_to_interpreter_flow_tests import run_p2i_flow_tests
            run_p2i_flow_tests(lexicon, tests)

        elif choice == "3":
            from kingdom.language.tests.full_loop_test import run_full_loop_test
            run_full_loop_test()

        elif choice == "4":
            print("Exiting...")
            return

        else:
            print("Invalid choice.")
    
if __name__ == "__main__":
    main()
