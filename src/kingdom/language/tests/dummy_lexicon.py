# dummy_lexicon.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from kingdom.language.lexicon import lexicon

# ------------------------------------------------------------
# Lexicon Entry Types
# ------------------------------------------------------------

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    synonyms: List[str]
    modifiers: List[str]
    uses_directions: bool = False

@dataclass(frozen=True)
class NounEntry:
    handle: str
    canonical: str
    display: str
    synonyms: List[str]
    adjectives: List[str] 
    category: Optional[str] = None


@dataclass(frozen=True)
class DirectionEntry:
    handle: str
    canonical: str
    reverse: Optional[str]
    synonyms: List[str]


@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    directions: List[DirectionEntry]
    modifiers: List[str]
    adjectives: List[str]   
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
        VerbEntry(
            canonical="go",
            synonyms=["walk", "move"],
            modifiers=[],
            uses_directions=True
        ),
        VerbEntry(
            canonical="look",
            synonyms=["examine", "inspect"],
            modifiers=["in"],
            uses_directions=False
        ),
        VerbEntry(
            canonical="take",
            synonyms=["grab", "pick", "pick up"],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="drop",
            synonyms=[],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="inventory",
            synonyms=["inv"],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="put",
            synonyms=[],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="talk",
            synonyms=["speak"],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="ask",
            synonyms=[],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="say",
            synonyms=[],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="attack",
            synonyms=["hit", "strike"],
            modifiers=[],
            uses_directions=False
        ),
        VerbEntry(
            canonical="sharpen",
            synonyms=[],
            modifiers=[],
            uses_directions=False
        ),
    ]

    token_to_verb = {}
    for v in verbs:
        token_to_verb[v.canonical] = v
        for a in v.synonyms:
            token_to_verb[a] = v


    # -----------------------------
    # Nouns (canonical + synonyms)
    # -----------------------------
    nouns = [
        NounEntry(
            handle="lamp",
            canonical="lamp",
            display="Lamp",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="all",
            canonical="all",
            display="All",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="sword",
            canonical="sword",
            display="Sword",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="shield",
            canonical="shield",
            display="Shield",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="table",
            canonical="table",
            display="Table",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="statue",
            canonical="statue",
            display="Statue",
            synonyms=[],
            adjectives=["strange"]
        ),
        NounEntry(
            handle="drawer",
            canonical="drawer",
            display="Drawer",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="door",
            canonical="door",
            display="Door",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="bag",
            canonical="bag",
        display="Bag",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="everything",
            canonical="everything",
            display="Everything",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="chest",
            canonical="chest",
            display="Chest",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="apple",
            canonical="apple",
            display="Apple",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="basket",
            canonical="basket",
            display="Basket",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="guard",
            canonical="guard",
            display="Guard",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="wizard",
            canonical="wizard",
            display="Wizard",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="amulet",
            canonical="amulet",
            display="Amulet",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="hello",
            canonical="hello",
            display="Hello",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="troll",
            canonical="troll",
            display="Troll",
            synonyms=[],
            adjectives=[]
        ),
        NounEntry(
            handle="knife",
            canonical="knife",
            display="Knife",
            synonyms=["machete"],
            adjectives=["pearly-white"]
        ),
    ]

    token_to_noun = {}
    for n in nouns:
        token_to_noun[n.canonical] = n
        for a in n.synonyms:
            token_to_noun[a] = n


    # -----------------------------
    # Directions
    # -----------------------------
    directions = [
        DirectionEntry("north", "north", "south", []),
        DirectionEntry("through", "through", "through", []),  # ambiguous
        DirectionEntry("inside", "inside", "outside", []),  # ambiguous
    ]

    token_to_direction = {}
    for d in directions:
        token_to_direction[d.canonical] = d
        for a in d.synonyms:
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
    adjectives = ["pearly-white"]

    modifiers = [
        "all",       
        "inside",    
        "in",        
        "through",   
    ]



    # -----------------------------
    # Final Lexicon Object
    # -----------------------------
    return Lexicon(
        verbs=verbs,
        nouns=nouns,
        directions=directions,
        modifiers=modifiers,
        adjectives=adjectives,
        prepositions=prepositions,
        conjunctions=conjunctions,
        particles=particles,
        token_to_verb=token_to_verb,
        token_to_noun=token_to_noun,
        token_to_direction=token_to_direction,
    )
