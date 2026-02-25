"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

from kingdom.models import Verb, Noun, Room, DispatchContext, GameOver
from kingdom.parser import normalize_direction_token
from kingdom.terminal_style import TRS80_WHITE, trs80_print, trs80_clear_and_show_room
from kingdom.renderer import render_current_room

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

    # ------------------------------------------------------------
    # Generic movement engine for GO, SWIM, CLIMB, etc.
    # ------------------------------------------------------------
    def perform_movement(self, context, direction, exit_dict, verb_name, success_verb):
        """
        Shared movement engine.

        exit_dict: dict[str, Room] (e.g., room.connections or room.swim_exits)
        verb_name: str ("go", "swim") for error messages
        success_verb: str ("go", "swim") for success messages
        """
        state = context.state
        game = context.game

        if state.current_room is None:
            return f"There is nowhere to {verb_name}."

        canonical = normalize_direction_token(direction)
        next_room = exit_dict.get(canonical)

        if next_room is None:
            return f"You can't {verb_name} {canonical} from here."

        # Move
        state.current_room = next_room

        # Scoring
        if not next_room.visited:
            game.score += getattr(next_room, "discover_points", 0)
            next_room.visited = True

        # Render
        trs80_print(f"You {success_verb} {canonical}.", style=TRS80_WHITE)
        render_current_room(state, clear=False)
        print()
        return ""

    # ------------------------------------------------------------
    # Direction resolution
    # ------------------------------------------------------------
    def resolve_direction(self, target, words):
        """Extract direction from noun or raw text."""
        if target is not None:
            direction = getattr(target, "canonical_direction", None)
            if direction is None and hasattr(target, "get_noun_name"):
                return normalize_direction_token(target.get_noun_name())
            return direction

        if words:
            return normalize_direction_token(words[0])

        return None

    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, context, target: Noun, words: list[str]):
        direction = self.resolve_direction(target, words)
        if not direction:
            return "Go where?"

        room = context.state.current_room
        return self.perform_movement(context, direction, room.connections, "go", "go")

    # ------------------------------------------------------------
    # SWIM verb (directional swim_exits)
    # ------------------------------------------------------------
    def swim(self, context, target: Noun, words: list[str]):
        state = context.state
        game = context.game
        room = state.current_room

        if room is None:
            return "There is nowhere to swim."

        # 1. Resolve direction
        direction = self.resolve_direction(target, words)
        if not direction:
            return "You splash around aimlessly."

        # 2. Drowning logic
        constraint_error = self._check_swim_constraints(game)
        if constraint_error:
            return constraint_error

        # 3. Use swim-only exits
        return self.perform_movement(context, direction, room.swim_exits, "swim", "swim")

    # ------------------------------------------------------------
    # Drowning logic (unchanged)
    # ------------------------------------------------------------
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



    def teleport(self, context, target: Noun, words: list[str]):
        """Teleport to any room by name or number. No target → list rooms."""
        state = context.state
        game = context.game

        if state.current_room is None:
            return "No current room — cannot teleport."

        # No argument → show list
        if not words and target is None:
            room_list = sorted(game.rooms.values(), key=lambda r: r.name)
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

        # 1. Direct noun target
        if target is not None:
            if isinstance(target, Room):
                target_room = target
            else:
                query = target.get_noun_name().lower()
                for r in game.rooms.values():
                    if query in r.name.lower() or query in r.get_noun_name().lower():
                        target_room = r
                        break

        # 2. Words fallback
        if target_room is None and words:
            query = " ".join(words).strip().lower()

            # Number?
            try:
                idx = int(query) - 1
                rooms_sorted = sorted(game.rooms.values(), key=lambda r: r.name)
                if 0 <= idx < len(rooms_sorted):
                    target_room = rooms_sorted[idx]
            except ValueError:
                pass

            # Name prefix/partial match
            if target_room is None:
                matches = [
                    r for r in game.rooms.values()
                    if query in r.name.lower() or query in r.get_noun_name().lower()
                ]
                if len(matches) == 1:
                    target_room = matches[0]
                elif len(matches) > 1:
                    names = ", ".join(r.name for r in matches)
                    return f"Ambiguous room name — matches: {names}"

        if target_room is None:
            return "No matching room. Use 'teleport' alone to list rooms."

        # Perform the teleport
        old_room_name = state.current_room.name
        state.current_room = target_room
        target_room.visited = True

        render_current_room(state, clear=True)
        print()

        







        # Add more movement verbs as needed
