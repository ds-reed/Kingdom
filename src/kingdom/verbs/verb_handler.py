# kingdom/verbs/verb_handler.py

from __future__ import annotations
import cmd
from typing import Any, Optional, Iterable, Callable
from enum import Enum, auto
from dataclasses import dataclass, field

from kingdom.model.noun_model import Noun, Item, Room, Container, World 
from kingdom.model.game_init import get_game
from kingdom.item_behaviors import VerbOutcome, VerbControl 
from kingdom.model.direction_model import DIRECTIONS


@dataclass
class ExecuteCommand:
    verb_token: str
    direct_object: Noun = None
    direct_object_token: str = None
    prep_phrases: list[dict] = field(default_factory=list)
    direction: Optional[str] = None
    modifiers: list[str] = field(default_factory=list)

    def __repr__(self):
        return (
            f"ExecuteCommand(verb_token={self.verb_token}, "
            f"direct_object_token={self.direct_object_token}, "
            f"prep_phrases={self.prep_phrases}, "
            f"direction={self.direction}, "
            f"modifiers={self.modifiers})"
        )



class VerbHandler:
    """
    Base class for all verb handlers.
    Provides shared helpers for accessing context, resolving nouns/words,
    common refusal patterns, ALL-handling, and message assembly.

    """

    # ------------------------------------------------------------
    # Context accessors
    # ------------------------------------------------------------
    def world(self):
        return get_game().world         
    
    def game(self):
        return get_game()     

    def room(self) -> Optional[Room]:
        return get_game().current_room

    def player(self):
        return get_game().current_player
    
    def lexicon(self):
        return get_game().lexicon

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
    # preposition/noun resolution helpers
    # ------------------------------------------------------------
    def extract_indirect_from_prep_phrases(
        self,
        prep_phrases: list[dict],
        preps: list[str]
    ) -> tuple[Optional[Noun], str, str]:

        pp = next((pp for pp in prep_phrases if pp["prep"] in preps), None)

        if not pp:
            return None, "", ""

        obj = pp["object"]
        return (
            obj.noun_object,
            obj.token_head,
            pp["prep"],
        )


    # ------------------------------------------------------------
    # Basic checks - used by multiple verbs 
    # ------------------------------------------------------------

    def basic_checks(self, target, *, verb_phrase=None, capability_attr=None, current_state_attr=None, desired_state=None, already_msg=None, indirect=None, ind_capability_attr=None, ind_phrase=None) -> Optional[str]:

        if capability_attr and not getattr(target, capability_attr, False):
            return self.cannot(target, verb_phrase)

        if ind_capability_attr and indirect is not None and not getattr(indirect, ind_capability_attr, False):
            return self.cannot(indirect, ind_phrase)

        if current_state_attr is not None:
            current = getattr(target, current_state_attr, None)
            if current == desired_state:
                return self.already(target, already_msg)

        return None
    
    def require_item(self, *, required_type:str, required_name:str = None, noun:Noun = None, verb_phrase=None, indirect:str = None) -> Optional[str]:
        player = self.player()
        inventory = player.get_inventory_items()
        for item in inventory:
 #    if the item has an attribute matching the string required type and the value of that attribute matches the required name, 
 #    then we consider the requirement met. This allows for flexible requirements like "a key that unlocks the chest" without 
 #    hardcoding specific item names in the verb handler.
            if hasattr(item, required_type):
                if required_name is None or getattr(item, required_type) == required_name:
                    return None  # requirement met
        else:
            return f"You don't have the right {indirect} to {verb_phrase} the {noun.canonical_name()}."

    def lookup_required_item_id(self, required_name, verb_phrase) -> Noun | None:
        required = Item.get_by_name(required_name)
        if required is None:
             print(f"Error: Required noun '{required_name}' not found in game data for {verb_phrase}.")
             return None
        return required   

  
    # ------------------------------------------------------------
    # Direction helpers  - remove when new parser is fully wired in
    # ------------------------------------------------------------
    def is_direction(self, token: str) -> bool:
        """
        True if the token is a known direction or synonym.
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
        return DIRECTIONS.get_canonical(token)

    def extract_direction_from_words(self, words: Iterable[str]) -> str | None:
        """
        Look at leftover words and return the first canonical direction if present.
        """
        for w in words:
            if DIRECTIONS.is_direction(w):
                return DIRECTIONS.get_canonical(w)
        return None

    def get_reverse_of(self, direction: str) -> Optional[str]:
        """
        Return the canonical reverse of a direction, or None if not a direction or no reverse.
        """
        if not self.is_direction(direction):
            return None
        return DIRECTIONS.get_reverse(direction)
    
    
    # ------------------------------------------------------------
    # Noun / word resolution - remove when new parser is fully wired in
    # ------------------------------------------------------------
    def resolve_noun_or_word(
        self,
        words: Iterable[str],
        interest: list[str] = [],
    ) -> dict:
        """
        This internal resolution system is in place until we upgrade the parser.
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
    

    # ------------------------------------------------------------
    # Message assembly - remove when new rendering system is developed
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
