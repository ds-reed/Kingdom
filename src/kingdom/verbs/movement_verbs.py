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
from kingdom.rendering.descriptions import render_current_room
from kingdom.verbs.verb_handler import VerbHandler, ExecuteCommand, VerbOutcome


class MovementVerbHandler(VerbHandler):


    # ------------------------------------------------------------
    # Generic movement engine for GO, SWIM, CLIMB, etc.
    # ------------------------------------------------------------
    def perform_movement(self, exit_obj, direction, success_verb_phrase, destination=None):
        game = self.game()
        if destination is None:
            destination = getattr(exit_obj, "destination", None)
        if destination is None:
            return f"ERROR - MISSING DESTINATION."

        # Move
        game.current_room = destination

        # Render
        lines = [f"You {success_verb_phrase} {direction}."]
        lines.extend(render_current_room(destination) or [])

        return lines
    
    def check_movement(self, exit_obj, movement_type, direction):
        passable = getattr(exit_obj, "is_passable", True)

        if not passable:
            return exit_obj.refuse_string or f"Something is holding you back from {movement_type}ing {direction}."

        return None

    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, target, words, cmd):
        direction = cmd.direction
        room = self.room()

        msgs = []

        #check all exits

        any_exit = room.get_exit("go", direction) or room.get_exit("swim", direction) or  room.get_exit("climb", direction)



        if not any_exit:
            return self.build_message(f"You can't travel {direction} from here.")

        go_exit  = room.get_exit("go", direction)    

        if go_exit:
            movement_refusal = self.check_movement(go_exit, "go", direction)
            if movement_refusal:
                return self.build_message(movement_refusal)
            return self.build_message(self.perform_movement(go_exit, direction, "go"))   #successful go movement

        # No go exit, but other move types have exits in this direction. Collect go_refuse_string(s) if present
        else:
            if any_exit:
                for movement_type in ["swim", "climb"]:
                    exit_obj = room.get_exit(movement_type, direction)
                    if exit_obj and exit_obj.go_refuse_string:
                        msgs.append(exit_obj.go_refuse_string)

        return self.build_message(msgs or f"You can't go {direction} from here.")



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

        exit_obj = room.get_exit("swim", direction)
        if exit_obj is None:
            return self.build_message(f"You can't swim {direction} from here.")
        
        movement_refusal = self.check_movement(exit_obj, "swim", direction)
        if movement_refusal:
            return self.build_message(movement_refusal)

        result_msg = self.perform_movement(exit_obj=exit_obj, direction=direction, success_verb_phrase="swim"
        )

        return self.build_message(result_msg)
    

    # ------------------------------------------------------------
    # CLIMB verb      
    # 
    # Note: Climb always requires a climbable item in the room.
    #       If you have stairs or a fixed ladder in the room,  
    #       you must provide a fixed object in the room to climb.
    #       Use "is_visible false" to hide the fixed object and 
    #       put the stairs or ladder in the room description.          
    # ------------------------------------------------------------
    
    def climb(self, target: Noun, words: list[str], cmd: ExecuteCommand):
        room = self.room()

        target = cmd.direct_object if cmd and cmd.direct_object else None
        direction = cmd.direction if cmd and cmd.direction else None
        verb_token = cmd.verb_token if cmd else "climb"

        # Room must have climb exits
        climb_exits = room.exits.get("climb", {})
        if not climb_exits:
            return self.build_message(f"There is nothing to {verb_token} {direction or 'here'}.")

        # If a direction is given, check if any climbable item is present
        climbable = False
        if direction is not None:
            for item in room.items:
                if getattr(item, "is_climbable", False):
                    climbable = True
                    break

        # If a climbable target is provided instead of a direction, use that to determine direction
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
                    return self.build_message(f"You can't {verb_token} {direction or ''} the {target.display_name()}.")

        # If neither a direction nor a target-derived direction exists
        if not (direction or target_direction):
            return self.build_message(f"{verb_token.capitalize()} where?")

        # Resolve final direction
        final_direction = direction or target_direction

        # Climbing constraint logic
        exit_obj = room.get_exit("climb", final_direction)
        if exit_obj:
            movement_refusal = self.check_movement(exit_obj, "climb", final_direction)
            if movement_refusal:
                return self.build_message(movement_refusal)
            return self.build_message(self.perform_movement(exit_obj, final_direction, verb_token))
        
        return self.build_message(f"You can't {verb_token} {final_direction} from here.")


    def teleport(self, target: Noun, words: list[str], cmd: "ExecuteCommand"):
        """Teleport to any room by name or number. No target → list rooms."""
        game = self.game()
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
        game.current_room = desired_room
        new_room_name = desired_room.canonical_name()

        return(self.build_message(self.perform_movement(exit_obj=None, direction="magically", success_verb_phrase="teleport", destination=desired_room)))


    
