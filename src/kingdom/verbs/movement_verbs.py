"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

import cmd
from unittest import result

from kingdom.model.noun_model import Noun, Room
from kingdom.model.game_init import GameOver
from kingdom.model.verb_model import Verb
from kingdom.renderer import render_current_room
from kingdom.verbs.verb_handler import VerbHandler, ExecuteCommand, VerbOutcome


class MovementVerbHandler(VerbHandler):


    # ------------------------------------------------------------
    # Generic movement engine for GO, SWIM, CLIMB, etc.
    # ------------------------------------------------------------
    def perform_movement(self, movement_type, direction, verb_phrase, success_verb_phrase):
        state = self.state()
        room = self.room()

        # 1. Try the correct movement type
        exit_obj = room.get_exit(movement_type, direction)

        if exit_obj is None:

            # Check other movement types for go_refuse_string
            for other_type, exits in room.exits.items():
                if other_type == movement_type:
                    continue

                other_exit = exits.get(direction)
                if other_exit:
                    # Wrong verb for an existing exit
                    if other_exit.go_refuse_string:
                        return other_exit.go_refuse_string
                    return f"You can't {verb_phrase} {direction} from here."

            # No exit of any kind
            return f"You can't {verb_phrase} {direction} from here."

        # 4. Exit exists for this movement type
        if exit_obj.refuse_string:
            return exit_obj.refuse_string

        next_room = exit_obj.destination

        # Move
        state.current_room = next_room

        # Scoring
        if not next_room.found:
            state.score += getattr(next_room, "discover_points", 0)
            next_room.found = True

        # Render
        lines = [f"You {success_verb_phrase} {direction}."]
        lines.extend(render_current_room(state))
        return lines

    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, target, words, cmd: ExecuteCommand):
        direction = cmd.direction if cmd and cmd.direction else None

        if direction is None:
            return self.build_message("Go where?")

        result = self.perform_movement(
            movement_type="go",
            direction=direction,
            verb_phrase="go",
            success_verb_phrase="go"
        )

        return self.build_message(result)



    def swim(self, target, words, cmd:ExecuteCommand):
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

        # 3. get direction 
        direction = cmd.direction if cmd and cmd.direction else None

        if direction is None:
            return self.build_message("You splash around aimlessly.")

        # 4. Perform swim movement using swim_exits
        result_msg = self.perform_movement(
            movement_type="swim",
            direction=direction,
            verb_phrase="swim",
            success_verb_phrase="swim"
        )

        return self.build_message(result_msg)
    
    def climb(self, target: Noun, words: list[str], cmd: ExecuteCommand):
        room = self.room()

        target = cmd.direct_object if cmd and cmd.direct_object else None
        direction = cmd.direction if cmd and cmd.direction else None

        # 1. Room must have climb exits
        climb_exits = room.exits.get("climb", {})
        if not climb_exits:
            return self.build_message("There is nowhere to climb here.")

        # 2. If a direction is given, check if any climbable item is present
        climbable = False
        if direction is not None:
            for item in room.items:
                if getattr(item, "is_climbable", False):
                    climbable = True
                    break

        # 3. If no direction is given, but a climbable target is provided
        target_direction = None
        if direction is None and target is not None:
            if getattr(target, "is_climbable", False):
                climbable = True
                climb_directions = getattr(target, "climb_directions", [])
                for d in climb_directions:
                    if d in climb_exits:
                        target_direction = d
                        break
                else:
                    return self.build_message(f"You can't climb the {target.display_name()}.")

        # If neither a direction nor a target-derived direction exists
        if not (direction or target_direction):
            return self.build_message("Climb where?")

        # Resolve final direction
        final_direction = direction or target_direction

        # 4. Climbing constraint logic
        exit_obj = room.get_exit("climb", final_direction)
        if exit_obj and not climbable:
            refusal = exit_obj.refuse_string
            default = "You try to climb, but it's too difficult from here."
            return self.build_message(refusal or default)

        # 5. Perform climb movement
        result_msg = self.perform_movement(
            movement_type="climb",
            direction=final_direction,
            verb_phrase="climb",
            success_verb_phrase="climb"
        )

        return self.build_message(result_msg)

    

    def teleport(self, target: Noun, words: list[str], cmd: "ExecuteCommand"):
        """Teleport to any room by name or number. No target → list rooms."""
        state = self.state()
        world = self.world()
        room = self.room()

        requested_room = cmd.direct_object_token if cmd.direct_object_token else None

        # No argument → show list
        if requested_room is None:
            room_list = sorted(world.rooms.values(), key=lambda r: r.name)

            lines = ["Teleport — available rooms:"]
            for i, room in enumerate(room_list, 1):
                lines.append(f"  {i:2d}. {room.canonical_name()}")
            lines.append("")
            lines.append("Usage: teleport <name or number>")
            lines.append("       goto 7")
            return "\n".join(lines)

        requested_room = requested_room.strip().lower()
        desired_room = None

        #check number 
        try:
            idx = int(requested_room) - 1
            rooms_sorted = sorted(world.rooms.values(), key=lambda r: r.canonical_name())
            if 0 <= idx < len(rooms_sorted):
                desired_room = rooms_sorted[idx]
        except ValueError:
            pass

        # Name prefix/partial match
        if desired_room is None:
            matches = [
                r for r in world.rooms.values()
                if requested_room in r.display_name().lower() or requested_room in r.canonical_name().lower()
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

    
