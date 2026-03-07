# run_parser_tests.py

import sys
from pathlib import Path

# Make sure Python can find the kingdom package
ROOT = Path(__file__).resolve().parents[3]   # adjust if needed
sys.path.insert(0, str(ROOT))

from kingdom.language.tests.parser_test_harness import run_parser_tests
from kingdom.language.tests.dummy_lexicon import build_dummy_lexicon
from kingdom.language.tests.test_parser_dataset import TESTS
from kingdom.language.parser import parser   # your parser module

def main():
    lex = build_dummy_lexicon()
    run_parser_tests(parser, lex, TESTS)

if __name__ == "__main__":
    main()
