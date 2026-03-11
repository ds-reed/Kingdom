# kingdom/verbs/verb_registry.py

from __future__ import annotations
from kingdom.model.verb_model import Verb



def register_verbs():
     """Build the complete verb registry.

     Keys include both canonical names and synonyms.
     Values are Verb objects.
     """

     # Import handlers inside the function to avoid circular dependencies
     from kingdom.verbs.inventory_verbs import InventoryVerbHandler
     from kingdom.verbs.meta_verbs import MetaVerbHandler
     from kingdom.verbs.movement_verbs import MovementVerbHandler
     from kingdom.verbs.state_changing_verbs import ChangeStateVerbHandler
     from kingdom.verbs.state_dependent_verbs import StatefulVerbHandler

     inventory = InventoryVerbHandler()
     meta = MetaVerbHandler()
     movement = MovementVerbHandler()
     change = ChangeStateVerbHandler()
     stateful = StatefulVerbHandler()

     # Rebuild from a clean slate so repeated calls don't accumulate duplicates.
     Verb.all_verbs.clear()
     Verb._by_name.clear()

     core_verbs = [

          # Movement verbs (all use directions)
          Verb("go", movement.go,
               synonyms=["walk", "move", "run", "head", "travel"],
               modifiers=[],
               uses_directions=True),

          Verb("swim", movement.swim,
               synonyms=[],
               modifiers=[],
               uses_directions=True),

          Verb("climb", movement.climb,
               synonyms=[],
               modifiers=[],
               uses_directions=True),

          Verb("teleport", movement.teleport,
               synonyms=["goto"],
               hidden=True,
               modifiers=[],
               uses_directions=True),

          # Change state verbs
          Verb("light", change.light,
               synonyms=[],
               modifiers=["all", "everything"],
               uses_directions=False),

          Verb("extinguish", change.extinguish,
               synonyms=["douse", "put out"],
               modifiers=["all", "everything"],
               uses_directions=False),

          Verb("open", change.open,
               synonyms=[],
               modifiers=["with","using", "all", "everything"],
               uses_directions=False),

          Verb("close", change.close,
               synonyms=[],
               modifiers=["all", "everything"],
               uses_directions=False),

          Verb("unlock", change.unlock,
               synonyms=[],
               modifiers=["with", "all", "everything"],
               uses_directions=False),

          Verb("tie", change.tie,
               synonyms=["affix", "connect"],
               modifiers=[],
               uses_directions=False),

          Verb("untie", change.untie,
               synonyms=["disconnect"],
               modifiers=["to"],
               uses_directions=False),

          #singleton - most should be pairs (maybe tarnish is opposite of rub)
          Verb("rub", change.rub,
               synonyms=["polish", "clean"],
               modifiers=["all", "everything"],
               uses_directions=False),


          # Stateful verbs (require state checks but no changes)

          Verb("say", stateful.say,
               synonyms=["speak", "talk", "shout", "whisper"],
               modifiers=["to djinni", "wish"],
               uses_directions=False),

          Verb("make", stateful.make,
               synonyms=[],
               hidden=True,
               modifiers=["wish"],
               uses_directions=False),

          Verb("look", stateful.look,
               synonyms=["examine", "inspect"],
               modifiers=["in", "inside", "at"],
               uses_directions=False),

          Verb("eat", stateful.eat,
               synonyms=["consume"],
               modifiers=["all", "everything"],
               uses_directions=False),


          # Meta verbs
          Verb("help", meta.help,
               synonyms=["commands", "h", "?"],
               modifiers=["commands"],
               uses_directions=False),

          Verb("score", meta.score,
               synonyms=["points"],
               modifiers=[],
               uses_directions=False),

          Verb("load", meta.load,
               synonyms=[],
               modifiers=[],
               uses_directions=False),

          Verb("save", meta.save,
               synonyms=[],
               modifiers=[],
               uses_directions=False),

          Verb("quit", meta.quit,
               synonyms=["q"],
               modifiers=[],
               uses_directions=False),

          Verb("die", meta.die,
               synonyms=[],
               hidden=True,
               modifiers=[],
               uses_directions=False),

          Verb("DEBUG", meta.DEBUG,
               synonyms=[],
               hidden=True,
               modifiers=[],
               uses_directions=False),

          # Inventory verbs
          Verb("inventory", inventory.inventory,
               synonyms=["inven"],
               modifiers=[],
               uses_directions=False),

          Verb("take", inventory.take,
               synonyms=["get"],
               modifiers=["all", "everything", "in", "from"],
               uses_directions=False),

          Verb("drop", inventory.drop,
               synonyms=["put"],
               modifiers=["all", "everything"],
               uses_directions=False),

#          Verb("put", inventory.put,
#               synonyms=[],
#               modifiers=["in", "on", "into", "onto", "all", "everything"],
#               uses_directions=False)
     ]

     return 
