from dataclasses import dataclass, field    
import token
from typing import List, Any, Optional

from kingdom.language.interpreter import InterpretedCommand
from kingdom.model.noun_model import DirectionNoun, World
from kingdom.model.verb_model import Verb
from kingdom.verbs.verb_handler import ExecuteCommand




@dataclass 
class CommandOutcome:
    verb: str
    command: InterpretedCommand
    message: str
    effects: List[str]

def execute(command: InterpretedCommand, world: World,  original_command: str ) -> CommandOutcome:
    
    def execute_with_old_contract():             #compatability layer - remove when all verbs are ported!

        def _iter_local_target_candidates(world: World):
            state = world.state
            if state.current_room is not None:
                for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
                    yield direction_noun

                yield state.current_room
                for item in state.current_room.items:
                    yield item
                for container in state.current_room.containers:
                    yield container
                    if not container.is_openable or container.is_open:
                        for item in container.contents:
                            yield item

            player = getattr(state, "current_player", None)
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
            # Implicit verb (direction or noun continuation)
            # For now, default to GO; later you can add last-explicit-verb continuation
            verb = Verb.get_by_name("go")  

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

        target = command.direct if command.direct else None


        # Resolve world object
        if target:
            target = _resolve_target_noun(world, target.noun_object.handle) if target.noun_object else None


        # Stage 1: words = all_tokens minus verb token.
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

        result = verb.execute(target, words, cmd=execute_command)

        outcome = CommandOutcome(
            verb=verb.canonical_name() if verb else 'None',
            command=command,
            message=result,
            effects=[]
        )
        return outcome


    return(execute_with_old_contract())