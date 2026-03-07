# Parser Refactor TODO (Unified + Updated)

## 0) Contract Freeze (Do First)
Lock down the parser’s public API and data structures before writing any logic.

### Parser API
`parse(text, lexicon, options) -> ParsedSyntax`

### Lexicon Contract
Single caller‑supplied object containing:

- verbs: canonical name, synonyms, modifiers, uses_directions  
- nouns: canonical name, synonyms, adjectives (future), category tag (optional)  
- directions: canonical name, reverse, synonyms        (note directions will no longer be in the noun class or noun registry)
- prepositions: global list  
- conjunctions  
- particles (optional)  


Parser must not import or depend on world/model state.

### ParsedSyntax Contract
All fields exist from day one, even if empty:

- raw_text  
- normalized_text  
- tokens[]  
- token_spans[]  

### Verb fields  
- verb_candidates[] — all matching verbs (canonical + synonyms)  
- primary_verb — the canonical Verb object  
- primary_verb_token — the actual token the user typed (e.g., “grab” → maps to “take”)  
- primary_verb_canonical — the canonical verb name (“take”)  

### Noun + phrase fields  
- noun_candidates[]  
- object_phrases[]  
- prep_phrases[]  
- conjunction_groups[]  

### Direction + modifier fields  
- direction_tokens[] — raw direction tokens (syntax only)  
- modifier_tokens[] — raw modifier tokens (syntax only; based on verb.modifiers)  

### Other fields  
- unknown_tokens[]  
- diagnostics[]  

### Acceptance
- Parser has zero world/model imports  
- Parser API signature is stable for all future stages  
- Resolver and main loop can evolve without parser changes  

---
## 0.5) Build Test Harness + Challenge Corpus

- Create a frozen test lexicon (dummy verbs, dummy nouns, prepositions, conjunctions, stopwords)
- Create a frozen challenge corpus (100 natural player commands)
- Create a test harness runner that:
  - loads the test lexicon
  - runs each command through the parser
  - compares ParsedSyntax to expected results
  - supports stage‑aware validation (only check fields relevant to current stage)
  - prints clear diffs for mismatches
- Add a ParsedSyntax pretty‑printer for debugging
- Add a diagnostics capture and display mechanism
- Add optional golden‑file mode for approving complex expected results
- Ensure the harness is independent of world/model state
- Ensure the harness remains stable across all parser stages

Acceptance:
- Test harness runs all stage‑1 tests with dummy parser
- Harness supports incremental parser development without modification
- Corpus and lexicon are frozen and reusable for Stage 6 diff‑logging



## 1) Stage 1: Minimal Syntax Extraction
Build the smallest useful parser that respects the frozen contract.

### Responsibilities
- Normalize + tokenize  
- Identify verb candidates (single‑token only)  
- Identify noun candidates (single‑token only)  
- Identify direction tokens (syntax only)  
- Identify modifier tokens (syntax only; based on verb.modifiers)  
- Capture unknown tokens  
- Populate token spans  
- Populate `primary_verb_token` and `primary_verb_canonical`  

### Acceptance
- Deterministic output for same input + same lexicon  
- No world access  
- Resolver can smoke‑test basic commands  

---

## 2) Stage 2: Phrase Grouping + Conjunctions
Move from token lists to structured phrases.

### Responsibilities
- Group noun tokens into noun phrases  
- Attach adjectives (future)  
- Detect conjunction chains (“apple and banana and fish”)  
- Preserve ordering + spans  

### Acceptance
- Resolver can distinguish single vs multiple objects  
- ParsedSyntax expresses phrase boundaries clearly  

---

## 3) Stage 3: Preposition + Modifier Structure
Introduce syntactic structure without semantics.

### Responsibilities
- Detect prepositions (global list)  
- Detect verb‑declared modifiers (“in”, “with”, “all”, “everything”, etc.)  
- Build prepositional phrase structures  
- Preserve ambiguity (e.g., “in” as both direction + modifier)  
- No semantic role assignment  

### Acceptance
- Resolver receives enough structure for:  
  - “look in box”  
  - “go in box”  
  - “take all in the bag”  
  - “enter in” (ambiguous)  
- Parser remains semantics‑free  

---

## 4) Stage 4: Multiword + synonym Support
Add richer lexeme matching.

### Responsibilities
- Greedy longest‑match for multiword verbs/nouns  
- Normalize synonyms in metadata  
- Preserve raw tokens for debugging  

### Acceptance
- Multiword lexemes behave as single syntax units  
- Unknown token behavior unchanged  

---

## 5) Stage 5: Resolver Integration (No Parser Changes)
Wire the new parser into the resolver pipeline.

### Responsibilities
- Feed ParsedSyntax into resolver  
- Resolver handles:  
  - noun resolution  
  - direction interpretation  
  - ambiguity resolution  
  - modifier semantics  
  - indirect objects  
  - implicit actions  
- Parser remains unchanged  

### Acceptance
- Main loop consumes ResolvedAction, not parser internals  
- Parser API unchanged from Stage 0  

---

## 6) Stage 6: Parallel Run + Diff Logging
Run old and new parsers side‑by‑side.

### Responsibilities
- Behind a debug flag, run both parsers  
- Log diffs for curated command corpus  
- Triage mismatches  

### Acceptance
- New parser reaches behavioral parity for target command set  
- No regressions in normal gameplay  

---

## 7) Stage 7: Cutover + Cleanup
Switch fully to the new parser.

### Responsibilities
- Replace old parser path  
- Remove adapters + transitional code  
- Keep test harness + corpus for regression  

### Acceptance
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

# ParsedSyntax Contract (Updated)
All fields exist from Stage 0 onward:

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

