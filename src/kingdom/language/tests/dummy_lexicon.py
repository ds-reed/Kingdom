# dummy_lexicon.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from kingdom.model.verb_model import Verb
from kingdom.model.noun_model import Noun

# ------------------------------------------------------------
# Lexicon Entry Types
# ------------------------------------------------------------

@dataclass(frozen=True)
class VerbEntry:
    canonical: str
    synonyms: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    uses_directions: bool = False
    expand_all: bool = False
    verb_object: Verb = None

@dataclass(frozen=True)
class NounEntry:
    handle: str
    canonical: str
    display: str
    synonyms: List[str] = field(default_factory=list)
    adjectives: List[str] = field(default_factory=list)
    category: Optional[str] = None

@dataclass(frozen=True)
class DirectionEntry:
    handle: str
    canonical: str
    reverse: Optional[str]
    synonyms: List[str]

@dataclass(frozen=True)
class PrepositionEntry:
    canonical: str
    synonyms: List[str]

@dataclass(frozen=True)
class Lexicon:
    verbs: List[VerbEntry]
    nouns: List[NounEntry]
    directions: List[DirectionEntry]
    modifiers: List[str]
    adjectives: List[str]

    # UPDATED
    prepositions: Dict[str, PrepositionEntry]
    conjunctions: List[str]
    particles: List[str]

    token_to_verb: Dict[str, VerbEntry]
    token_to_noun: Dict[str, NounEntry]
    token_to_direction: Dict[str, DirectionEntry]

    # NEW
    token_to_preposition: Dict[str, List[str]]


# ------------------------------------------------------------
# Dummy Lexicon Builder
# ------------------------------------------------------------

def build_dummy_lexicon() -> Lexicon:

    # ============================================================
    # VERBS
    # ============================================================
    verbs = [
        VerbEntry("go", ["walk", "move"], [], True),
        VerbEntry("look", ["examine", "inspect", "peer"], ["in", "inside"], False),
        VerbEntry("take", ["grab", "pick", "pick up"], [], False),
        VerbEntry("drop", ["put down"], [], False),
        VerbEntry("put", ["place", "set"], [], False),
        VerbEntry("open", ["unseal", "unlatch"], [], False),
        VerbEntry("close", ["shut"], [], False),
        VerbEntry("push", ["press"], [], False),
        VerbEntry("pull", ["yank"], [], False),
        VerbEntry("break", ["shatter", "smash"], [], False),
        VerbEntry("cut", ["slice", "chop"], [], False),
        VerbEntry("pour", [], [], False),
        VerbEntry("fill", [], [], False),
        VerbEntry("stir", [], [], False),
        VerbEntry("mix", ["combine"], [], False),
        VerbEntry("remove", [], [], False),
        VerbEntry("trade", [], [], False),
        VerbEntry("swap", [], [], False),
        VerbEntry("throw", ["toss", "hurl"], [], False),
        VerbEntry("hang", [], [], False),
        VerbEntry("lay", [], [], False),
        VerbEntry("stand", [], [], False),
        VerbEntry("sit", [], [], False),
        VerbEntry("climb", [], [], True),
        VerbEntry("crawl", [], [], True),
        VerbEntry("jump", [], [], True),
        VerbEntry("run", [], [], True),
        VerbEntry("roll", [], [], False),
        VerbEntry("slide", [], [], False),
        VerbEntry("give", ["hand", "offer"], [], False),
        VerbEntry("show", [], [], False),
        VerbEntry("feed", [], [], False),
        VerbEntry("light", [], [], False),
        VerbEntry("extinguish", ["blow out"], [], False),
        VerbEntry("talk", ["speak"], [], False),
        VerbEntry("ask", [], [], False),
        VerbEntry("say", [], [], False),
        VerbEntry("attack", ["hit", "strike","fight"], [], False),
        VerbEntry("sharpen", [], [], False),
    ]

    token_to_verb = {}
    for v in verbs:
        token_to_verb[v.canonical] = v
        for s in v.synonyms:
            token_to_verb[s] = v

    noun_specs = [
        # Existing nouns
        ("lamp", [], []),
        ("sword", [], []),
        ("shield", [], []),
        ("table", [], []),
        ("statue", [], ["strange"]),
        ("drawer", [], []),
        ("door", [], []),
        ("bag", [], []),
        ("everything", [], []),
        ("chest", [], []),
        ("apple", [], []),
        ("basket", [], []),
        ("guard", [], []),
        ("wizard", [], []),
        ("amulet", [], []),
        ("hello", [], []),
        ("troll", [], []),
        ("knife", ["machete"], ["pearly-white"]),
        ("key", ["skeleton key"], []),
        ("box", [], []),
        ("envelope", [], []),
        ("desk", [], []),
        ("pedestal", [], []),
        ("floor", [], []),
        ("ceiling", [], []),
        ("hatch", [], []),
        ("panel", [], []),
        ("curtain", [], []),
        ("gate", [], []),
        ("jug", [], []),
        ("basin", [], []),
        ("hook", [], []),
        ("wall", [], []),
        ("figurine", [], []),
        ("crystal", [], []),
        ("parchment", [], []),
        ("boots", ["shoes"], []),
        ("cloak", ["cape"], []),
        ("wardrobe", [], []),
        ("anvil", [], []),
        ("shard", [], []),
        ("rope", ["cord", "line"], []),
        ("moss", [], []),
        ("dirt", [], []),
        ("wine", [], []),
        ("journal", [], []),
        ("page", [], []),
        ("mirror", [], []),
        ("coin", ["coins", "currency"], []),
        ("stone", ["stones"], []),
        ("powder", ["powders"], []),
        ("gear", ["gears"], []),
        ("spring", ["springs"], []),
        ("pill", ["pills"], []),
        ("bread", [], []),
        ("water", [], []),
        ("stew", [], []),
        ("meat", [], []),
        ("barrel", [], []),
        ("beanstalk", [], []),
        ("river", [], []),
        ("fence", [], []),
        ("cellar", [], []),
        ("elf", [], []),
        ("king", [], []),
        ("thief", [], []),
        ("beggar", [], []),
        ("wraith", [], []),
        ("prisoner", [], []),
        ("goblin", [], []),
        ("dragon", [], []),
        ("bed", [], []),

        # ------------------------------------------------------------
        # NEW nouns required for Stage 3 test suite
        # ------------------------------------------------------------

        ("map", [], []),
        ("ring", [], []),
        ("lever", [], []),
        ("bolt", [], []),
        ("handle", [], []),

        ("sip", [], []),
        ("handful", [], []),
        ("piece", [], []),
        ("stack", [], []),
        ("clump", [], []),
        ("drop", [], []),
        ("length", [], []),

        ("look", [], []),  # noun sense of "take a look"

        ("donkey", [], []),
        ("torch", [], []),
        ("idol", [], []),
        ("button", [], []),
        ("post", [], []),
        ("steak", [], []),
        ("grave", [], []),
        ("candle", [], []),
        ("crate", [], []),
        ("pot", [], []),
        ("link", [], []),
        ("shirt", [], []),

        ("pile", [], []),
        ("altar", [], []),
        ("bracket", [], []),
        ("shelf", [], []),
    ]


    nouns = []
    token_to_noun = {}
    for canonical, synonyms, adjectives in noun_specs:
        entry = NounEntry(
            handle=canonical,
            canonical=canonical,
            display=canonical.capitalize(),
            synonyms=synonyms,
            adjectives=adjectives
        )
        nouns.append(entry)
        token_to_noun[canonical] = entry
        for s in synonyms:
            token_to_noun[s] = entry

    # ============================================================
    # DIRECTIONS
    # ============================================================
    directions = [
        DirectionEntry("north", "north", "south", []),
        DirectionEntry("south", "south", "north", []),
        DirectionEntry("east", "east", "west", []),
        DirectionEntry("west", "west", "east", []),
        DirectionEntry("up", "up", "down", []),
        DirectionEntry("down", "down", "up", []),
        DirectionEntry("inside", "inside", "outside", []),
        DirectionEntry("outside", "outside", "inside", []),
        DirectionEntry("through", "through", "through", []),
        DirectionEntry("past", "past", None, []),
        DirectionEntry("toward", "toward", None, []),
    ]

    token_to_direction = {}
    for d in directions:
        token_to_direction[d.canonical] = d
        for s in d.synonyms:
            token_to_direction[s] = d

    # ============================================================
    # PREPOSITIONS (canonical + synonyms)
    # ============================================================
    preposition_entries = {
        "into": PrepositionEntry("into", ["in", "inside", "within", "in to"]),
        "onto": PrepositionEntry("onto", ["on", "upon", "on to"]),
        "from": PrepositionEntry("from", ["out of", "off of", "off", "out"]),
        "with": PrepositionEntry("with", ["by", "via"]), 
        "at": PrepositionEntry("at", []),
        "in": PrepositionEntry("in", []),
        "on": PrepositionEntry("on", []),
        "to": PrepositionEntry("to", []),
        "toward": PrepositionEntry("toward", ["towards"]),
        "through": PrepositionEntry("through", ["thru"]),
        "across": PrepositionEntry("across", []),
        "past": PrepositionEntry("past", []),
        "under": PrepositionEntry("under", ["beneath", "underneath"]),
        "behind": PrepositionEntry("behind", []),
        "beyond": PrepositionEntry("beyond", []),
        "above": PrepositionEntry("above", []),
        "below": PrepositionEntry("below", []),
        "outside": PrepositionEntry("outside", []),
        "of": PrepositionEntry("of", []),
        "atop": PrepositionEntry("atop", []),
        "over": PrepositionEntry("over", []),
        "between": PrepositionEntry("between", []),
    }



    # Build token_to_preposition (supports ambiguity)
    token_to_preposition = {}
    for canonical, entry in preposition_entries.items():
        token_to_preposition.setdefault(canonical, []).append(canonical)
        for syn in entry.synonyms:
            token_to_preposition.setdefault(syn, []).append(canonical)

    # ============================================================
    # MODIFIERS, ADJECTIVES, CONJUNCTIONS, PARTICLES
    # ============================================================
    modifiers = [
        "all", "everything",
        "inside", "in", "through",
        "up", "down", "away", "off", "out",
        "immediately", "then"
    ]

    adjectives = [
        "shimmering", "translucent", "blue",
        "badly", "charred", "half-burnt",
        "massive", "ancient", "reinforced",
        "extremely", "heavy", "rusted", "iron",
        "small", "intricately", "carved", "ivory",
        "long", "sharp", "jagged", "glass",
        "smelly", "old", "tattered", "leather",
        "barely", "legible", "faded", "crimson",
        "thick", "solid", "granite",
        "huge", "dusty", "mahogany",
        "pearly-white"
    ]

    conjunctions = ["and", "or"]
    particles = ["the", "a", "an"]

    # ============================================================
    # FINAL LEXICON
    # ============================================================
    return Lexicon(
        verbs=verbs,
        nouns=nouns,
        directions=directions,
        modifiers=modifiers,
        adjectives=adjectives,
        prepositions=preposition_entries,
        conjunctions=conjunctions,
        particles=particles,
        token_to_verb=token_to_verb,
        token_to_noun=token_to_noun,
        token_to_direction=token_to_direction,
        token_to_preposition=token_to_preposition,
    )
