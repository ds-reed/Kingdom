Parser Design Note (Updated)
Purpose
The development parser is a parallel, syntax-only parser prototype that establishes the final parser contract early, so downstream integration can evolve without repeated function signature changes.

Primary Goal
Freeze parser input/output contracts now.
Implement capabilities in stages, but keep the same parser call shape throughout.

Architectural Position

Parser is syntax only.
Resolver is semantics.
Parser must not depend on world/model runtime state.
Target Files

Parser prototype: development_parser.py
Existing parser path: parser.py
Semantic handoff target: resolver.py
Orchestration consumer: main.py
Architecture reference: architecture_plan.md
Contract Freeze (Must stay stable)

Parser entrypoint
parse(text, lexicon, options) -> ParsedSyntax

Required inputs

text: raw player command string
lexicon: caller-supplied vocabulary object (no global registries)
options: parser behavior flags/toggles (optional defaults allowed)
Lexicon shape (single object, extensible)

verbs (canonical + synonyms)
nouns (canonical + synonyms, optional category tag)
prepositions
conjunctions
particles (optional)
stopwords (optional)
ParsedSyntax shape (include future fields now)

raw_text
normalized_text
tokens
token_spans
verb_candidates
primary_verb
noun_candidates
object_phrases
prep_phrases
conjunction_groups
unknown_tokens
diagnostics
Note: In early stages, some fields may be empty placeholders, but they should still exist.

Responsibilities (In Scope)

Normalize and tokenize text
Match vocabulary entries against tokens
Return structured syntax evidence with positions
Preserve unknown words for resolver/main decisions
Non-Responsibilities (Out of Scope)

No object lookup in world state
No disambiguation decisions
No direction semantics or implicit command rewriting
No user-facing error message generation
No game-state mutation
Stage 1 Behavior (Current Target)

Single-token matching only
Detect verbs and nouns from provided lexicon
Provide primary verb candidate if present
Return unknown tokens and spans
Populate future fields minimally (empty lists where not implemented yet)
Resolver Boundary

Resolver consumes ParsedSyntax and world context to produce semantic intent.
Resolver owns:

direct/indirect object interpretation
direction interpretation
ambiguity handling
command intent shaping for verbs
Parser should provide enough structure for resolver growth, without embedding semantics.

Compatibility Strategy

Keep development parser in parallel with existing runtime parser path.
Use adapter logic at integration boundaries, not inside parser core.
Preserve parser call signature from contract freeze onward.
Quality Criteria

Deterministic output for same text + same lexicon
Zero dependency on model/world globals
Structured output usable for resolver smoke testing
Stable contract that avoids repeated integration churn