"""Action dispatch model for verb handlers.

"""
from __future__ import annotations

from dataclasses import dataclass

from pathlib import Path
from typing import Callable 

from kingdom.model.models import   Game   
from kingdom.model.verb_model import Verb   

from kingdom.verbs.inventory_verbs import InventoryVerbHandler
inventory_handler = InventoryVerbHandler()  

from kingdom.verbs.meta_verbs import MetaVerbHandler
meta_handler = MetaVerbHandler()

from kingdom.verbs.movement_verbs import MovementVerbHandler
movement_handler = MovementVerbHandler()

from kingdom.verbs.state_changing_verbs import StateVerbHandler
state_handler = StateVerbHandler()


def _register_aliases(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    for alias in verb.synonyms:
        verb_lookup[alias] = verb

def _register_verb(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    verb_lookup[verb.name] = verb
    _register_aliases(verb_lookup, verb)

def _build_core_verbs(
) -> list[Verb]:

# refactored verbs. 

    #--------------- movement verbs ------------------------------
    verb_go        = Verb("go", movement_handler.go, synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"])
    verb_swim      = Verb("swim", movement_handler.swim)
    verb_teleport  = Verb("teleport", movement_handler.teleport, synonyms=["goto"], hidden=True)


    #--------------- state-changing verbs -------------------------
    verb_light      = Verb("light", state_handler.light)
    verb_extinguish = Verb("extinguish", state_handler.extinguish, synonyms=["douse", "put out"])
    verb_open       = Verb("open", state_handler.open)
    verb_close      = Verb("close", state_handler.close)
    verb_unlock     = Verb("unlock", state_handler.unlock)
    verb_eat        = Verb("eat", state_handler.eat, synonyms=["consume"])
    verb_rub        = Verb("rub", state_handler.rub, synonyms=["polish", "clean"]) 
    verb_say        = Verb("say", state_handler.say, synonyms=["speak", "talk", "shout", "whisper"])
    verb_make       = Verb("make", state_handler.make, synonyms=["wish"], hidden=True)     # make is used for make wish only right now
    verb_look       = Verb("look", state_handler.look, synonyms=["examine", "inspect"])


    #---------------- meta verbs ----------------------------
    verb_help = Verb("help", meta_handler.help, synonyms=["commands", "h", "?"])  #right now "?" is intercepted by parser, but we can change that late
    verb_score = Verb("score", meta_handler.score, synonyms=["points"])
    verb_load = Verb("load", meta_handler.load)
    verb_save = Verb("save", meta_handler.save)
    verb_quit = Verb("quit", meta_handler.quit, synonyms=["q"])

    # debug subset - not intended to be player commands
    verb_die  = Verb("die", meta_handler.die, hidden=True)  # for testing game over handling - not intended to be a player command
    verb_debug = Verb("DEBUG", meta_handler.DEBUG, hidden=True)




    #---------------- inventory verbs ----------------------------
    verb_inventory = Verb("inventory", inventory_handler.inventory, synonyms=["inven"]) 
    verb_take = Verb("take", inventory_handler.take, synonyms=["get"])
    verb_drop = Verb("drop", inventory_handler.drop)


    return [
        verb_quit,
        verb_go,
        verb_swim,
        verb_save,
        verb_load,
        verb_look,
        verb_inventory,
        verb_score,
        verb_take,
        verb_drop,
        verb_light,
        verb_extinguish,
        verb_open,
        verb_close,
        verb_unlock,
        verb_teleport,
        verb_help,
        verb_debug,
        verb_eat,
        verb_rub,
        verb_say,
        verb_make,
        verb_die,
    ]


def build_verbs(
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}
    for verb in _build_core_verbs():
        _register_verb(verbs, verb)
    return verbs
