"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

from kingdom.dispatch_context import DispatchContext
from kingdom.models import Verb, Noun, Room
from kingdom.parser import normalize_direction_token
from kingdom.terminal_style import TRS80_WHITE, trs80_print, trs80_clear_and_show_room
from kingdom.render import render_current_room

_DIRECTION_ORDER = {
    "up": 0,
    "down": 1,
    "north": 2,
    "south": 3,
    "east": 4,
    "west": 5,
}

_VERTICAL_DIRECTION_LABELS = {
    "up": "above",
    "down": "below",
}



class MovementVerbHandler:

    def transition(self, state, direction):
        """Core movement engine: normalize, validate, move, render."""
        if state.current_room is None:
            return "There is nowhere to go."

        canonical = normalize_direction_token(direction)
        next_room = state.current_room.get_connection(canonical)

        if next_room is None:
            return f"You can't go {canonical} from here."

        state.current_room = next_room
        trs80_print(f"You go {canonical}.", style=TRS80_WHITE)
        render_current_room(state, clear=False)
        print()
        return ""

    def resolve_direction(self, target, target_words):
        """Extract direction from noun or raw text."""
        if target is not None:
            direction = getattr(target, "canonical_direction", None)
            if direction is None and hasattr(target, "get_noun_name"):
                return normalize_direction_token(target.get_noun_name())
            return direction

        if target_words:
            return normalize_direction_token(target_words[0])

        return None

    def go(self, context, target, target_words):
        """High-level GO verb."""
        state = context.state
        direction = self.resolve_direction(target, target_words)

        if not direction:
            return "Go where?"

        return self.transition(state, direction)










    # Add more movement verbs as needed
