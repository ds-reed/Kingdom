from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import try_item_special_handler, VerbOutcome


from kingdom.models import Noun, DispatchContext, Player

def basic_checks(target, words, *,capability_attr, current_state_attr=None, desired_state=None, verb, already_msg=None):
    if target is None:
        if words and words[0]:
            return f"I see no {words[0]} here."
        else:
            return f"{verb.capitalize()} what?"

    if capability_attr and not getattr(target, capability_attr, False):
        return f"You can't {verb} the {target.get_noun_name()}."

    if current_state_attr is not None:
        current = getattr(target, current_state_attr, None)
        if current == desired_state:
            return f"The {target.get_noun_name()} is already {already_msg}."

    return None

def require_item(ctx, *, noun, required_noun_name, verb):
    inventory = ctx.game.current_player.sack.contents
    for item in inventory:
        if getattr(item, "noun_name", "").lower() == required_noun_name.lower():
            return item  # success
    return f"You don't have the {required_noun_name} to {verb} the {noun.get_noun_name()}."


def apply_state_change(
    ctx,
    target,
    verb,
    *,
    state_attr=None,
    desired_state=None,
    used_item=None,
):

    # 1. Optional mutation
    if state_attr is not None:
        setattr(target, state_attr, desired_state)

    # 2. Build the message
    if used_item:
        return f"You {verb} {target.get_name()} with {used_item.get_name()}."
    else:
        return f"You {verb} {target.get_name()}."



class StateVerbHandler:


    def open(
        self,
        ctx: DispatchContext,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:

        # 1. Basic capability + already-open checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_openable",
            current_state_attr="is_open",
            desired_state=True,
            verb="open",
            already_msg="open",
        )
        if refusal:
            return refusal

        # 2. Locked refusal (special case)
        if getattr(target, "is_lockable", False) and getattr(target, "is_locked", False):
            return (
                getattr(target, "locked_description", None)
                or f"The {target.get_noun_name()} is locked."
            )

        # 3. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "open", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or ""

        # 4. Unified state-change pipeline
        result = apply_state_change(
            ctx=ctx,
            target=target,
            verb="open",
            state_attr="is_open",
            desired_state=True,
        )

        # 5. Post-mutation side effect: reveal exit if configured
        revealed_text = ""
        direction = getattr(target, "open_exit_direction", None)
        destination = getattr(target, "open_exit_destination", None)

        if direction and destination:
            room = ctx.state.current_room
            game = ctx.game
            destination_room = game.rooms.get(destination)

            if room and destination_room:
                room.connections[direction] = destination_room

                reverse = {
                    "north": "south",
                    "south": "north",
                    "east": "west",
                    "west": "east",
                    "up": "down",
                    "down": "up",
                }.get(direction)

                if reverse:
                    destination_room.connections[reverse] = room

                revealed_text = f"You notice a passage leading {direction}."

        # 6. Build the final return string
        parts: list[str] = []

        # Action text (from special handler or state-change)
        if outcome and outcome.message:
            parts.append(outcome.message)
        elif result:
            parts.append(result)

        # State-based description (opened_state_description)
        opened_desc = getattr(target, "opened_state_description", None)
        if opened_desc and getattr(target, "is_open", False):
            parts.append(opened_desc)

        # Revealed exit text
        if revealed_text:
            parts.append(revealed_text)

        return "\n".join(parts) if parts else ""


    def close(
        self,
        ctx: DispatchContext,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:

        # 1. Basic capability + already-closed checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_openable",
            current_state_attr="is_open",
            desired_state=False,
            verb="close",
            already_msg="closed",
        )
        if refusal:
            return refusal
        
        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "close", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or ""

        # 3. Unified state-change pipeline (special handlers + noun override + mutation)
        return_message  = apply_state_change(
            ctx=ctx,
            target=target,
            verb="close",
            state_attr="is_open",
            desired_state=False,
        )

        # 4. Post-mutation side effects: hide exit if configured
        if getattr(target, "close_hides_exit", False) and getattr(target, "open_exit_direction", None):
            direction = target.open_exit_direction
            room = ctx.state.current_room
            if room:
                room.connections.pop(direction, None)

        return (outcome.message if outcome else None) or return_message or ""

    def unlock(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:

        # 1. Basic capability + already-unlocked checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_lockable",
            current_state_attr="is_locked",
            desired_state=False,
            verb="unlock",
            already_msg="unlocked",
        )
        if refusal:
            return refusal
        
        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "unlock", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Required key (if any)
        key_name = getattr(target, "unlock_key", None)
        if key_name:
            key_or_refusal = require_item(
                ctx,
                noun=target,
                required_noun_name=key_name,
                verb="unlock",
            )
            if isinstance(key_or_refusal, str):
                return key_or_refusal
            key_item = key_or_refusal
        else:
            key_item = None

        # 4. Unified state-change pipeline
        return_message = apply_state_change(
            ctx=ctx,
            target=target,
            verb="unlock",
            state_attr="is_locked",
            desired_state=False,
            used_item=key_item,
        )
        return (outcome.message if outcome else None) or return_message or ""
    
    def light(self, ctx: DispatchContext, target: Optional[Noun], words: tuple[str, ...]) -> str:
        # 1. Basic capability + already-lit checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=True,
            verb="light",
            already_msg="lit",
        )
        if refusal:
            return refusal

        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "light", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Required ignition source
        ignition_source = next(
            (item for item in ctx.game.current_player.sack.contents
            if getattr(item, "can_ignite", False)),
            None
        )
        if not ignition_source:
            return f"You have nothing to light the {target.get_noun_name()} with."

        # 4. Unified state-change pipeline
        return_message = apply_state_change(
            ctx=ctx,
            target=target,
            verb="light",
            state_attr="is_lit",
            desired_state=True,
            used_item=ignition_source,
        )
        return (outcome.message if outcome else None) or return_message or ""

    def extinguish(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        # 1. Basic capability + already-extinguished checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=False,    
            verb="extinguish",
            already_msg="extinguished",
        )
        if refusal:
            return refusal

        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "extinguish", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Unified state-change pipeline
        return_message = apply_state_change(
            ctx=ctx,
            target=target,
            verb="extinguish",
            state_attr="is_lit",
            desired_state=False,
        )
        return (outcome.message if outcome else None) or return_message or ""
    

    def eat(
        self,
        ctx: DispatchContext,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:
        # 1. Basic capability checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_edible",
            desired_state=True,
            verb="eat",
        )
        if refusal:
            return refusal

        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "eat", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Unified state-change pipeline
        return_msg = apply_state_change(
            ctx=ctx,
            target=target,
            verb="eat",
            state_attr=None,
            desired_state=None,
        )   
        if getattr(target, "eaten_success_string", None):
            return_msg = target.eaten_success_string

        # 4. Post-mutation side effect: remove item from inventory   # note for when refactoring - we can eat things that are in the room, not just inventory, so we'll need to look for it and remove it from the appropriate place
        inventory = ctx.game.current_player.sack.contents
        if target in inventory:
            inventory.remove(target)
        return return_msg


    def rub(
        self,
        ctx: DispatchContext,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:
        # 1. Basic capability checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_rubbable",
            desired_state=True,
            verb="rub",
        )
        if refusal:
            return refusal

        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "rub", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Unified state-change pipeline
        return_message = apply_state_change(
            ctx=ctx,
            target=target,
            verb="rub",
            state_attr="is_rubbed",
            desired_state=True,
        )   
        

        return (outcome.message if outcome else None) or return_message or ""
     

    def say(
        self,
        ctx: DispatchContext,
        target: Optional[Noun] = None,
        words: tuple[str, ...] = (),
    ) -> str:
        # 1. Basic capability checks
        refusal = basic_checks(
            target,
            words=words,
            capability_attr="is_verbally_interactive",
            desired_state=True,
            verb="say",
        )
        if refusal:
            return "You speak to the wind; the wind does not hear. The wind cannot hear." if target is None else refusal

        # 2. Unified special-handling pipeline
        outcome: VerbOutcome | None = try_item_special_handler(target, "say", words, ctx)
        if outcome and outcome.stop:
            return outcome.message or "" 

        # 3. Unified state-change pipeline
        return_message = apply_state_change(
            ctx=ctx,
            target=target,
            verb="say",
            state_attr="has_been_spoken_to",
            desired_state=True,
        )
        

        return (outcome.message if outcome else None) or return_message or ""
                

    def make(self, ctx, target=None, words=()):

        # Implicit Djinni targeting - clean this all up when we can do other things with make
        if target is None:
            room = ctx.state.current_room
            for obj in room.items:
                if getattr(obj, "noun_name", None) == "djinni":
                    target = obj
                    break

        outcome = try_item_special_handler(target, "make", words, ctx)

        if outcome and outcome.stop:
            return outcome.message or ""

        return "Nothing happens."
