"""Action dispatch model for verb handlers.

"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, Sequence, TypeAlias

from kingdom.models import Box, Game, Item, Player, Room, Verb, Noun, DispatchContext, QuitGame
from kingdom.parser import normalize_direction_token

from kingdom.state_changing_verbs import StateVerbHandler
state_handler = StateVerbHandler()

from kingdom.movement_verbs import MovementVerbHandler
movement_handler = MovementVerbHandler()

from kingdom.world_verbs import WorldVerbHandler
world_handler = WorldVerbHandler()

from kingdom.ui_verbs import UIVerbHandler
ui_handler = UIVerbHandler()

from kingdom.meta_verbs import MetaVerbHandler
meta_handler = MetaVerbHandler()


from kingdom.terminal_style import TRS80_WHITE, trs80_clear_and_show_room, trs80_print


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


def look_action(
    *target_words: str,
    target: Noun | None = None,
    ctx: DispatchContext | None = None,
    dispatch_context: DispatchContext | None = None,
) -> str:
    active_ctx = ctx or dispatch_context
    state = active_ctx.state if active_ctx is not None else None
    if state is None:
        return "There is nothing to look at."

    if state.current_room is None:
        return "There is nothing to look at."

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
            return f"You look at {target.get_name()} carefully."

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
            return f"You look at {obj.get_name()} carefully."

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

# refactored verbs. These still use adapter to match old handler signature to Verb.execute contract - Remove adapter after refactoring is complete

#--------------- movement verbs ------------------------------
    verb_go        = Verb("go", adapt_method(movement_handler.go),
                        synonyms=["move", "walk", "run", "slide", "head", "jog", "travel"])

    verb_swim      = Verb("swim", adapt_method(movement_handler.swim))

    verb_climb     = Verb("climb", adapt_method(movement_handler.climb),
                        synonyms=["scale", "ascend", "descend"])

    verb_teleport  = Verb("teleport", adapt_method(movement_handler.teleport),
                        synonyms=["goto"], hidden=True)


    #--------------- state-changing verbs -------------------------
    verb_light      = Verb("light", adapt_method(state_handler.light))

    verb_extinguish = Verb("extinguish", adapt_method(state_handler.extinguish))

    verb_open       = Verb("open", adapt_method(state_handler.open))

    verb_close      = Verb("close", adapt_method(state_handler.close))

    verb_unlock     = Verb("unlock", adapt_method(state_handler.unlock))


    #---------------- UI verbs ----------------------------
    verb_load = Verb("load", adapt_method(ui_handler.load))

    verb_save = Verb("save", adapt_method(ui_handler.save))

    verb_quit = Verb("quit", adapt_method(ui_handler.quit),
                    synonyms=["q"])


    #---------------- world-state verbs ----------------------------
    verb_score = Verb("score", adapt_method(world_handler.score),
                    synonyms=["points"])


    #---------------- meta verbs ----------------------------
    verb_help = Verb("help", adapt_method(meta_handler.help),
                    synonyms=["commands", "h", "?"])




# todo  - refactor these verbs
    look_verb = Verb("look", look_action, synonyms=["inspect", "examine"])

# item management verbs - refactor to use new verb handler
    inventory_verb = Verb("inventory", inventory_action, synonyms=["inven"])
    take_verb = Verb("take", take_action, synonyms=["get"])
    drop_verb = Verb("drop", drop_action)

    
    return [
        verb_quit,
        verb_go,
        verb_swim,
        verb_climb,
        verb_save,
        verb_load,
#        verb_look,
#        verb_inventory,
        verb_score,
#        verb_take,
#        verb_drop,
        verb_light,
        verb_extinguish,
        verb_open,
        verb_close,
        verb_unlock,
        verb_teleport,
        verb_help,
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