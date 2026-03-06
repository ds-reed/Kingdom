# lexicon.py

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

from kingdom.model.noun_model import DirectionNoun, Noun
from kingdom.model.verb_model import Verb

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    aliases: List[str]
    modifiers: List[str] = field(default_factory=list)
    uses_directions: bool = False

    def __repr__(self):
        return f"VerbEntry(canonical={self.canonical}, aliases={self.aliases}, modifiers={self.modifiers}, uses_directions={self.uses_directions}\n)"

@dataclass(frozen=True)
class NounEntry:
    handle: str
    canonical: str
    display: str
    aliases: List[str]
    category: Optional[str] = None   # "item", "feature", "room", etc.

    def __repr__(self):
        return f"NounEntry(handle={self.handle}, canonical={self.canonical}, display={self.display}, aliases={self.aliases}, category={self.category} \n)"


@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    prepositions: List[str]
    conjunctions: List[str]
    particles: List[str]
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
        verb_entries.append(VerbEntry(
            canonical=verb.canonical_name(),
            aliases=list(verb.synonym_names()),
            modifiers=list(verb.modifiers),
            uses_directions=verb.uses_directions,
        ))

    print(f"Built {len(verb_entries)} verb entries")
    token_to_verb = {}

    for entry in verb_entries:
        # canonical
        token_to_verb[entry.canonical] = entry

        # synonyms
        for syn in entry.aliases:
            token_to_verb[syn] = entry

    print(f"Built token_to_verb mapping with {len(token_to_verb)} entries")


    # -----------------------------
    # Build NOUN entries
    # -----------------------------

    all_tokens = [
    token
    for token, noun in Noun._by_name.items()
    if noun.get_class_name() != "DirectionNoun"
]

    noun_entries = []

    for token in all_tokens:
        noun = Noun.get_by_name(token)
        noun_entries.append(NounEntry(
            handle=noun.handle,
            canonical=noun.canonical_name(),
            display=noun.display_name(),
            aliases=list(noun.synonym_names()),
            category=noun.get_class_name(),
        ))

    print(f"Built {len(noun_entries)} noun entries")
    print(noun_entries)

    token_to_noun = {}

    for entry in noun_entries:
        # canonical
        token_to_noun[entry.canonical] = entry

        # synonyms
        for syn in entry.aliases:
            token_to_noun[syn] = entry

    print(f"Built token_to_noun mapping with {len(token_to_noun)} entries")


 
    return Lexicon(
            verbs=[ verb_entry for verb_entry in verb_entries ],
            nouns=[ noun_entry for noun_entry in noun_entries ],
            prepositions=["in", "on", "under", "with", "at", "to", "from", "into", "onto", "off"],
            conjunctions=["and", "or", "but"],
            particles=["the", "a", "an"],
            token_to_verb=token_to_verb,  # TODO: build mapping from all verb tokens to their entries
            token_to_noun=token_to_noun,  # TODO: build mapping from all noun tokens to their entries
    )

