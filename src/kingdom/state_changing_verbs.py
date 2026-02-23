from __future__ import annotations
from typing import Callable, Optional, Iterable

from .models import Noun, DispatchContext


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

    # 2. Noun override
    override: Optional[Callable[[DispatchContext, Iterable[str]], Optional[str]]] = (
        getattr(target, override_method, None)
    )

    if override is not None:
        result = override(ctx, words)
        if result is not None:
            return result

    # 3. Default world-state mutation
    if not hasattr(target, state_attr):
        # Noun forgot to define the attribute — safest fallback
        return f"You {fallback_verb} the {target.get_noun_name()}."

    setattr(target, state_attr, desired_state)

    # 4. Generic fallback
    return f"You {fallback_verb} the {target.get_noun_name()}."


class StateVerbHandler:

    def open(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        return apply_state_change(
            ctx=ctx,
            target=target,
            words=words,
            override_method="on_open",
            state_attr="is_open",
            desired_state=True,
            fallback_verb="open",
        )

    def close(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        return apply_state_change(
            ctx=ctx,
            target=target,
            words=words,
            override_method="on_close",
            state_attr="is_open",
            desired_state=False,
            fallback_verb="close",
        )

    def unlock(
        self,
        ctx: DispatchContext,
        target: Optional[Noun],
        words: tuple[str, ...],
    ) -> str:
        return apply_state_change(
            ctx=ctx,
            target=target,
            words=words,
            override_method="on_unlock",
            state_attr="is_locked",
            desired_state=False,
            fallback_verb="unlock",
        )

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
