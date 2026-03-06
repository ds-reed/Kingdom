# dummy_lexicon.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ------------------------------------------------------------
# Lexicon Entry Types
# ------------------------------------------------------------

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    aliases: List[str]
    modifiers: List[str] = field(default_factory=list)
    uses_directions: bool = False

@dataclass(frozen=True)
class NounEntry:
    canonical: str
    aliases: List[str]
    category: Optional[str] = None  # item, feature, etc.

@dataclass(frozen=True)
class DirectionEntry:
    canonical: str
    aliases: List[str]

@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    directions: List[DirectionEntry]
    prepositions: List[str]
    conjunctions: List[str]
    particles: List[str]
    token_to_verb: Dict[str, VerbEntry]
    token_to_noun: Dict[str, NounEntry]
    token_to_direction: Dict[str, DirectionEntry]


# ------------------------------------------------------------
# Dummy Lexicon Builder
# ------------------------------------------------------------

def build_dummy_lexicon() -> Lexicon:

    # -----------------------------
    # Verbs (canonical + synonyms)
    # -----------------------------
    verbs = [
        VerbEntry("go", ["walk", "move"], uses_directions=True),
        VerbEntry("look", ["examine", "inspect"]),
        VerbEntry("take", ["grab", "pick", "pick up"]),
        VerbEntry("drop", []),
        VerbEntry("inventory", ["inv"]),
        VerbEntry("put", []),
        VerbEntry("talk", ["speak"]),
        VerbEntry("ask", []),
        VerbEntry("say", []),
        VerbEntry("attack", ["hit", "strike"]),
        VerbEntry("sharpen", []),
    ]

    token_to_verb = {}
    for v in verbs:
        token_to_verb[v.canonical] = v
        for a in v.aliases:
            token_to_verb[a] = v


    # -----------------------------
    # Nouns (canonical + synonyms)
    # -----------------------------
    nouns = [
        NounEntry("lamp", []),
        NounEntry("all", []),
        NounEntry("sword", []),
        NounEntry("shield", []),
        NounEntry("table", []),
        NounEntry("statue", []),
        NounEntry("drawer", []),
        NounEntry("door", []),
        NounEntry("bag", []),
        NounEntry("everything", []),
        NounEntry("chest", []),
        NounEntry("apple", []),
        NounEntry("basket", []),
        NounEntry("guard", []),
        NounEntry("wizard", []),
        NounEntry("amulet", []),
        NounEntry("hello", []),
        NounEntry("troll", []),
        NounEntry("knife", []),
    ]

    token_to_noun = {}
    for n in nouns:
        token_to_noun[n.canonical] = n
        for a in n.aliases:
            token_to_noun[a] = n


    # -----------------------------
    # Directions
    # -----------------------------
    directions = [
        DirectionEntry("north", []),
        DirectionEntry("through", []),  # ambiguous
        DirectionEntry("inside", []),  # ambiguous
    ]

    token_to_direction = {}
    for d in directions:
        token_to_direction[d.canonical] = d
        for a in d.aliases:
            token_to_direction[a] = d


    # -----------------------------
    # Prepositions, Conjunctions, Particles
    # -----------------------------
    prepositions = [
        "in", "on", "under", "with", "at", "to", "from",
        "into", "onto", "off", "about", "through", "inside"
    ]

    conjunctions = ["and", "or"]
    particles = ["the", "a", "an"]


    # -----------------------------
    # Final Lexicon Object
    # -----------------------------
    return Lexicon(
        verbs=verbs,
        nouns=nouns,
        directions=directions,
        prepositions=prepositions,
        conjunctions=conjunctions,
        particles=particles,
        token_to_verb=token_to_verb,
        token_to_noun=token_to_noun,
        token_to_direction=token_to_direction,
    )
