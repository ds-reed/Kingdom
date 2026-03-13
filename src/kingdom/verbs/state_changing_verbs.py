from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.verbs.verb_handler import ExecuteCommand, VerbHandler

from kingdom.model.noun_model import Noun, Item, Container, DirectionRegistry, Feature
from kingdom.renderer import RoomRenderer, render_current_room




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
        if used_item:
            return f"You {verb_phrase} {target.display_name()} with {used_item}."
        elif indirect:
            return f"You {verb_phrase} {target.display_name()} {preposition} {indirect.display_name()}."
        else:
            return f"You {verb_phrase} {target.display_name()}."

#----------------- the core state-changing verbs -------------------------

    def open(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        **kwargs
    ) -> str:

        room = self.room()
        world = self.world()
        
        parse = self.resolve_noun_or_word(words, interest=['sesame', 'all', 'everything'])
        keywords = parse["keywords"]

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
        outcome: VerbOutcome | None = try_item_special_handler(target, "open", words)
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
        destination = getattr(target, "open_exit_destination", None)

        if direction and destination:
            destination_room = world.rooms.get(destination)

            if room and destination_room:
                room.go_exits[direction] = destination_room
                reverse = self.get_reverse_of(direction)
                destination_room.go_exits[reverse] = room

                side_effect_msg = f"You notice a passage leading {direction}."

        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        # State-based description (opened_state_description)
        opened_desc = getattr(target, "opened_state_description", None)
        if opened_desc:
            parts.append(f"You see {opened_desc}")
        else:
            parts.append(f"The {target.canonical_name()} is opened.")

        # Revealed exit text
        if side_effect_msg:
            parts.append(side_effect_msg)

        return self.build_message(parts)


    def close(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        **kwargs
    ) -> str:

        room = self.room()
        world = self.world()
        
        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]

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
        outcome: VerbOutcome | None = try_item_special_handler(target, "close", words)
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

        # Post-change side effect: hide exit if configured
        side_effect_msg = ""
        direction = getattr(target, "open_exit_direction", None)
        destination = getattr(target, "open_exit_destination", None)

        if direction and destination:
            destination_room = world.rooms.get(destination)

            if room and destination_room:
                room.go_exits.pop(direction, None)   # should use room_remove_exit function when we have it

                reverse = self.get_reverse_of(direction)
                destination_room.go_exits.pop(reverse, None)   # should use room_remove_exit function when we have it

                side_effect_msg = f"You seal off the passage leading {direction}."


        # ------------- Build the final return string ----------------
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result_msg:
            parts.append(result_msg)

        # State-based description (closed_state_description)
        state_desc = getattr(target, "closed_state_description", None)
        if state_desc:
            parts.append(f"You see {state_desc}")
        else:
            parts.append(f"The {target.canonical_name()} is closed.")

        # Hidden exit text
        if side_effect_msg:
            parts.append(side_effect_msg)

        return self.build_message(parts)

    def unlock(
        self,
        target: Optional[Noun],
        words: tuple[str, ...],
        **kwargs
    ) -> str:

        room = self.room()
        world = self.world()
        
        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]

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
        outcome: VerbOutcome | None = try_item_special_handler(target, "unlock", words)
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

        # State-based description (unlocked_state_description)
        state_desc = getattr(target, "unlocked_state_description", None)
        if state_desc:
            parts.append(f"You see {state_desc}")
        else:
            parts.append(f"The {target.canonical_name()} is unlocked.")

        return self.build_message(parts)
    
    def light(self, target: Optional[Noun], words: tuple[str, ...], **kwargs) -> str:

        room = self.room()
        world = self.world()
        player = self.player()
        inventory = player.sack.contents
        
        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]

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
        outcome: VerbOutcome | None = try_item_special_handler(target, "light", words)
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

        # State-based description (lit_state_description)
        state_desc = getattr(target, "lit_state_description", None)
        if state_desc:
            parts.append(f"You see {state_desc}")
        else:
             parts.append(f"The {target.canonical_name()} is lit.")

        return self.build_message(parts)


    def extinguish(
        self,
        target: Optional[Noun],
        words: tuple[str, ...],
        **kwargs
    ) -> str:
        
        parse = self.resolve_noun_or_word(words, interest=['all', 'everything', 'hands', 'hand'])
        keywords = parse["keywords"]        
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "extinguish", words)
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

        # State-based description (unlit_state_description)
        state_desc = getattr(target, "unlit_state_description", None)
        if state_desc:
            parts.append(f"You see {state_desc}")
        else:
             parts.append(f"The {target.canonical_name()} is freshly charred and blackened, with a faint wisp of smoke still rising from it.")

        return self.build_message(parts)
    

    def rub(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        **kwargs
    ) -> str:
        
        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]        
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "rub", words)
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
    

    def tie(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
        cmd: ExecuteCommand = None
    ) -> str:
        
        keywords = cmd.modifiers
        target = cmd.direct_object if cmd.direct_object else None  

        preposition = ("to")
        indirect, indirect_name = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, preposition)
      
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "tie", words)
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
            preposition=preposition
        )

        # Post-change side effect: enable item for climbing
        target.is_climbable = True
        side_effect_msg =  f"The {target.canonical_name()} is now tied to the {indirect.canonical_name()} and dangles down the cliff face below."

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


    def untie(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:
        return self.build_message("Not implemented yet")    
    
 