from __future__ import annotations
from typing import Optional

from kingdom.engine.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.engine.verbs.verb_handler import ExecuteCommand, VerbHandler
from kingdom.language.outcomes import CommandOutcome

from kingdom.model.noun_model import Noun, Container, Feature
from kingdom.rendering.descriptions import render_current_room, render_item, render_container, render_container_contents, render_feature



class StatefulVerbHandler(VerbHandler):
    def eat(self, cmd: ExecuteCommand = None) -> CommandOutcome:

        player = self.player()
        room = self.room()

        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.outcome_no_op(
                self.build_message("You must be starving! One thing at a time, please."),
                code="eat_all_not_supported",
            )

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.outcome_missing_target(self.build_message(self.missing_target("eat")), code="missing_direct_target")
        
        if not player.has_item(target):
            return self.outcome_not_available(
                self.build_message(f"You don't have the {target.canonical_name()}."),
                code="eat_target_not_in_inventory",
            )

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "eat")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.outcome_success(self.build_message(outcome.message or ""), code="item_handler_stop")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------       
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_edible",
            verb_phrase="eat",
        )
        if cant_msg:
            return self.outcome_blocked(self.build_message(cant_msg), code="eat_not_allowed")

        # state-change pipeline - no state change for eat - just get the message

        if getattr(target, "eaten_success_description", None):
            result_msg = target.eaten_success_description
        else:
            result_msg = f"The {target.canonical_name()} was delicious!"

        # 4. Post-execution side effect: remove item from inventory  

        if player.has_item(target):
            player.remove_from_sack(target)
        if room.has_item(target):
            room.remove_item(target)

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        return self.outcome_success(self.build_message(parts))
    

    def say(self, cmd: ExecuteCommand = None) -> CommandOutcome:
        
        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "wish" in keywords:    # special case for djinni lamp
            outcome: VerbOutcome | None = try_item_special_handler(target, "say")
            if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
                return self.outcome_success(self.build_message(outcome.message or ""), code="item_handler_stop")
            return self.outcome_no_op(self.build_message("Nothing happens."), code="wish_no_effect")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.outcome_missing_target(
                self.build_message("You speak to the wind; the wind does not hear. The wind cannot hear"),
                code="missing_direct_target",
            )

        cant_msg = self.basic_checks(
            target,
            capability_attr="can_be_spoken_to",
            verb_phrase="speak to",
        )
        if cant_msg:
            return self.outcome_blocked(self.build_message(cant_msg), code="say_not_allowed")
        
        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "say")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.outcome_success(self.build_message(outcome.message or ""), code="item_handler_stop")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        
        # ------------- Build the final return string ----------------
        parts: list[str] = []

        if getattr(target, "speak_description", None):
            parts.append(target.speak_description)
        else:
            parts.append(f"You say something to the {target.canonical_name()}, but it doesn't respond.") 

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)

        return self.outcome_success(self.build_message(parts))
                

    def make(self, cmd: ExecuteCommand = None) -> CommandOutcome:

        room = self.room()

        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.outcome_no_op(
                self.build_message("Busy, busy making everything! Maybe focus on one thing at a time?"),
                code="make_all_not_supported",
            )
        
        if "wish" in keywords:    # special case for djinni lamp
            required = self.lookup_required_item_id("djinni", "make wish")
            if target is None and room.has_item(required): target = required  
            outcome: VerbOutcome | None = try_item_special_handler(target, "make")
            if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
                return self.outcome_success(self.build_message(outcome.message or ""), code="item_handler_stop")
            return self.outcome_no_op(self.build_message("Nothing happens."), code="wish_no_effect")

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.outcome_missing_target(self.build_message(self.missing_target("make")), code="missing_direct_target")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "make")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.outcome_success(self.build_message(outcome.message or ""), code="item_handler_stop")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_makeable",
            desired_state=True,
            verb_phrase="make",
        )

        if cant_msg:
            return self.outcome_blocked(self.build_message(cant_msg), code="make_not_allowed")

        # nothing to make yet, so not implementing a state change here.
        return self.outcome_no_op(self.build_message("Nothing happens."), code="make_not_implemented")
 

    def look(self, cmd: ExecuteCommand= None) -> CommandOutcome:

        room = self.room()
        target = cmd.direct_object if cmd.direct_object else None
        verb_token = cmd.verb_token if cmd and cmd.verb_token else None

        dest, dest_name, prep = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, preps=("in"))
        if prep and dest:
            target = dest

        # synonym "search" equates to "look insside" for containers - don't have a generql way to map synonyms to verb+modifier combinations yet, so handling as a special case here
        look_inside = prep or (verb_token.lower() == "search" and (target.get_class_name() if target else None) == "Container")
    
        if look_inside:
            if target is None:
                return self.outcome_missing_target(
                    self.build_message(f"{verb_token}{(' '+ prep +' ') if prep else ' '}what?"),
                    code="missing_look_target",
                )
            if isinstance(target, Container):
                msg = [f"You {verb_token}{(' '+ prep +' ') if prep else ' '}the {target.canonical_name()}. ", render_container_contents(room, target)]
                return self.outcome_raw(self.build_message(msg), code="look_inside_container")

            if getattr(target, "is_open", False):
                message = getattr(target, "opened_state_description", None) or f"You {verb_token}, but don't see anything special."
                return self.outcome_success(self.build_message(message), code="look_inside_open_target")
            return self.outcome_invalid_target(
                self.build_message(f"You can't {verb_token} inside the {target.display_name()}."),
                code="look_inside_invalid_target",
            )
        
        if target is None:
            if cmd.direct_object_token:
                return self.outcome_not_available(
                    self.build_message(f"I see no {cmd.direct_object_token} here."),
                    code="look_target_not_here",
                )
            else:
                return self.outcome_raw(self.build_message(render_current_room(room, look=True)), code="look_room")
        
        lines = []
        if target.get_class_name() == "Item":
            lines.append(self.build_message(render_item(room, target, look=True)))
            lines.append("But you don't notice anything else.")
            return self.outcome_raw(self.build_message(lines), code="look_item")
        elif target.get_class_name() == "Container":
            lines.append(self.build_message(render_container(room, target, look=True)))
            lines.append("But you don't notice anything else.")
            return self.outcome_raw(self.build_message(lines), code="look_container")
        elif isinstance(target, Feature):
            return self.outcome_raw(self.build_message(render_feature(room, target, look=True)), code="look_feature")

        return self.outcome_invalid_target(self.build_message("You don't notice anything unusual."), code="look_unknown_target_type")
        
    def listen(self, cmd: ExecuteCommand = None) -> CommandOutcome:
        room = self.room()
        target = cmd.direct_object if cmd.direct_object else None

        if target is None:  #listen to room
            return self.outcome_success(
                self.build_message(room.listen_description  if getattr(room, "listen_description", None) else "You listen carefully but don't hear anything unusual."),
                code="listen_room",
            )

        if getattr(target, "listen_description", None):
            return self.outcome_success(self.build_message(target.listen_description), code="listen_target")
        else:
            return self.outcome_success(
                self.build_message(f"You listen to the {target.canonical_name()}, but don't hear anything unusual."),
                code="listen_target_default",
            )

