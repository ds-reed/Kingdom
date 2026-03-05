# kingdom/verbs/verb_handler.py

from __future__ import annotations
from typing import Optional, Iterable, Callable
from enum import Enum, auto
from dataclasses import dataclass

from kingdom.model.noun_model import Noun, Item, Room, Container, World, DirectionNoun, DIRECTIONS
from kingdom.model.game_init import get_action_state
from kingdom.item_behaviors import VerbOutcome, VerbControl 

class VerbHandler:
    """
    Base class for all verb handlers.
    Provides shared helpers for accessing context, resolving nouns/words,
    common refusal patterns, ALL-handling, and message assembly.

    It supports a standard pipeline for verb excution as follows:
    1. The parser identifies the verb and resolves a target noun.
    2. The verb dispatcher calls the corresponding method on the appropriate 
    VerbHandler subclass, passing context token, target noun, and leftover words.
    3. The verb handler method uses the following flow
         - First call self.resolve_noun_or_word() to parse the target noun and any keywords 
           of interest from the leftover words.
         - Next check for keywords in the leftover words to modify behavior if appropriate
         - Then call self.run_special_handler() to check for any item-specific special 
           handling that should take precedence over default verb logic.
         - If no special handling occurs, perform main logic based on the resolved target 
           and context.
         - Finally, returns a message  (string, list of strings, list of lists...) to be 
           displayed to the player using the self.build_message() helper
        -  Note: internal helper functions should return strings or lists and not call 
                 build_message directly 
    """

    class LocationType(Enum):
        """Where an item can physically be in the game world."""
        INVENTORY     = auto()   # directly in player's sack/inventory
        ROOM_FLOOR    = auto()   # loose on the room floor
        CONTAINER_IN_ROOM   = auto()   # the container itself is present in the room
        INSIDE_CONTAINER    = auto()   # inside a container

    @dataclass(frozen=True)
    class ItemLocation:
        """Precise, type-safe description of an item's location."""
        type: 'VerbHandler.LocationType'
        container: Optional['Container'] = None   # only relevant for INSIDE_CONTAINER

        def is_accessible(self) -> bool:
            """Quick default rule — override or extend per verb if needed."""
            match self.type:
                case VerbHandler.LocationType.INVENTORY | VerbHandler.LocationType.ROOM_FLOOR | VerbHandler.LocationType.CONTAINER_IN_ROOM:
                    return True
                case VerbHandler.LocationType.INSIDE_CONTAINER:
                    # Assuming Container has .is_open (bool) or similar
                    return self.container is not None and self.container.is_open
                case _:
                    return False

        def describe(self) -> str:
            """Human-readable phrase for messages."""
            match self.type:
                case VerbHandler.LocationType.INVENTORY:
                    return "in your inventory"
                case VerbHandler.LocationType.ROOM_FLOOR:
                    return "here on the ground"
                case VerbHandler.LocationType.CONTAINER_IN_ROOM:
                    return "here (as a container)"
                case VerbHandler.LocationType.INSIDE_CONTAINER if self.container:
                    return f"inside the {self.container.display_name()}"
                case _:
                    return "somewhere strange"



    # ------------------------------------------------------------
    # Context accessors
    # ------------------------------------------------------------
    def game(self):
        return get_action_state().game

    def state(self):
        return get_action_state()

    def room(self) -> Optional[Room]:
        return get_action_state().current_room

    def player(self):
        return get_action_state().current_player

    # ------------------------------------------------------------
    # Standard refusal helpers
    # ------------------------------------------------------------
    def missing_target(self, verb_phrase: str) -> str:
        return f"{verb_phrase.capitalize()} what?"

    def not_here(self, noun: Noun) -> str:
        return f"You don't see any {noun.canonical_name()} here."   #calling with non-target may provide spoilers. Need to refine with a 'found' flag on item in the future.

    def not_in_inventory(self, noun: Noun) -> str:
        return f"You don't have any {noun.canonical_name()}."       #calling with non-target may provide spoilers. Need to refine with a 'found' flag on item in the future.

    def cannot(self, noun: Noun, verb_phrase: str) -> str:
        return f"You can't {verb_phrase} the {noun.canonical_name()}."
    
    def already(self, noun: Noun, msg: str) -> str:
        return f"The {noun.canonical_name()} is already {msg}."
    
    def unrecognized_word(self, object_word: str) -> str:           
        return f"I see no {object_word} here."
    

    # ------------------------------------------------------------
    # Noun / word resolution
    # ------------------------------------------------------------
    def resolve_noun_or_word(
        self,
        words: Iterable[str],
        interest: list[str] = [],
    ) -> dict:
        """
        This internal resolution system is in place until we upgrade the parser. Right now, 
        verbs get passed a target noun and a list of leftover words. The target noun has
        been pre-resolved to be a valid target Item or DirectionNoun for the room the player
        is in. (i.e. only nouns that are present in the room or valid directions will be passed as
        the target argument.) 
        
        This function allows verb handlers to resolve an item or direction from the leftover words.

        It also enables verbs to modify their behavior based on keywords in the leftover words, 
        e.g. "look inside"  

        The function returns a dict with the following keys:
        - "noun": the resolved Noun (or None if no noun found in words)
        - "direction": the resolved canonical direction string (or None if no direction found)
        - "keywords": a set of any keywords of interest that were found in the words
        - "raw": a tuple of the original leftover words

        Note that the target noun is not handled in the resolution - we just parse the leftover words.
        """

        result = {
            "noun": None,
            "direction": None,
            "keywords": set(),
            "raw": tuple(words),
        }
        
        interest_set = {w.lower() for w in interest}
        
        for w in words:
            lw = w.lower().strip()
            matching_nouns = [noun for noun in Noun.all_nouns if noun.canonical_name() == lw]
            if matching_nouns and result["noun"] is None:  # take the first match if multiple - can only handle one right now
                result["noun"] = matching_nouns[0]            
            if self.is_direction(lw):
                canon = self.canonical_direction(lw)
                if canon and result["direction"] is None:  # take the first match if multiple - can only handle one right now
                    result["direction"] = canon
            if lw in interest_set and lw not in result["keywords"]:
                result["keywords"].add(lw)                  # supports multiple keywords, but order is not preserved (use a list if order matters)


        return result

    def basic_checks(self, target, *, verb_phrase=None, capability_attr=None, current_state_attr=None, desired_state=None, already_msg=None):

        if capability_attr and not getattr(target, capability_attr, False):
            return self.cannot(target, verb_phrase)

        if current_state_attr is not None:
            current = getattr(target, current_state_attr, None)
            if current == desired_state:
                return self.already(target, already_msg)

        return None

    # ------------------------------------------------------------
    # ALL-handling framework  - needs a re-write
    # ------------------------------------------------------------
    def handle_all(
        self,
        items: Iterable[Noun],
        single_fn: Callable[[Noun, tuple[str, ...]], str],
        verb_name: str,
    ) -> str:
        """
        Generic ALL handler:  
        - loops through items
        - calls the single-item handler
        - accumulates messages
        - returns a summary
        """
        items = list(items)
        if not items:
            return f"There is nothing you can {verb_name}."

        messages = []
        names = []

        for item in items:
            result = single_fn(item, ("all",))
            if result:
                messages.append(result)
            names.append(item.canonical_name())

        return "\n".join(messages)

    # looks for item in inventory, room or in containers or a container itself if asked for.
    def locate_item(self, item: Noun) -> Optional[ItemLocation]:
        """
        Determine exactly where an item is located, returning a rich ItemLocation
        or None if the item cannot be found in the current context.
        """
        player = self.player()
        room = self.room()

        if room is None:
            return None  # rare safety case

        # 1. Directly in player's inventory / sack
        if player.has_item(item):                  # ← use your Player helper method
            return self.ItemLocation(self.LocationType.INVENTORY)

        # 2. Loose on the room floor
        if room.has_item(item):      # ← use your Room helper
            return self.ItemLocation(self.LocationType.ROOM_FLOOR)

        # 3. The item is a containerand is present in the room itself
        if isinstance(item, Container) and room.has_container(item):   # ← use your Room helper
            return self.ItemLocation(self.LocationType.CONTAINER_IN_ROOM)

        # 4. Item is inside some container in the room
        containing_container = room.find_containing_container(item)   # ← use your Room helper
        if containing_container is not None:
            return self.ItemLocation(self.LocationType.INSIDE_CONTAINER, container=containing_container)

        return None

    # ------------------------------------------------------------
    # Direction helpers
    # ------------------------------------------------------------
    def is_direction(self, token: str) -> bool:
        """
        True if the token is a known direction or alias.
        """
        if not token:
            return False
        return DIRECTIONS.is_direction(token)

    def canonical_direction(self, token: str) -> str | None:
        """
        Return the canonical direction for a token, or None if not a direction.
        """
        if not token:
            return None
        if not DIRECTIONS.is_direction(token):
            return None
        return DIRECTIONS.to_canonical(token)

    def extract_direction_from_words(self, words: Iterable[str]) -> str | None:
        """
        Look at leftover words and return the first canonical direction if present.
        """
        for w in words:
            if DIRECTIONS.is_direction(w):
                return DIRECTIONS.to_canonical(w)
        return None

    def get_reverse_of(self, direction: str) -> Optional[str]:
        """
        Return the canonical reverse of a direction, or None if not a direction or no reverse.
        """
        if not self.is_direction(direction):
            return None
        return DIRECTIONS.reverse_of(direction)

    # ------------------------------------------------------------
    # Message assembly
    # ------------------------------------------------------------
    def build_message(self, *parts) -> str:
        """
        Combine non-empty message parts into a single string with newlines.
        
        Accepts:
        - strings
        - a single list (flat or nested)
        - a mix of strings and lists (any depth)

        """
        def flatten(items):
            """Recursively flatten any nesting of lists/strings/None."""
            result = []
            for item in items:
                if item is None:
                    continue
                if isinstance(item, str):
                    if item.strip():  # skip empty/whitespace-only strings
                        result.append(item)
                elif isinstance(item, (list, tuple)):
                    result.extend(flatten(item))
                else:
                    # Convert anything else to string (safety)
                    s = str(item).strip()
                    if s:
                        result.append(s)
            return result

        # Flatten everything that was passed
        flat_parts = flatten(parts)

        return "\n".join(flat_parts)

    # ------------------------------------------------------------
    # Special handler pipeline
    # ------------------------------------------------------------
    def run_special_handler(self, target: Noun, verb: str, words):
        """
        Wrapper for item special handlers.
        Subclasses call this before performing their main logic.
        """
        from kingdom.item_behaviors import try_item_special_handler

        outcome = try_item_special_handler(target, verb, words, None)
        if outcome:
            return outcome
        
        return None
