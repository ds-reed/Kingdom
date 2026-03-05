# lexicon.py

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    aliases: List[str]
    modifiers: List[str] = field(default_factory=list)
    uses_directions: bool = False


@dataclass(frozen=True)
class NounEntry:
    handle: str
    canonical: str
    display: str
    aliases: List[str]
    category: Optional[str] = None   # "item", "feature", "room", etc.


@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    prepositions: List[str]
    conjunctions: List[str]
    particles: List[str]
    stopwords: List[str]

    # Optional: lookup tables for parser speed
    token_to_verb: Dict[str, VerbEntry] = field(default_factory=dict)
    token_to_noun: Dict[str, NounEntry] = field(default_factory=dict)



# ------------------------------------------------------------
# Main lex() function
# ------------------------------------------------------------
def lex(noun_registry, verb_registry,
        prepositions, conjunctions, particles, stopwords) -> Lexicon:

    # -----------------------------
    # Build verb entries
    # -----------------------------
    verb_entries: List[VerbEntry] = []
    for verb in verb_registry.all_verbs():
        verb_entries.append(
            VerbEntry(
                canonical=verb.canonical,
                aliases=verb.aliases,
                modifiers=verb.modifiers,
                uses_directions=verb.uses_directions,
            )
        )

    # -----------------------------
    # Build noun entries
    # -----------------------------
    noun_entries: List[NounEntry] = []
    for handle, meta in noun_registry.handle_metadata.items():
        noun_entries.append(
            NounEntry(
                handle=handle,
                canonical=meta["canonical"],
                display=meta["display"],
                aliases=noun_registry.get_aliases_for_handle(handle),
                category=noun_registry.get_category_for_handle(handle),
            )
        )

    # -----------------------------
    # Build lookup tables
    # -----------------------------
    token_to_verb: Dict[str, VerbEntry] = {}
    for v in verb_entries:
        # canonical
        token_to_verb[normalize_token(v.canonical)] = v
        # aliases
        for alias in v.aliases:
            token_to_verb[normalize_token(alias)] = v

    token_to_noun: Dict[str, NounEntry] = {}
    for n in noun_entries:
        # handle
        token_to_noun[normalize_token(n.handle)] = n
        # canonical
        token_to_noun[normalize_token(n.canonical)] = n
        # aliases
        for alias in n.aliases:
            token_to_noun[normalize_token(alias)] = n

    # -----------------------------
    # Return unified lexicon
    # -----------------------------
    return Lexicon(
        verbs=verb_entries,
        nouns=noun_entries,
        prepositions=prepositions,
        conjunctions=conjunctions,
        particles=particles,
        stopwords=stopwords,
        token_to_verb=token_to_verb,
        token_to_noun=token_to_noun,
    )
