# kingdom/verbs/verb_registry.py

from __future__ import annotations
from kingdom.model.verb_model import Verb


def build_verb_registry() -> dict[str, Verb]:
    """Build the complete verb registry.

    Keys include both canonical names and synonyms.
    Values are Verb objects.
    """

    # Import handlers inside the function to avoid circular dependencies
    from kingdom.verbs.inventory_verbs import InventoryVerbHandler
    from kingdom.verbs.meta_verbs import MetaVerbHandler
    from kingdom.verbs.movement_verbs import MovementVerbHandler
    from kingdom.verbs.state_changing_verbs import StateVerbHandler

    inventory = InventoryVerbHandler()
    meta = MetaVerbHandler()
    movement = MovementVerbHandler()
    state = StateVerbHandler()

    core_verbs = [

        # Movement verbs (all use directions)
        Verb("go", movement.go,
             synonyms=["walk", "move", "run", "slide", "head", "jog", "travel"],
             modifiers=set(),
             uses_directions=True),

        Verb("swim", movement.swim,
             synonyms=[],
             modifiers=set(),
             uses_directions=True),

        Verb("teleport", movement.teleport,
             synonyms=["goto"],
             hidden=True,
             modifiers=set(),
             uses_directions=True),

        # State-changing verbs
        Verb("light", state.light,
             synonyms=[],
             modifiers={"all", "everything"},
             uses_directions=False),

        Verb("extinguish", state.extinguish,
             synonyms=["douse", "put out"],
             modifiers={"all", "everything"},
             uses_directions=False),

        Verb("open", state.open,
             synonyms=[],
             modifiers={"with","using", "all", "everything"},
             uses_directions=False),

        Verb("close", state.close,
             synonyms=[],
             modifiers={"all", "everything"},
             uses_directions=False),

        Verb("unlock", state.unlock,
             synonyms=[],
             modifiers={"with", "all", "everything"},
             uses_directions=False),

        Verb("eat", state.eat,
             synonyms=["consume"],
             modifiers={"all", "everything"},
             uses_directions=False),

        Verb("rub", state.rub,
             synonyms=["polish", "clean"],
             modifiers={"all", "everything"},
             uses_directions=False),

        Verb("say", state.say,
             synonyms=["speak", "talk", "shout", "whisper"],
             modifiers=set(),
             uses_directions=False),

        Verb("make", state.make,
             synonyms=["wish"],
             hidden=True,
             modifiers={"wish"},
             uses_directions=False),

        Verb("look", state.look,
             synonyms=["examine", "inspect"],
             modifiers={"in", "inside", "at"},
             uses_directions=False),

        # Meta verbs
        Verb("help", meta.help,
             synonyms=["commands", "h", "?"],
             modifiers=set(),
             uses_directions=False),

        Verb("score", meta.score,
             synonyms=["points"],
             modifiers=set(),
             uses_directions=False),

        Verb("load", meta.load,
             synonyms=[],
             modifiers=set(),
             uses_directions=False),

        Verb("save", meta.save,
             synonyms=[],
             modifiers=set(),
             uses_directions=False),

        Verb("quit", meta.quit,
             synonyms=["q"],
             modifiers=set(),
             uses_directions=False),

        Verb("die", meta.die,
             synonyms=[],
             hidden=True,
             modifiers=set(),
             uses_directions=False),

        Verb("DEBUG", meta.DEBUG,
             synonyms=[],
             hidden=True,
             modifiers=set(),
             uses_directions=False),

        # Inventory verbs
        Verb("inventory", inventory.inventory,
             synonyms=["inven"],
             modifiers=set(),
             uses_directions=False),

        Verb("take", inventory.take,
             synonyms=["get"],
             modifiers={"all", "everything", "in", "from"},
             uses_directions=False),

        Verb("drop", inventory.drop,
             synonyms=[],
             modifiers={"all", "everything"},
             uses_directions=False),
    ]

    registry: dict[str, Verb] = {}

    for verb in core_verbs:
        registry[verb.name] = verb
        for syn in verb.synonyms:
            registry[syn] = verb

    return registry
