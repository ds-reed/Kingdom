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

    def climb(self, context, target, target_words):
        """High-level CLIMB verb."""
        state = context.state
        if state.current_room is None:
            return "There is nowhere to climb."

        # Try to resolve a direction (up/down)
        direction = self.resolve_direction(target, target_words)

        # No direction given → infer from available exits
        if direction is None:
            vertical_exits = [
                d for d in state.current_room.available_directions(visible_only=True)
                if d in {"up", "down"}
            ]

            if len(vertical_exits) == 1:
                # Only one vertical exit → climb it
                return self.transition(state, vertical_exits[0])

            if not vertical_exits:
                return "There is nothing here to climb."

            return "Climb where? Up or down?"

        # Direction given but not vertical
        if direction not in {"up", "down"}:
            return "You can only climb up or down."

        # Normal movement
        return self.transition(state, direction)

    def swim(self, context, target, target_words):
        """High-level SWIM verb."""
        state = context.state
        game = context.game

        if state.current_room is None:
            return "There is nowhere to swim."

        # 1. Resolve direction
        direction = self.resolve_direction(target, target_words)

        # 2. Check player constraints (drowning logic)
        constraint_error = self._check_swim_constraints(game)
        if constraint_error:
            return constraint_error

        # 3. Room-specific swim destination
        room = state.current_room
        destination_room = self._resolve_swim_destination(game, room)

        if destination_room:
            # If direction is given but invalid, reject it
            if direction and room.get_connection(direction) is None:
                return f"You can't go {direction} from here."

            # Teleport-style swim
            state.current_room = destination_room
            trs80_print("You swim across.", style=TRS80_WHITE)
            render_current_room(state, clear=False)
            print()
            return ""

        # 4. No special swim_destination → treat like GO
        if not direction:
            return "There is nowhere to swim across."

        if room.get_connection(direction) is None:
            return f"You can't go {direction} from here."

        return self.transition(state, direction)


    def _resolve_swim_destination(self, game, room):
        """Return a destination Room or None if no swim_destination is defined."""
        destination_name = getattr(room, "swim_destination", None)
        if not destination_name:
            return None

        # Look up by name
        for r in game.rooms:
            if r.name.lower() == destination_name.lower():
                return r
        return None


    def _check_swim_constraints(self, game):
        """Return an error string or raise GameOver if player cannot swim."""
        player = game.require_player(return_error=True)
        if isinstance(player, str):
            return player

        heavy_item = next(
            (item for item in player.sack.contents if getattr(item, "too_heavy_to_swim", False)),
            None
        )
        if heavy_item is not None:
            raise GameOver(
                "The gold bar drags you under as you try to swim. You drown. GAME OVER."
            )

        return None

    def teleport(self, context, target, target_words):
        """Teleport to any room by name or number. No target → list rooms."""
        state = context.state
        game = context.game

        if state.current_room is None:
            return "No current room — cannot teleport."

        # No argument → show list
        if not target_words and target is None:
            room_list = sorted(game.rooms, key=lambda r: r.name)
            if not room_list:
                return "No rooms in the world yet."

            lines = ["Debug teleport — available rooms:"]
            for i, room in enumerate(room_list, 1):
                lines.append(f"  {i:2d}. {room.name}")
            lines.append("")
            lines.append("Usage: teleport <name or number>")
            lines.append("       goto 7")
            return "\n".join(lines)

        # Resolve target room
        target_room = None

        # 1. Direct noun target (e.g. "teleport throne room" where throne room is a DirectionNoun or other noun)
        if target is not None:
            if isinstance(target, Room):
                target_room = target
            else:
                # Try matching noun name against room names
                query = target.get_noun_name().lower()
                for r in game.rooms:
                    if query in r.name.lower() or query in r.get_noun_name().lower():
                        target_room = r
                        break

        # 2. Words fallback (e.g. "teleport kitchen" or "tp 4")
        if target_room is None and target_words:
            query = " ".join(target_words).strip().lower()

            # Number?
            try:
                idx = int(query) - 1
                rooms_sorted = sorted(game.rooms, key=lambda r: r.name)
                if 0 <= idx < len(rooms_sorted):
                    target_room = rooms_sorted[idx]
            except ValueError:
                pass

            # Name prefix/partial match
            if target_room is None:
                matches = [r for r in game.rooms if query in r.name.lower() or query in r.get_noun_name().lower()]
                if len(matches) == 1:
                    target_room = matches[0]
                elif len(matches) > 1:
                    names = ", ".join(r.name for r in matches)
                    return f"Ambiguous room name — matches: {names}"
                # else → error below

        if target_room is None:
            return "No matching room. Use 'teleport' alone to list rooms."

        # Perform the teleport
        old_room_name = state.current_room.name
        state.current_room = target_room

        # Mark visited so full description shows immediately
        target_room.visited = True

        # Render the new room
        render_current_room(state, clear=True)  # or False if you prefer keeping the prompt visible
        print()  # extra line for readability

        return f"Teleported: {old_room_name} → {target_room.name}"






        # Add more movement verbs as needed
