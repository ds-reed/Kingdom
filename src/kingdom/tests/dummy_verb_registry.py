# ------------------------------------------------------------
# Dummy handler for all test verbs
# ------------------------------------------------------------
def dummy_handler(target, words):
    return f"[dummy handler executed for verb: {words}]"

# ------------------------------------------------------------
# Test Verb Registry (auto-generated from 100-command corpus)
# Each Verb uses dummy_handler and includes synonyms where natural.
# ------------------------------------------------------------

from kingdom.model.verb_model import Verb

test_verbs = [

    # Movement verbs
    Verb("go", dummy_handler,
         synonyms=["walk", "head", "enter", "run", "return", "step"],
         modifiers=set(),
         uses_directions=True),

    Verb("climb", dummy_handler,
         synonyms=["ascend", "descend"],
         modifiers=set(),
         uses_directions=True),

    Verb("crawl", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=True),

    Verb("jump", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=True),

    Verb("swim", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=True),

    Verb("wade", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=True),

    Verb("squeeze", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=True),

    # Looking / examining
    Verb("look", dummy_handler,
         synonyms=["examine", "inspect", "search"],
         modifiers={"in", "inside", "at", "behind", "under"},
         uses_directions=False),

    Verb("read", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    # Inventory / taking / dropping
    Verb("take", dummy_handler,
         synonyms=["get", "pick", "grab"],
         modifiers={"all", "everything", "from", "in"},
         uses_directions=False),

    Verb("drop", dummy_handler,
         synonyms=[],
         modifiers={"all", "everything"},
         uses_directions=False),

    Verb("inventory", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    # Object manipulation
    Verb("open", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("close", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("unlock", dummy_handler,
         synonyms=[],
         modifiers={"with"},
         uses_directions=False),

    Verb("lock", dummy_handler,
         synonyms=[],
         modifiers={"with"},
         uses_directions=False),

    Verb("push", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("pull", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("turn", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("twist", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("press", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("flip", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("place", dummy_handler,
         synonyms=[],
         modifiers={"in", "on"},
         uses_directions=False),

    Verb("put", dummy_handler,
         synonyms=[],
         modifiers={"in", "on"},
         uses_directions=False),

    Verb("remove", dummy_handler,
         synonyms=[],
         modifiers={"from"},
         uses_directions=False),

    Verb("pour", dummy_handler,
         synonyms=[],
         modifiers={"into"},
         uses_directions=False),

    Verb("fill", dummy_handler,
         synonyms=[],
         modifiers={"with"},
         uses_directions=False),

    Verb("empty", dummy_handler,
         synonyms=[],
         modifiers={"into", "from"},
         uses_directions=False),

    Verb("reach", dummy_handler,
         synonyms=[],
         modifiers={"into"},
         uses_directions=False),

    Verb("throw", dummy_handler,
         synonyms=[],
         modifiers={"at"},
         uses_directions=False),

    Verb("tie", dummy_handler,
         synonyms=[],
         modifiers={"to"},
         uses_directions=False),

    Verb("cut", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    # Talking / social
    Verb("talk", dummy_handler,
         synonyms=[],
         modifiers={"to"},
         uses_directions=False),

    Verb("ask", dummy_handler,
         synonyms=[],
         modifiers={"about", "to"},
         uses_directions=False),

    Verb("say", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("tell", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("shout", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("whisper", dummy_handler,
         synonyms=[],
         modifiers={"to"},
         uses_directions=False),

    Verb("greet", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    # Combat verbs (dummy only)
    Verb("attack", dummy_handler,
         synonyms=["fight"],
         modifiers=set(),
         uses_directions=False),

    Verb("hit", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("stab", dummy_handler,
         synonyms=[],
         modifiers={"with"},
         uses_directions=False),

    Verb("kick", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("punch", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("defend", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("dodge", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("aim", dummy_handler,
         synonyms=[],
         modifiers={"at"},
         uses_directions=False),

    # Using items
    Verb("light", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("extinguish", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("eat", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("drink", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("wear", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("sharpen", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("clean", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    # Meta verbs
    Verb("save", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("load", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("quit", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("restart", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),

    Verb("help", dummy_handler,
         synonyms=[],
         modifiers=set(),
         uses_directions=False),
]

# ------------------------------------------------------------
# Build a registry dict just like your real verb registry
# ------------------------------------------------------------
test_registry = {}
for v in test_verbs:
    test_registry[v.name] = v
    for syn in v.synonyms:
        test_registry[syn] = v
