# ------------------------------------------------------------
# Dummy Noun Registry for Parser Test Harness
# ------------------------------------------------------------
# This registry:
# - includes all nouns extracted from the 100‑command corpus
# - includes simple synonyms where natural
# - includes placeholder adjective lists (empty for now)
# - uses a DummyNoun class compatible with your future noun registry
# - does NOT include world state, locations, or object behavior
# ------------------------------------------------------------

class DummyNoun:
    def __init__(self, canonical, synonyms=None, adjectives=None, category=None):
        self.canonical = canonical
        self.synonyms = set(synonyms or [])
        self.adjectives = set(adjectives or [])
        self.category = category  # optional future field

    def canonical_name(self):
        return self.canonical

    def display_name(self):
        return self.canonical


# ------------------------------------------------------------
# Noun list extracted from the 100‑command corpus
# ------------------------------------------------------------

noun_entries = [

    # Directions (treated as nouns for parser purposes)
    ("north", [], [], "direction"),
    ("south", [], [], "direction"),
    ("east", [], [], "direction"),
    ("west", [], [], "direction"),
    ("up", [], [], "direction"),
    ("down", [], [], "direction"),
    ("inside", [], [], "direction"),   # ambiguous
    ("out", [], [], "direction"),      # ambiguous

    # Places / geography
    ("river", [], []),
    ("cave", [], []),
    ("ladder", [], []),
    ("hole", [], []),
    ("hallway", [], []),
    ("tree", [], []),
    ("stairs", [], []),
    ("gap", [], []),
    ("pit", [], []),
    ("water", [], []),
    ("lake", [], []),
    ("mud", [], []),
    ("table", [], []),
    ("vines", [], []),
    ("crack", [], []),

    # Inventory / objects
    ("lamp", [], []),
    ("key", ["blue key"], ["blue"]),
    ("sword", [], []),
    ("shield", [], []),
    ("coin", ["rusty coin"], ["rusty"]),
    ("bag", [], []),
    ("pockets", [], []),

    # Containers / doors
    ("door", [], []),
    ("chest", [], []),
    ("gate", [], []),
    ("drawer", [], []),
    ("basket", [], []),
    ("book", [], []),
    ("note", [], []),
    ("gem", [], []),
    ("pedestal", [], []),
    ("bottle", [], []),
    ("bucket", [], []),

    # Environmental objects
    ("statue", ["strange statue"], ["strange"]),
    ("floor", [], []),
    ("inscription", [], []),
    ("curtain", [], []),
    ("bed", [], []),
    ("box", [], []),
    ("wall", ["west wall"], ["west"]),
    ("window", [], []),

    # Characters
    ("guard", [], []),
    ("wizard", [], []),
    ("amulet", [], []),
    ("djinni", [], []),
    ("merchant", [], []),
    ("ghost", [], []),
    ("target", [], []),

    # Clothing / items
    ("torch", [], []),
    ("apple", [], []),
    ("potion", [], []),
    ("cloak", [], []),
    ("boots", [], []),
    ("rope", [], []),
    ("hook", [], []),
    ("knife", [], []),
    ("mirror", [], []),
]

# ------------------------------------------------------------
# Build noun registry dict
# ------------------------------------------------------------

test_noun_registry = {}

for canonical, syns, adjs, *rest in noun_entries:
    category = rest[0] if rest else None
    noun = DummyNoun(canonical, syns, adjs, category)
    test_noun_registry[canonical] = noun
    for s in syns:
        test_noun_registry[s] = noun

# test_noun_registry is now ready for parser lexicon injection
