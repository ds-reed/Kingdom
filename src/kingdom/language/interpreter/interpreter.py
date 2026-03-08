# Interpreter.py
# Converts ParsedActions → InterpretedCommands (zero, one, or many)
# Pure, deterministic, no world mutation.

from dataclasses import dataclass
from typing import List, Optional

from kingdom.language.parser.parser import ParsedAction
from kingdom.language.lexicon.lexicon import Lexicon, VerbEntry, NounEntry

from dataclasses import dataclass, field
from typing import Optional, List

from kingdom.model.noun_model import Item, World

@dataclass(frozen=False)
class InterpretedTarget:
    token_phrase: str
    token_head: str
    token_adjectives: List[str]
    canonical_head: str


@dataclass(frozen=False)
class InterpretedCommand:
    # Required fields (no defaults)
    verb: VerbEntry                                                     # verb to be used in command
    all_tokens: List[str] = field(default_factory=list)

    # Optional semantic fields

    direct: List[InterpretedTarget] = field(default_factory=list)       # the direct object(s) of the verb, if any
    indirect: List[InterpretedTarget] = field(default_factory=list)     # the indirect object(s) of the verb, if any

    direction: Optional[str] = None                                     # canonical direction (e.g., "north", "up", etc.) if verb uses directions and a direction token was present
    direction_tokens: List[str] = field(default_factory=list)           # all direction tokens from the input (unclear purpose)

    modifier_tokens: List[str] = field(default_factory=list)            # e.g., ["all"], ["quickly"], etc.




def interpret(actions: List[ParsedAction], world: World, lexicon: Lexicon) -> List[InterpretedCommand]:
    """Entry point: interpret a list of ParsedActions into InterpretedCommands.

    The Interpreter performs semantic interpretation and disambiguation.
    It converts each ParsedAction into zero, one, or many InterpretedCommands.

    Responsibilities:
        - Verb lookup and validation
        - Noun phrase resolution
        - Ambiguity detection
        - Direction interpretation
        - Prepositional phrase classification
        - Modifier interpretation
        - ALL expansion (when allowed)
        - Argument rule enforcement
        - Surface form preservation
    """


    # ----------------------------------------------------------------------
    # Internal workflow for a single ParsedAction
    # ----------------------------------------------------------------------

    def _interpret_single_action(action: ParsedAction) -> List[InterpretedCommand]:
        """Interpret a single ParsedAction into zero, one, or many InterpretedCommands."""

        base_cmd.verb = _resolve_verb(action)
        if base_cmd.verb is None:
            return []  # Unrecognized verb → no commands

        # Resolve objects, directions, modifiers, etc.
        base_cmd.direct = _resolve_direct_object(action)
        base_cmd.indirect = _resolve_indirect_object(action)
        base_cmd.direction = _resolve_direction(action, base_cmd.verb.uses_directions if base_cmd.verb else False)
        base_cmd.modifier_tokens = _resolve_modifiers(action)

        # Handle ambiguity (may return zero commands)
        if _is_ambiguous(base_cmd.direct, base_cmd.indirect):
            return _handle_ambiguity(action, base_cmd.direct, base_cmd.indirect)


        # ALL expansion (may return multiple commands)
        if _should_expand_all(base_cmd.verb, base_cmd.modifier_tokens):
            return _expand_all(base_cmd)

        # Normal case: one command
        return [base_cmd]

    # ----------------------------------------------------------------------
    # Verb resolution
    # ----------------------------------------------------------------------

    def _resolve_verb(action: ParsedAction) -> Optional[VerbEntry]:
        """Return the canonical VerbEntry or None if unknown."""
        return action.primary_verb

    # ----------------------------------------------------------------------
    # Object resolution
    # ----------------------------------------------------------------------

    def _resolve_direct_object(action: ParsedAction) -> Optional[InterpretedTarget]:
        if not action.noun_candidates:
            return None

        if _should_expand_all(base_cmd.verb, base_cmd.modifier_tokens):
            head = _expand_all(base_cmd)  # list all possible candidates for the verb if "all" modifier is present and verb allows expansion
        else:
            head = [action.noun_candidates[0]]  # assume target is first noun for now  - update in later parser phases


        return InterpretedTarget(
            token_phrase=head,          # until we wire real phrases
            token_head=head,
            token_adjectives=[],        # no adjectives yet
            canonical_head=head,        # will later become lexicon-resolved
        )


    def _resolve_indirect_object(action: ParsedAction) -> Optional[InterpretedTarget]:
        """Resolve the indirect object phrase."""
        # TODO
        return None


    # ----------------------------------------------------------------------
    # Direction resolution
    # ----------------------------------------------------------------------

    def _resolve_direction(action: ParsedAction, uses_directions: bool) -> Optional[str]:
        """Interpret direction tokens into canonical directions."""
        if not action.direction_tokens or not uses_directions:
            return None
        return action.direction_tokens[0]

    # ----------------------------------------------------------------------
    # Modifiers
    # ----------------------------------------------------------------------

    def _resolve_modifiers(action: ParsedAction): 
        """Interpret modifiers (including 'all')."""
        return [action.modifier_tokens] if action.modifier_tokens else []


    def _is_ambiguous(direct, indirect) -> bool:
        """Determine if the command is ambiguous based on unresolved targets."""
        return False  # Placeholder
    
    def _handle_ambiguity(action: ParsedAction, direct, indirect, location) -> List[InterpretedCommand]:
        """Handle ambiguity by generating multiple InterpretedCommands or adding diagnostics."""    
        return []  # Placeholder    
    
    def _should_expand_all(verb: VerbEntry, modifiers: List[str]) -> bool:
        if "all" in modifiers and verb and verb.expand_all:
            return True
        return False   
    
    def _expand_all(base_cmd: InterpretedCommand) -> List[InterpretedCommand]:
        if world is None or base_cmd.verb is None:
            return []

        room = world.state.current_room
        getable: list[Item] = []

        for item in room.items:
             getable.append(item)

        # Items in open containers otherwise the container itself
        for container in room.containers:
            if container.is_openable and container.is_open:
                for item in container.contents:
                    getable.append(item)
            else:
                getable.append(container) 

        return [getable] 
    
    # ----------------------------------------------------------------------
    # Main flow
    # ----------------------------------------------------------------------

    interpreted_commands: List[InterpretedCommand] = []

    base_cmd = InterpretedCommand(    #empty template to fill in during interpretation
            verb=None,   
            all_tokens=None
            )      

    for action in actions:
        cmds = _interpret_single_action(action)
        interpreted_commands.extend(cmds)

    return interpreted_commands

 