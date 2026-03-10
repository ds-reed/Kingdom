from dataclasses import dataclass
from typing import List

from kingdom.language.interpreter import InterpretedCommand
from kingdom.model.noun_model import DirectionNoun, World
from kingdom.language.lexicon import Lexicon

@dataclass 
class CommandOutcome:
    verb: str
    command: InterpretedCommand
    message: str
    effects: List[str]

def execute(command: InterpretedCommand, world: World, lexicon: Lexicon, original_command: str ) -> CommandOutcome:
    
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
            verb = command.verb.verb_object

        elif command.verb_source == "implicit":
            # Implicit verb (direction or noun continuation)
            # For now, default to GO; later you can add last-explicit-verb continuation
            go_entry = lexicon.token_to_verb.get("go")
            verb = go_entry.verb_object

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

        # for Stage 1 parser output: direct is a list, but verbs expect a single target
        target = command.direct[0] if command.direct else None

        # Resolve world object
        if target:
            target = _resolve_target_noun(world, target.canonical_head.canonical)


        # Stage 1: words = all_tokens
        words = list(command.all_tokens) if command.all_tokens else []

        # Stage 1: ALL disables target
        if "all" in command.modifier_tokens:
            target = None

        result = verb.execute(target, words)

        outcome = CommandOutcome(
            verb=verb.canonical_name() if verb else 'None',
            command=command,
            message=result,
            effects=[]
        )
        return outcome


    return(execute_with_old_contract())