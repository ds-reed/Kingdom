# tests/test_parser_harness.py

import sys
sys.path.append("./src")

from kingdom.tests.dummy_lexicon import build_dummy_lexicon
from kingdom.tests.test_parser_dataset import TESTS
from kingdom.tests.parser_test_harness import run_parser_tests
from kingdom.language.parser.parser import NewParser

parser = NewParser()
lexicon = build_dummy_lexicon()

run_parser_tests(parser, lexicon, TESTS)

def main():
    parser = NewParser()
    run_parser_tests(parser, lexicon, TESTS)


if __name__ == "__main__":
    main()

