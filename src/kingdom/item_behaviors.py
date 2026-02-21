from typing import Callable

from kingdom.dispatch_context import DispatchContext

ItemBehaviorHandler = Callable[[object, str, tuple[str, ...], DispatchContext | None], str | None]

_ITEM_BEHAVIORS: dict[str, ItemBehaviorHandler] = {}
_DEFAULT_ITEM_BEHAVIORS: dict[str, tuple[str, ...]] = {
    "fish": ("eat_fish",),
}


def register_item_behavior(name: str):
    def decorator(func: ItemBehaviorHandler) -> ItemBehaviorHandler:
        _ITEM_BEHAVIORS[name] = func
        return func

    return decorator


def resolve_item_behaviors(names: list[str] | tuple[str, ...] | None) -> list[ItemBehaviorHandler]:
    if not names:
        return []
    handlers: list[ItemBehaviorHandler] = []
    for name in names:
        handler = _ITEM_BEHAVIORS.get(str(name))
        if handler is not None:
            handlers.append(handler)
    return handlers


def get_default_item_behavior_ids(noun_name: str | None) -> tuple[str, ...]:
    if noun_name is None:
        return ()
    return _DEFAULT_ITEM_BEHAVIORS.get(str(noun_name).strip().lower(), ())


def _spawn_room_item(dispatch_context: DispatchContext | None, *, name: str, noun_name: str, pickupable: bool, presence_string: str, refuse_string: str) -> None:
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


@register_item_behavior("eat_fish")
def eat_fish_behavior(item: object, verb_name: str, args: tuple[str, ...], dispatch_context: DispatchContext | None) -> str | None:
    if verb_name != "eat":
        return None

    if not getattr(item, "pickupable", True):
        return "You can't eat that."

    remove_method = getattr(item, "_remove_from_known_containers", None)
    if not callable(remove_method):
        return "I don't understand that command."

    if not remove_method(dispatch_context=dispatch_context):
        return "YOU HAVE NO FISH!"

    _spawn_room_item(
        dispatch_context,
        name="vomit",
        noun_name="vomit",
        pickupable=False,
        presence_string="There is vomit on a nearby wall.",
        refuse_string="EW! You can't get that",
    )

    return "YOU BARELY GET THE FISH TO YOUR NOSE WHEN YOU VOMIT VIOLENTLY ON A NEARBY WALL."

