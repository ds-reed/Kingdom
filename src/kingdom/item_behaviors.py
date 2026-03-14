"""
Item behavior registry and dispatch.

Defines item-specific behavior handlers, registration decorators,
lookup utilities, and the unified special-handling pipeline.

This module is the single source of truth for item-driven puzzle logic.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from enum import Enum, auto

from kingdom.model.game_init import get_game
from kingdom.model.noun_model import Noun


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
    return handler(target, verb_name, words)



# ------------------------------------------------------------
# Puzzle helpers 
# ------------------------------------------------------------

def _spawn_room_item(dispatch_context: "object | None", *, name: str, handle: str, is_takeable: bool,  take_refuse_string: str) -> None:
    state = get_game().action_state
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
        is_takeable=is_takeable,
        take_refuse_string=take_refuse_string,
        )
    
    room.items.append(new_item)   



# ------------------------------------------------------------
# Behavior implementations go below this line
# ------------------------------------------------------------

# @register_item_behavior("example_behavior")
# def example_behavior(item, verb, words):
#     ...
#     return VerbOutcome("Example!", stop_outer=True)

#----------------- the Magic Bean test item ---------------------------------

@register_item_behavior("open_bean")
def open_bean(item, verb_name, words):

    print("Ha Ha - you tried to open a magical bean!")  # or log it
    return VerbOutcome(message="you reached me!!!!", control=VerbControl.SKIP)   

# ----------------- the fish ---------------------------------

@register_item_behavior("eat_fish")
def eat_fish(item, verb, words):

    state = get_game().action_state
    world = getattr(state, "world", None)
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
    vomit = _spawn_room_item(world, 
        name="it looks like someone has been violently ill on a nearby wall",
        handle="vomit",
        is_takeable=False,      
        take_refuse_string="EW! The nasty vomit just makes your hands dirty."
    )

    # Final message - TRS80 old-school style
    return VerbOutcome(
        message="You barely get the fish to your nose when you vomit violently on a nearby wall.",
        control=VerbControl.STOP
    )


#----------------- the Lamp and Djinni ---------------------------------

@register_item_behavior("rub_lamp")
def rub_lamp(item, verb, words):

    state = get_game().action_state
    world = state.world if state else None
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
            if world is None:
                return VerbOutcome(
                    message="No active world.",
                    control=VerbControl.STOP
                )

            djinni_room, djinni = world.find_item_in_game("djinni")
            if djinni:
                world.move_item_between_rooms(djinni, djinni_room, room)

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
    item.description = "a battered but shiny brass lamp"
    return VerbOutcome(
        message="You have a feeling of accomplishment as you rub the lamp. It looks shinier now.",
        control=VerbControl.CONTINUE
    )

# ----------------- the Djinni ---------------------------------

@register_item_behavior("speak_djinni")
def speak_djinni(item, verb, words):
    return _djinni_scripted_action(item, verb, words)


@register_item_behavior("make_djinni")
def make_djinni(item, verb, words):
    return _djinni_scripted_action(item, verb, words)


def _djinni_scripted_action(item, verb, words):
    """
    The Djinni does not understand English; any SAY or MAKE attempt
    triggers his pre-ordained magical action.
    """

    state = get_game().action_state
    room = getattr(state, "current_room", None)
    world = state.world if state else None


    message_lines = [
        "The Djinni seems puzzled by your exotic language.",
        "Genies aren't omniscient, just omnipotent!",
        "But seeing that you are at a dead end and wanting to be helpful,",
        "he places a doorway in the west wall and disappears."
    ]

    # ------------------------------------------------------------
    # 1. reveal and open the west exit in current room
    # ------------------------------------------------------------

    direction = "west"
    reverse_direction = "east"

    forward_exit = room.get_exit("go", direction)
    if forward_exit:
        forward_exit.set_existing("is_visible", True)
        forward_exit.set_existing("is_passable", True)
        message_lines.append(f"You notice a new passage leading {direction}.")

        destination = forward_exit.destination

        reverse_exit = destination.get_exit("go", reverse_direction)
        if reverse_exit:
            reverse_exit.set_existing("is_visible", True)
            reverse_exit.set_existing("is_passable", True)
    else:
        message_lines.append(f"ERROR - no direction found in room data for {direction}.")


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

#---------------------------burning torch!------------------------------

@register_item_behavior("drop_torch")
def put_torch(item, verb_name, indirect_obj):
    active_state = get_game().action_state
    room = getattr(active_state, "current_room", None)

    message = []
    if getattr(item, "is_lit", False):
        if not indirect_obj:
            return None

        container = Noun.get_by_name(indirect_obj[0])
        if container and getattr(container, "is_flamable", False):
            message.append(f"As you put the burning torch into {container.display_name()} it catches on fire!")
            for contained_item in list(container.contents):
                if getattr(contained_item, "is_flamable", False):
                    message.append(f"{contained_item.display_name()} is destroyed by the fire!")
                    container.remove_item(contained_item)
                else:
                    message.append(f"{contained_item.display_name()} is unharmed by the fire and drops to the ground.")
                    if room is not None:
                        room.add_item(contained_item)
            message.append(f"{container.display_name()} is destroyed by the fire!")
            if room is not None:
                room.remove_container(container)  # remove the container itself


            return VerbOutcome(message=message, control=VerbControl.STOP)
    return None