# ======================================================================
# PARSER TEST HARNESS (Stage-Aware)
# ======================================================================

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from kingdom.language.parser import ParserOptions
from kingdom.language.parser import parse


# ----------------------------------------------------------------------
# Pretty Printer for ParsedAction
# ----------------------------------------------------------------------
def pretty_print(parsed, index=None):
    header = f"=== ParsedAction #{index} ===" if index is not None else "=== ParsedAction ==="
    print(header)
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
# Stage-specific field sets
# ----------------------------------------------------------------------
STAGE_FIELDS = {
    1: [
        "normalized_text",
        "tokens",
        "token_spans",
        "verb_candidates",
        "primary_verb_token",
        "primary_verb_canonical",
        "noun_candidates",
        "direction_tokens",
        "modifier_tokens",
        "unknown_tokens",
    ],
    2: [
        "object_phrases",
        "conjunction_groups",
    ],
    3: [
        "modifier_tokens",
        "prep_phrases",
        "direction_tokens",
    ],
    4: [
        "primary_verb_token",
        "primary_verb_canonical",
        "object_phrases",
        "prep_phrases",
        "modifier_tokens",
    ],
}


# ----------------------------------------------------------------------
# Stage-aware comparison for a single ParsedAction
# ----------------------------------------------------------------------
def compare_stage(parsed, expected, stage):
    failures = []
    allowed = STAGE_FIELDS.get(stage, [])

    for key, expected_value in expected.items():
        if key not in allowed:
            continue

        actual_value = getattr(parsed, key, None)

        # Special handling for object_phrases: expected is a subset
        if key == "object_phrases":
            for exp_np in expected_value:
                if exp_np not in actual_value:
                    failures.append((key, expected_value, actual_value))
                    break
            continue

        # Normal exact match
        if actual_value != expected_value:
            failures.append((key, expected_value, actual_value))

    return failures


# ----------------------------------------------------------------------
# Diff printer
# ----------------------------------------------------------------------
def diff(action_index, failures):
    print(f"❌ Test Failed in action #{action_index}:")
    for key, expected, actual in failures:
        print(f"  Field: {key}")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
    print()


# ----------------------------------------------------------------------
# Test Runner
# ----------------------------------------------------------------------
def run_parser_tests(lexicon, tests):
    print("\n==============================")
    print(" RUNNING PARSER TEST SUITE")
    print("==============================\n")

    for stage_name, stage_tests in tests.items():
        stage_num = int(stage_name.split("_")[1])
        print(f"--- {stage_name.upper()} ---")

        for test in stage_tests:
            phrase = test["input"]
            expected_actions = test["expected"]  # now a list of expected dicts

            options = ParserOptions(stage=stage_num)
            parsed_actions = parse(phrase, lexicon, options)

            # Length mismatch check
            if len(parsed_actions) != len(expected_actions):
                print(f"❌ Input: {phrase}")
                print(f"  Expected {len(expected_actions)} actions, got {len(parsed_actions)}")
                for i, p in enumerate(parsed_actions, start=1):
                    pretty_print(p, i)
                continue

            all_failures = []
            for i, (parsed, expected) in enumerate(zip(parsed_actions, expected_actions), start=1):
                failures = compare_stage(parsed, expected, stage_num)
                if failures:
                    all_failures.append((i, failures))

            if all_failures:
                print(f"Input: {phrase}")
                for action_index, failures in all_failures:
                    diff(action_index, failures)
                print("ParsedAction dump:")
                for i, p in enumerate(parsed_actions, start=1):
                    pretty_print(p, i)
            else:
                print(f"✔ {phrase}")

        print()

    print("Test suite complete.\n")
