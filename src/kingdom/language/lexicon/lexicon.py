# lexicon.py

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

from kingdom.model.direction_model import NewDIRECTIONS
from kingdom.model.noun_model import Noun, DirectionRegistry, DIRECTIONS
from kingdom.model.verb_model import Verb

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    synonyms: List[str]
    modifiers: List[str] = field(default_factory=list)
    uses_directions: bool = False

    def __repr__(self):
        return f"VerbEntry(canonical={self.canonical}, synonyms={self.synonyms}, modifiers={self.modifiers}, uses_directions={self.uses_directions}\n)"

@dataclass(frozen=True)
class NounEntry:
    handle: str
    canonical: str
    display: str
    synonyms: List[str]
    category: Optional[str] = None   # "item", "feature", "room", etc.

    def __repr__(self):
        return f"NounEntry(handle={self.handle}, canonical={self.canonical}, display={self.display}, synonyms={self.synonyms}, category={self.category} \n)"

@dataclass(frozen=True)
class DirectionEntry:
    handle: str
    canonical: str
    reverse: str | None
    synonyms: List[str]


    def __repr__(self):
        return f"DirectionEntry(handle={self.handle}, canonical={self.canonical}, reverse={self.reverse}, synonyms={self.synonyms} \n)"

@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    directions: List[DirectionEntry]
    prepositions: List[str]
    conjunctions: List[str]
    particles: List[str]
    token_to_verb: Dict[str, VerbEntry] = field(default_factory=dict)
    token_to_noun: Dict[str, NounEntry] = field(default_factory=dict)
    token_to_direction: Dict[str, DirectionEntry] = field(default_factory=dict)

    def __repr__(self):
        return f"Lexicon(verbs={self.verbs}, nouns={self.nouns}, directions={self.directions}, prepositions={self.prepositions}, conjunctions={self.conjunctions}, particles={self.particles})"



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
            synonyms=list(verb.synonym_names()),
            modifiers=list(verb.modifiers),
            uses_directions=verb.uses_directions,
        ))

    print(f"Built {len(verb_entries)} verb entries")
    token_to_verb = {}

    for entry in verb_entries:
        # canonical
        token_to_verb[entry.canonical] = entry

        # synonyms
        for syn in entry.synonyms:
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
            synonyms=list(noun.synonym_names()),
            category=noun.get_class_name(),
        ))

    print(f"Built {len(noun_entries)} noun entries")

    token_to_noun = {}

    for entry in noun_entries:
        # canonical
        token_to_noun[entry.canonical] = entry

        # synonyms
        for syn in entry.synonyms:
            token_to_noun[syn] = entry

    print(f"Built token_to_noun mapping with {len(token_to_noun)} entries")

    # -----------------------------
    # Build DIRECTION entries
    # -----------------------------

    all_directions = NewDIRECTIONS.get_all_directions()
    direction_entries = []
    for canonical in all_directions:
        info = NewDIRECTIONS.data[canonical]
        direction_entries.append(DirectionEntry(
            handle=canonical,
            canonical=canonical,
            reverse=info["reverse"],
            synonyms=info["synonyms"],

        ))

    print(f"Built {len(direction_entries)} direction entries")

    token_to_direction = {}
    for entry in direction_entries:
        # canonical
        token_to_direction[entry.canonical] = entry

        # synonyms
        for syn in entry.synonyms:
            token_to_direction[syn] = entry

    print(f"Built token_to_direction mapping with {len(token_to_direction)} entries")
    print(token_to_direction)

    return Lexicon(
            verbs=[ verb_entry for verb_entry in verb_entries ],
            nouns=[ noun_entry for noun_entry in noun_entries ],
            directions=[ direction_entry for direction_entry in direction_entries ],
            prepositions=["in", "on", "under", "with", "at", "to", "from", "into", "onto", "off"],
            conjunctions=["and", "or", "but"],
            particles=["the", "a", "an"],
            token_to_verb=token_to_verb,  
            token_to_noun=token_to_noun,  
            token_to_direction=token_to_direction, 
    )

