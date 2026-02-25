#------------------------------
hold all the puzzle verb code we are removing from the actions.py


def eat_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    default_refuse = "You can't eat that."
    default_success = "YUM! TASTES GOOD."
    active_ctx = ctx or dispatch_context

    if target is None:
        return "Eat what?"

    if not isinstance(target, Item):
        return default_refuse

    if not target.edible:
        return target.eat_refuse_string or default_refuse

    missing_message = target.eat_missing_string or default_refuse
    consumed, error_message = consume_if_getable_and_present(target, active_ctx, missing_message)
    if not consumed:
        return error_message or target.eat_refuse_string or default_refuse



def rub_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if target is None:
        return "Rub what?"

    if not isinstance(target, Item):
        return "You can't rub that."

    if not getattr(target, "rubbable", False):
        return "You can't rub that."

    target_name = target.get_noun_name()
    transformed_name = getattr(target, "rubbed_name", None)
    if transformed_name and target.name == transformed_name:
        message = getattr(target, "rub_repeat_string", None) or f"The {target_name} is already shiny."
    else:
        if transformed_name:
            target.name = transformed_name

        transformed_presence = getattr(target, "rubbed_presence_string", None)
        if transformed_presence is not None:
            target.presence_string = transformed_presence

        message = getattr(target, "rub_success_string", None) or f"You rub the {target_name}."

    state = dispatch_context.state if dispatch_context is not None else None
    current_room = getattr(state, "current_room", None)
    trigger_room = getattr(target, "rub_trigger_room", None)

    if current_room is not None and trigger_room and current_room.name == trigger_room:
        djinni_present = any(getattr(item, "noun_name", None) == "djinni" for item in current_room.items)
        if not djinni_present:
            djinni_item = Item(
                "a helpful Djinni",
                is_gettable=False,
                noun_name="djinni",
                presence_string="A helpful Djinni materializes in a swirl of sweet smoke.",
            )
            djinni_item.wish_exit_direction = "west"
            djinni_item.wish_exit_destination = "Colossal Cave"
            current_room.items.append(djinni_item)
            tease = getattr(target, "rub_minigame_tease", None) or "The Djinni smiles and offers a small challenge."
            return f"{message} {tease}"

    return message


def _find_room_djinni(dispatch_context: DispatchContext | None) -> tuple[Room | None, Item | None, Game | None]:
    state = dispatch_context.state if dispatch_context is not None else None
    game = dispatch_context.game if dispatch_context is not None else None
    room = getattr(state, "current_room", None)
    if room is None:
        return None, None, game

    for item in room.items:
        if getattr(item, "noun_name", None) == "djinni":
            return room, item, game

    return room, None, game


def _trigger_djinni_wish(dispatch_context: DispatchContext | None) -> str | None:
    room, djinni, game = _find_room_djinni(dispatch_context)
    if room is None or djinni is None:
        return None

    destination_name = getattr(djinni, "wish_exit_destination", None) or "Demo Landing"
    destination_room = _resolve_room_by_name(game, destination_name)
    direction = getattr(djinni, "wish_exit_direction", None) or "west"

    if destination_room is not None:
        reveal_exit(room, direction, destination_room)

    if djinni in room.items:
        room.items.remove(djinni)

    return (
        "The Djinni seems puzzled by your exotic language. Djinn aren't omniscient, just omnipotent! "
        "But seeing that you are at a dead end and wanting to be helpful, he places a doorway in the west wall and disappears."
    )


def _is_djinni_target(target: object | None) -> bool:
    if target is None:
        return False

    noun_name = getattr(target, "noun_name", None)
    if isinstance(noun_name, str) and noun_name.strip().lower() == "djinni":
        return True

    matches_reference = getattr(target, "matches_reference", None)
    if callable(matches_reference):
        return bool(matches_reference("djinni"))

    return False


def make_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if not target_words:
        return "Make what?"

    if normalize_direction_token(target_words[0]) != "wish" and target_words[0].strip().lower() != "wish":
        return "Make what?"

    wish_result = _trigger_djinni_wish(dispatch_context)
    if wish_result is not None:
        return wish_result

    return "Nothing happens."


def say_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if not target_words:
        return "Say what?"

    wish_result = _trigger_djinni_wish(dispatch_context)
    if wish_result is not None:
        return wish_result

    return f"You say, '{' '.join(target_words)}.'"


def talk_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if target is None:
        return "Talk to whom?"

    if _is_djinni_target(target):
        wish_result = _trigger_djinni_wish(dispatch_context)
        if wish_result is not None:
            return wish_result

    return "They don't seem interested in talking."


def ask_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if target is None:
        return "Ask whom?"

    if _is_djinni_target(target):
        wish_result = _trigger_djinni_wish(dispatch_context)
        if wish_result is not None:
            return wish_result

    return "They have no answer for you."