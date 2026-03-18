from dataclasses import dataclass, field    
import token
from typing import List, Any, Optional

from kingdom.language.interpreter import InterpretedCommand
from kingdom.model.noun_model import World
from kingdom.model.verb_model import Verb
from kingdom.engine.verbs.verb_handler import ExecuteCommand
from kingdom.model.game_model import get_game



@dataclass 
class CommandOutcome:
    verb: str
    command: InterpretedCommand
    message: str
    effects: List[str]

def execute(command: InterpretedCommand, world: World,  original_command: str ) -> CommandOutcome:

    outcome = None

    # Determine verb 
    if command.verb is not None:
        # Explicit verb
        verb = command.verb

    elif command.verb_source == "implicit":
        # Implicit verb - look for noun continuation when supported by verb handler
        if not command.direction:        # if we have a direction, then interpreter has handled as implicit "go"
            return CommandOutcome(
                verb="None",
                command=command,
                message="What would you like to do? (type help for assistance)",
                effects=[]
        )

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

    execute_command =  ExecuteCommand(
        verb_token = command.verb_token,
        direct_object = command.direct.noun_object if command.direct else None,
        direct_object_token = command.direct.token_head if command.direct else None,
        prep_phrases = command.prep_phrases if command.prep_phrases else {},
        direction = command.direction if command.direction else None,
        modifiers = command.modifier_tokens if command.modifier_tokens else [],
        )

    result = verb.execute(cmd=execute_command)

    outcome = CommandOutcome(
        verb=verb.canonical_name() if verb else 'None',
        command=command,
        message=result,
        effects=[]
    )

    return outcome





