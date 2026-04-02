from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from kingdom.language.lexicon import Lexicon, VerbEntry
from typing import Any, List, Optional, Tuple

TokenSpan = Tuple[int, int]  # (start_index_in_text, end_index_exclusive)


@dataclass
class ParsedAction:
    # Core text + tokens
    raw_text: str = ""
    tokens: List[str] = field(default_factory=list)

    # Verb fields
    primary_verb: Optional[VerbEntry] = None
    primary_verb_token: Optional[str] = None
    verb_source: Optional[str] = None

    # Noun + phrase fields
    object_phrases: List[Any] = field(default_factory=list)   # Stage 2+
    prep_phrases: List[Any] = field(default_factory=list)     # Stage 3+
    conjunction_groups: List[Any] = field(default_factory=list)

    # Direction + modifier fields
    direction_tokens: List[str] = field(default_factory=list)
    modifier_tokens: List[str] = field(default_factory=list)

    # Other fields
    unknown_tokens: List[str] = field(default_factory=list)


    def __repr__(self): 
        return f"ParsedAction(raw_text='{self.raw_text}', tokens={self.tokens}, \n \
        primary_verb={self.primary_verb.canonical if self.primary_verb else None}, \n \
        verb_source={self.verb_source}, \n \
        primary_verb_token={self.primary_verb_token}, \n \
        prep_phrases={self.prep_phrases}, conjunction_groups={self.conjunction_groups}, \n \
        direction_tokens={self.direction_tokens}, \n \
        modifier_tokens={self.modifier_tokens}, \n \
        unknown_tokens={self.unknown_tokens}, \n"


def parse(text: str, lexicon: Lexicon) -> list[ParsedAction]:

    def is_noun(tok): return tok in lexicon.token_to_noun
    def is_verb(tok): return tok in lexicon.token_to_verb
    def is_direction(tok): return tok in lexicon.token_to_direction
    def is_preposition(tok): return tok in lexicon.token_to_preposition
    def is_conjunction(tok): return tok in lexicon.conjunctions
    def is_particle(tok): return tok in lexicon.particles
    def is_modifier(tok): return tok in lexicon.modifiers
    def is_unknown(tok): return (
        tok not in lexicon.token_to_noun and
        tok not in lexicon.token_to_verb and
        tok not in lexicon.token_to_direction and
        tok not in lexicon.token_to_preposition and
        tok not in lexicon.conjunctions and
        tok not in lexicon.particles and
        tok not in lexicon.modifiers
        )

    def stage1_tokenizing():

        # 1. Normalize
        normalized = text.strip().lower()

        # Strip punctuation that breaks lexicon matching, but keep hyphens and apostrophes
        # Removes: , . ! ? ; :
        import re
        normalized = re.sub(r"[.,!?;:]", "", normalized)

        ps.normalized_text = normalized

        # 2. Tokenize 
        tokens = normalized.split() if normalized else []
        ps.tokens = tokens



        #  Classify each token
        verb_candidates = []
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
            matched_any = False
            if v:
                matched_any = True
                verb_entries.append(v)
                if primary_verb_entry is None:
                    primary_verb_entry = v
                    primary_verb_token = tok
                    
            # Noun? Stage 1 should only classify token type, not bind noun entries.
            if is_noun(tok):
                matched_any = True


            # Direction?
            d = lexicon.token_to_direction.get(tok)
            if d:
                direction_tokens.append(d.canonical)           # always canonicalize directions - we match by canonical name in the verb handlers.
                matched_any = True


            # Modifier? (only if we already know the primary verb)
            # Stage 1 rule: modifiers only come from the primary verb’s modifier list.
            if primary_verb_entry and tok in primary_verb_entry.modifiers:
                modifier_tokens.append(tok)
                matched_any = True


            # Unknown
            if not matched_any:
                unknown_tokens.append(tok)


        # Populate ParsedAction fields
        ps.direction_tokens = direction_tokens
        ps.modifier_tokens = modifier_tokens
        ps.unknown_tokens = unknown_tokens


        # Determine verb source
        verb_source = None
        raw_verb_token = None

        if primary_verb_entry is not None:
            verb_source = "explicit"
            raw_verb_token = primary_verb_token

        elif ps.tokens:
            first = ps.tokens[0]

            if first in ps.direction_tokens:
                verb_source = "implicit"
                raw_verb_token = None

            elif len(ps.tokens) == 1 and is_noun(first):
                verb_source = "implicit"
                raw_verb_token = None

            elif first in ps.unknown_tokens:
                verb_source = "unknown"
                raw_verb_token = first

            else:
                verb_source = "unknown"
                raw_verb_token = first
        else:
            verb_source = None
            raw_verb_token = None

        ps.verb_source = verb_source

        # Stage 1 output format
        ps.primary_verb = primary_verb_entry                           # full object
        ps.primary_verb_token = primary_verb_token or raw_verb_token   # string

    def stage2_phrase_grouping():
        """
        Stage 2: Convert flat Stage 1 tokens into:
        - object_phrases: list of noun phrases
        - conjunction_groups: list of [NP1.head, NP2.head]
        - prep_phrases: list of {preposition, object}

        Tokens are plain strings. Classification is done via lexicon maps/lists.
        """

        object_phrases = []
        conjunction_groups = []
        prep_phrases = []
        tokens = ps.tokens

        i = 0
        n = len(tokens)

        # ------------------------------------------------------------
        # Index variable guide:
        #
        #   i   = main scan index (current token being examined)
        #   i2  = index immediately AFTER the first noun phrase (NP1)
        #   i3  = index immediately AFTER the conjunction ("and"), start of NP2
        #   i4  = index immediately AFTER the second noun phrase (NP2)
        #
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


            head = None
            
            # Special case: quantifiers like "all" behave as NP heads
            if i < n and tokens[i] in ("all", "everything"):
                head = tokens[i]
                i += 1
                return {
                    "head": head,
                    "adjectives": [],
                    "span": (start, i),
                }, i

            if i < n and is_noun(tokens[i]):
                head = tokens[i]
                i += 1
            elif adjectives:
                head = adjectives.pop()  # Treat last unknown as noun-like head

            if head is None:
                return None, start

            # span end is EXCLUSIVE index of end of NP
            span = (start, i)
            return {
                "head": head,
                "adjectives": adjectives,
                "span": span,
            }, i

        # ------------------------------------------------------------
        # Main scan
        # ------------------------------------------------------------
        while i < n:
            t = tokens[i]

            # -------------------------
            # Prepositional phrase
            # -------------------------
            if is_preposition(t):
                canonical_list = lexicon.token_to_preposition.get(t, [])
                prep = canonical_list[0] if canonical_list else t

                i += 1
                np, i2 = consume_noun_phrase(i)

                # Always record the preposition, even if no object follows
                prep_phrases.append({
                    "preposition": prep,
                    "object": np,
                })

                # Only advance past the noun phrase if one was found
                if np:
                    object_phrases.append(np)
                    i = i2
                else:
                    # No NP → just move past the preposition
                    # (i already incremented by 1 above)
                    pass

                continue


            # -------------------------
            # Noun phrase (possibly NP1 AND NP2)
            # -------------------------
            if (is_particle(t) or is_noun(t) or (is_unknown(t) and not is_conjunction(t)) or t in ("all", "everything")):     #treat all or everything as noun-like heads for phrase grouping
  
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
            

        ps.prep_phrases = prep_phrases
        ps.object_phrases = object_phrases
        ps.conjunction_groups = conjunction_groups 

        return  

    def stage3_enrich():
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

        tokens = ps.tokens
        n = len(tokens)

        prep_phrases = []
        direction_tokens = []
        modifier_tokens = []


        # ------------------------------------------------------------
        # Minimal NP consumer (for prepositional objects)
        # We only care about the head noun string.
        # ------------------------------------------------------------
        def consume_noun_phrase(i):
            # Skip particles/determiners
            while i < n and is_particle(tokens[i]):
                i += 1

            # Skip adjectives (unknowns before noun)
            adjectives = []
            while i < n and is_unknown(tokens[i]):
                adjectives.append(tokens[i])
                i += 1

            head = None
            if i < n and is_noun(tokens[i]):
                head = tokens[i]
                i += 1
            elif adjectives:
                head = adjectives.pop()  # Treat last unknown as noun-like head

            return head, i

        # ------------------------------------------------------------
        # Main scan for phase 3
        # ------------------------------------------------------------
        i = 0
        while i < n:
            t = tokens[i]
            next_i = i + 1

            # Canonicalize prep phrases from phase 2
            prep_phrases = []
            for pp in ps.prep_phrases:
                prep = pp["preposition"]
                np = pp["object"]

                # Canonicalize the preposition
                canonical_list = lexicon.token_to_preposition.get(prep, [])
                canonical = canonical_list[0] if canonical_list else prep

                # Extract the head noun string (Stage 2 NP dict → string)
                if np is None:
                    head = None
                else:
                    head = np["head"]  

                prep_phrases.append({
                    "prep": canonical,
                    "object": head,
                })


            if is_direction(t):
                direction_tokens.append(t)          

            if t in lexicon.modifiers:
                modifier_tokens.append(t)

            i = next_i

        # ------------------------------------------------------------
        # Write back to ParsedAction
        # ------------------------------------------------------------
        ps.prep_phrases = prep_phrases
        ps.direction_tokens = direction_tokens
        ps.modifier_tokens = modifier_tokens



#---------------------------------------------------------
#                    Main Parser Flow
#---------------------------------------------------------

    ps_return = []
    ps_return.append(ParsedAction(raw_text=text))
    ps = ps_return[0]

    stage1_tokenizing()

    stage2_phrase_grouping()

    stage3_enrich()

    return ps_return




