"""Action dispatch model for verb handlers.

"""
from __future__ import annotations

from dataclasses import dataclass

from pathlib import Path
from typing import Callable 

from kingdom.models import   Game,   Verb 

from kingdom.state_changing_verbs import StateVerbHandler
state_handler = StateVerbHandler()

from kingdom.movement_verbs import MovementVerbHandler
movement_handler = MovementVerbHandler()

from kingdom.world_verbs import WorldVerbHandler
world_handler = WorldVerbHandler()

from kingdom.ui_verbs import UIVerbHandler
ui_handler = UIVerbHandler()

from kingdom.meta_verbs import MetaVerbHandler
meta_handler = MetaVerbHandler()

ConfirmAction = Callable[[str], bool]
PromptAction = Callable[[str], str]


def _register_aliases(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    for alias in verb.synonyms:
        verb_lookup[alias] = verb


def _register_verb(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    verb_lookup[verb.name] = verb
    _register_aliases(verb_lookup, verb)

def _build_core_verbs(
    state: "GameActionState",
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None,
    prompt_action: PromptAction | None,
) -> list[Verb]:

# refactored verbs. 

#--------------- movement verbs ------------------------------
    verb_go        = Verb("go", movement_handler.go, synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"])

    verb_swim      = Verb("swim", movement_handler.swim)

    verb_climb     = Verb("climb", movement_handler.climb, synonyms=["scale", "ascend", "descend"])

    verb_teleport  = Verb("teleport", movement_handler.teleport, synonyms=["goto"], hidden=True)


    #--------------- state-changing verbs -------------------------
    verb_light      = Verb("light", state_handler.light)

    verb_extinguish = Verb("extinguish", state_handler.extinguish)

    verb_open       = Verb("open", state_handler.open)

    verb_close      = Verb("close", state_handler.close)

    verb_unlock     = Verb("unlock", state_handler.unlock)


    #---------------- UI verbs ----------------------------
    verb_load = Verb("load", ui_handler.load)

    verb_save = Verb("save", ui_handler.save)

    verb_quit = Verb("quit", ui_handler.quit, synonyms=["q"])


    #---------------- world-state verbs ----------------------------
    verb_score = Verb("score", world_handler.score, synonyms=["points"])


    #---------------- meta verbs ----------------------------
    verb_help = Verb("help", meta_handler.help, synonyms=["commands", "h", "?"])


    return [
        verb_quit,
        verb_go,
        verb_swim,
        verb_climb,
        verb_save,
        verb_load,
#        verb_look,
#        verb_inventory,
        verb_score,
#        verb_take,
#        verb_drop,
        verb_light,
        verb_extinguish,
        verb_open,
        verb_close,
        verb_unlock,
        verb_teleport,
        verb_help,
    ]


def build_verbs(
    state: "GameActionState",
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None = None,
    prompt_action: PromptAction | None = None,
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}
    for verb in _build_core_verbs(state, game, default_save_path, confirm_action, prompt_action):
        _register_verb(verbs, verb)
    return verbs



"""
# todo  - refactor these verbs
    look_verb = Verb("look", look_action, synonyms=["inspect", "examine"])

# item management verbs - refactor to use new verb handler
    inventory_verb = Verb("inventory", inventory_action, synonyms=["inven"])
    take_verb = Verb("take", take_action, synonyms=["get"])
    drop_verb = Verb("drop", drop_action)
"""