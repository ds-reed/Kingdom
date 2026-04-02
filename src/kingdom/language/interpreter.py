# Interpreter.py
# Converts ParsedActions -> InterpretedCommands (zero, one, or many)
# Pure, deterministic, no world mutation.

from dataclasses import dataclass, field
from typing import List, Optional

from kingdom.language.parser import ParsedAction
from kingdom.language.lexicon import Lexicon, VerbEntry

from kingdom.model.direction_model import DIRECTIONS
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Item, World, Room
from kingdom.model.verb_model import Verb 

@dataclass(frozen=False)
class InterpretedTarget:
    token_phrase: str
    token_head: str
    token_adjectives: List[str]
    noun_object: Item
    
    def __repr__(self):
        return f"InterpretedTarget(token_phrase={self.token_phrase}, token_head={self.token_head}, token_adjectives={self.token_adjectives})"


@dataclass(frozen=False)
class InterpretedCommand:
    # Required fields (no defaults)
    verb: VerbEntry  
    verb_token: str                                                     # user entered verb token                                                   
    all_tokens: List[str]                                               # all tokens from the input

    # Optional semantic fields

    verb_source: Optional[str] = "explicit"                             # how the verb was determined (e.g., "explicit", "implicit", "unknown")


    direct: InterpretedTarget = None                                    # the direct object of the verb, if any
    direct_object_token: Optional[str] = None                           # the token of the direct object, if any
    
    prep_phrases: List[dict] = field(default_factory=list)              # list of {"prep": preposition, "object": InterpretedTarget} for any prepositional phrases

    direction: Optional[str] = None                                     # canonical direction (e.g., "north", "up", etc.) if verb uses directions and a direction token was present
    direction_tokens: List[str] = field(default_factory=list)           # all direction tokens from the input (unclear purpose)

    modifier_tokens: List[str] = field(default_factory=list)            # e.g., ["all"], ["quickly"], etc.

    def __repr__(self):
        return f"InterpretedCommand(verb={self.verb.name if self.verb else None}, verb_source={self.verb_source}, verb_token={self.verb_token}, \n \
        direct={self.direct.token_head if self.direct else None},  \n \
        prep_phrases={self.prep_phrases}, \n \
        direction={self.direction}, modifiers={self.modifier_tokens}, all_tokens={self.all_tokens}) \n" 


def _iter_local_target_candidates(room: Room):
    """Yield all noun objects visible from the given room (items, containers, features, player inventory)."""
    yield room
    for item in room.items:
        yield item
    for container in room.containers:
        yield container
        if getattr(container, "is_transparent", False):
            for item in container.contents:
                yield item
    for feature in room.features:
        yield feature

    player = getattr(get_game(), "current_player", None)
    if player is not None:
        for item in player.sack.contents:
            yield item


def _resolve_target_noun(room: Room, target_name: str) -> object | None:
    """Backward-compatible wrapper that resolves by head noun only."""
    return _resolve_target_noun_with_adjectives(room, target_name, token_adjectives=[])


def _normalize_tokens_for_match(values: List[str]) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        parts = [part for part in str(value).strip().lower().split() if part]
        if parts:
            normalized.add(" ".join(parts))
    return normalized


def _score_candidate_by_adjectives(candidate: object, token_adjectives: List[str]) -> int:
    if not token_adjectives:
        return 0

    candidate_adjectives = _normalize_tokens_for_match(getattr(candidate, "adjectives", []))
    if not candidate_adjectives:
        return 0

    requested_adjectives = _normalize_tokens_for_match(token_adjectives)
    return sum(1 for adjective in requested_adjectives if adjective in candidate_adjectives)


def _resolve_target_noun_with_adjectives(
    room: Room,
    target_name: str,
    token_adjectives: List[str] | None,
) -> object | None:
    """Resolve local target with two-pass strategy: head-match, then adjective scoring."""
    matches = [
        candidate
        for candidate in _iter_local_target_candidates(room)
        if candidate.matches_reference(target_name)
    ]

    if not matches:
        return None

    # Preserve historical behavior when we have no ambiguity signal.
    if not token_adjectives or len(matches) == 1:
        return matches[0]

    scored = [(_score_candidate_by_adjectives(candidate, token_adjectives), candidate) for candidate in matches]
    best_score = max(score for score, _ in scored)
    if best_score <= 0:
        return matches[0]

    # Deterministic tie-break: keep local iteration order (first among equals).
    for score, candidate in scored:
        if score == best_score:
            return candidate

    return matches[0]


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

        # ----------------------------------------------------------------------
        # Verb resolution
        # ----------------------------------------------------------------------

        def _resolve_verb(action: ParsedAction) -> tuple[Optional[Verb], Optional[str], Optional[str]]:
            """Return the Verb or None if unknown."""
            return getattr(action.primary_verb, "verb_object", None), action.verb_source , action.primary_verb_token 

        # ----------------------------------------------------------------------
        # Object resolution
        # ----------------------------------------------------------------------
        def _resolve_target(head: Optional[str], token_phrase, token_adjectives: Optional[List[str]] = None) -> InterpretedTarget:
            room = get_game().current_room
            target = (
                _resolve_target_noun_with_adjectives(room, head, token_adjectives or [])
                if room is not None and head
                else None
            )
            return InterpretedTarget(
                token_phrase=token_phrase,
                token_head=head,
                token_adjectives=token_adjectives or [],
                noun_object=target if target else None,
            )


        def _resolve_direct_object(action: ParsedAction) -> Optional[InterpretedTarget]:

            # No direct object at all

            if not action.object_phrases:
                return None

            # TODO: The direct object NP is always the first object phrase until multi object support is implemented.  
            np = action.object_phrases[0]
            head = np["head"]

            return _resolve_target(
                head=head,
                token_phrase=np,
                token_adjectives=np.get("adjectives", []),
            )

            
        def _resolve_prep_phrases(action: ParsedAction) -> list[dict]:
            resolved = []

            for pp in action.prep_phrases:
                prep = pp["prep"]          # canonical preposition
                head = pp["object"]        # surface noun token

                target = _resolve_target(
                    head=head,
                    token_phrase=prep,
                    token_adjectives=[],
                )

                resolved.append({
                    "prep": prep,
                    "object": target
                })

            return resolved


        def _resolve_direction(action: ParsedAction, uses_directions: bool) -> Optional[str]:
            """Interpret direction tokens into canonical directions."""
            if not action.direction_tokens or not uses_directions:
                return None
            return DIRECTIONS.get_canonical(action.direction_tokens[0])     # only handling one direction at the moment

        def _resolve_modifiers(action: ParsedAction): 
            """Interpret modifiers (including 'all')."""
            return action.modifier_tokens if action.modifier_tokens else []

        def _is_ambiguous(direct, prep_phrases) -> bool:
            """Determine if the command is ambiguous based on unresolved targets."""
            return False  # Placeholder
        
        def _handle_ambiguity(action: ParsedAction, direct, prep_phrases, location) -> List[InterpretedCommand]:
            """Handle ambiguity by generating multiple InterpretedCommands or adding diagnostics."""    
            return []  # Placeholder    
        
        def _handle_no_verb_case(cmd: InterpretedCommand):
            """Handle cases where no verb was identified (e.g., just a noun or direction)."""
            if base_cmd.direct_object_token:
                return  # may be a follow-up response. Pass the noun with no verb
            for word in base_cmd.all_tokens:
                if word in lexicon.token_to_direction:
                    base_cmd.verb = Verb.get_by_name("go")
                    base_cmd.verb_source = "implicit"
                    base_cmd.direction = lexicon.token_to_direction[word].canonical
                    return  
            return  
    

    # ----------------------------------------------------------------------
    # Single Action Flow
    # ----------------------------------------------------------------------
        base_cmd = InterpretedCommand(    #empty template to fill in during interpretation
        verb=None,
        verb_token="",   
        all_tokens=action.tokens,
        )      

        base_cmd.verb, base_cmd.verb_source, base_cmd.verb_token = _resolve_verb(action)

        # Resolve objects, directions, modifiers, etc.
        base_cmd.direct = _resolve_direct_object(action)
        base_cmd.direct_object_token = base_cmd.direct.token_head if base_cmd.direct else None
        base_cmd.prep_phrases = _resolve_prep_phrases(action)
        base_cmd.direction = _resolve_direction(action, base_cmd.verb.uses_directions if base_cmd.verb else False)
        base_cmd.modifier_tokens = _resolve_modifiers(action)

        # Handle ambiguity (may return zero commands)
        if _is_ambiguous(base_cmd.direct, base_cmd.prep_phrases):
            _handle_ambiguity(action, base_cmd.direct, base_cmd.prep_phrases, location=None)

        #handle no verb case after everythingn is resolved - will populate InterpretedCommand with implicit verb and direction if found
        if base_cmd.verb is None:
            _handle_no_verb_case(base_cmd)



        # Normal case: one command
        return [base_cmd]

    
    # ----------------------------------------------------------------------
    # Main flow
    # ----------------------------------------------------------------------

    interpreted_commands: List[InterpretedCommand] = []

    for action in actions:
        cmds = _interpret_single_action(action)
        interpreted_commands.extend(cmds)

    return interpreted_commands

 