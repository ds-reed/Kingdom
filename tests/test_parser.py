# tests/test_parser_harness.py

from kingdom.verbs.verb_registry import build_verb_registry
from kingdom.development_parser import NewParser

def run_test(command):
    registry = build_verb_registry()
    parser = NewParser(registry)
    result = parser.parse(command)
    print(f"INPUT: {command}")
    print(f"VERB: {result.verb.name if result else None}")
    print(f"TARGET: {result.target}")
    print(f"MODIFIERS: {result.modifiers}")
    print(f"DIRECTION: {result.direction_candidate}")
    print(f"TOKENS: {result.tokens}")
    print("-" * 40)

if __name__ == "__main__":
    run_test("look in box")
    run_test("go in box")
    run_test("take all in the bag")
    run_test("enter in")
