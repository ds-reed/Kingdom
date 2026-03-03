# models/verb_registry.py
# note this is in verbs for now but we'll rework the modules a bit later.

from __future__ import annotations

from kingdom.model.verb_model import Verb

# Import handler classes or instances
from kingdom.verbs.inventory_verbs import InventoryVerbHandler
from kingdom.verbs.meta_verbs import MetaVerbHandler
from kingdom.verbs.movement_verbs import MovementVerbHandler
from kingdom.verbs.state_changing_verbs import StateVerbHandler


def build_verb_registry() -> dict[str, Verb]:
    """Construct the complete verb registry.

    Keys include both canonical names and synonyms.
    Values are Verb objects.
    """

    inventory = InventoryVerbHandler()
    meta = MetaVerbHandler()
    movement = MovementVerbHandler()
    state = StateVerbHandler()

    # Define canonical verbs
    core_verbs = [
        Verb("go", movement.go, synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"]),
        Verb("swim", movement.swim),
        Verb("teleport", movement.teleport, synonyms=["goto"], hidden=True),

        Verb("light", state.light),
        Verb("extinguish", state.extinguish, synonyms=["douse", "put out"]),
        Verb("open", state.open),
        Verb("close", state.close),
        Verb("unlock", state.unlock),
        Verb("eat", state.eat, synonyms=["consume"]),
        Verb("rub", state.rub, synonyms=["polish", "clean"]),
        Verb("say", state.say, synonyms=["speak", "talk", "shout", "whisper"]),
        Verb("make", state.make, synonyms=["wish"], hidden=True),
        Verb("look", state.look, synonyms=["examine", "inspect"]),

        Verb("help", meta.help, synonyms=["commands", "h", "?"]),
        Verb("score", meta.score, synonyms=["points"]),
        Verb("load", meta.load),
        Verb("save", meta.save),
        Verb("quit", meta.quit, synonyms=["q"]),
        Verb("die", meta.die, hidden=True),
        Verb("DEBUG", meta.DEBUG, hidden=True),

        Verb("inventory", inventory.inventory, synonyms=["inven"]),
        Verb("take", inventory.take, synonyms=["get"]),
        Verb("drop", inventory.drop),
    ]

    # Build lookup table
    registry: dict[str, Verb] = {}

    for verb in core_verbs:
        # canonical name
        registry[verb.name] = verb

        # synonyms
        for syn in verb.synonyms:
            registry[syn] = verb

    return registry
