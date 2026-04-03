"""
movement_verbs.py

Handlers for verbs related to movement (e.g., GO, CLIMB, SWIM, EXIT, JUMP, RUN, WALK).
This module centralizes movement verb logic for clarity and maintainability.
"""

import cmd
from unittest import result

from kingdom.model.noun_model import Noun, Room
from kingdom.model.game_model import GameOver
from kingdom.model.verb_model import Verb
from kingdom.rendering.descriptions import render_current_room
from kingdom.engine.verbs.verb_handler import VerbHandler, ExecuteCommand, VerbOutcome
from kingdom.model.direction_model import DIRECTIONS
from kingdom.language.outcomes import CommandOutcome


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
        lines = [f"You {success_verb_phrase} {direction}.", ""]
        lines.extend(render_current_room(destination) or [])

        return lines
    
    def check_movement(self, exit_obj, movement_type, direction):
        passable = getattr(exit_obj, "is_passable", True)

        if not passable:
            return exit_obj.refuse_description or f"Something is holding you back from {movement_type}ing {direction}."

        return None

    # ------------------------------------------------------------
    # GO verb
    # ------------------------------------------------------------
    def go(self, cmd: ExecuteCommand) -> CommandOutcome:
        direction = cmd.direction
        room = self.room()

        if direction is None:
            return self.outcome_missing_target(self.build_message("Go where?"), code="missing_direction")

        msgs = []

        #check all exits

        any_exit = room.get_all_exits(direction = direction)

        if not any_exit:
            return self.outcome_not_available(self.build_message(f"You can't travel {direction} from here."), code="no_exit_in_direction")
      
        go_exit = room.get_exit("go", direction)
  
        if go_exit:
            movement_refusal = self.check_movement(go_exit, "go", direction)
            if movement_refusal:
                return self.outcome_blocked(self.build_message(movement_refusal), code="movement_blocked")
            return self.outcome_raw(self.build_message(self.perform_movement(go_exit, direction, "go")), code="movement_success")   #successful go movement

        # No go exit, but other move types have passable exits in this direction. Collect go_refuse_description(s) if present
        else:
            if any_exit:
                for movement_type in ["swim", "climb"]:
                    exit_obj = room.get_exit(movement_type, direction)
                    if exit_obj and exit_obj.go_refuse_description:
                        msgs.append(exit_obj.go_refuse_description if exit_obj.is_passable else f"Something is holding you back from {movement_type}ing {direction}.")

        return self.outcome_not_available(self.build_message(msgs or f"You can't go {direction} from here."), code="no_go_exit")


    def swim(self, cmd:ExecuteCommand) -> CommandOutcome:
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
            return self.outcome_not_available(self.build_message("There is nowhere to swim here."), code="no_water")

        # 2. Drowning / constraint logic
        constraint_error = check_swim_constraints()
        if constraint_error:
            return constraint_error

        # 3. get direction 
        direction = cmd.direction if cmd and cmd.direction else None

        if direction is None:
            return self.outcome_no_op(self.build_message("You splash around aimlessly."), code="missing_direction")

        exit_obj = room.get_exit("swim", direction)
        if exit_obj is None:
            return self.outcome_not_available(self.build_message(f"You can't swim {direction} from here."), code="no_swim_exit")
        
        movement_refusal = self.check_movement(exit_obj, "swim", direction)
        if movement_refusal:
            return self.outcome_blocked(self.build_message(movement_refusal), code="movement_blocked")

        result_msg = self.perform_movement(exit_obj=exit_obj, direction=direction, success_verb_phrase="swim"
        )

        return self.outcome_raw(self.build_message(result_msg), code="movement_success")
    

    # ------------------------------------------------------------
    # CLIMB verb      
    # 
    # Note: Climb always requires a climbable item in the room.
    #       If you have stairs or a fixed ladder in the room,  
    #       you must provide a fixed object in the room to climb.
    #       Use "is_visible false" to hide the fixed object and 
    #       put the stairs or ladder in the room description.          
    # ------------------------------------------------------------
    
    def climb(self, cmd: ExecuteCommand) -> CommandOutcome:
        room = self.room()
        verb_token = cmd.verb_token if cmd else "climb"

        # No climb exits in room at all → early exit
        climb_exits = room.exits.get("climb", {})
        if not climb_exits:
            return self.outcome_not_available(self.build_message(f"There is nothing to {verb_token} here."), code="no_climb_exits")

        direction = cmd.direction if cmd else None
        target = cmd.direct_object if cmd else None

        # ───────────────────────────────────────────────
        # Case 1: Direction given → try to find matching climbable object
        # ───────────────────────────────────────────────
        if direction:
            # Look for any climbable item that supports this direction
            matching_climbable = None
            for obj in room.items + room.containers:  # include containers if pole could be inside one
                if getattr(obj, "is_climbable", False):
                    climb_dirs = getattr(obj, "climb_directions", [])
                    if direction in climb_dirs:
                        matching_climbable = obj
                        break

            if matching_climbable:
                chosen = matching_climbable
            else:
                return self.outcome_not_available(
                    self.build_message(f"There is nothing here you can {verb_token} {direction}."),
                    code="no_matching_climbable",
                )

        # ───────────────────────────────────────────────
        # Case 2: No direction, but target given → infer direction from target
        # ───────────────────────────────────────────────
        elif target:
            if not getattr(target, "is_climbable", False):
                return self.outcome_invalid_target(
                    self.build_message(f"You can't {verb_token} the {target.display_name()}."),
                    code="target_not_climbable",
                )

            climb_dirs = getattr(target, "climb_directions", [])
            if not climb_dirs:
                return self.outcome_not_available(
                    self.build_message(f"The {target.display_name()} can't be climbed right now."),
                    code="target_no_climb_directions",
                )

            # Find the first direction that actually has a climb exit
            possible_dirs = [d for d in climb_dirs if d in climb_exits]
            if not possible_dirs:
                return self.outcome_not_available(
                    self.build_message(f"You can't {verb_token} the {target.display_name()} from here."),
                    code="target_not_climbable_here",
                )

            # Default to the first supported direction 
            direction = possible_dirs[0]
            chosen = target  # remember for flavor text if desired

        # ───────────────────────────────────────────────
        # No direction and no target → ambiguous
        # ───────────────────────────────────────────────
        else:
            return self.outcome_missing_target(
                self.build_message(f"{verb_token.capitalize()} what? Or which way?"),
                code="missing_target_or_direction",
            )

        # ───────────────────────────────────────────────
        # At this point we have a direction → try to move
        # ───────────────────────────────────────────────
        exit_obj = room.get_exit("climb", direction)
        if not exit_obj:
            return self.outcome_not_available(
                self.build_message(f"You can't {verb_token} {direction} from here."),
                code="no_climb_exit",
            )

        movement_refusal = self.check_movement(exit_obj, "climb", direction)
        if movement_refusal:
            return self.outcome_blocked(self.build_message(movement_refusal), code="movement_blocked")


        # Perform the movement (your existing logic)
        move_result = self.perform_movement(exit_obj, direction, verb_token)

        return self.outcome_raw(self.build_message(move_result), code="movement_success")


    def teleport(self,  cmd: ExecuteCommand) -> CommandOutcome:
        """Teleport to any room by name or number. No target → list rooms."""
        game = self.game()
        world = self.world()
        room = self.room()

        if not game.debug_mode:
            return self.outcome_not_available(self.build_message("Teleport not permitted"), code="debug_only")

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
            return self.outcome_raw("\n".join(lines), code="teleport_list")

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
                return self.outcome_invalid_target(
                    self.build_message(f"Ambiguous room name - matches: {names}"),
                    code="ambiguous_room",
                )

        if desired_room is None:
            return self.outcome_not_available(
                self.build_message("No matching room. Type 'teleport' to list rooms."),
                code="room_not_found",
            )
        
        if desired_room is room:
            return self.outcome_no_op(
                self.build_message(f"You are already in {room.canonical_name()}."),
                code="already_in_room",
            )

        # Perform the teleport
        game.current_room = desired_room


        return self.outcome_raw(
            self.build_message(self.perform_movement(exit_obj=None, direction="magically", success_verb_phrase="teleport", destination=desired_room)),
            code="movement_success",
        )


    
