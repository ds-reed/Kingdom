"""
Item behavior registry and dispatch.

Defines item-specific behavior handlers, registration decorators,
lookup utilities, and the unified special-handling pipeline.

This module is the single source of truth for item-driven puzzle logic.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from enum import Enum, auto

class VerbControl(Enum):
    CONTINUE = auto()  # fall through to default behavior
    SKIP = auto()      # skip this item but continue ALL
    STOP = auto()      # abort the entire verb // not implemented


@dataclass
class VerbOutcome:
    control: VerbControl = VerbControl.CONTINUE
    message: Optional[str] = None




# ------------------------------------------------------------
# Behavior registry
# ------------------------------------------------------------

ItemBehaviorHandler = Callable[
    [object, str, tuple[str, ...], "object | None"],
    Optional[VerbOutcome] | Optional[str] | None
]

_ITEM_BEHAVIORS: dict[str, ItemBehaviorHandler] = {}


def _active_state():
    from kingdom.model.game_init import get_action_state

    try:
        return get_action_state()
    except RuntimeError:
        return None


def register_item_behavior(name: str):
    """Decorator to register an item-specific behavior by name."""
    def decorator(func: ItemBehaviorHandler) -> ItemBehaviorHandler:
        _ITEM_BEHAVIORS[name] = func
        return func
    return decorator


def get_behavior(name: str) -> Optional[ItemBehaviorHandler]:
    """Look up a registered behavior by name."""
    return _ITEM_BEHAVIORS.get(str(name).strip())


#--------------------------------------------------------------
# Verb central lookup and pass control for item-specific special handling
#--------------------------------------------------------------

def try_item_special_handler(
    target: object,
    verb_name: str,
    words: tuple[str, ...],
    ctx: "object | None",
) -> str | None:
    """
    Unified special-handler lookup and execution.
    Returns the handler's result if it overrides the verb,
    or None if no special handling occurred.
    """

    if target is None:
        return None

    # Look up handler name from the item's special_handlers dict
    handler_name = getattr(target, "special_handlers", {}).get(verb_name)
    if not handler_name:
        return None

    # Resolve the behavior function
    handler = get_behavior(handler_name)
    if handler is None:
        return None

    # Execute the handler
    return handler(target, verb_name, words, ctx)



# ------------------------------------------------------------
# Puzzle helpers 
# ------------------------------------------------------------

def _spawn_room_item(dispatch_context: "object | None", *, name: str, handle: str, is_gettable: bool,  get_refuse_string: str) -> None:
    state = _active_state()
    if state is None:
        return

    room = getattr(state, "current_room", None)
    if room is None:
        return

    for existing in getattr(room, "items", []):
        if getattr(existing, "obj_handle", lambda: None)() == handle:
            return

    from kingdom.model.noun_model import Item

    new_item = Item(
        name,
        handle=handle,
        is_gettable=is_gettable,
        get_refuse_string=get_refuse_string,
        )
    
    room.items.append(new_item)   



# ------------------------------------------------------------
# Behavior implementations go below this line
# ------------------------------------------------------------

# @register_item_behavior("example_behavior")
# def example_behavior(item, verb, words, ctx):
#     ...
#     return VerbOutcome("Example!", stop_outer=True)

#----------------- the Magic Bean test item ---------------------------------

@register_item_behavior("open_bean")
def open_bean(item, verb_name, words, ctx):

    print("Ha Ha - you tried to open a magical bean!")  # or log it
    return VerbOutcome(message="you reached me!!!!", control=VerbControl.SKIP)   

# ----------------- the fish ---------------------------------

@register_item_behavior("eat_fish")
def eat_fish(item, verb, words, ctx):

    state = _active_state()
    player = getattr(state, "current_player", None)
    if player is None:
        return VerbOutcome(
            message="No active player.",
            control=VerbControl.STOP
        )
    inventory = player.sack.contents

    if item not in inventory:
        return VerbOutcome(
            message="You have no fish.",
            control=VerbControl.SKIP
        )
    
    room = getattr(state, "current_room", None)
    if room is None:
        return VerbOutcome(
            message="No active room.",
            control=VerbControl.STOP
        )

    # Check if vomit already exists to prevent duplicates
    for obj in room.items: 
        if getattr(obj, "obj_handle", lambda: None)() == "vomit": 
            return VerbOutcome( message="You made quite a mess here!", control=VerbControl.SKIP )
        
    # spawn vomit if it doesn't already exist
    vomit = _spawn_room_item(ctx, 
        name="There is vomit on a nearby wall.",
        handle="vomit",
        is_gettable=False,      
        get_refuse_string="EW! You can't get that."
    )

    # Final message - TRS80 old-school style
    return VerbOutcome(
        message="You barely get the fish to your nose when you vomit violently on a nearby wall.",
        control=VerbControl.STOP
    )


#----------------- the Lamp and Djinni ---------------------------------

@register_item_behavior("rub_lamp")
def rub_lamp(item, verb, words, ctx):

    state = _active_state()
    player = getattr(state, "current_player", None)
    if player is None:
        return VerbOutcome(
            message="No active player.",
            control=VerbControl.STOP
        )
    inventory = player.sack.contents

    # Must be holding the lamp
    if item not in inventory:
        return VerbOutcome(
            message="You have no lamp.",
            control=VerbControl.STOP
        )

    room = getattr(state, "current_room", None)
    if room is None:
        return VerbOutcome(
            message="No active room.",
            control=VerbControl.STOP
        )
    trigger_room_name = getattr(item, "trigger_room", None)

    # Only trigger Djinni in the correct room
    if room.name == trigger_room_name:

        # Presence check for list-based room.items
        djinni_present = any(
            getattr(obj, "obj_handle", lambda: None)() == "djinni" for obj in room.items
        )

        if not djinni_present:
            game = getattr(state, "game", None)
            if game is None:
                return VerbOutcome(
                    message="No active game.",
                    control=VerbControl.STOP
                )

            djinni_room, djinni = game.find_item_in_game("djinni")
            if djinni:
                game.move_item_between_rooms(djinni, djinni_room, room)

        return VerbOutcome(
            message=(
                "The lamp begins to emit a cloud of bluish smoke, which fills the air.\n"
                "The smoke solidifies into a an imposing djinni!\n"
                "He intones: 'MYPCLY JUBURUAY MIT DE DIGNIC PIC?' and looks at you inquiringly.\n"
                "(This means in magic Arabic, 'I will grant you one wish.')"
            ),
            control=VerbControl.STOP
        )

    # Default case: lamp gets shinier
    item.name = "a battered but shiny brass lamp"
    return VerbOutcome(
        message="You have a feeling of accomplishment as you rub the lamp. It looks shinier now.",
        control=VerbControl.SKIP
    )

# ----------------- the Djinni ---------------------------------

@register_item_behavior("speak_djinni")
def speak_djinni(item, verb, words, ctx):
    return _djinni_scripted_action(item, verb, words, ctx)


@register_item_behavior("make_djinni")
def make_djinni(item, verb, words, ctx):
    return _djinni_scripted_action(item, verb, words, ctx)


def _djinni_scripted_action(item, verb, words, ctx):
    """
    The Djinni does not understand English; any SAY or MAKE attempt
    triggers his pre-ordained magical action.
    """

    state = _active_state()
    room = getattr(state, "current_room", None)
    game = getattr(state, "game", None)
    if room is None or game is None:
        return VerbOutcome(
            message="The Djinni fizzles out due to unstable magic.",
            control=VerbControl.STOP
        )

    message_lines = [
        "The Djinni seems puzzled by your exotic language.",
        "Genies aren't omniscient, just omnipotent!",
        "But seeing that you are at a dead end and wanting to be helpful,",
        "he places a doorway in the west wall and disappears."
    ]

    # ------------------------------------------------------------
    # 1. Add a west exit (Room object, not string)
    # ------------------------------------------------------------
    if "west" not in room.connections:
        dest_name = getattr(item, "wish_exit_destination", "Colossal Cave")
        destination = game.rooms.get(dest_name)
        if destination is None:
            print(f"DEBUG: Could not find destination room '{dest_name}'")
        else:
            room.connections["west"] = destination

    # ------------------------------------------------------------
    # 2. Remove the Djinni from the current room
    # ------------------------------------------------------------
    if item in room.items:
        room.items.remove(item)

    # ------------------------------------------------------------
    # 3. Return narrative text
    # ------------------------------------------------------------
    return VerbOutcome(
        message="\n".join(message_lines),
        control=VerbControl.STOP
    )

