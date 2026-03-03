## Parser Refactor TODO (Draft) ##   
Goal: build a syntax-only parser in parallel, with a stable contract that supports final-stage resolver behavior without changing function signatures later.

0) Contract Freeze (Do First)
-  Freeze parser entrypoint: parse(text, lexicon, options) -> ParsedSyntax
-  Freeze lexicon input object shape (single object, caller-supplied)
-  Freeze output packet fields (include future fields now, even if empty at first)
- Confirm parser has no model/world imports  
    Acceptance 
    - Parser API signature is considered stable for all stages below
    - Main/resolver integration can evolve without parser call changes
---
1) Stage 1: Minimal Syntax Extraction  
- Normalize and tokenize text  
- Match known verbs (single-token only)  
- Match known nouns (single-token only)  
- Return unknown tokens  
- Return token spans/positions  
    Acceptance   
    - Deterministic output for same input + same lexicon  
    - No world-state access  
    - Useful packet for resolver smoke tests  
---
2) Stage 2: Phrase Grouping + Conjunctions
- Group noun candidates into object phrase units
- Detect conjunction chains (e.g., “banana and fish”)
-  Preserve ordering and token spans  
    Acceptance  
    - Resolver can distinguish one object vs multiple objects from packet alone  
---
3) Stage 3: Preposition Structure
 - Detect prepositions (in, at, through, to, from, etc.)
 - Build prepositional phrase attachments
 - Keep parse structural only (no semantic role decisions yet)  
    Acceptance  
    - Resolver gets enough structure for “go through east door” / “look at west wall”  
---
4) Stage 4: Multiword + Alias Support
- Add multiword lexeme matching (greedy longest-match)
- Add alias normalization hooks in parser output metadata
- Keep raw token trace for debugging  
    Acceptance
    - Multiword nouns/verbs resolve as one syntax unit
    - Unknown token behavior remains stable
---
5) Stage 5: Resolver Integration (No Parser API Changes)
- Feed parser packet into resolver
- Move semantic work to resolver (implicit direction handling, object selection,ambiguity)
- Keep parser unaware of item/room/direction semantics  
    Acceptance
    - Main consumes resolver output contract, not parser internals  
    - Parser call signature unchanged from Stage 0  
---
6) Stage 6: Parallel Run + Diff Logging
- Run old parser and new parser in parallel behind debug flag
- Log parse diffs for curated command corpus
- Triage behavior mismatches before cutover   
    Acceptance  
    - New parser reaches parity for target command set  
    - No user-facing regressions in normal flow  
---
7) Stage 7: Cutover and Cleanup
- Switch runtime to new parser + resolver path
- Remove transitional adapters and duplicate paths
- Keep smoke harness and corpus for regression checks 
    Acceptance  
    - Demo and gameplay sanity checks pass  
    - No dead parser code paths remain  

---
**Lexicon Contract (Draft)**  
verbs: entries with canonical + aliases  
nouns: entries with canonical + aliases (+ optional category tag for future)  
- prepositions
- conjunctions
- particles (optional)
- stopwords (optional)
Note: category tags can be optional now, but field should exist in contract.
---
**ParsedSyntax Contract (Draft)**
- raw_text
- normalized_text
- tokens[]