from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import get_behavior


from kingdom.models import Noun, DispatchContext, Player

def basic_checks(target, *, capability_attr, current_state_attr=None, desired_state=None, verb, already_msg=None):
    if target is None:
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
    override_method,
    state_attr,
    desired_state,
    used_item=None,
):
    # 1. Special handler
    handler_name = getattr(target, "special_handlers", {}).get(verb)
    if handler_name:
        handler = get_behavior(handler_name)
        if handler:
            result = handler(target, verb, (), ctx)
            if result is not None:
                return result

    # 2. Noun override
    override = getattr(target, override_method, None)
    if callable(override):
        result = override(ctx, ())
        if result is not None:
            return result

    # 3. Default mutation
    setattr(target, state_attr, desired_state)

    # 4. Message
    if used_item:
        return f"You {verb} the {target.get_noun_name()} with the {used_item.get_noun_name()}."
    return f"You {verb} the {target.get_noun_name()}."



class StateVerbHandler:

    def open(self, ctx: DispatchContext, target: Optional[Noun] = None, words: tuple[str, ...] = ()) -> str:
        if target is None:
            return "Open what?"

        # Standard refusals (locked, already open, not openable)
        if not target.is_openable:
            return f"You can't open the {target.get_noun_name()}."

        if target.is_lockable and target.is_locked:
            return getattr(target, "locked_description", None) or f"The {target.get_noun_name()} is locked."


        if target.is_open:
            return f"The {target.get_noun_name()} is already open."

        # Ask noun: any special behavior for this verb?
        handler_name = getattr(target, "special_handlers", {}).get("open")
        
        if handler_name:
            handler = get_behavior(handler_name)
            if handler:
                result = handler(target, "open", words, ctx)
                if result is not None:
                    return result

        # Normal open
        target.is_open = True

        # Exit reveal if configured
        direction = getattr(target, "open_exit_direction", None)
        destination = getattr(target, "open_exit_destination", None)
        if direction and destination:
            room = ctx.state.current_room
            game = ctx.game
            destination_room = game.rooms.get(destination)
            if room and destination_room:
                room.connections[direction] = destination_room
                reverse = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}.get(direction)
                if reverse:
                    destination_room.connections[reverse] = room

        # Message
        return getattr(target, "open_action_description", None) or f"You open the {target.get_noun_name()}."

    def close(self, ctx: DispatchContext, target: Optional[Noun] = None, words: tuple[str, ...] = ()) -> str:
        if target is None:
            return "Close what?"

        # 1. Basic checks (refusals)
        if not getattr(target, "is_openable", False):
            return f"You can't close the {target.get_noun_name()}."

        if not getattr(target, "is_open", False):
            return f"The {target.get_noun_name()} is already closed."

        # 2. Ask noun: any special behavior for this verb?
        handler_name = getattr(target, "special_handlers", {}).get("close")
        
        if handler_name:
            handler = get_behavior(handler_name)
            if handler:
                result = handler(target, "close", words, ctx)
                if result is not None:
                    return result

        # 3. Perform state change
        target.is_open = False

        # 4. Hide exit if configured
        if getattr(target, "close_hides_exit", False) and getattr(target, "open_exit_direction", None):
            direction = target.open_exit_direction
            if ctx.state.current_room:
                ctx.state.current_room.connections.pop(direction, None)

        # 5. Return message: custom action first, then generic
        if getattr(target, "close_action_description", None):
            return target.close_action_description

        return f"You close the {target.get_noun_name()}."


    def unlock(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        if target is None:
            return "Unlock what?"

        # 1. Basic checks (refusals)
        if not getattr(target, "is_lockable", False):
            return f"You can't unlock the {target.get_noun_name()}."

        if not getattr(target, "is_locked", False):
            return f"The {target.get_noun_name()} is already unlocked."

        # 2. Player must have the key
        inventory = ctx.game.current_player.sack.contents
        key_name = getattr(target, "unlock_key", None) 
        if key_name:
            has_key = any(
                getattr(item, "noun_name", "").lower() == key_name.lower()
                for item in inventory
            )
            if not has_key:
                return f"You don't have the key to unlock the {target.get_noun_name()}."


        # 3. Item-specific special handler
        handler_name = getattr(target, "special_handlers", {}).get("unlock")
        if handler_name:
            handler = get_behavior(handler_name)
            if handler:
                result = handler(target, "unlock", words, ctx)
                if result is not None:
                    return result

        # 4. Default unlock
        target.is_locked = False
        return f"You unlock the {target.get_noun_name()}."

    

    def light(self, ctx: DispatchContext, target: Optional[Noun], words: tuple[str, ...]) -> str:
        # 1. Basic capability + already-lit checks
        refusal = basic_checks(
            target,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=True,
            verb="light",
            already_msg="lit",
        )
        if refusal:
            return refusal

        # 2. Required ignition source
        ignition_source = next(
            (item for item in ctx.game.current_player.sack.contents
            if getattr(item, "can_ignite", False)),
            None
        )
        if not ignition_source:
            return f"You have nothing to light the {target.get_noun_name()} with."

        # 3. Unified state-change pipeline
        return apply_state_change(
            ctx=ctx,
            target=target,
            verb="light",
            override_method="on_light",
            state_attr="is_lit",
            desired_state=True,
            used_item=ignition_source,
        )


    def extinguish(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        # 1. Basic capability + already-extinguished checks
        refusal = basic_checks(
            target,
            capability_attr="is_lightable",
            current_state_attr="is_lit",
            desired_state=False,    
            verb="extinguish",
            already_msg="extinguished",
        )
        if refusal:
            return refusal

        # 2. Unified state-change pipeline
        return apply_state_change(
            ctx=ctx,
            target=target,
            verb="extinguish",
            override_method="on_extinguish",
            state_attr="is_lit",
            desired_state=False,
        )

    # Add similar methods for TURN, PUSH, PRESS, BREAK, SMASH, RUB, DIAL, etc.
