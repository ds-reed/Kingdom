# Parser Refactor TODO (Unified + Updated for Interpreter Pipeline)

The parser produces **pure syntax** only.  
It outputs **List[ParsedAction]**, each representing one syntactic command fragment.  
The parser does **not** perform semantic interpretation, world lookup, ambiguity resolution, or ALL expansion.

This document defines the full parser roadmap.

---

# 0) Contract Freeze (Do First)

Freeze the parser’s public API and data structures before writing any logic.

## Parser API
```
parse(text, lexicon, options) -> List[ParsedAction]
```

The parser returns **zero, one, or many ParsedAction objects**, one per syntactic command fragment (e.g., “unlock and open trapdoor” → two ParsedActions).

## Lexicon Contract
A single caller‑supplied object containing:

- **verbs**: canonical name, synonyms, modifiers, uses_directions  
- **nouns**: canonical name, synonyms, adjectives (future), category tag (optional)  
- **directions**: canonical name, synonyms  
- **prepositions**: global list  
- **conjunctions**  
- **particles** (optional)  
- **stopwords** (optional)

Parser must not import or depend on world/model state.

## ParsedAction Contract (Updated)
All fields exist from Stage 0 onward, even if empty:

### Core fields
- `raw_text`  
- `normalized_text`  
- `tokens[]`  
- `token_spans[]`  

### Verb fields
- `verb_candidates[]` — all matching verbs (canonical + synonyms)  
- `primary_verb` — canonical VerbEntry  
- `primary_verb_token` — the token the user typed  
- `primary_verb_canonical` — canonical verb name  

### Noun + phrase fields
- `noun_candidates[]`  
- `object_phrases[]` — syntactic noun phrases  
- `prep_phrases[]` — syntactic prepositional phrases  
- `conjunction_groups[]` — syntactic grouping only  

### Direction + modifier fields
- `direction_tokens[]` — raw direction tokens  
- `modifier_tokens[]` — raw modifier tokens (syntax only)  

### Other fields
- `unknown_tokens[]`  
- `diagnostics[]`  

## Acceptance
- Parser has **zero world/model imports**  
- Parser API signature is stable for all future stages  
- Interpreter and main loop can evolve without parser changes  

---

# 0.5) Build Test Harness + Challenge Corpus

- Create a frozen test lexicon (dummy verbs, nouns, prepositions, conjunctions, stopwords)
- Create a frozen challenge corpus (100 natural player commands)
- Create a test harness runner that:
  - loads the test lexicon  
  - runs each command through the parser  
  - compares ParsedAction output to expected results  
  - supports stage‑aware validation (only check fields relevant to current stage)  
  - prints clear diffs for mismatches  
- Add a ParsedAction pretty‑printer  
- Add diagnostics capture  
- Add optional golden‑file mode  
- Ensure harness is independent of world/model state  
- Ensure harness remains stable across all parser stages  

Acceptance:
- Stage‑1 tests run with dummy parser  
- Harness supports incremental development  
- Corpus and lexicon remain frozen for Stage 6 diff‑logging  

---

## Stage 1 — Minimal Syntax Extraction

Stage 1 produces the smallest stable syntactic structure needed for later phases. It performs no grouping, no semantic inference, and no multi‑token interpretation. Every decision is based strictly on the lexicon.

### Responsibilities
- Normalize input (lowercase, trim).
- Tokenize and compute character spans.
- Classify each token using only the lexicon:
  - **Verb** if the token appears in `lexicon.token_to_verb` (canonical verbs + synonyms).
  - **Noun** if the token appears in `lexicon.token_to_noun` (canonical nouns only).
  - **Direction** if the token appears in `lexicon.token_to_direction`.
  - **Modifier** only if it appears in the **primary verb’s** declared modifier list.
  - **Unknown** otherwise (adjectives, particles, prepositions, conjunctions, plural nouns, unrecognized verbs, etc.).
- Identify the **primary verb** (first recognized verb).
- Populate Stage 1 fields on the ParsedAction:
  - `tokens`, `token_spans`
  - `verb_candidates` (canonical forms)
  - `noun_candidates`
  - `direction_tokens`
  - `modifier_tokens`
  - `unknown_tokens`
  - `primary_verb_token`
  - `primary_verb_canonical`

### Guarantees
- Deterministic output.
- No world access.
- Strict lexicon boundaries (no inference).
- Single‑token verb model (multi‑word verbs not recognized).
- Syntax‑only; no phrase grouping or prepositional structure.

---

## Stage 2 — Phrase Grouping and Conjunctions

Stage 2 transforms the flat Stage 1 token stream into structured noun phrases and conjunction chains. It still performs no semantic interpretation and does not resolve roles like direct/indirect objects.

### Responsibilities
- Identify noun phrases (NPs):
  - Skip particles (“the”, “a”, “an”).
  - Collect adjectives (unknown tokens before a noun).
  - Identify head nouns using `lexicon.token_to_noun`.
- Detect conjunction chains:
  - NP1 **and** NP2 → record both NPs and a conjunction group.
- Detect prepositional phrases syntactically:
  - Preposition + NP → record as a prepositional phrase.
  - No semantic role assignment (e.g., not deciding “to the elf” is an indirect object).
- Populate Stage 2 fields:
  - `object_phrases`
  - `conjunction_groups`
  - `prepositional_phrases`

### Guarantees
- Purely syntactic grouping; no meaning inferred.
- Preserves token order and spans.
- Handles multiple NPs and conjunction chains.
- Prepositions recognized only by membership in `lexicon.prepositions`.

---

## Stage 3 — Prepositions, Modifiers, and Direction Enrichment

Stage 3 enriches the Stage 2 structure with additional syntactic information. It still performs no semantic interpretation and does not resolve ambiguous cases.

### Responsibilities
- Identify prepositional phrases in final form:
  - Preposition + NP → `{ prep, object }`.
- Identify direction tokens using `lexicon.token_to_direction`.
- Identify modifiers using the **global** modifier list (`lexicon.modifiers`).
- Preserve ambiguity:
  - Tokens like “in”, “up”, “inside”, “through” may be both prepositions and directions; Stage 3 records all applicable classifications.
- Populate Stage 3 fields:
  - `prep_phrases`
  - `direction_tokens`
  - `modifier_tokens`

### Guarantees
- No semantic role assignment (e.g., “give X to Y” is not interpreted).
- No resolution of ambiguous prepositions/directions.
- Provides enough structure for the interpreter to handle:
  - “look in box”
  - “go in box”
  - “take all in the bag”
  - “enter in” (ambiguous)

---


# 3.5) Develop Interpreter (formerly Semantic Resolver)

Before moving further in parser development, implement the Interpreter:

- Converts ParsedAction → zero/one/many ResolvedCommands  
- Handles ambiguity  
- Handles ALL expansion  
- Handles direction interpretation  
- Handles prepositional semantics  
- Enforces verb argument rules  

Parser remains unchanged.

---

# 4) Stage 4: Interpreter Integration (No Parser Changes)

Wire the new parser into the Interpreter pipeline.

## Responsibilities
- Feed ParsedActions into Interpreter  
- Interpreter handles:
  - noun resolution  
  - direction interpretation  
  - ambiguity resolution  
  - modifier semantics  
  - indirect objects  
  - implicit actions  
- Parser remains unchanged  

## Acceptance
- Main loop consumes ResolvedCommands  
- Parser API unchanged from Stage 0  

---

# 5) Stage 5: Multiword + Synonym Support

Add richer lexeme matching.

## Responsibilities
- Greedy longest‑match for multiword verbs/nouns  
- Normalize synonyms in metadata  
- Preserve raw tokens for debugging  

## Acceptance
- Multiword lexemes behave as single syntax units  
- Unknown token behavior unchanged  

---

# 6) Stage 6: Parallel Run + Diff Logging

Run old and new parsers side‑by‑side.

## Responsibilities
- Behind a debug flag, run both parsers  
- Log diffs for curated command corpus  
- Triage mismatches  

## Acceptance
- New parser reaches behavioral parity  
- No regressions in gameplay  

---

# 7) Stage 7: Cutover + Cleanup

Switch fully to the new parser.

## Responsibilities
- Replace old parser path  
- Remove adapters + transitional code  
- Keep test harness + corpus for regression  

## Acceptance
- Gameplay sanity checks pass  
- No dead parser code remains  

---

# Lexicon Contract (Updated)

A single object passed into the parser:

- verbs: canonical name, synonyms, modifiers, uses_directions  
- nouns: canonical name, synonyms, adjectives (future), category tag (optional)  
- directions: canonical name, synonyms  
- prepositions: global list  
- conjunctions  
- particles (optional)  
- stopwords (optional)

Parser must not depend on world state or global registries.

---

# ParsedAction Contract (Updated)

All fields exist from Stage 0 onward:

### Core
- raw_text  
- normalized_text  
- tokens[]  
- token_spans[]  

### Verb fields
- verb_candidates[]  
- primary_verb  
- primary_verb_token  
- primary_verb_canonical  

### Noun + phrase fields
- noun_candidates[]  
- object_phrases[]  
- prep_phrases[]  
- conjunction_groups[]  

### Direction + modifier fields
- direction_tokens[]  
- modifier_tokens[]  

### Other fields
- unknown_tokens[]  
- diagnostics[]  

