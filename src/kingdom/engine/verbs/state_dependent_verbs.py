from __future__ import annotations
from typing import Optional

from kingdom.engine.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.engine.verbs.verb_handler import ExecuteCommand, VerbHandler

from kingdom.model.noun_model import Noun, Container, Feature
from kingdom.rendering.descriptions import render_current_room, render_item, render_container, render_container_contents, render_feature



class StatefulVerbHandler(VerbHandler):
    def eat(self, cmd: ExecuteCommand = None) -> str:

        player = self.player()
        room = self.room()

        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("You must be starving! One thing at a time, please.")

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("eat"))
        
        if not player.has_item(target):
            return self.build_message(f"You don't have the {target.canonical_name()}.")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "eat")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------       
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_edible",
            verb_phrase="eat",
        )
        if cant_msg:
            return self.build_message(cant_msg)

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

        return self.build_message(parts)
    

    def say(self, cmd: ExecuteCommand = None) -> str:
        
        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "wish" in keywords:    # special case for djinni lamp
            outcome: VerbOutcome | None = try_item_special_handler(target, "say")
            if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
                return self.build_message(outcome.message or "") 
            return self.build_message("Nothing happens.")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message("You speak to the wind; the wind does not hear. The wind cannot hear")

        cant_msg = self.basic_checks(
            target,
            capability_attr="can_be_spoken_to",
            verb_phrase="speak to",
        )
        if cant_msg:
            return self.build_message(cant_msg)
        
        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "say")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "") 

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

        return self.build_message(parts)
                

    def make(self, cmd: ExecuteCommand = None) -> str:

        room = self.room()

        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("Busy, busy making everything! Maybe focus on one thing at a time?")
        
        if "wish" in keywords:    # special case for djinni lamp
            required = self.lookup_required_item_id("djinni", "make wish")
            if target is None and room.has_item(required): target = required  
            outcome: VerbOutcome | None = try_item_special_handler(target, "make")
            if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
                return self.build_message(outcome.message or "") 
            return self.build_message("Nothing happens.")

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("make"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "make")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

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
            return self.build_message(cant_msg)

        # nothing to make yet, so not implementing a state change here.
 

    def look(self, cmd: ExecuteCommand= None) -> str:

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
                return self.build_message(f"{verb_token}{(' '+ prep +' ') if prep else ' '}what?")
            if isinstance(target, Container):
                msg = [f"You {verb_token}{(' '+ prep +' ') if prep else ' '}the {target.canonical_name()}. ", render_container_contents(room, target)]
                return self.build_message(msg)

            if getattr(target, "is_open", False):
                message = getattr(target, "opened_state_description", None) or f"You {verb_token}, but don't see anything special."
                return self.build_message(message)
            return self.build_message(f"You can't {verb_token} inside the {target.display_name()}.")
        
        if target is None:
            if cmd.direct_object_token:
                return self.build_message(f"I see no {cmd.direct_object_token} here.")
            else:
                return self.build_message(render_current_room(room, look=True))
        
        lines = []
        if target.get_class_name() == "Item":
            lines.append(self.build_message(render_item(room, target, look=True)))
            lines.append("But you don't notice anything else.")
            return self.build_message(lines)
        elif target.get_class_name() == "Container":
            lines.append(self.build_message(render_container(room, target, look=True)))
            lines.append("But you don't notice anything else.")
            return self.build_message(lines)
        elif isinstance(target, Feature):
            return self.build_message(render_feature(room, target, look=True))
        
    def listen(self, cmd: ExecuteCommand = None) -> str:
        room = self.room()
        target = cmd.direct_object if cmd.direct_object else None

        if target is None:  #listen to room
            return self.build_message(room.listen_description  if getattr(room, "listen_description", None) else "You listen carefully but don't hear anything unusual.")

        if getattr(target, "listen_description", None):
            return self.build_message(target.listen_description)
        else:
            return self.build_message(f"You listen to the {target.canonical_name()}, but don't hear anything unusual.")

