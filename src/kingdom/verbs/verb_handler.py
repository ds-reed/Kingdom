# kingdom/verbs/verb_handler.py

from __future__ import annotations
from typing import Optional, Iterable, Callable

from kingdom.models import DispatchContext, Noun, Item, Room, Box, ItemLocation, LocationType, Game, DirectionNoun
from kingdom.models import DIRECTIONS
from kingdom.item_behaviors import VerbOutcome, VerbControl 

class VerbHandler:
    """
    Base class for all verb handlers.
    Provides shared helpers for accessing context, resolving nouns/words,
    common refusal patterns, ALL-handling, and message assembly.
    """

    # ------------------------------------------------------------
    # Context accessors
    # ------------------------------------------------------------
    def game(self, ctx: DispatchContext):
        return ctx.game

    def state(self, ctx: DispatchContext):
        return ctx.state

    def room(self, ctx: DispatchContext) -> Optional[Room]:
        return ctx.state.current_room

    def player(self, ctx: DispatchContext):
        return ctx.game.current_player

    # ------------------------------------------------------------
    # Standard refusal helpers
    # ------------------------------------------------------------
    def missing_target(self, verb: str) -> str:
        return f"{verb.capitalize()} what?"

    def not_here(self, noun: Noun) -> str:
        return f"You don't see the {noun.display_name()} here."

    def not_in_inventory(self, noun: Noun) -> str:
        return f"You aren't carrying the {noun.display_name()}."

    # ------------------------------------------------------------
    # Noun / word resolution
    # ------------------------------------------------------------
    def resolve_noun_or_word(
        self,
        target: Optional[Noun],
        words: Iterable[str],
        interest: list[str] = [],
    ) -> dict:
        """
        Resolve either a noun, direction (highest priority) or any keywords of interest
        found in the leftover words. Returns a dict with structured results.
        """

        result = {
            "noun": None,
            "direction": None,
            "keywords": set(),
            "raw": tuple(words),
        }
        # 1. If we already have a resolved target
        if target is not None:
            if isinstance(target, DirectionNoun):    #check the special case of direction noun first, and resolve it immediately if so.
                direction = target.canonical_direction
                result["noun"] = target
                result["direction"] = direction
                return result
            else:
                # Regular noun — early return
                result["noun"] = target
                return result


        # 2. No resolved target → scan words for direction (even if not in legal candidates)
        for w in words:
            lw = w.lower().strip()
            if self.is_direction(lw):
                canon = self.canonical_direction(lw)
                if canon:
                    result["direction"] = canon
                    # Optionally store the raw word that matched
                    result["direction_raw"] = w
                    break  # take the first direction word found

        # 3. If no direction, look for keywords of interest
        interest_set = {w.lower() for w in interest}
        for w in words:
            lw = w.lower()
            if lw in interest_set and lw not in result["keywords"]:
                result["keywords"].add(lw)

        return result

    # ------------------------------------------------------------
    # ALL-handling framework 
    # ------------------------------------------------------------
    def handle_all(
        self,
        ctx: DispatchContext,
        items: Iterable[Noun],
        single_fn: Callable[[DispatchContext, Noun, tuple[str, ...]], str],
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
            result = single_fn(ctx, item, ("all",))
            if result:
                messages.append(result)
            names.append(item.canonical_name())

        summary = (
            f"You {verb_name} {len(names)} "
            f"item{'s' if len(names) != 1 else ''}: {', '.join(names)}."
        )

        return "\n".join(messages + [summary])

    # looks for item in inventory, room or in boxes or a box itself if asked for.
    def locate_item(self, ctx: DispatchContext, item: Noun) -> Optional[ItemLocation]:
        """
        Determine exactly where an item is located, returning a rich ItemLocation
        or None if the item cannot be found in the current context.
        """
        player = self.player(ctx)
        room = self.room(ctx)

        if room is None:
            return None  # rare safety case

        # 1. Directly in player's inventory / sack
        if player.has_item(item):                  # ← use your Player helper method
            return ItemLocation(LocationType.INVENTORY)

        # 2. Loose on the room floor
        if room.has_item(item):      # ← use your Room helper
            return ItemLocation(LocationType.ROOM_FLOOR)

        # 3. The item is a box/container and is present in the room itself
        if isinstance(item, Box) and room.has_box(item):   # ← use your Room helper
            return ItemLocation(LocationType.BOX_IN_ROOM)

        # 4. Item is inside some box/container in the room
        containing_box = room.find_containing_box(item)   # ← use your Room helper
        if containing_box is not None:
            return ItemLocation(LocationType.INSIDE_BOX, container=containing_box)

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
    def run_special_handler(self, target: Noun, verb: str, words, ctx: DispatchContext):
        """
        Wrapper for item special handlers.
        Subclasses call this before performing their main logic.
        """
        from kingdom.item_behaviors import try_item_special_handler

        outcome = try_item_special_handler(target, verb, words, ctx)
        if outcome:
            return outcome
        
        return None
