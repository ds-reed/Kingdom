from typing import Any, Dict, List

from kingdom.language.interpreter import InterpretedCommand
from kingdom.language.outcomes import (
    CommandOutcome,
    CommandStatus,
    RenderMode,
    make_outcome,
)
from kingdom.model.noun_model import World
from kingdom.engine.verbs.verb_handler import ExecuteCommand

def _outcome(
    *,
    status: CommandStatus,
    verb: str,
    command: InterpretedCommand,
    message: str,
    code: str | None = None,
    details: Dict[str, Any] | None = None,
    effects: List[str] | None = None,
    render_mode: RenderMode = RenderMode.NORMALIZE,
) -> CommandOutcome:
    return make_outcome(
        status=status,
        verb=verb,
        command=command,
        message=message,
        code=code,
        details=details,
        effects=effects,
        render_mode=render_mode,
    )


def _require_command_outcome(
    result: object,
    *,
    verb_name: str,
    command: InterpretedCommand,
) -> CommandOutcome:
    if not isinstance(result, CommandOutcome):
        raise TypeError(
            f"Verb '{verb_name}' returned {type(result).__name__}; expected CommandOutcome."
        )

    if result.command is None:
        result.command = command
    if not result.verb:
        result.verb = verb_name
    return result

def execute(command: InterpretedCommand, world: World,  original_command: str ) -> CommandOutcome:

    outcome = None

    # Determine verb 
    if command.verb is not None:
        # Explicit verb
        verb = command.verb

    elif command.verb_source == "implicit":
        # Implicit verb - look for noun continuation when supported by verb handler
        if not command.direction:        # if we have a direction, then interpreter has handled as implicit "go"
            return _outcome(
                status=CommandStatus.NO_OP,
                verb="None",
                command=command,
                message="What would you like to do? (type help for assistance)",
                code="implicit_without_direction",
            )

    elif command.verb_source == "unknown":
        # User typed something in the verb slot that is not a verb
        return _outcome(
            status=CommandStatus.INVALID_TARGET,
            verb="None",
            command=command,
            message=f"I don't know how to '{original_command}'.",
            code="unknown_verb",
            details={"original_command": original_command},
        )

    else:
        # Empty input or something structurally odd may not be reachable
        return _outcome(
            status=CommandStatus.NO_OP,
            verb="None",
            command=command,
            message="What would you like to do? (type help for assistance)",
            code="empty_or_unreachable",
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

    outcome = _require_command_outcome(
        result,
        verb_name=verb.canonical_name() if verb else "None",
        command=command,
    )

    return outcome





