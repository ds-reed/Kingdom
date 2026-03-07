# parser/parser.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any

from .types import ParsedAction, Diagnostic

from kingdom.language.lexicon.lexicon import Lexicon


@dataclass
class ParserOptions:
    stage: int = 1
    debug: bool = False


def parse(text: str, lexicon: Lexicon, options: Optional[ParserOptions] = None) -> list[ParsedAction]:
    if options is None:
        options = ParserOptions()

    ps_return = []
    ps_return.append(ParsedAction(raw_text=text))
    ps = ps_return[0]

    # ------------------------------------------------------------
    # 1. Normalize
    # ------------------------------------------------------------
    normalized = text.strip().lower()

    # Strip punctuation that breaks lexicon matching, but keep hyphens and apostrophes
    # Removes: , . ! ? ; :
    import re
    normalized = re.sub(r"[.,!?;:]", "", normalized)

    ps.normalized_text = normalized

    # ------------------------------------------------------------
    # 2. Tokenize 
    # ------------------------------------------------------------
    tokens = normalized.split() if normalized else []
    ps.tokens = tokens


    # ------------------------------------------------------------
    # 3. Stage 1: classify each token
    # ------------------------------------------------------------
    verb_candidates = []
    noun_candidates = []
    direction_tokens = []
    modifier_tokens = []
    unknown_tokens = []

    # We will fill this after scanning tokens
    primary_verb_entry = None
    primary_verb_token = None

    # Collect full VerbEntry objects
    verb_entries = []

    for tok in tokens:
        v = lexicon.token_to_verb.get(tok)
        if v:
            verb_entries.append(v)
            if primary_verb_entry is None:
                primary_verb_entry = v
                primary_verb_token = tok
            continue


        # Noun?
        n = lexicon.token_to_noun.get(tok)
        if n:
            noun_candidates.append(n)
            continue

        # Direction?
        d = lexicon.token_to_direction.get(tok)
        if d:
            direction_tokens.append(tok)
            continue

        # Modifier? (only if we already know the primary verb)
        # Stage 1 rule: modifiers only come from the primary verb’s modifier list.
        if primary_verb_entry and tok in primary_verb_entry.modifiers:
            modifier_tokens.append(tok)
            continue

        # Unknown
        unknown_tokens.append(tok)

    # ------------------------------------------------------------
    # 4. Populate ParsedAction fields
    # ------------------------------------------------------------
    ps.verb_candidates = verb_candidates
    ps.noun_candidates = noun_candidates
    ps.direction_tokens = direction_tokens
    ps.modifier_tokens = modifier_tokens
    ps.unknown_tokens = unknown_tokens

    # Stage 1 output format
    ps.verb_candidates = [v.canonical for v in verb_entries]

    ps.primary_verb = primary_verb_entry          # full object
    ps.primary_verb_token = primary_verb_token    # string
    ps.primary_verb_canonical = (
        primary_verb_entry.canonical if primary_verb_entry else None
        )



    # ------------------------------------------------------------
    # 5. Stage 2: phrase grouping (noun phrases, prepositions, conjunctions)
    # ------------------------------------------------------------
    if options.stage >= 2:
        obj_phrases, conj_groups, prep_phrases = stage2_phrase_grouping(
            tokens=ps.tokens,
            lexicon=lexicon
        )
        ps.object_phrases = obj_phrases
        ps.conjunction_groups = conj_groups
        ps.prepositional_phrases = prep_phrases

    # ------------------------------------------------------------
    # 6. Stage 3: enrich parsed syntax with additional information
    # ------------------------------------------------------------

    if options.stage >= 3:
        stage3_enrich(ps, lexicon)


    return ps_return



def stage2_phrase_grouping(tokens, lexicon):
    """
    Stage 2: Convert flat Stage 1 tokens into:
      - object_phrases: list of noun phrases
      - conjunction_groups: list of [NP1.head, NP2.head]
      - prepositional_phrases: list of {preposition, object}

    Tokens are plain strings. Classification is done via lexicon maps/lists.
    """

    object_phrases = []
    conjunction_groups = []
    prepositional_phrases = []

    i = 0
    n = len(tokens)

    # ------------------------------------------------------------
    # Token classification helpers
    # ------------------------------------------------------------
    def is_noun(tok: str) -> bool:
        return tok in lexicon.token_to_noun

    def is_preposition(tok: str) -> bool:
        return tok in lexicon.prepositions

    def is_conjunction(tok: str) -> bool:
        return tok in lexicon.conjunctions

    def is_particle(tok: str) -> bool:
        return tok in lexicon.particles

    def is_unknown(tok: str) -> bool:
        return (
            tok not in lexicon.token_to_noun
            and tok not in lexicon.prepositions
            and tok not in lexicon.conjunctions
            and tok not in lexicon.particles
            and tok not in lexicon.token_to_verb
            and tok not in lexicon.token_to_direction
        )

    # ------------------------------------------------------------
    # Index variable guide:
    #
    #   i   = main scan index (current token being examined)
    #   i2  = index immediately AFTER the first noun phrase (NP1)
    #   i3  = index immediately AFTER the conjunction ("and"), start of NP2
    #   i4  = index immediately AFTER the second noun phrase (NP2)
    #
    # Example: "grab the sword and shield"
    #   tokens: 0:grab 1:the 2:sword 3:and 4:shield
    #
    #   i = 1  → "the"
    #   consume_noun_phrase(1) → NP1 = "the sword", i2 = 3
    #   tokens[i2] = "and"
    #   i3 = i2 + 1 = 4
    #   consume_noun_phrase(i3) → NP2 = "shield", i4 = 5
    #
    #   i = i4 = 5 → continue scanning
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # Noun phrase parser
    # ------------------------------------------------------------
    def consume_noun_phrase(i):
        start = i

        # Skip determiners/particles
        while i < n and is_particle(tokens[i]):
            i += 1
            start = i  # NP starts after particles

        adjectives = []

        # Collect adjectives (unknown tokens before a noun)
        while i < n and is_unknown(tokens[i]):
            adjectives.append(tokens[i])
            i += 1

        # Expect a noun
        if i < n and is_noun(tokens[i]):
            noun_index = i
            i += 1
            # span end is EXCLUSIVE index of end of NP
            span = (start, i)
            return {
                "head": tokens[noun_index],
                "adjectives": adjectives,
                "span": span,
            }, i

        return None, start

    # ------------------------------------------------------------
    # Main scan
    # ------------------------------------------------------------
    while i < n:
        t = tokens[i]

        # -------------------------
        # Prepositional phrase
        # -------------------------
        if is_preposition(t):
            prep = t
            i += 1
            np, i2 = consume_noun_phrase(i)
            if np:
                prepositional_phrases.append({
                    "preposition": prep,
                    "object": np,
                })
                object_phrases.append(np)  # required by harness
                i = i2
                continue
            else:
                continue

        # -------------------------
        # Noun phrase (possibly NP1 AND NP2)
        # -------------------------
        if is_particle(t) or is_noun(t) or (is_unknown(t) and not is_conjunction(t)):
            np1, i2 = consume_noun_phrase(i)
            if np1:

                # Check for conjunction: NP1 AND NP2
                if i2 < n and is_conjunction(tokens[i2]):
                    i3 = i2 + 1
                    np2, i4 = consume_noun_phrase(i3)
                    if np2:
                        conjunction_groups.append([np1["head"], np2["head"]])
                        object_phrases.append(np1)
                        object_phrases.append(np2)
                        i = i4
                        continue

                # Normal noun phrase
                object_phrases.append(np1)
                i = i2
                continue

        # -------------------------
        # Everything else → skip
        # -------------------------
        i += 1

    return object_phrases, conjunction_groups, prepositional_phrases

def stage3_enrich(parsed, lexicon):
    """
    Stage 3: Prepositions + Modifiers + Directions

    Assumes:
      - parsed.tokens is populated
      - Stage 2 has already run (object_phrases, etc.)
    Populates:
      - parsed.prep_phrases: [{'prep': <str>, 'object': <head_noun_str>}]
      - parsed.direction_tokens: [<str>, ...]
      - parsed.modifier_tokens: [<str>, ...]
    """

    tokens = parsed.tokens
    n = len(tokens)

    prep_phrases = []
    direction_tokens = []
    modifier_tokens = []

    # ------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------
    def is_noun(tok: str) -> bool:
        return tok in lexicon.token_to_noun

    def is_preposition(tok: str) -> bool:
        return tok in lexicon.prepositions

    def is_direction(tok: str) -> bool:
        return tok in lexicon.token_to_direction

    def is_conjunction(tok: str) -> bool:
        return tok in lexicon.conjunctions

    def is_particle(tok: str) -> bool:
        return tok in lexicon.particles

    def is_verb(tok: str) -> bool:
        return tok in lexicon.token_to_verb

    def is_unknown(tok: str) -> bool:
        return (
            tok not in lexicon.token_to_noun
            and tok not in lexicon.prepositions
            and tok not in lexicon.conjunctions
            and tok not in lexicon.particles
            and tok not in lexicon.token_to_verb
            and tok not in lexicon.token_to_direction
        )

    # ------------------------------------------------------------
    # Minimal NP consumer (for prepositional objects)
    # We only care about the head noun string.
    # ------------------------------------------------------------
    def consume_noun_phrase(i):
        # Skip particles/determiners
        while i < n and is_particle(tokens[i]):
            i += 1

        # Skip adjectives (unknowns before noun)
        while i < n and is_unknown(tokens[i]):
            i += 1

        # Expect noun
        if i < n and is_noun(tokens[i]):
            head = tokens[i]
            i += 1
            return head, i

        return None, i

    # ------------------------------------------------------------
    # Main scan for phase 3
    # ------------------------------------------------------------
    i = 0
    while i < n:
        t = tokens[i]
        next_i = i + 1

        if is_preposition(t):
            head, j = consume_noun_phrase(i + 1)
            if head is not None:
                prep_phrases.append({"prep": t, "object": head})
                next_i = j

        if is_direction(t):
            direction_tokens.append(t)

        if t in lexicon.modifiers:
            modifier_tokens.append(t)

        i = next_i

    # ------------------------------------------------------------
    # Write back to ParsedAction
    # ------------------------------------------------------------
    parsed.prep_phrases = prep_phrases
    parsed.direction_tokens = direction_tokens
    parsed.modifier_tokens = modifier_tokens
