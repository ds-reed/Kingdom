from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.verbs.verb_handler import VerbHandler

from kingdom.model.noun_model import Noun, Item, Container, DirectionRegistry, Feature
from kingdom.renderer import RoomRenderer, render_current_room, render_item, render_container, render_container_contents



class StatefulVerbHandler(VerbHandler):
    def eat(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        **kwargs
    ) -> str:
        
        player = self.player()
        room = self.room()

        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]        
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

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "eat", words)
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

        if getattr(target, "eaten_success_string", None):
            result_msg = target.eaten_success_string
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
    

    def say(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        **kwargs
    ) -> str:
        
        parse = self.resolve_noun_or_word(words, interest=['wish'])
        keywords = parse["keywords"]        
        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "wish" in keywords:    # special case for djinni lamp
            outcome: VerbOutcome | None = try_item_special_handler(target, "say", words)
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "say", words)
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "") 

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        
        # ------------- Build the final return string ----------------
        parts: list[str] = []

        if getattr(target, "speak_string", None):
            parts.append(target.speak_string)
        else:
            parts.append(f"You say something to the {target.canonical_name()}, but it doesn't respond.") 

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)

        return self.build_message(parts)
                

    def make(self, target=None, words=(), **kwargs):

        room = self.room()
        parse = self.resolve_noun_or_word(words, interest=['wish', 'all', 'everything'])
        keywords = parse["keywords"]        
        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("Busy, busy making everything! Maybe focus on one thing at a time?")
        
        if "wish" in keywords:    # special case for djinni lamp
            required = self.lookup_required_item_id("djinni", "make wish")
            if target is None and room.has_item(required): target = required  
            outcome: VerbOutcome | None = try_item_special_handler(target, "make", words)
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "make", words)
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

    # moved from UI - not following the usual pattern yet.    

    def look(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs) -> str:

        room = self.room()

        parse = self.resolve_noun_or_word(words, interest=["inside", "in"])
        noun = parse["noun"]
        keywords = parse["keywords"]
        raw = parse["raw"]

        if "inside" in keywords or "in" in keywords:
            if target is None:
                return self.build_message("Look inside what?")
            if isinstance(target, Container):
                return self.build_message(render_container_contents(room, target))
            return self.build_message(f"You can't look inside the {target.display_name()}.")
        
        if not target: target = noun

        if target is not None:
            if target.get_class_name() == "Item":
                return self.build_message(render_item(room, target))
            elif target.get_class_name() == "Container":
                return self.build_message(render_container(room, target))
            elif isinstance(target, Feature):
                return self.build_message(f"Looking closely at the {target.canonical_name()}, you see {target.description}")

            
        if raw: return self.build_message("I don't understand what you want to look at.")

        return self.build_message(render_current_room(room, look=True))
