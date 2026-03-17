from __future__ import annotations
from typing import  Optional

from kingdom.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.verbs.verb_handler import ExecuteCommand, VerbHandler

from kingdom.model.noun_model import Noun




class ChangeStateVerbHandler(VerbHandler):

    # ------------------------------------------------------------
    # state change helper
    # ------------------------------------------------------------
      
    def apply_state_change(
        self,
        target,
        verb_phrase,
        *,
        state_attr=None,
        desired_state=None,
        used_item=None,
        indirect=None,
        preposition=None,
    ):

        # 1. Apply the state change
        if state_attr is not None:
            setattr(target, state_attr, desired_state)

        # 2. Build the message
        if getattr(target, f"{verb_phrase}_action_description", None):
            return getattr(target, f"{verb_phrase}_action_description")
        if used_item:
            return f"You {verb_phrase} {target.display_name()} with {used_item}."
        elif indirect:
            return f"You {verb_phrase} {target.display_name()} {preposition} {indirect.display_name()}."
        else:
            return f"You {verb_phrase} {target.display_name()}."

#----------------- the core state-changing verbs -------------------------

    def open(self, cmd: ExecuteCommand = None) -> str:

        room = self.room()
        
        keywords = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object if cmd.direct_object else None

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "sesame" in keywords:
            return self.build_message("Nothing happens.")
        if "all" in keywords or "everything" in keywords:
            return self.build_message("One at a time, please.")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("open"))
        
        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "open")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------

        cant_msg = self.basic_checks(
            target,
            capability_attr="is_openable",
            current_state_attr="is_open",
            desired_state=True,
            verb_phrase="open",
            already_msg="open",
        )
        if cant_msg:
            return self.build_message(cant_msg)
        
        # Lock check 
        if getattr(target, "is_locked", False):
            return self.build_message(
                getattr(target, "locked_description", None)
                or f"The {target.canonical_name()} is locked."
            )

        # change the state
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="open",
            state_attr="is_open",
            desired_state=True,
        )

        # Post-change side effect: reveal exit if configured
        side_effect_msg = ""
        direction = getattr(target, "open_exit_direction", None)
    
        if direction is not None:  #opening has a side effect of unblocking an exit in the room
            reverse_direction = self.get_reverse_of(direction)

            forward_exit = room.get_exit(getattr(target, "open_exit_type", "go"), direction)
            if forward_exit:
                forward_exit.set_existing("is_passable", True)
                side_effect_msg = f"You opened a passage leading {direction}."

            destination = forward_exit.destination if forward_exit else None

            reverse_exit = destination.get_exit(getattr(target, "open_exit_type", "go"), reverse_direction) if destination else None
            if reverse_exit:
                never_passable = getattr(reverse_exit, "is_never_passable", False)   # sometimes, even an open exit isn't enough (i.e. one way passages)
                if not never_passable:
                    reverse_exit.set_existing("is_passable", True)


        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        # Opened exit text
        if side_effect_msg:
            parts.append("")
            parts.append(side_effect_msg)

        return self.build_message(parts)


    def close(self, cmd: ExecuteCommand = None) -> str:

        room = self.room()
        world = self.world()
        
        keywords = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object  if cmd.direct_object else None

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("One at a time, please.")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("close"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "close")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_openable",
            current_state_attr="is_open",
            desired_state=False,
            verb_phrase="close",
            already_msg="closed",
        )
        if cant_msg:
            return self.build_message(cant_msg)

        # change the state
        result_msg  = self.apply_state_change(
            target=target,
            verb_phrase="close",
            state_attr="is_open",
            desired_state=False,
        )

        # Post-change side effect: block exit if configured
        side_effect_msg = ""
        direction = getattr(target, "open_exit_direction", None)
        destination = getattr(target, "open_exit_type", None)
   
        if direction is not None:  
            reverse_direction = self.get_reverse_of(direction)

            forward_exit = room.get_exit(getattr(target, "open_exit_type", "go"), direction)
            if forward_exit:
                forward_exit.set_existing("is_passable", False)
                side_effect_msg = f"You seal off a passage leading {direction}."

            destination = forward_exit.destination if forward_exit else None

            reverse_exit = destination.get_exit(getattr(target, "open_exit_type", "go"), reverse_direction) if destination else None
            if reverse_exit:
                reverse_exit.set_existing("is_passable", False)


        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        # closed exit text
        if side_effect_msg:
            parts.append("")
            parts.append(side_effect_msg)

        return self.build_message(parts)

    def unlock(self, cmd: ExecuteCommand = None) -> str:

        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "all" in keywords or "everything" in keywords:
            return self.build_message("One at a time, please.")

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("unlock"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "unlock")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")


        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_lockable",
            current_state_attr="is_locked",
            desired_state=False,
            verb_phrase="unlock",
            already_msg="unlocked",
        )

        if cant_msg:
            return self.build_message(cant_msg)
        

        #  Required key (if any)
        key_name = getattr(target, "unlock_key", None)

        if key_name:
            no_key_msg = self.require_item(
                required_type="unlock_key",
                required_name=key_name,
                noun=target,
                verb_phrase="unlock",
                indirect="key",
            )
        if no_key_msg:                
            return self.build_message(no_key_msg)

        # Change the state
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="unlock",
            state_attr="is_locked",
            desired_state=False,
            used_item=key_name,
        )

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        return self.build_message(parts)
    
    def light(self, cmd: ExecuteCommand = None) -> str:


        player = self.player()
        inventory = player.sack.contents
        
        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "all" in keywords or "everything" in keywords:
            return self.build_message("You manically try to light everything at once, but soon calm down and focus on one thing at a time.")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("light"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "light")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=True,
            verb_phrase="light",
            already_msg="lit",
        )
        if cant_msg:
            return self.build_message(cant_msg)

        # Required ignition source
        ignition_source = next(
            (item for item in inventory
            if getattr(item, "can_ignite", False)),
            None
        )
        if not ignition_source:
            return self.build_message(f"You have nothing to light the {target.canonical_name()} with.")
        
        lighter_name = ignition_source.display_name()

        # change state
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="light",
            state_attr="is_lit",
            desired_state=True,
            used_item=lighter_name,
        )

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        return self.build_message(parts)


    def extinguish(self, cmd: ExecuteCommand = None) -> str:
        
        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []

        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("One at a time, please.")
        
        if "hands" in keywords or "hand" in keywords:
            return self.build_message("Ouch! You decide that's a bad idea.")
        
        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("extinguish"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "extinguish")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=False,    
            verb_phrase="extinguish",
            already_msg="extinguished",
        )
        if cant_msg:
            return self.build_message(cant_msg)

        # change the state
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="extinguish",
            state_attr="is_lit",
            desired_state=False,
        )

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        return self.build_message(parts)
    

    def rub(self, cmd: ExecuteCommand = None) -> str:
        
        target = cmd.direct_object if cmd.direct_object else None
        keywords = cmd.modifiers if cmd.modifiers else []
        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("Hmmm...")

        # ------------------------------------------------------------
        # 2. Missing target check
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("rub"))

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "rub")
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_rubbable",
            current_state_attr="is_rubbed",
            desired_state=True,
            verb_phrase="rub",
        )
        if cant_msg:
            return self.build_message(cant_msg)

        # state-change pipeline
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="rub",
            state_attr="is_rubbed",
            desired_state=True,
        )   
        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        return self.build_message(parts)
    

    def tie(self, cmd: ExecuteCommand = None) -> str:
        
        player=self.player()
        current_room=self.room()
        keywords = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object if cmd.direct_object else None  

        indirect, indirect_name, prep = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, preps=("to", "onto"))
      
        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------

        if "all" in keywords or "everything" in keywords:
            return self.build_message("you run around frantically waving the rope than calm down to reassess what you really want to do")

        # ------------------------------------------------------------
        # 2. Missing target and indirect checks
        # ------------------------------------------------------------
        if target is None:
            return self.build_message(self.missing_target("tie"))

        if indirect is None:
            if indirect_name:
                return self.build_message(f"You don't see any {indirect_name} here to tie the {target.canonical_name()} to.")
            return self.build_message(f"Tie {target.canonical_name()} to what?")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "tie", indirect_obj=indirect)
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        cant_msg = self.basic_checks(
            target,
            capability_attr="is_tieable",
            current_state_attr="is_tied",
            desired_state=True,
            verb_phrase="tie",
            indirect = indirect,
            ind_capability_attr = "can_be_tied_to",
            ind_phrase = f"tie the {target.canonical_name()} to {indirect_name}" 
        )
        if cant_msg:
            return self.build_message(cant_msg)

        # state-change pipeline
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="tie",
            state_attr="is_tied",
            desired_state=True,
            indirect=indirect,
            preposition="to"
        )

        # Post-change side effect: enable item for climbing - this is hardcoded for a rope dangling down a cliff at the moment.
        # should make this a special_handler

        #-------- this is all ugly

        side_effect_msg =  f"The {target.canonical_name()} is now tied to the {indirect.canonical_name()} and dangles down the cliff face below."
        player.drop_item_to_room(target, current_room)  # remove the item from inventory since it's now tied to a feature in the room and can be climbed on. This is a bit of a hack and should be handled more elegantly when we have a better item/feature system in place.
        target.set_existing("is_climbable", True)
        target.set_existing("is_takeable", False)
        connected_room = current_room.get_exit("climb", "down").destination if current_room.get_exit("climb", "down") else None
        if connected_room:
            connected_room.get_exit("climb", "up").set_existing("is_passable", True)
            connected_room.get_exit("climb", "up").set_existing("is_visible", True)
            connected_room.add_item(target)  # add the item to the room so it can be interacted with there - it will be in two rooms

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        # Revealed exit text
        if side_effect_msg:
            parts.append(side_effect_msg)

        return self.build_message(parts)


    def untie(self, cmd: ExecuteCommand = None) -> str:
        return self.build_message("Not implemented yet")    
    
 