from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import get_behavior


from kingdom.models import Noun, DispatchContext, Player


def apply_state_change(
    ctx: DispatchContext,
    target: Optional[Noun],
    words: Iterable[str],
    override_method: str,
    state_attr: str,
    desired_state: bool,
    fallback_verb: str,
) -> str:
    """
    Generic helper for state-changing verbs in the new override-first architecture.
    """

    # 1. No target
    if target is None:
        return f"{fallback_verb.capitalize()} what?"
    
    # 2. Item override
    handler_name = getattr(target, "special_handlers", {}).get(fallback_verb)
    if handler_name:
        handler = get_behavior(handler_name)
        if handler:
            result = handler(target, fallback_verb, tuple(words), ctx)
            if result is not None:
                return result

    # 3. Noun override
    override: Optional[Callable[[DispatchContext, Iterable[str]], Optional[str]]] = (
        getattr(target, override_method, None)
    )

    if override is not None:
        result = override(ctx, words)
        if result is not None:
            return result

    # 4. Default world-state mutation
    if not hasattr(target, state_attr):
        # Noun forgot to define the attribute — safest fallback
        return f"You {fallback_verb} the {target.get_noun_name()}."

    setattr(target, state_attr, desired_state)

    # 45. Generic fallback
    return f"You {fallback_verb} the {target.get_noun_name()}."


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
        print(f"DEBUG: unlock_key for {target.get_noun_name()} is {key_name}")  # Debug statement
        print(f"DEBUG: Player inventory contains {[item.name for item in inventory]}")  # Debug statement   
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

    

    def light(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        return apply_state_change(
            ctx=ctx,
            target=target,
            words=words,
            override_method="on_light",
            state_attr="is_lit",
            desired_state=True,
            fallback_verb="light",
        )

    def extinguish(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        return apply_state_change(
            ctx=ctx,
            target=target,
            words=words,
            override_method="on_extinguish",
            state_attr="is_lit",
            desired_state=False,
            fallback_verb="extinguish",
        )

    # Add similar methods for TURN, PUSH, PRESS, BREAK, SMASH, RUB, DIAL, etc.
