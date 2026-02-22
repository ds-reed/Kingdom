"""
state_changing_verbs.py

Handlers for verbs that change the state of objects or rooms (e.g., OPEN, CLOSE, UNLOCK, LIGHT, TURN, PUSH, PRESS, BREAK, SMASH, RUB, DIAL).

This module centralizes state-changing verb logic for clarity and maintainability.
"""

from .models import Room, Noun, DispatchContext

def state_change_helper(
    target: Noun | None,
    capability_attr: str,
    state_attr: str,
    desired_state: bool,
    already_msg: str,
    success_msg: str,
    fail_msg: str,
) -> str:
    if target and hasattr(target, capability_attr) and getattr(target, capability_attr):
        current = getattr(target, state_attr, not desired_state)
        if current == desired_state:
            return already_msg.format(target=target)
        setattr(target, state_attr, desired_state)
        return success_msg.format(target=target)
    return fail_msg.format(target=target)


class StateChangingVerbHandler:

    def open(self, context: DispatchContext, target: Noun | None, words: list[str]) -> str:
        return state_change_helper(
            target,
            capability_attr='is_openable',
            state_attr='is_open',
            desired_state=True,
            already_msg="The {target.name} is already open.",
            success_msg="You open the {target.name}.",
            fail_msg="You can't open that."
        )

    def close(self, context: DispatchContext, target: Noun | None, words: list[str]) -> str:
        return state_change_helper(
            target,
            capability_attr='is_openable',
            state_attr='is_open',
            desired_state=False,
            already_msg="The {target.name} is already closed.",
            success_msg="You close the {target.name}.",
            fail_msg="You can't close that."
        )

    def unlock(self, context: DispatchContext, target: Noun | None, words: list[str]) -> str:
        return state_change_helper(
            target,
            capability_attr='is_lockable',
            state_attr='is_locked',
            desired_state=False,
            already_msg="The {target.name} is already unlocked.",
            success_msg="You unlock the {target.name}.",
            fail_msg="You can't unlock that."
        )

    def light(self, context: DispatchContext, target: Noun | None, words: list[str]) -> str:
        return state_change_helper(
            target,
            capability_attr='is_lightable',
            state_attr='is_lit',
            desired_state=True,
            already_msg="The {target.name} is already lit.",
            success_msg="You light the {target.name}.",
            fail_msg="You can't light that."
        )
    
    def extinguish(self, context: DispatchContext, target: Noun | None, words: list[str]) -> str:
        return state_change_helper(
            target,
            capability_attr='is_lightable',
            state_attr='is_lit',
            desired_state=False,
            already_msg="The {target.name} is already extinguished.",
            success_msg="You extinguish the {target.name}.",
            fail_msg="You can't extinguish that."
        )

    # Add similar methods for TURN, PUSH, PRESS, BREAK, SMASH, RUB, DIAL, etc.
