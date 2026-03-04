# development_parser.py
'''
Design Note: Development Parser (v2, Syntax-Only)

Purpose

This module is a parallel parser prototype used to validate the target parser architecture before integration into runtime flow.
It must remain syntax-only and deterministic.
Scope

In scope: normalize text, tokenize input, detect known verbs, detect known nouns, identify unknown tokens.
Out of scope: world lookup, noun-object resolution, direction semantics, implicit command rewriting, user-facing error messages.
Inputs

Raw command text (string)
Known verbs (list/iterable of strings, caller-supplied)
Known nouns (list/iterable of strings, caller-supplied)
Outputs

Parsed command payload with:
raw_text
normalized_text
tokens (ordered)
matched_verbs
matched_nouns
primary_verb (or None)
unknown_tokens
Architectural Constraints

No imports from model registries or global game state.
No dependency on runtime world context.
No mutation of game state.
Same input + same vocab must always produce the same output.
Boundary with Resolver

Resolver owns semantics and ambiguity handling.
Parser output is purely candidate-level syntax evidence.
Any implicit behavior (for example, single direction interpreted as movement) belongs in resolver, not parser.
Compatibility Strategy

Keep this parser in parallel with the existing parser path.
Add adapter logic only at integration boundaries (main/resolver), not inside parser core.
Stage 1 matching policy: single-token matching only; multi-word phrase matching deferred.
Success Criteria (for this phase)

Cleanly parses valid and noisy commands with no world coupling.
Produces stable unknown-token output for downstream resolver decisions.
Can be smoke-tested independently with supplied noun/verb lists.

'''

# ======================================================================
# Dummy NewParser for Harness Testing
# ======================================================================
# This parser:
#   - Accepts the real parser API: parse(text, lexicon, options)
#   - Looks up expected results from the TESTS dataset
#   - Returns a ParsedSyntax object populated with those expected values
#   - Produces intentional mismatches for a few phrases to test failure mode
#
# This lets you validate the test harness, diff printer, and stage-aware
# comparison logic before implementing the real parser.
# ======================================================================

from kingdom.tests.test_parser_dataset import TESTS


# ----------------------------------------------------------------------
# Minimal ParsedSyntax stub matching your frozen contract
# ----------------------------------------------------------------------
class ParsedSyntax:
    def __init__(self):
        self.raw_text = ""
        self.normalized_text = ""
        self.tokens = []
        self.token_spans = []

        self.verb_candidates = []
        self.primary_verb_token = None
        self.primary_verb_canonical = None

        self.noun_candidates = []
        self.object_phrases = []
        self.prep_phrases = []
        self.conjunction_groups = []

        self.direction_tokens = []
        self.modifier_tokens = []

        self.unknown_tokens = []
        self.diagnostics = []


# ----------------------------------------------------------------------
# Dummy parser implementation
# ----------------------------------------------------------------------
class NewParser:
    def __init__(self):
        # Build a lookup table: phrase → expected dict
        self.expected_map = {}
        for stage_tests in TESTS.values():
            for entry in stage_tests:
                phrase = entry["input"].strip().lower()
                self.expected_map[phrase] = entry["expected"]

        # Add intentional failure cases
        self.expected_map["intentional failure 1"] = {
            "primary_verb_token": "expected_verb",
        }
        self.expected_map["intentional failure 2"] = {
            "tokens": ["this", "should", "fail"],
        }

    def parse(self, text, lexicon, options):
        phrase = text.strip().lower()

        parsed = ParsedSyntax()
        parsed.raw_text = text
        parsed.normalized_text = phrase

        # If we have an expected entry, populate fields accordingly
        if phrase in self.expected_map:
            expected = self.expected_map[phrase]            
            if "intentional failure" in phrase:
                expected = {"diagnostics": ["This is not what we expcetcd - this is an intentional failure case."]}

            # Populate only the fields present in expected
            for key, value in expected.items():
                setattr(parsed, key, value)

            # Provide minimal tokens if not specified
            if not parsed.tokens:
                parsed.tokens = phrase.split()

            return parsed

        # Default behavior for unknown phrases
        parsed.tokens = phrase.split()
        parsed.unknown_tokens = parsed.tokens
        parsed.diagnostics.append("No expected test entry for this phrase.")
        return parsed
