"""
Item behavior registry and dispatch.

Defines item-specific behavior handlers, registration decorators,
lookup utilities, and the unified special-handling pipeline.

This module is the single source of truth for item-driven puzzle logic.
"""

from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class VerbOutcome:
    """Standardized return type for item behavior handlers."""
    message: Optional[str] = None
    stop: bool = False



# ------------------------------------------------------------
# Behavior registry
# ------------------------------------------------------------

ItemBehaviorHandler = Callable[
    [object, str, tuple[str, ...], "DispatchContext | None"],
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
    ctx: "DispatchContext | None",
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
# Central special-handling pipeline
# ------------------------------------------------------------

def run_special_handling(
    ctx: "DispatchContext",
    target: object,
    verb: str,
    words: tuple[str, ...]
) -> Optional[VerbOutcome]:
    """
    Runs item-specific special handling for a verb.

    If the item defines a special handler for this verb, dispatch to it.
    If the handler returns a VerbOutcome, the verb is intercepted.
    If it returns None, normal verb logic continues.
    """

    handler_name = getattr(target, "special_handlers", {}).get(verb)
    if not handler_name:
        return None

    handler = get_behavior(handler_name)
    if not handler:
        return None

    result = handler(target, verb, words, ctx)

    # Unified return contract
    if isinstance(result, VerbOutcome):
        return result

    return None


# ------------------------------------------------------------
# Puzzle helpers (kept exactly as-is)
# ------------------------------------------------------------

def _spawn_room_item(
    dispatch_context: "DispatchContext | None",
    *,
    name: str,
    noun_name: str,
    pickupable: bool,
    presence_string: str,
    refuse_string: str
) -> None:
    """Spawn an item into the current room unless it already exists."""
    if dispatch_context is None:
        return

    state = dispatch_context.state
    room = getattr(state, "current_room", None)
    if room is None:
        return

    for existing in getattr(room, "items", []):
        matches_reference = getattr(existing, "matches_reference", None)
        if callable(matches_reference) and matches_reference(noun_name):
            return

    from kingdom.models import Item

    room.items.append(
        Item(
            name,
            pickupable=pickupable,
            refuse_string=refuse_string,
            presence_string=presence_string,
            noun_name=noun_name,
        )
    )


def _spawn_room_item(dispatch_context: "DispatchContext | None", *, name: str, noun_name: str, pickupable: bool,  get_refuse_string: str) -> None:
    if dispatch_context is None:
        return

    state = dispatch_context.state
    room = getattr(state, "current_room", None)
    if room is None:
        return

    for existing in getattr(room, "items", []):
        if getattr(existing, "noun_name", None) == noun_name:
            return

    from kingdom.models import Item

    print(f"DEBUG: Spawning item '{name}' in room '{room.name}'")  # Debug log

    new_item = Item(
        name,
        noun_name=noun_name,
        pickupable=pickupable,
        get_refuse_string=get_refuse_string,
        )

    print("DEBUG: new_item =", new_item, "type:", type(new_item))    
    
    room.items.append(new_item)   

    print(f"DEBUG: Item '{name}' added to room '{room.name}'. Current items in room: {[item.name for item in room.items]}")  # Debug log


# ------------------------------------------------------------
# Behavior implementations go below this line
# ------------------------------------------------------------

# @register_item_behavior("example_behavior")
# def example_behavior(item, verb, words, ctx):
#     ...
#     return VerbOutcome("Example!", stop_outer=True)


@register_item_behavior("open_bean")
def open_bean(item, verb_name, words, ctx):
    if verb_name != "open":
        return None
    print("Ha Ha - you tried to open a magical bean!")  # or log it
    return VerbOutcome(message="you reached me!!!!", stop=True)  # or return None to use generic


@register_item_behavior("eat_fish")
def eat_fish(item, verb, words, ctx):
    if verb != "eat":
        return None

    player = ctx.game.current_player
    inventory = player.sack.contents

    if item not in inventory:
        return VerbOutcome(
            message="YOU HAVE NO FISH!",
            stop=True
        )
    
    room = ctx.state.current_room

    # Check if vomit already exists to prevent duplicates
    for obj in room.items: 
        if getattr(obj, "noun_name", None) == "vomit": 
            return VerbOutcome( message="You made quite a mess here!", stop=True )
        
    # spawn vomit if it doesn't already exist
    vomit = _spawn_room_item(ctx, 
        name="There is vomit on a nearby wall.",
        noun_name="vomit",
        pickupable=False,      
        get_refuse_string="EW! You can't get that."
    )

    # Final message - TRS80 old-school style
    return VerbOutcome(
        message="YOU BARELY GET THE FISH TO YOUR NOSE WHEN YOU VOMIT VIOLENTLY ON A NEARBY WALL.",
        stop=True
    )

@register_item_behavior("rub_lamp")
def rub_lamp(item, verb, words, ctx):
    if verb != "rub":
        return None

    player = ctx.game.current_player
    inventory = player.sack.contents

    if item not in inventory:
        return VerbOutcome(
            message="YOU HAVE NO LAMP!",
            stop=True
        )
    
    room = ctx.state.current_room
    trigger_room_name = getattr(item, "trigger_room", None)

    print("DEBUG: Player is rubbing the lamp in room:", room.name, "with trigger room:", trigger_room_name)  # Debug log

    if room.name == trigger_room_name:
        print("DEBUG: Lamp's trigger_room matches current room. Spawning Djinni.")  # Debug log
        _spawn_room_item(ctx, 
            name="A djinni appears in a cloud of smoke!",
            noun_name="djinni",
            pickupable=False,      
            get_refuse_string="The 10 foot tall djinni glares at you."
        )
    item.name = "a battered but shiny brass lamp"
    return VerbOutcome(
        message="",
        stop=False
    )






















"""Item behavior registry and dispatch.

Defines item-specific behavior handlers, registration decorators, and lookup utilities.
Used for dynamic item actions (e.g., eat fish) and custom item logic.


from typing import Callable

ItemBehaviorHandler = Callable[
    [object, str, tuple[str, ...], "DispatchContext | None"],
    str | None
]

The air fills with smoke. After it clears you cannot believe your eyes: a Djinni has appeared before you. He mutters some words, 'MYPCLY JUBURUAY MIT DE NURDY SMUDY DIGNIC PIC?' and looks at you inquiringly. This means (in magic Arabic), 'I will grant you one wish.'"

def get_behavior(name: str) -> ItemBehaviorHandler | None:
    return _ITEM_BEHAVIORS.get(str(name).strip())


def register_item_behavior(name: str):
    def decorator(func: ItemBehaviorHandler) -> ItemBehaviorHandler:
        _ITEM_BEHAVIORS[name] = func
        return func

    return decorator

# likely obsolete with new architecture
def resolve_item_behaviors(names: list[str] | tuple[str, ...] | None) -> list[ItemBehaviorHandler]:
    if not names:
        return []
    handlers: list[ItemBehaviorHandler] = []
    for name in names:
        handler = _ITEM_BEHAVIORS.get(str(name))
        if handler is not None:
            handlers.append(handler)
    return handlers

# likely obsolete with new architecture
def get_default_item_behavior_ids(noun_name: str | None) -> tuple[str, ...]:
    if noun_name is None:
        return ()
    return _DEFAULT_ITEM_BEHAVIORS.get(str(noun_name).strip().lower(), ())







    """