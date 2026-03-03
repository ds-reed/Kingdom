from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import try_item_special_handler, VerbOutcome, VerbControl
from kingdom.verbs.verb_handler import VerbHandler

from kingdom.model.models import Noun, Item, DirectionRegistry
from kingdom.renderer import RoomRenderer, render_current_room




class StateVerbHandler(VerbHandler):

    # ------------------------------------------------------------
    # state change helper
    # ------------------------------------------------------------
    
    def basic_checks(self, target, *, verb_phrase=None, capability_attr=None, current_state_attr=None, desired_state=None, already_msg=None):

        if capability_attr and not getattr(target, capability_attr, False):
            return self.cannot(target, verb_phrase)

        if current_state_attr is not None:
            current = getattr(target, current_state_attr, None)
            if current == desired_state:
                return self.already(target, already_msg)

        return None

    def require_item(self, *, required_item_id:Noun = None, noun:Noun = None, verb_phrase=None):
        player = self.player()
        if not player.has_item(required_item_id):
            return f"You don't have the {required_item_id.canonical_name()} to {verb_phrase} the {noun.canonical_name()}."
        return None

    def lookup_required_item_id(self, required_noun_name, verb_phrase) -> Noun | None:
        required = Item.get_by_name(required_noun_name)
        if required is None:
             print(f"Error: Required noun '{required_noun_name}' not found in game data for {verb_phrase}.")
             return None
        return required                

    def apply_state_change(
        self,
        target,
        verb_phrase,
        *,
        state_attr=None,
        desired_state=None,
        used_item=None,
    ):

        # 1. Apply the state change
        if state_attr is not None:
            setattr(target, state_attr, desired_state)

        # 2. Build the message
        if used_item:
            return f"You {verb_phrase} {target.display_name()} with {used_item}."
        else:
            return f"You {verb_phrase} {target.display_name()}."

#----------------- the core state-changing verbs -------------------------

    def open(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:

        room = self.room()
        game = self.game()
        
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "open", words, None)
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
            destination_room = game.rooms.get(destination)

            if room and destination_room:
                room.connections[direction] = destination_room
                reverse = self.get_reverse_of(direction)
                destination_room.connections[reverse] = room

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
    ) -> str:

        room = self.room()
        game = self.game()
        
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "close", words, None)
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

        side_effect_msg = ""
        direction = getattr(target, "open_exit_direction", None)
        destination = getattr(target, "open_exit_destination", None)

        if direction and destination:
            destination_room = game.rooms.get(destination)

            if room and destination_room:
                room.connections.pop(direction, None)   # should use room_remove_exit function when we have it

                reverse = self.get_reverse_of(direction)
                destination_room.connections.pop(reverse, None)   # should use room_remove_exit function when we have it

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
    ) -> str:

        room = self.room()
        game = self.game()
        
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "unlock", words, None)
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
        key_id = self.lookup_required_item_id(key_name, "unlock") 

        if key_name and key_id:
            no_key_msg = self.require_item(
                required_item_id=key_id,
                noun=target,
                verb_phrase="unlock",
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
    
    def light(self, target: Optional[Noun], words: tuple[str, ...]) -> str:

        room = self.room()
        game = self.game()
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "light", words, None)
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "extinguish", words, None)
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
    

    def eat(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "eat", words, None)
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

        # 4. Post-mutation side effect: remove item from inventory  

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
    

    def rub(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "rub", words, None)
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

    def say(
        self,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:
        
        parse = self.resolve_noun_or_word(words, interest=['wish'])
        keywords = parse["keywords"]        
        # ------------------------------------------------------------
        # 1. Verb modifier checks
        # ------------------------------------------------------------
        if "wish" in keywords:    # special case for djinni lamp
            outcome: VerbOutcome | None = try_item_special_handler(target, "say", words, None)
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
            capability_attr="is_verbally_interactive",
            verb_phrase="speak to",
        )
        if cant_msg:
            return self.build_message(cant_msg)
        
        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome: VerbOutcome | None = try_item_special_handler(target, "say", words, None)
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "") 

        # ------------------------------------------------------------
        # 4. Main logic
        # ------------------------------------------------------------   
        result_msg = self.apply_state_change(
            target=target,
            verb_phrase="say",
            state_attr="has_been_spoken_to",
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
                

    def make(self, target=None, words=()):

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
            outcome: VerbOutcome | None = try_item_special_handler(target, "make", words, None)
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
        outcome: VerbOutcome | None = try_item_special_handler(target, "make", words, None)
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

    def look(self, target: Noun | None, words: tuple[str, ...] = ()):

        room = self.room()

        parse= self.resolve_noun_or_word(words, interest=["inside", "in"])
        noun = parse["noun"]
        keywords = parse["keywords"]
        raw = parse["raw"]

        renderer = RoomRenderer()

        if "inside" in keywords or "in" in keywords:
            if target is None:
                return self.build_message("Look inside what?")
            if isinstance(target, Box):
                return self.build_message(renderer.describe_box_contents(target))
            return self.build_message(f"You can't look inside the {target.get_noun_name()}.")
        
        if not target: target = noun

        if target is not None:
            if getattr(target, "examine_string", None) is not None:
                return self.build_message(target.examine_string)
            elif isinstance(target, Box):
                return self.build_message(f"You see {target.display_name()}. There might be something interesting inside.")
            elif room.has_item(target):
                return self.build_message(f"You see {target.display_name()} here.")
            else:
                return self.build_message(f"You see no {target.canonical_name()} here.")
            
        if raw: return self.build_message("I don't understand what you want to look at.")

        return self.build_message(renderer.describe_room(room))
