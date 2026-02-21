from typing import Callable

ItemBehaviorHandler = Callable[[object, str, tuple[str, ...], dict | None], str | None]

_ITEM_BEHAVIORS: dict[str, ItemBehaviorHandler] = {}
_DEFAULT_ITEM_BEHAVIORS: dict[str, tuple[str, ...]] = {
    "fish": ("eat_fish",),
    "djinni": ("talk_djinni",),
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


def _spawn_room_item(dispatch_context: dict | None, *, name: str, noun_name: str, pickupable: bool, presence_string: str, refuse_string: str) -> None:
    if not dispatch_context:
        return

    state = dispatch_context.get("state")
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
def eat_fish_behavior(item: object, verb_name: str, args: tuple[str, ...], dispatch_context: dict | None) -> str | None:
    if verb_name != "eat":
        return None

    is_present = (dispatch_context or {}).get("is_present_in_known_containers") if dispatch_context else None
    if not callable(is_present):
        return "I don't understand that command."

    if not getattr(item, "pickupable", True):
        return "You can't eat that."

    if not is_present(item, dispatch_context):
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


@register_item_behavior("talk_djinni")
def talk_djinni_behavior(item: object, verb_name: str, args: tuple[str, ...], dispatch_context: dict | None) -> str | None:
    if verb_name == "talk":
        return "The Djinni bows and smiles. 'Speak your wish clearly, traveler.'"

    if verb_name == "ask":
        topic = " ".join(str(part).strip() for part in args if str(part).strip()).strip()
        if topic.lower().startswith("about "):
            topic = topic[6:].strip()
        if topic:
            return f"The Djinni strokes his beard. 'About {topic}? First prove your wit, then we bargain.'"
        return "Ask about what?"

    return None
