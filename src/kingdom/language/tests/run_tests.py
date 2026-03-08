#!/usr/bin/env python3

import sys
from pathlib import Path

# Make sure Python can find the kingdom package
ROOT = Path(__file__).resolve().parents[3]   # adjust if needed
sys.path.insert(0, str(ROOT))


from kingdom.language.tests import parser_test_harness
from kingdom.language.tests.dummy_lexicon import build_dummy_lexicon
from kingdom.language.tests.test_parser_dataset import TESTS
from kingdom.language.parser import parser   # your parser module
from kingdom.language.lexicon.lexicon import Lexicon

def main():

    lexicon = build_dummy_lexicon()
    tests = TESTS


    print("Select test suite:")
    print("1) Parser only")
    print("2) Parser + Interpreter flow")
    choice = input("> ").strip()

    if choice == "1":
        from kingdom.language.tests.parser_test_harness import run_parser_tests
        run_parser_tests(parser, lexicon, tests)

    elif choice == "2":
        from kingdom.language.tests.parser_to_interpreter_flow_tests import run_p2i_flow_tests
        run_p2i_flow_tests(lexicon, tests)
    

    else:
        print("Invalid choice.")
    
if __name__ == "__main__":
    main()
