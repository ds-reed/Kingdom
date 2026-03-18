"""
Item behavior registry and dispatch.

Defines item-specific behavior handlers, registration decorators,
lookup utilities, and the unified special-handling pipeline.

This module is the single source of truth for item-driven puzzle logic.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from enum import Enum, auto

from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Item, Noun, Room
from kingdom.rendering.descriptions import render_current_room


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
    [object, str, "object | None", dict],
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
    indirect_obj: object = None,
    **kwargs,
) -> str | None:


    if target is None and indirect_obj is None:
        return None

    if target and getattr(target, "special_handlers", {}).get(verb_name):
        handler_name = target.special_handlers[verb_name]
        handler = get_behavior(handler_name)
        if handler:
            return handler(target, verb_name, indirect_obj=indirect_obj, **kwargs)
        
    if indirect_obj and getattr(indirect_obj, "special_handlers", {}).get(verb_name):
        handler_name = indirect_obj.special_handlers[verb_name]
        handler = get_behavior(handler_name)
        if handler:
            return handler(target, verb_name, indirect_obj=indirect_obj, **kwargs)

    return None




# ------------------------------------------------------------
# Puzzle helpers 
# ------------------------------------------------------------

def _spawn_room_item(dispatch_context: "object | None", *, name: str, handle: str, is_takeable: bool,  take_refuse_description: str) -> None:

    game=get_game()
    room = getattr(game, "current_room", None)
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
        take_refuse_description=take_refuse_description,
        )
    
    room.items.append(new_item)   



# ------------------------------------------------------------
# Behavior implementations go below this line
# ------------------------------------------------------------

# @register_item_behavior("example_behavior")
# def example_behavior(item, verb, words):
#     ...
#     return VerbOutcome("Example!", stop_outer=True)

# ----------------- the fish ---------------------------------

@register_item_behavior("eat_fish")
def eat_fish(item, verb, **kwargs):

    game = get_game() 
    world = getattr(game, "world", None)
    room = getattr(game, "current_room", None)

    # Check if vomit already exists to prevent duplicates
    for obj in room.items: 
        if getattr(obj, "obj_handle", lambda: None)() == "vomit": 
            return VerbOutcome( message="You made quite a mess here!", control=VerbControl.SKIP )
        
    # spawn vomit if it doesn't already exist
    _spawn_room_item(world, 
        name="it looks like someone has been violently ill on a nearby wall",
        handle="vomit",
        is_takeable=False,      
        take_refuse_description="EW! The nasty vomit just makes your hands dirty."
    )

    # Final message
    return VerbOutcome(
        message="You barely get the fish to your nose when you vomit violently on a nearby wall.",
        control=VerbControl.STOP
    )


#--------------------------- eat banana ---------------------------------

@register_item_behavior("eat_banana")
def eat_banana(item, verb, **kwargs):

    game = get_game()
    player = getattr(game, "current_player", None)
    room = getattr(game, "current_room", None)

    player.remove_from_sack(item)
    player.add_to_sack(Item.get_by_name("peel"))

    # Final message 
    return VerbOutcome(
        message="You peel the banana and wolf it down hungrily, leaving only the slippery peel behind.",
        control=VerbControl.SKIP
    )

#----------------- the Lamp and Djinni ---------------------------------

@register_item_behavior("rub_lamp")
def rub_lamp(item, verb, **kwargs):

    game = get_game()
    world = getattr(game, "world", None)
    player = getattr(game, "current_player", None)
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

    room = getattr(game, "current_room", None)
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
                "He intones: ' \"MYPCLY JUBURUAY MIT DE NURDY SMUDY DIGNIC PIC?\"' and looks at you inquiringly.\n"
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
def speak_djinni(item, verb, **kwargs):
    return _djinni_scripted_action(item, verb, **kwargs)


@register_item_behavior("make_djinni")
def make_djinni(item, verb, **kwargs):
    return _djinni_scripted_action(item, verb, **kwargs)


def _djinni_scripted_action(item, verb, **kwargs):
    """
    The Djinni does not understand English; any SAY or MAKE attempt
    triggers his pre-ordained magical action.
    """

    game = get_game()
    room = getattr(game, "current_room", None)
    world = getattr(game, "world", None)


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
def drop_torch(item, verb_name, indirect_obj = None, **kwargs):
    game = get_game()
    room = getattr(game, "current_room", None)

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


#----------------------- magic victrola ------------------
@register_item_behavior("hit_victrola")
def hit_victrola(item, verb_name, indirect_obj = None, **kwargs):
    game = get_game()
    room = getattr(game, "current_room", None)

    message = []
    message.append("You strike the Victrola with a mighty blow!")
    message.append("The Victrola shudders violently and begins to play.")
    message.append("The haunting magical melody swells and seems to fill the room.")

    desired_room_name = game.world.start_room_name
    desired_room = Room.by_name(desired_room_name)
    game.current_room = desired_room

    message.append("Suddenly, you find yourself transported back to your starting location!")
    message.append("")

    message.append(render_current_room(desired_room))

    return VerbOutcome(message=message, control=VerbControl.SKIP)


#----------------------- mermaid ------------------
@register_item_behavior("take_mermaid")
def take_mermaid(item, verb_name, indirect_obj = None, **kwargs):

    if indirect_obj and indirect_obj.canonical_name() == "mermaid":
        if item.current_container and item.current_container.canonical_name() == "mermaid":
            message = f"The mermaid clutches {item.canonical_name()} protectively and refuses to let you take it.\n"
            message += "You notice she eyes your inventory hungrily."
            return VerbOutcome(message=message, control=VerbControl.SKIP)
        else:
            message = f"The mermaid doesn't have {item.canonical_name()}."
            return VerbOutcome(message=message, control=VerbControl.SKIP)
    if item.canonical_name() == "mermaid":
        message = "The mermaid sees your intentions and bares her sharply pointed teeth menacingly."
        return VerbOutcome(message=message, control=VerbControl.SKIP)
    return None

    