"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

from kingdom.model.noun_model import Noun, Room
from kingdom.model.game_init import GameOver
from kingdom.model.verb_model import Verb
from kingdom.renderer import render_current_room
from kingdom.verbs.verb_handler import VerbHandler


class MovementVerbHandler(VerbHandler):


    # ------------------------------------------------------------
    # Generic movement engine for GO, SWIM, CLIMB, etc.
    # ------------------------------------------------------------
    def perform_movement(self, canonical_direction, exit_dict, verb_phrase, success_verb_phrase):
        """
        Shared movement engine.

        exit_dict: dict[str, Room] (e.g., room.connections or room.swim_exits)
        verb_phrase: str ("go", "swim") for error messages
        success_verb_phrase: str ("go", "swim") for success messages
        """
        state = self.state()
        room = self.room()
    

        next_room = exit_dict.get(canonical_direction)
        if next_room is None:

            refuse_string = None
            other_exits = list(room.swim_exits.keys()) + list(room.climb_exits.keys())

            if canonical_direction in other_exits:
                # Player is trying to use the wrong movement verb for an existing exit
                field_name = f"{canonical_direction}_refuse_string"
                refuse_string = getattr(room, field_name, None)

            if refuse_string:
                return refuse_string
            return f"You can't {verb_phrase} {canonical_direction} from here."

        # Move
        state.current_room = next_room

        # Scoring
        if not next_room.found:
            state.score += getattr(next_room, "discover_points", 0)

        # Render
        lines = [f"You {success_verb_phrase} {canonical_direction}."]
        lines.extend(render_current_room(state))

        return lines


    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, target, words, **kwargs):

        parsed = self.resolve_noun_or_word(words, interest=[])

        direction = parsed["direction"]

        if direction is None:
            return self.build_message("Go where?")

        result_msg= self.perform_movement(direction, self.room().connections, "go", "go")

        return self.build_message(result_msg)


    def swim(self, target: Noun, words: list[str], **kwargs):
        room = self.room()

        def check_swim_constraints():
            player = self.player()
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
        constraint_error = check_swim_constraints()
        if constraint_error:
            return constraint_error

        # 3. Parse direction
        parsed = self.resolve_noun_or_word(words, interest=[])
        direction = parsed["direction"]

        if direction is None:
            return self.build_message("You splash around aimlessly.")

        # 4. Perform swim movement using swim_exits
        result_msg = self.perform_movement(
            direction,
            room.swim_exits,
            verb_phrase="swim",
            success_verb_phrase="swim"
        )

        return self.build_message(result_msg)
    

    def climb(self, target: Noun, words: list[str], **kwargs):
        room = self.room()
        
        # 1. Room must allow climbing 

        if not getattr(room, "climb_exits", False):
            return self.build_message("There is nowhere to climb here.")
        
        # 2. Parse direction or resolve from target
        parsed = self.resolve_noun_or_word(words, interest=[])
        direction = parsed["direction"]

        climbable = False
        if direction is not None:
            for item in room.items:
                if getattr(item, "is_climbable", False):
                    climbable = True
                    break

        target_direction = None
        if direction is None and target is not None:
            if getattr(target, "is_climbable", False):
                climb_directions = getattr(target, "climb_directions", [])
                for d in climb_directions:
                    for e in room.climb_exits:
                       if d == e:
                        target_direction = d
                        break
                    if target_direction is not None:
                        break
                else:
                    return self.build_message(f"You can't climb the {target.display_name()}.")

        if  not (direction or target_direction):
            return self.build_message("Climb where?")

        # 3. Climbing constraint logic

        if direction in room.climb_exits and not climbable:

            # Climb refusal
            climb_refusal = getattr(room, "climb_refuse_string", None)

            # Default fallback
            default = "You try to climb, but it's too difficult from here."

            return self.build_message(climb_refusal or default)
    
        

        # 4. Perform climb movement using climb_exits
        result_msg = self.perform_movement(
            direction or target_direction,
            room.climb_exits,
            verb_phrase="climb",
            success_verb_phrase="climb"
        )

        return self.build_message(result_msg)

    def teleport(self, target: Noun, words: list[str], **kwargs):
        """Teleport to any room by name or number. No target → list rooms."""
        state = self.state()
        world = self.world()
        room = self.room()

        # No argument → show list
        if not words and target is None:
            room_list = sorted(world.rooms.values(), key=lambda r: r.name)

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
                rooms_sorted = sorted(world.rooms.values(), key=lambda r: r.canonical_name())
                if 0 <= idx < len(rooms_sorted):
                    desired_room = rooms_sorted[idx]
            except ValueError:
                pass

            # Name prefix/partial match
            if desired_room is None:
                matches = [
                    r for r in world.rooms.values()
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
        desired_room.found = True

        lines = [f"You teleport from {old_room_name} to {new_room_name}."]
        lines.extend(render_current_room(state))
        return self.build_message(lines)

    
