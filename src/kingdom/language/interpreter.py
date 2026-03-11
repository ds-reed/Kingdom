# Interpreter.py
# Converts ParsedActions → InterpretedCommands (zero, one, or many)
# Pure, deterministic, no world mutation.

from dataclasses import dataclass
from typing import List, Optional

from kingdom.language.parser import ParsedAction
from kingdom.language.lexicon import Lexicon, VerbEntry, NounEntry

from dataclasses import dataclass, field
from typing import Optional, List

from kingdom.model.noun_model import Item, World
from kingdom.model.verb_model import Verb 

@dataclass(frozen=False)
class InterpretedTarget:
    token_phrase: str
    token_head: str
    token_adjectives: List[str]
    noun_object: Item


@dataclass(frozen=False)
class InterpretedCommand:
    # Required fields (no defaults)
    verb: VerbEntry                                                     
    all_tokens: List[str]                                               # all tokens from the input

    # Optional semantic fields

    verb_source: Optional[str] = "explicit"                             # how the verb was determined (e.g., "explicit", "implicit", "unknown")

    direct: InterpretedTarget = None                                    # the direct object of the verb, if any
    prep_phrases: List[dict] = field(default_factory=list)              # list of {"prep": preposition, "object": InterpretedTarget} for any prepositional phrases

    direction: Optional[str] = None                                     # canonical direction (e.g., "north", "up", etc.) if verb uses directions and a direction token was present
    direction_tokens: List[str] = field(default_factory=list)           # all direction tokens from the input (unclear purpose)

    modifier_tokens: List[str] = field(default_factory=list)            # e.g., ["all"], ["quickly"], etc.

    def __repr__(self):
        return f"InterpretedCommand(verb={self.verb.name if self.verb else None}, verb_source={self.verb_source}, \n \
        direct={self.direct.token_head if self.direct else None},  \n \
        prep_phrases={self.prep_phrases}, \n \
        direction={self.direction}, modifiers={self.modifier_tokens}, all_tokens={self.all_tokens}) \n" 




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

        def _resolve_verb(action: ParsedAction) -> tuple[Optional[Verb], Optional[str]]:
            """Return the Verb or None if unknown."""
            return getattr(action.primary_verb, "verb_object", None), action.verb_source 

        # ----------------------------------------------------------------------
        # Object resolution
        # ----------------------------------------------------------------------
        def _resolve_direct_object(action: ParsedAction) -> List[InterpretedTarget]:
            # No direct object at all

            if not action.object_phrases:
                return None

            # The direct object NP is always the first object phrase
            np = action.object_phrases[0]
            head = np["head"]

            # Normal (non-ALL) case
            noun_entry = lexicon.token_to_noun.get(head)
            if not noun_entry:
                return None

            return InterpretedTarget(
                    token_phrase=head,
                    token_head=head,
                    token_adjectives=np.get("adjectives", []),
                    noun_object=noun_entry.noun_object,
                )
            

            
        def _resolve_prep_phrases(action: ParsedAction) -> list[dict]:
            resolved = []

            for pp in action.prep_phrases:
                prep = pp["prep"]          # canonical preposition
                head = pp["object"]        # surface noun token

                # Resolve surface noun → NounEntry
                noun_entry = lexicon.token_to_noun.get(head)

                if noun_entry:
                    target = InterpretedTarget(
                        token_phrase=prep,
                        token_head=head,
                        token_adjectives=[],
                        noun_object=noun_entry.noun_object,
                    )

                    resolved.append({
                        "prep": prep,
                        "object": target
                    })

            return resolved


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
            return action.modifier_tokens if action.modifier_tokens else []

        def _is_ambiguous(direct, prep_phrases) -> bool:
            """Determine if the command is ambiguous based on unresolved targets."""
            return False  # Placeholder
        
        def _handle_ambiguity(action: ParsedAction, direct, prep_phrases, location) -> List[InterpretedCommand]:
            """Handle ambiguity by generating multiple InterpretedCommands or adding diagnostics."""    
            return []  # Placeholder    
    

    # ----------------------------------------------------------------------
    # Single Action Flow
    # ----------------------------------------------------------------------
        base_cmd = InterpretedCommand(    #empty template to fill in during interpretation
        verb=None,   
        all_tokens=action.tokens,
        )      

        base_cmd.verb, base_cmd.verb_source = _resolve_verb(action)

        # Resolve objects, directions, modifiers, etc.
        base_cmd.direct = _resolve_direct_object(action)
        base_cmd.prep_phrases = _resolve_prep_phrases(action)
        base_cmd.direction = _resolve_direction(action, base_cmd.verb.uses_directions if base_cmd.verb else False)
        base_cmd.modifier_tokens = _resolve_modifiers(action)

        # Handle ambiguity (may return zero commands)
        if _is_ambiguous(base_cmd.direct, base_cmd.prep_phrases):
            return _handle_ambiguity(action, base_cmd.direct, base_cmd.prep_phrases, location=None)

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

 