"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

from kingdom.models import Verb, Noun, Room, DispatchContext, GameOver
from kingdom.renderer import render_current_room
from kingdom.verbs.verb_handler import VerbHandler


class MovementVerbHandler(VerbHandler):

    # ------------------------------------------------------------
    # Generic movement engine for GO, SWIM, CLIMB, etc.
    # ------------------------------------------------------------
    def perform_movement(self, ctx, canonical, exit_dict, verb_phrase, success_verb_phrase):
        """
        Shared movement engine.

        exit_dict: dict[str, Room] (e.g., room.connections or room.swim_exits)
        verb_phrase: str ("go", "swim") for error messages
        success_verb_phrase: str ("go", "swim") for success messages
        """
        state = self.state(ctx)
        game = self.game(ctx)

        next_room = exit_dict.get(canonical)
        if next_room is None:
            return f"You can't {verb_phrase} {canonical} from here."

        # Move
        state.current_room = next_room

        # Scoring
        if not next_room.visited:
            game.score += getattr(next_room, "discover_points", 0)

        # Render
        lines = [f"You {success_verb_phrase} {canonical}."]
        lines.extend(render_current_room(state, display=False))

        return lines


    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, ctx, target, words):

        parsed = self.resolve_noun_or_word(words, interest=[])

        direction = parsed["direction"]

        if direction is None:
            return self.build_message("Go where?")

        result_msg= self.perform_movement(ctx, direction, self.room(ctx).connections, "go", "go")

        return self.build_message(result_msg)


    def swim(self, ctx, target: Noun, words: list[str]):
        room = self.room(ctx)

        def check_swim_constraints(ctx):
            player = self.player(ctx)
            inventory = player.get_inventory_items()

            heavy_item = next(
                (item for item in inventory if getattr(item, "too_heavy_to_swim", False)),
                None
            )
            if heavy_item is not None:
                raise GameOver(
                    f"{heavy_item.canonical_name()} drags you under as you try to swim. You drown. GAME OVER."
                )

            return None

        # 1. Room must allow swimming
        if not getattr(room, "has_water", False):
            return self.build_message("There is nowhere to swim here.")

        # 2. Drowning / constraint logic
        constraint_error = check_swim_constraints(ctx)
        if constraint_error:
            return constraint_error

        # 3. Parse direction
        parsed = self.resolve_noun_or_word(words, interest=[])
        direction = parsed["direction"]

        if direction is None:
            return self.build_message("You splash around aimlessly.")

        # 4. Perform swim movement using swim_exits
        result_msg = self.perform_movement(
            ctx,
            direction,
            room.swim_exits,
            verb_phrase="swim",
            success_verb_phrase="swim"
        )

        return self.build_message(result_msg)



    def teleport(self, ctx, target: Noun, words: list[str]):
        """Teleport to any room by name or number. No target → list rooms."""
        state = self.state(ctx)
        game = self.game(ctx)
        room = self.room(ctx)

        # No argument → show list
        if not words and target is None:
            room_list = sorted(game.rooms.values(), key=lambda r: r.name)

            lines = ["Teleport — available rooms:"]
            for i, room in enumerate(room_list, 1):
                lines.append(f"  {i:2d}. {room.canonical_name()}")
            lines.append("")
            lines.append("Usage: teleport <name or number>")
            lines.append("       goto 7")
            return "\n".join(lines)

        # Resolve target room
        desired_room = None

        # 1. find desired room from words because only nouns in the current room or inventory are considered targets by the parser
        if desired_room is None and words:
            query = " ".join(words).strip().lower()

            # Number?
            try:
                idx = int(query) - 1
                rooms_sorted = sorted(game.rooms.values(), key=lambda r: r.canonical_name())
                if 0 <= idx < len(rooms_sorted):
                    desired_room = rooms_sorted[idx]
            except ValueError:
                pass

            # Name prefix/partial match
            if desired_room is None:
                matches = [
                    r for r in game.rooms.values()
                    if query in r.display_name().lower() or query in r.canonical_name().lower()
                ]
                if len(matches) == 1:
                    desired_room = matches[0]
                elif len(matches) > 1:
                    names = ", ".join(r.canonical_name() for r in matches)
                    return self.build_message(f"Ambiguous room name — matches: {names}")

        if desired_room is None:
            return self.build_message("No matching room. Type 'teleport' to list rooms.")
        
        if desired_room is room:
            return self.build_message(f"You are already in {room.canonical_name()}.")

        # Perform the teleport
        old_room_name = room.canonical_name()
        state.current_room = desired_room
        new_room_name = desired_room.canonical_name()
        desired_room.visited = True

        lines = [f"You teleport from {old_room_name} to {new_room_name}."]
        lines.extend(render_current_room(state, display=False))
        return self.build_message(lines)

    
