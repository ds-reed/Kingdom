from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, Sequence, TypeAlias

from kingdom.dispatch_context import DispatchContext
from kingdom.models import Box, Game, Item, Player, Room, Verb
from kingdom.parser import normalize_direction_token
from kingdom.terminal_style import TRS80_WHITE, trs80_clear_and_show_room, trs80_print


@dataclass
class GameActionState:
    current_room: Room | None = None
    hero_name: str | None = None


class QuitGame(Exception):
    pass


class GameOver(Exception):
    pass


ConfirmAction = Callable[[str], bool]
PromptAction = Callable[[str], str]
LegacyVerbSpec: TypeAlias = tuple[str, tuple[str, ...]]

LEGACY_VERB_SPECS: tuple[LegacyVerbSpec, ...] = (
    ("throw", ()),
    ("read", ()),
    ("kick", ()),
    ("knock", ()),
    ("shoot", ()),
    ("turn", ()),
    ("wash", ()),
    ("push", ("press",)),
    ("dial", ()),
    ("break", ("smash",)),
    ("drink", ()),
    ("drag", ()),
    ("kill", ()),
    ("swing", ()),
    ("untie", ()),
    ("tie", ()),
)

def quit_action() -> None:
    raise QuitGame()


def _derive_player_save_path(default_save_path: Path, hero_name: str | None) -> Path:
    if not hero_name:
        return default_save_path

    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in hero_name.strip())
    cleaned = cleaned.strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    if not cleaned:
        return default_save_path

    return default_save_path.with_name(f"{cleaned}.sav")


def _prompt_for_path(prompt_action: PromptAction | None, prompt_label: str, default_path: Path) -> Path:
    if prompt_action is None:
        return default_path

    raw_path = prompt_action(f"{prompt_label} file name [{default_path}]: ").strip()
    if not raw_path:
        return default_path
    return Path(raw_path)


def _is_game_command_target(target_words: tuple[str, ...], target: object | None) -> bool:
    normalized_words = [word.strip().lower() for word in target_words if word.strip()]
    if target is not None and not isinstance(target, Game):
        return False
    return isinstance(target, Game) or not normalized_words or normalized_words == ["game"]


def save_action(
    game: Game,
    default_save_path: Path,
    prompt_action: PromptAction | None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not _is_game_command_target(target_words, target):
        return "You can't save that."

    save_path = _prompt_for_path(prompt_action, "Save", default_save_path)

    game.save_world(save_path)
    return f"Game saved to {save_path}"


def load_action(
    game: Game,
    default_save_path: Path,
    prompt_action: PromptAction | None,
    state: GameActionState | None = None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not _is_game_command_target(target_words, target):
        return "You can't load that."

    load_path = _prompt_for_path(prompt_action, "Load", default_save_path)

    game.load_world(load_path)

    if state is not None:
        state.current_room = game.rooms[0] if game.rooms else None
        if state.current_room is not None:
            render_current_room(state, clear=False)
            print()

    return f"Game loaded from {load_path}"


def go_action(state: GameActionState, direction: str) -> str:
    if state.current_room is None:
        return "There is nowhere to go."

    canonical_direction = normalize_direction_token(direction)

    next_room = state.current_room.get_connection(canonical_direction)
    if next_room is None:
        return f"You can't go {canonical_direction} from here."

    state.current_room = next_room
    trs80_print(f"You go {canonical_direction}.", style=TRS80_WHITE)
    render_current_room(state, clear=False)
    print()
    return ""


def xyzzy_action(state: GameActionState, game: Game) -> str:
    destination = next((room for room in game.rooms if room.name.lower() == "tower cell"), None)
    if destination is None:
        return "Nothing happens."

    state.current_room = destination
    player = _active_player_or_none(game)
    if player is not None:
        player.current_room = destination

    trs80_print("You utter XYZZY.", style=TRS80_WHITE)
    render_current_room(state, clear=False)
    print()
    return ""


_DIRECTION_ORDER = {"up": 0, "down": 1, "north": 2, "south": 3, "east": 4, "west": 5}
_VERTICAL_DIRECTION_LABELS = {"up": "above", "down": "below"}
_LOOK_INSIDE_TOKENS = {"inside", "in"}


def _order_directions(directions: Sequence[str]) -> list[str]:
    return sorted(directions, key=lambda direction: _DIRECTION_ORDER.get(direction, 99))


def _join_with_and(parts: Sequence[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _direction_choice_label(direction: str) -> str:
    return _VERTICAL_DIRECTION_LABELS.get(direction, direction)


def _direction_phrase(direction: str) -> str:
    if direction in _VERTICAL_DIRECTION_LABELS:
        return _VERTICAL_DIRECTION_LABELS[direction]
    return f"to the {direction}"


def _format_exit_choices(directions: Sequence[str]) -> list[str]:
    ordered = _order_directions(directions)
    return [_direction_choice_label(direction) for direction in ordered]


def _build_visible_exits_text(directions: Sequence[str]) -> str:
    ordered = _order_directions(directions)
    if not ordered:
        return "There are no visible exits."

    vertical = [direction for direction in ordered if direction in _VERTICAL_DIRECTION_LABELS]
    horizontal = [direction for direction in ordered if direction not in _VERTICAL_DIRECTION_LABELS]

    phrases: list[str] = []
    if vertical:
        phrases.append(_join_with_and([_direction_phrase(direction) for direction in vertical]))
    if horizontal:
        phrases.append(_join_with_and([_direction_phrase(direction) for direction in horizontal]))

    if len(ordered) == 1:
        return f"There is an exit {phrases[0]}."

    return f"There are exits {_join_with_and(phrases)}."


def _is_dark_room(room: Room) -> bool:
    if not bool(getattr(room, "is_dark", False)):
        return False

    has_lit_source = getattr(room, "has_lit_light_source", None)
    if callable(has_lit_source) and has_lit_source():
        return False

    player = _active_player_or_none(Game.get_instance())
    if player is not None:
        for item in player.sack.contents:
            if item.get_noun_name() == "torch" and getattr(item, "is_lit", False):
                return False

    return True


def _dark_room_message(room: Room) -> str:
    return getattr(room, "dark_description", None) or "It is too dark to see anything."


def _room_display_lines(room: Room) -> list[str]:
    if _is_dark_room(room):
        return [_dark_room_message(room)]

    lines: list[str] = []
    if not bool(getattr(room, "visited", False)):
        lines.append(room.description)
    lines.extend(obj.get_presence_text() for obj in [*room.items, *room.boxes])
    return lines


def render_current_room(state: GameActionState, clear: bool = True) -> None:
    room = state.current_room
    if room is None:
        return

    if not bool(getattr(room, "visited", False)):
        game = Game.get_instance()
        current_score = getattr(game, "score", 0)
        try:
            current_score = int(current_score)
        except (TypeError, ValueError):
            current_score = 0

        room_points = getattr(room, "discover_points", 10)
        try:
            room_points = int(room_points)
        except (TypeError, ValueError):
            room_points = 10

        game.score = max(0, current_score + room_points)

    lines = _room_display_lines(room)
    trs80_clear_and_show_room(room.name, lines, hero_name=state.hero_name, clear=clear)
    room.visited = True


def _describe_box_contents(box: Box) -> str:
    if box.openable and not box.is_open:
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
        if not box.openable or box.is_open
    )
    return sources


def _closed_room_boxes(room: Room) -> list[Box]:
    return [box for box in room.boxes if box.openable and not box.is_open]


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


def climb_action(state: GameActionState, *target_words: str, target: object | None = None) -> str:
    if state.current_room is None:
        return "There is nowhere to climb."

    direction: str | None = None

    if target is not None:
        direction = getattr(target, "canonical_direction", None)
        if direction is None and hasattr(target, "get_noun_name"):
            direction = normalize_direction_token(target.get_noun_name())

    if direction is None and target_words:
        direction = normalize_direction_token(target_words[0])

    if direction is None:
        vertical_exits = [d for d in state.current_room.available_directions(visible_only=True) if d in {"up", "down"}]
        if len(vertical_exits) == 1:
            return go_action(state, vertical_exits[0])
        if not vertical_exits:
            return "There is nothing here to climb."
        return "Climb where? Up or down?"

    if direction not in {"up", "down"}:
        return "You can only climb up or down."

    return go_action(state, direction)


def swim_action(state: GameActionState, game: Game, *target_words: str, target: object | None = None) -> str:
    if state.current_room is None:
        return "There is nowhere to swim."

    requested_direction: str | None = None
    if target is not None:
        requested_direction = getattr(target, "canonical_direction", None)
        if requested_direction is None and hasattr(target, "get_noun_name"):
            requested_direction = normalize_direction_token(target.get_noun_name())

    if requested_direction is None and target_words:
        requested_direction = normalize_direction_token(target_words[0])

    player = _require_player_for_action(game)
    if isinstance(player, str):
        return player

    heavy_item = next((item for item in player.sack.contents if getattr(item, "too_heavy_to_swim", False)), None)
    if heavy_item is not None:
        raise GameOver(
            "The gold bar drags you under as you try to swim. You drown. GAME OVER."
        )

    destination_name = getattr(state.current_room, "swim_destination", None)
    if not destination_name:
        if requested_direction is None:
            return "There is nowhere to swim across."

        if state.current_room.get_connection(requested_direction) is None:
            return f"You can't go {requested_direction} from here."
        return go_action(state, requested_direction)

    if requested_direction is not None and state.current_room.get_connection(requested_direction) is None:
        return f"You can't go {requested_direction} from here."

    destination_room = _resolve_room_by_name(game, destination_name)
    if destination_room is None:
        return "There is nowhere to swim across."

    state.current_room = destination_room
    trs80_print("You swim across.", style=TRS80_WHITE)
    render_current_room(state, clear=False)
    print()
    return ""


def exit_action(
    state: GameActionState,
    confirm_action: ConfirmAction | None,
    prompt_action: PromptAction | None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not target_words and target is None:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    target_text = " ".join(target_words).strip().lower()

    if isinstance(target, Room) or target_text in {"room", "here"}:
        if state.current_room is None:
            return "There is nowhere to exit from."

        exits = state.current_room.available_directions(visible_only=True)
        if not exits:
            return "There are no visible exits from here."
        if len(exits) == 1:
            return go_action(state, exits[0])

        displayed_exits = _format_exit_choices(exits)
        if prompt_action is None:
            return f"Which direction do you want to exit? ({', '.join(displayed_exits)})"

        chosen_raw = prompt_action(f"Which direction? ({', '.join(displayed_exits)}): ").strip().lower()
        if not chosen_raw:
            return "Exit cancelled."
        return go_action(state, chosen_raw)

    if target_text in {"game", "program"}:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    if target_words:
        maybe_direction = normalize_direction_token(target_words[0])
        if maybe_direction in Room.DIRECTIONS:
            return go_action(state, maybe_direction)

    return "Exit where?"


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


def examine_action(state: GameActionState, *target_words: str, target: object | None = None) -> str:
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
            if not box.openable or box.is_open
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


def verbs_action(verbs: Mapping[str, object]) -> str:
    canonical_verbs: dict[str, Verb] = {}
    for verb in verbs.values():
        if isinstance(verb, Verb):
            if getattr(verb, "hidden", False):
                continue
            canonical_verbs.setdefault(verb.verb, verb)

    parts: list[str] = []
    for name in sorted(canonical_verbs.keys()):
        verb = canonical_verbs[name]
        if verb.synonyms:
            parts.append(f"{name} ({', '.join(verb.synonyms)})")
        else:
            parts.append(name)

    return f"Available verbs: {', '.join(parts)}"


def legacy_stub_action(verb_name: str, *args: str) -> str:
    if args:
        return f"'{verb_name}' is recognized but not implemented yet. ({' '.join(args)})"
    return f"'{verb_name}' is recognized but not implemented yet."


def inventory_action(game: Game) -> str:
    player = _require_player_for_action(game)
    if isinstance(player, str):
        return player

    sack_items = [item.name for item in player.sack.contents]
    if not sack_items:
        return f"{player.name}'s sack is empty."

    item_label = "item" if len(sack_items) == 1 else "items"
    return f"{player.name}'s sack contains ({len(sack_items)} {item_label}): {', '.join(sack_items)}"


def score_action(game: Game) -> str:
    score_value = getattr(game, "score", 0)
    try:
        normalized_score = int(score_value)
    except (TypeError, ValueError):
        normalized_score = 0
    game.score = normalized_score
    return f"Your score is {normalized_score}."


def take_action(state: GameActionState, game: Game, *target_words: str, target: object | None = None) -> str:
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


def drop_action(state: GameActionState, game: Game, *target_words: str, target: object | None = None) -> str:
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


def build_dispatch_context(
    state: GameActionState,
    game: Game,
    confirm_action: ConfirmAction | None = None,
    prompt_action: PromptAction | None = None,
) -> DispatchContext:
    return DispatchContext(
        state=state,
        game=game,
        confirm_callback=confirm_action,
        prompt_callback=prompt_action,
    )


def eat_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    default_refuse = "You can't eat that."
    default_success = "YUM! TASTES GOOD."

    if target is None:
        return "Eat what?"

    if not isinstance(target, Item):
        return default_refuse

    if not target.edible:
        return target.eat_refuse_string or default_refuse

    missing_message = target.eat_missing_string or default_refuse
    consumed, error_message = consume_if_getable_and_present(target, dispatch_context, missing_message)
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


def _toggle_open_state(target: object, desired_open: bool, dispatch_context: DispatchContext | None = None) -> str:
    verb_word = "open" if desired_open else "close"
    current = "open" if desired_open else "closed"

    if target is None:
        return f"{verb_word.capitalize()} what?"

    if not isinstance(target, (Item, Box)):
        return f"You can't {verb_word} that."

    if not getattr(target, "openable", False):
        return f"You can't {verb_word} that."

    if desired_open and getattr(target, "lockable", False) and getattr(target, "is_locked", False):
        target_name = target.get_noun_name()
        return f"The {target_name} is locked."

    if bool(getattr(target, "is_open", False)) == desired_open:
        return f"It's already {current}."

    target.is_open = desired_open
    _apply_open_close_exit_side_effect(target, desired_open, dispatch_context)
    target_name = target.get_noun_name()
    return f"You {verb_word} the {target_name}."


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


def light_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if target is None:
        return "Light what?"

    if not isinstance(target, Item):
        return "You can't light that."

    if not getattr(target, "light_source", False):
        return "You can't light that."

    target_name = target.get_noun_name()
    if getattr(target, "is_lit", False):
        return f"The {target_name} is already lit."

    if not _player_has_item(dispatch_context, "lighter"):
        return "You need a lighter."

    target.is_lit = True
    return f"You light the {target_name}."


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


def unlock_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    if target is None:
        return "Unlock what?"

    if not isinstance(target, (Item, Box)):
        return "You can't unlock that."

    if not getattr(target, "lockable", False):
        return "You can't unlock that."

    if not getattr(target, "is_locked", False):
        return "It's already unlocked."

    key_name = getattr(target, "unlock_key", None)
    if key_name and not _player_has_key(dispatch_context, key_name):
        return f"You need the {key_name}."

    target.is_locked = False
    target_name = target.get_noun_name()
    return f"You unlock the {target_name}."


def insert_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    return unlock_action(*target_words, target=target, dispatch_context=dispatch_context)


def open_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    return _toggle_open_state(target, desired_open=True, dispatch_context=dispatch_context)


def close_action(*target_words: str, target: object | None = None, dispatch_context: DispatchContext | None = None) -> str:
    return _toggle_open_state(target, desired_open=False, dispatch_context=dispatch_context)


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
    state: GameActionState,
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None,
    prompt_action: PromptAction | None,
) -> list[Verb]:
    player_default_save_path = _derive_player_save_path(default_save_path, state.hero_name)

    def confirmed_quit_action() -> str | None:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    def confirmed_save_action(*words: str, target: object | None = None) -> str:
        if not _is_game_command_target(words, target):
            return "You can't save that."
        if not _confirm("Save game?", confirm_action):
            return "Save cancelled."
        return save_action(game, player_default_save_path, prompt_action, *words, target=target)

    def confirmed_load_action(*words: str, target: object | None = None) -> str:
        if not _is_game_command_target(words, target):
            return "You can't load that."
        if not _confirm("Load game?", confirm_action):
            return "Load cancelled."
        return load_action(game, player_default_save_path, prompt_action, state, *words, target=target)

    quit_verb = Verb("quit", confirmed_quit_action, synonyms=["q"])
    exit_verb = Verb(
        "exit",
        lambda *words, target=None: exit_action(state, confirm_action, prompt_action, *words, target=target),
        synonyms=["leave"],
    )
    go_verb = Verb(
        "go",
        lambda direction: go_action(state, direction),
        synonyms=["move", "walk", "run", "skip", "slide", "head", "jog", "travel"],
    )
    swim_verb = Verb("swim", lambda *words, target=None: swim_action(state, game, *words, target=target))
    climb_verb = Verb("climb", lambda *words, target=None: climb_action(state, *words, target=target))
    save_verb = Verb("save", confirmed_save_action, synonyms=["write"])
    load_verb = Verb("load", confirmed_load_action, synonyms=["restore"])
    examine_verb = Verb("examine", lambda *words, target=None: examine_action(state, *words, target=target), synonyms=["inspect", "look"])
    inventory_verb = Verb("inventory", lambda: inventory_action(game), synonyms=["inven"])
    score_verb = Verb("score", lambda: score_action(game))
    take_verb = Verb("take", lambda *words, target=None: take_action(state, game, *words, target=target), synonyms=["get"])
    drop_verb = Verb("drop", lambda *words, target=None: drop_action(state, game, *words, target=target))
    eat_verb = Verb("eat", lambda *words, target=None: eat_action(*words, target=target))
    rub_verb = Verb("rub", lambda *words, target=None, dispatch_context=None: rub_action(*words, target=target, dispatch_context=dispatch_context))
    talk_verb = Verb("talk", lambda *words, target=None, dispatch_context=None: talk_action(*words, target=target, dispatch_context=dispatch_context), synonyms=["speak"])
    ask_verb = Verb("ask", lambda *words, target=None, dispatch_context=None: ask_action(*words, target=target, dispatch_context=dispatch_context), synonyms=["question"])
    say_verb = Verb("say", lambda *words, target=None, dispatch_context=None: say_action(*words, target=target, dispatch_context=dispatch_context))
    make_verb = Verb("make", lambda *words, target=None, dispatch_context=None: make_action(*words, target=target, dispatch_context=dispatch_context))
    light_verb = Verb("light", lambda *words, target=None, dispatch_context=None: light_action(*words, target=target, dispatch_context=dispatch_context))
    insert_verb = Verb("insert", lambda *words, target=None, dispatch_context=None: insert_action(*words, target=target, dispatch_context=dispatch_context))
    open_verb = Verb("open", lambda *words, target=None, dispatch_context=None: open_action(*words, target=target, dispatch_context=dispatch_context))
    close_verb = Verb("close", lambda *words, target=None, dispatch_context=None: close_action(*words, target=target, dispatch_context=dispatch_context))
    unlock_verb = Verb("unlock", lambda *words, target=None, dispatch_context=None: unlock_action(*words, target=target, dispatch_context=dispatch_context))
    xyzzy_verb = Verb("xyzzy", lambda: xyzzy_action(state, game), synonyms=["plugh"], hidden=True)
    return [
        quit_verb,
        exit_verb,
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
        insert_verb,
        open_verb,
        close_verb,
        unlock_verb,
        xyzzy_verb,
    ]


def _build_legacy_stub_verbs(specs: Sequence[LegacyVerbSpec] = LEGACY_VERB_SPECS) -> list[Verb]:
    return [
        Verb(canonical_name, partial(legacy_stub_action, canonical_name), synonyms=list(aliases))
        for canonical_name, aliases in specs
    ]


def _register_legacy_stubs(verb_lookup: dict[str, Verb]) -> None:
    for legacy_verb in _build_legacy_stub_verbs():
        existing = verb_lookup.get(legacy_verb.verb)
        if existing is None:
            _register_verb(verb_lookup, legacy_verb)
            continue
        _merge_aliases(verb_lookup, existing, legacy_verb.synonyms)


def build_verbs(
    state: GameActionState,
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None = None,
    prompt_action: PromptAction | None = None,
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}

    for verb in _build_core_verbs(state, game, default_save_path, confirm_action, prompt_action):
        _register_verb(verbs, verb)

    verbs_verb = Verb("verbs", lambda: verbs_action(verbs), synonyms=["help", "commands"])
    _register_verb(verbs, verbs_verb)

    _register_legacy_stubs(verbs)

    return verbs