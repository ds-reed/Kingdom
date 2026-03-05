# lexicon.py

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

from kingdom.model.verb_model import Verb

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
#def lex(noun_registry, verb_registry,
#       prepositions, conjunctions, particles, stopwords) -> Lexicon:

def lex() -> Lexicon:

    # -----------------------------
    # Build verb entries
    # -----------------------------

    all_tokens = Verb._by_name.keys()


    verb_entries = []

    for token in all_tokens:
        verb = Verb.get_by_name(token)
        verb_entries.append({
            "canonical": verb.canonical_name(),
            "aliases": list(verb.synonym_names()),
            "modifiers": list(verb.modifiers),
            "uses_directions": verb.uses_directions,
        })

    print(f"Registered {len(verb_entries)} unique verbs.")
    print(f"Verbs: {[entry['canonical'] for entry in verb_entries]}")

    return Lexicon(
            verbs=[ verb_entry for verb_entry in verb_entries ],
            nouns=[],  # TODO: build noun entries from game data
            prepositions=["in", "on", "under", "with", "at", "to", "from", "into", "onto", "off"],
            conjunctions=["and", "or", "but"],
            particles=["the", "a", "an"],
            stopwords=[]
    )

