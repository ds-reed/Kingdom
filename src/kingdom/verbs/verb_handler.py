# kingdom/verbs/verb_handler.py

from __future__ import annotations
from typing import Optional, Iterable, Callable

from kingdom.models import DispatchContext, Noun, Item, Room


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
    def resolve_noun_or_word(self, target: Optional[Noun], words: Iterable[str]):
        """
        Generic helper for verbs that accept either a noun or a raw word.
        Subclasses can override for verb-specific logic.
        """
        if target is not None:
            return target.canonical_name()

        if words:
            return words[0]

        return None

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
    def find_item_location(self, ctx: DispatchContext, item: Noun):
        """
        Returns 'inventory', 'room', 'box', or None.
        """
        player = self.player(ctx)
        room = self.room(ctx)

        # Player inventory
        if item in player.sack.contents:
            return "inventory"

        # Items on the floor
        if item in room.items:
            return "room"

        # Boxes in the room (the missing case!)
        if item in room.boxes:
            return "box"

        # Items inside boxes
        for box in room.boxes:
            if item in box.contents:
                return "box"

        return None


    # ------------------------------------------------------------
    # Message assembly
    # ------------------------------------------------------------
    def build_message(self, *parts: Optional[str]) -> str:
        """
        Combine non-empty message parts into a single string.
        """
        return "\n".join(p for p in parts if p)

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
        if outcome and outcome.stop:
            return outcome.message or ""
        return None
