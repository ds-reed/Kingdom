from dataclasses import dataclass, field    
import token
from typing import List, Any, Optional

from kingdom.language.interpreter import InterpretedCommand
from kingdom.model.noun_model import World
from kingdom.model.verb_model import Verb
from kingdom.verbs.verb_handler import ExecuteCommand
from kingdom.model.game_init import get_game



@dataclass 
class CommandOutcome:
    verb: str
    command: InterpretedCommand
    message: str
    effects: List[str]

def execute(command: InterpretedCommand, world: World,  original_command: str ) -> CommandOutcome:
    
    def execute_with_old_contract():             #compatability layer - remove when all verbs are ported!

        def _iter_local_target_candidates(world: World):
            game = get_game()
            if getattr(game, "current_room", None) is not None:

                yield game.current_room
                for item in game.current_room.items:
                    yield item
                for container in game.current_room.containers:
                    yield container
                    if not container.is_openable or container.is_open:
                        for item in container.contents:
                            yield item

            player = getattr(game, "current_player", None)
            if player is not None:
                for item in player.sack.contents:
                    yield item


        def _resolve_target_noun(world: World, target_name) -> object | None:

            local_candidates = list(_iter_local_target_candidates(world))
            for candidate in local_candidates:
                if candidate.matches_reference(target_name):
                    return candidate
            return None

#--------- start of old contract verb execution logic, to be removed when all verbs use new structure --------

        outcome = None

        # Determine verb 
        if command.verb is not None:
            # Explicit verb
            verb = command.verb

        elif command.verb_source == "implicit":
            # Implicit verb - look for noun continuation when supported by verb handler
            if not command.direction:        # if we have a direction, then interpreter has handled as implicit "go"
                pass # will need to handle noun continuation here

        elif command.verb_source == "unknown":
            # User typed something in the verb slot that is not a verb
            return CommandOutcome(
                verb="None",
                command=command,
                message=f"I don't know how to '{original_command}'.",
                effects=[]
            )

        else:
            # Empty input or something structurally odd may not be reachable
            return CommandOutcome(
                verb="None",
                command=command,
                message="What would you like to do? (type help for assistance)",
                effects=[]
            )

        target_candidate = command.direct if command.direct else None

        target = None
        # Resolve world object
        if target_candidate is not None:
            target = _resolve_target_noun(world, target_candidate.noun_object.handle) if target_candidate.noun_object else None

        if command and command.direct:
                command.direct.noun_object = target         # Over-write direct.noun_object with None if not a valid target for room. maybe handle in interpreter instead?

        # old verb expectation
        # For implicit verbs (e.g. bare direction "west"), the verb is not in
        # all_tokens, so pass all tokens unchanged.
        if command.verb_source == "implicit":
            words = list(command.all_tokens) if command.all_tokens else []
        else:
            words = list(command.all_tokens[1:]) if command.all_tokens else []  # strip off verb token

        execute_command =  ExecuteCommand(
            verb_token = command.verb_token,
            direct_object = command.direct.noun_object if command.direct else None,
            direct_object_token = command.direct.token_head if command.direct else None,
            prep_phrases = command.prep_phrases if command.prep_phrases else {},
            direction = command.direction if command.direction else None,
            modifiers = command.modifier_tokens if command.modifier_tokens else [],
            )
        
# pass old and new verb contract data to verb handler during transition

        result = verb.execute(target, words, cmd=execute_command)

        outcome = CommandOutcome(
            verb=verb.canonical_name() if verb else 'None',
            command=command,
            message=result,
            effects=[]
        )
        return outcome


    return(execute_with_old_contract())