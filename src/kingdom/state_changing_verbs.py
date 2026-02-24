from __future__ import annotations
from typing import Callable, Optional, Iterable

from kingdom.item_behaviors import get_behavior


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

        # 3. Unified state-change pipeline
        result = apply_state_change(
            ctx=ctx,
            target=target,
            verb="open",
            override_method="on_open",
            state_attr="is_open",
            desired_state=True,
        )

        # 4. Post-mutation side effect: reveal exit if configured
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

        return result


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

        # 2. Unified state-change pipeline (special handlers + noun override + mutation)
        result = apply_state_change(
            ctx=ctx,
            target=target,
            verb="close",
            override_method="on_close",
            state_attr="is_open",
            desired_state=False,
        )

        # 3. Post-mutation side effects: hide exit if configured
        if getattr(target, "close_hides_exit", False) and getattr(target, "open_exit_direction", None):
            direction = target.open_exit_direction
            room = ctx.state.current_room
            if room:
                room.connections.pop(direction, None)

        return result


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

        # 2. Required key (if any)
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

        # 3. Unified state-change pipeline
        return apply_state_change(
            ctx=ctx,
            target=target,
            verb="unlock",
            override_method="on_unlock",
            state_attr="is_locked",
            desired_state=False,
            used_item=key_item,
        )


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
            words=words,
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
