"""Action dispatch model for verb handlers.

"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, Sequence, TypeAlias

from kingdom.models import Box, Game, Item, Player, Room, Verb, Noun, DispatchContext, QuitGame
from kingdom.parser import normalize_direction_token

from kingdom.state_changing_verbs import StateChangingVerbHandler
state_changer = StateChangingVerbHandler()

from kingdom.movement_verbs import MovementVerbHandler
movement = MovementVerbHandler()

from kingdom.game_state_verbs import GameStateVerbHandler
game_verb = GameStateVerbHandler()

from kingdom.terminal_style import TRS80_WHITE, trs80_clear_and_show_room, trs80_print

from kingdom.UI import (
    _describe_room,
    _describe_box_contents,
    _is_dark_room,
    _dark_room_message,
    _build_visible_exits_text,
    _format_exit_choices,
)     #temporary until render logic is fully decoupled from actions


# temporary adapters to match new handler method signatures to Verb.execute contract - Remove after refactoring is complete
def adapt_method(method):

    def handler(*words, target=None, ctx=None, dispatch_context=None, **kwargs):
        context = dispatch_context 
        return method(context, target, list(words))
    return handler

ConfirmAction = Callable[[str], bool]
PromptAction = Callable[[str], str]




_LOOK_INSIDE_TOKENS = {"inside", "in"}



#

def _describe_box_contents(box: Box) -> str:
    if box.is_openable and not box.is_open:
        return f"The {box.get_noun_name()} is closed."
    if not box.contents:
        return f"The {box.get_noun_name()} is empty."
    visible_contents = ", ".join(item.name for item in box.contents)
    return f"Inside the {box.get_noun_name()} you see: {visible_contents}."


def _build_take_sources(room: Room) -> list[tuple[str, list[Item]]]:
    sources: list[tuple[str, list[Item]]] = [(room.name, room.items)]
    sources.extend(
        (box.box_name, box.contents)
        for box in room.boxes
        if not box.is_openable or box.is_open
    )
    return sources


def _closed_room_boxes(room: Room) -> list[Box]:
    return [box for box in room.boxes if box.is_openable and not box.is_open]


def _move_item_to_sack(item: Item, player) -> None:
    item.current_box = player.sack
    player.sack.contents.append(item)


def _drop_item_to_room(item: Item, room: Room) -> None:
    item.current_box = None
    room.items.append(item)


def _active_player_or_none(game: Game | None) -> Player | None:
    if game is None:
        return None

    player = game.require_player(return_error=True)
    if isinstance(player, str):
        return None
    return player


def _require_player_for_action(game: Game) -> Player | str:
    return game.require_player(return_error=True)


def _describe_room(room: Room) -> str:
    if _is_dark_room(room):
        return _dark_room_message(room)

    exits = room.available_directions(visible_only=True)
    visible_text = [obj.get_presence_text() for obj in [*room.items, *room.boxes]]
    exits_text = _build_visible_exits_text(exits)
    long_description = room.description.strip() if room.description else room.name
    if visible_text:
        return f"{long_description} {' '.join(visible_text)} {exits_text}"
    return f"{long_description} {exits_text}"


def examine_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    active_ctx = ctx or dispatch_context
    state = active_ctx.state if active_ctx is not None else None
    if state is None:
        return "There is nothing to examine."

    if state.current_room is None:
        return "There is nothing to examine."

    if not target_words:
        return _describe_room(state.current_room)

    if target is not None:
        if isinstance(target, Room):
            return _describe_room(state.current_room)

        if _is_dark_room(state.current_room):
            return _dark_room_message(state.current_room)

        if isinstance(target, Box):
            return _describe_box_contents(target)

        if isinstance(target, Item):
            return f"You examine {target.get_name()} carefully."

    target_name = " ".join(target_words).strip().lower()

    if target_name in _LOOK_INSIDE_TOKENS:
        open_boxes = [
            box for box in state.current_room.boxes
            if not box.is_openable or box.is_open
        ]
        if not open_boxes:
            return "There are no open containers to look inside."
        return " ".join(_describe_box_contents(box) for box in open_boxes)

    if target_name in {"room", state.current_room.name.lower()}:
        return _describe_room(state.current_room)

    if _is_dark_room(state.current_room):
        return _dark_room_message(state.current_room)

    for obj in [*state.current_room.items, *state.current_room.boxes]:
        if obj.matches_reference(target_name):
            if isinstance(obj, Box):
                return _describe_box_contents(obj)
            return f"You examine {obj.get_name()} carefully."

    return f"You don't see {target_name} here."



def inventory_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    active_ctx = ctx or dispatch_context
    game = active_ctx.game if active_ctx is not None else None
    if game is None:
        return "No game is active yet."

    player = _require_player_for_action(game)
    if isinstance(player, str):
        return player

    sack_items = [item.name for item in player.sack.contents]
    if not sack_items:
        return f"{player.name}'s sack is empty."

    item_label = "item" if len(sack_items) == 1 else "items"
    return f"{player.name}'s sack contains ({len(sack_items)} {item_label}): {', '.join(sack_items)}"


def take_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    active_ctx = ctx or dispatch_context
    state = active_ctx.state if active_ctx is not None else None
    game = active_ctx.game if active_ctx is not None else None
    if state is None:
        return "There is nothing to take here."
    if game is None:
        return "No game is active yet."

    if state.current_room is None:
        return "There is nothing to take here."

    player = _require_player_for_action(game)
    if isinstance(player, str):
        return player

    sources = _build_take_sources(state.current_room)
    closed_boxes = _closed_room_boxes(state.current_room)

    if target is not None:
        if not isinstance(target, Item):
            return "You can't take that."

        if player.sack.capacity is not None and len(player.sack.contents) >= player.sack.capacity:
            return f"{player.name}'s sack is full (max {player.sack.capacity} items)!"

        for container_name, contents in sources:
            if target in contents:
                contents.remove(target)
                _move_item_to_sack(target, player)
                return f"{player.name} takes {target.name} from {container_name}."

        for box in closed_boxes:
            if target in box.contents:
                return f"The {box.get_noun_name()} is closed."

        return f"You don't see {target.get_noun_name()} here."

    if not target_words:
        return "Take what?"

    target_name = " ".join(target_words).strip().lower()
    if not target_name:
        return "Take what?"

    if target_name == "all":
        picked_up: list[str] = []

        for container_name, contents in sources:
            for item in list(contents):
                if not item.pickupable:
                    continue
                if player.sack.capacity is not None and len(player.sack.contents) >= player.sack.capacity:
                    if not picked_up:
                        return f"{player.name}'s sack is full (max {player.sack.capacity} items)!"
                    item_word = "item" if len(picked_up) == 1 else "items"
                    return f"{player.name} takes {len(picked_up)} {item_word}: {', '.join(picked_up)}."
                contents.remove(item)
                _move_item_to_sack(item, player)
                picked_up.append(item.name)

        if not picked_up:
            return "There is nothing here you can take."

        item_word = "item" if len(picked_up) == 1 else "items"
        return f"{player.name} takes {len(picked_up)} {item_word}: {', '.join(picked_up)}."

    found_item = None
    found_contents = None
    found_container_name = ""

    for container_name, contents in sources:
        for item in contents:
            if item.matches_reference(target_name):
                found_item = item
                found_contents = contents
                found_container_name = container_name
                break
        if found_item is not None:
            break

    if found_item is None or found_contents is None:
        for box in closed_boxes:
            for item in box.contents:
                if item.matches_reference(target_name):
                    return f"The {box.get_noun_name()} is closed."
        return f"You don't see {target_name} here."

    if not found_item.pickupable:
        return found_item.refuse_string

    if player.sack.capacity is not None and len(player.sack.contents) >= player.sack.capacity:
        return f"{player.name}'s sack is full (max {player.sack.capacity} items)!"

    found_contents.remove(found_item)
    _move_item_to_sack(found_item, player)
    return f"{player.name} takes {found_item.name} from {found_container_name}."


def drop_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    active_ctx = ctx or dispatch_context
    state = active_ctx.state if active_ctx is not None else None
    game = active_ctx.game if active_ctx is not None else None
    if state is None:
        return "There is nowhere to drop anything."
    if game is None:
        return "No game is active yet."

    if state.current_room is None:
        return "There is nowhere to drop anything."

    player = _require_player_for_action(game)
    if isinstance(player, str):
        return player

    if target is not None:
        if not isinstance(target, Item):
            return "You can't drop that."
        if target not in player.sack.contents:
            return f"{player.name} doesn't have {target.get_noun_name()}!"

        player.sack.contents.remove(target)
        _drop_item_to_room(target, state.current_room)
        return f"{player.name} drops {target.name}."

    if not target_words:
        return "Drop what?"

    target_name = " ".join(target_words).strip().lower()
    if not target_name:
        return "Drop what?"

    if target_name == "all":
        if not player.sack.contents:
            return f"{player.name}'s sack is empty."

        dropped_names: list[str] = []
        for item in list(player.sack.contents):
            player.sack.contents.remove(item)
            _drop_item_to_room(item, state.current_room)
            dropped_names.append(item.name)

        item_word = "item" if len(dropped_names) == 1 else "items"
        return f"{player.name} drops {len(dropped_names)} {item_word}: {', '.join(dropped_names)}."

    for item in player.sack.contents:
        if item.matches_reference(target_name):
            player.sack.contents.remove(item)
            _drop_item_to_room(item, state.current_room)
            return f"{player.name} drops {item.name}."

    return f"{player.name} doesn't have {target_name}!"


def is_present_in_known_containers(item: object, dispatch_context: DispatchContext | None) -> bool:
    current_box = getattr(item, "current_box", None)
    if current_box is not None and item in getattr(current_box, "contents", []):
        return True

    if dispatch_context is None:
        return False

    state = dispatch_context.state
    room = getattr(state, "current_room", None) if state is not None else None
    if room is not None:
        if item in getattr(room, "items", []):
            return True
        for box in getattr(room, "boxes", []):
            if item in getattr(box, "contents", []):
                return True

    game = dispatch_context.game
    player = _active_player_or_none(game)
    if player is not None and item in getattr(player.sack, "contents", []):
        return True

    return False


def consume_if_getable_and_present(item: object, dispatch_context: DispatchContext | None, missing_message: str) -> tuple[bool, str | None]:
    if not getattr(item, "pickupable", True):
        return False, "You can't eat that."

    if not is_present_in_known_containers(item, dispatch_context):
        return False, missing_message

    remove_method = getattr(item, "_remove_from_known_containers", None)
    if not callable(remove_method):
        return False, missing_message

    removed = remove_method(dispatch_context=dispatch_context)
    if not removed:
        return False, missing_message

    return True, None


def reveal_exit(room: Room, direction: str, destination: Room) -> bool:
    if not isinstance(room, Room) or not isinstance(destination, Room):
        return False

    canonical_direction = normalize_direction_token(direction)
    existing = room.get_connection(canonical_direction)
    if existing is destination:
        changed = room.set_exit_visibility(canonical_direction, visible=True)
        return bool(changed)

    room.connect_room(canonical_direction, destination, visible=True)
    return True


def hide_exit(room: Room, direction: str) -> bool:
    if not isinstance(room, Room):
        return False

    canonical_direction = normalize_direction_token(direction)
    if room.get_connection(canonical_direction) is None:
        return False

    return bool(room.set_exit_visibility(canonical_direction, visible=False))


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

    return target.eat_success_string or default_success


def _resolve_room_by_name(game: object | None, room_name: str | None) -> Room | None:
    if game is None or not room_name:
        return None
    for room in getattr(game, "rooms", []):
        if getattr(room, "name", None) == room_name:
            return room
    return None


def _apply_open_close_exit_side_effect(target: object, desired_open: bool, dispatch_context: DispatchContext | None) -> None:
    if not isinstance(target, Item):
        return

    direction = getattr(target, "open_exit_direction", None)
    if not direction:
        return

    state = dispatch_context.state if dispatch_context is not None else None
    current_room = getattr(state, "current_room", None)
    if current_room is None:
        return

    if desired_open:
        destination_name = getattr(target, "open_exit_destination", None)
        destination_room = _resolve_room_by_name(dispatch_context.game if dispatch_context is not None else None, destination_name)
        if destination_room is not None:
            reveal_exit(current_room, direction, destination_room)
        return

    if not getattr(target, "close_hides_exit", False):
        return

    hide_exit(current_room, direction)


def _player_has_key(dispatch_context: DispatchContext | None, key_name: str | None) -> bool:
    return _player_has_item(dispatch_context, key_name)


def _player_has_item(dispatch_context: DispatchContext | None, item_name: str | None) -> bool:
    if not item_name:
        return False

    game = dispatch_context.game if dispatch_context is not None else None
    player = _active_player_or_none(game)
    if player is None:
        return False

    item_token = str(item_name).strip().lower()
    if not item_token:
        return False

    for item in getattr(player.sack, "contents", []):
        matches_reference = getattr(item, "matches_reference", None)
        if callable(matches_reference) and matches_reference(item_token):
            return True
    return False


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
                pickupable=False,
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


def insert_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    return unlock_action(*target_words, target=target, dispatch_context=dispatch_context)


def _register_aliases(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    for alias in verb.synonyms:
        verb_lookup[alias] = verb


def _register_verb(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    verb_lookup[verb.verb] = verb
    _register_aliases(verb_lookup, verb)


def _merge_aliases(verb_lookup: dict[str, Verb], verb: Verb, aliases: Sequence[str]) -> None:
    merged_synonyms = list(verb.synonyms)
    for alias in aliases:
        if alias not in merged_synonyms:
            merged_synonyms.append(alias)
        verb_lookup[alias] = verb
    verb.synonyms = tuple(sorted(set(merged_synonyms)))


def _confirm(prompt_text: str, confirm_action: ConfirmAction | None) -> bool:
    if confirm_action is None:
        return True
    return confirm_action(prompt_text)


def _build_core_verbs(
    state: "GameActionState",
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None,
    prompt_action: PromptAction | None,
) -> list[Verb]:

#--------------- movement verbs ------------------------------
    go_verb = Verb("go", adapt_method(movement.go), synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"]) # todo: refactor test and re-enable direct use of movement method
    # go_verb = Verb("go", movement.go, synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"])   
    swim_verb = Verb("swim", adapt_method(movement.swim)) # todo: refactor test and re-enable direct use of movement method 
    #   swim_verb = Verb("swim", movement.swim)
    climb_verb = Verb("climb", adapt_method(movement.climb), synonyms=["scale", "ascend", "descend"]) # todo: refactor test and re-enable direct use of movement method
    # climb_verb = Verb("climb", movement.climb, synonyms=["scale", "ascend", "descend"])
    teleport_verb = Verb("teleport", adapt_method(movement.teleport), synonyms=["goto"], hidden=True) # todo: refactor test and re-enable direct use of state_changer method
    # teleport_verb = Verb("teleport", movement.teleport, synonyms=["goto"], hidden=True)

#--------------- state-changing verbs -------------------------
    light_verb = Verb("light", adapt_method(state_changer.light))
    # light_verb = Verb("light", state_changer.light)   # todo: refactor test and re-enable direct use of state_changer method
    extinguish_verb = Verb("extinguish", adapt_method(state_changer.extinguish))
    # extinguish_verb = Verb("extinguish", state_changer.extinguish)   # todo: refactor test and re-enable direct use of state_changer method
    insert_verb = Verb("insert", insert_action)
    open_verb = Verb("open", adapt_method(state_changer.open))
    # open_verb = Verb("open", state_changer.open)   # todo: refactor test and re-enable direct use of state_changer method
    close_verb = Verb("close", adapt_method(state_changer.close))
    # close_verb = Verb("close", state_changer.close)   # todo: refactor test and re-enable direct use of state_changer method
    unlock_verb = Verb("unlock", adapt_method(state_changer.unlock))
    # unlock_verb = Verb("unlock", state_changer.unlock)   # todo: refactor test and re-enable direct use of state_changer method

#----------------UI and game state related verbs ----------------------------

    load_verb = Verb("load", adapt_method(game_verb.load))
    #load_verb = Verb("load", game_verb.load)
    save_verb = Verb("save", adapt_method(game_verb.save))
    #save_verb = Verb("save", game_verb.save)
    score_verb = Verb("score", adapt_method(game_verb.score), synonyms=["points"])
    #score_verb = Verb("score", game_verb.score, synonyms=["points"])
    help_verb = Verb("help", adapt_method(game_verb.help), synonyms=["commands", "h", "?"])
    #help_verb = Verb("help", game_verb.help, synonyms=["commands", "h"])
    quit_verb = Verb("quit", adapt_method(game_verb.quit), synonyms=["q"])
    #quit_verb = Verb("quit", game_verb.quit, synonyms=["exit", "q"]



# todo  - refactor these verbs
    examine_verb = Verb("examine", examine_action, synonyms=["inspect", "look"])
    inventory_verb = Verb("inventory", inventory_action, synonyms=["inven"])
    take_verb = Verb("take", take_action, synonyms=["get"])
    drop_verb = Verb("drop", drop_action)
    eat_verb = Verb("eat", eat_action)
    rub_verb = Verb("rub", rub_action)
    talk_verb = Verb("talk", talk_action, synonyms=["speak"])
    ask_verb = Verb("ask", ask_action, synonyms=["question"])
    say_verb = Verb("say", say_action)
    make_verb = Verb("make", make_action)


    
    return [
        quit_verb,
        go_verb,
        swim_verb,
        climb_verb,
        save_verb,
        load_verb,
        examine_verb,
        inventory_verb,
        score_verb,
        take_verb,
        drop_verb,
        eat_verb,
        rub_verb,
        talk_verb,
        ask_verb,
        say_verb,
        make_verb,
        light_verb,
        extinguish_verb,
        insert_verb,
        open_verb,
        close_verb,
        unlock_verb,
        teleport_verb,
        help_verb,
    ]

def build_verbs(
    state: "GameActionState",
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None = None,
    prompt_action: PromptAction | None = None,
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}
    for verb in _build_core_verbs(state, game, default_save_path, confirm_action, prompt_action):
        _register_verb(verbs, verb)
    return verbs