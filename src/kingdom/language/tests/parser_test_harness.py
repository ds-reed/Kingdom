# ======================================================================
# PARSER TEST HARNESS
# ======================================================================
# This module provides:
#   - run_parser_tests(): main entrypoint
#   - pretty_print(): human-readable ParsedSyntax dump
#   - compare(): deep comparison of expected vs actual
#   - diff(): structural diff printer
#
# The harness is stage-aware: it only checks fields present in the
# expected dict for that stage. All other fields are ignored.
#
# This lets you evolve the parser incrementally without rewriting tests.
# ======================================================================

from pprint import pprint


# ----------------------------------------------------------------------
# Pretty Printer for ParsedSyntax
# ----------------------------------------------------------------------
def pretty_print(parsed):
    print("=== ParsedSyntax ===")
    print(f"raw_text: {parsed.raw_text}")
    print(f"normalized_text: {parsed.normalized_text}")
    print(f"tokens: {parsed.tokens}")
    print(f"token_spans: {parsed.token_spans}")
    print(f"verb_candidates: {parsed.verb_candidates}")
    print(f"primary_verb_token: {parsed.primary_verb_token}")
    print(f"primary_verb_canonical: {parsed.primary_verb_canonical}")
    print(f"noun_candidates: {parsed.noun_candidates}")
    print(f"object_phrases: {parsed.object_phrases}")
    print(f"prep_phrases: {parsed.prep_phrases}")
    print(f"conjunction_groups: {parsed.conjunction_groups}")
    print(f"direction_tokens: {parsed.direction_tokens}")
    print(f"modifier_tokens: {parsed.modifier_tokens}")
    print(f"unknown_tokens: {parsed.unknown_tokens}")
    print(f"diagnostics: {parsed.diagnostics}")
    print("====================\n")


# ----------------------------------------------------------------------
# Deep comparison of expected vs actual ParsedSyntax
# ----------------------------------------------------------------------
def compare(parsed, expected):
    """
    Compare only the fields present in expected.
    This allows stage-by-stage testing without requiring full parser output.
    """
    failures = []

    for key, expected_value in expected.items():
        actual_value = getattr(parsed, key, None)

        if actual_value != expected_value:
            failures.append((key, expected_value, actual_value))

    return failures


# ----------------------------------------------------------------------
# Diff printer
# ----------------------------------------------------------------------
def diff(failures):
    """
    Print a readable diff for mismatched fields.
    """
    print("❌ Test Failed:")
    for key, expected, actual in failures:
        print(f"  Field: {key}")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
    print()


# ----------------------------------------------------------------------
# Test Runner
# ----------------------------------------------------------------------
def run_parser_tests(parser, lexicon, tests):
    """
    parser: instance of your NewParser
    lexicon: test lexicon object
    tests: dict of test groups (stage_1, stage_2, ...)
    """
    print("\n==============================")
    print(" RUNNING PARSER TEST SUITE")
    print("==============================\n")

    for stage_name, stage_tests in tests.items():
        print(f"--- {stage_name.upper()} ---")

        for test in stage_tests:
            phrase = test["input"]
            expected = test["expected"]

            parsed = parser.parse(phrase, lexicon, {})

            failures = compare(parsed, expected)

            if failures:
                print(f"Input: {phrase}")
                diff(failures)
                print("ParsedSyntax dump:")
                pretty_print(parsed)
            else:
                print(f"✔ {phrase}")

        print()

    print("Test suite complete.\n")
