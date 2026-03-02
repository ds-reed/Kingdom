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