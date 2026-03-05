# ======================================================================
# Dummy Lexicon Loader
# ======================================================================
# Loads the dummy verb and noun registries from the test directory and
# assembles them into a lexicon object matching the frozen parser contract.
#
# Prepositions, conjunctions, particles, and stopwords can be expanded
# later, but we include minimal sets now so the parser has something
# to work with.
# ======================================================================

from kingdom.tests.dummy_verb_registry import test_registry as dummy_verbs
from kingdom.tests.dummy_noun_registry import test_noun_registry as dummy_nouns


# ----------------------------------------------------------------------
# Minimal placeholder lists (expand later)
# ----------------------------------------------------------------------
DUMMY_PREPOSITIONS = [
    "in", "inside", "into", "through", "past", "over", "around", "across",
    "under", "behind", "from", "with", "at", "on", "to"
]

DUMMY_CONJUNCTIONS = ["and", ","]

DUMMY_PARTICLES = ["up", "out", "off", "over", "through"]

DUMMY_STOPWORDS = ["the", "a", "an", "my", "for", "of", "is", "who", "he", "she", "it"]


# ----------------------------------------------------------------------
# Lexicon builder
# ----------------------------------------------------------------------
def build_dummy_lexicon():
    """
    Returns a dict matching the parser's lexicon contract:
        {
            "verbs": { ... },
            "nouns": { ... },
            "prepositions": [...],
            "conjunctions": [...],
            "particles": [...],
            "stopwords": [...],
        }
    """
    return {
        "verbs": dummy_verbs,
        "nouns": dummy_nouns,
        "prepositions": DUMMY_PREPOSITIONS,
        "conjunctions": DUMMY_CONJUNCTIONS,
        "particles": DUMMY_PARTICLES,
        "stopwords": DUMMY_STOPWORDS,
    }
