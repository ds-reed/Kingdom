


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



def render_current_room(state: Any, clear: bool = True) -> None:
    """
    Render the player's current room, awarding discovery points if needed.
    """
    room = state.current_room
    if room is None:
        return

    # Award discovery points on first visit
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

    # Build room description lines
    lines = _room_display_lines(room)

    # Render via terminal UI
    trs80_clear_and_show_room(
        room.name,
        lines,
        hero_name=state.hero_name,
        clear=clear
    )

    room.visited = True


# ---------------------------------------------------------------------------
# Room description helpers
# ---------------------------------------------------------------------------

def _room_display_lines(room: Room) -> list[str]:
    """
    Build the list of lines that describe the room:
    description, items, boxes, exits, etc.
    """
    # Dark room handling
    if _is_dark_room(room):
        return [_dark_room_message(room)]

    lines: list[str] = []

    # Room description
    desc = getattr(room, "description", None)
    if desc:
        lines.append(desc)

    # Items in the room
    items = getattr(room, "items", [])
    if items:
        item_names = ", ".join(item.name for item in items)
        lines.append(f"You see: {item_names}")

    # Boxes in the room
    boxes = getattr(room, "boxes", [])
    if boxes:
        box_names = ", ".join(box.name for box in boxes)
        lines.append(f"There are containers here: {box_names}")

    # Exits
    exits = room.available_directions(visible_only=True)
    exits_text = _build_visible_exits_text(exits)
    if exits_text:
        lines.append(exits_text)

    return lines




# ---------------------------------------------------------------------------
# Box description helpers
# ---------------------------------------------------------------------------

def _describe_box_contents(box: Box) -> str:
    if box.is_openable and not box.is_open:
        return f"The {box.get_noun_name()} is closed."
    if not box.contents:
        return f"The {box.get_noun_name()} is empty."
    visible_contents = ", ".join(item.name for item in box.contents)
    return f"Inside the {box.get_noun_name()} you see: {visible_contents}."


# ---------------------------------------------------------------------------
# Dark room helpers
# ---------------------------------------------------------------------------


def _is_dark_room(room: Room) -> bool:
    """
    Return True if the room is effectively dark (requires light but none present/lit).
    """
    game = Game.get_instance()
    player = game.current_player

    if not getattr(room, "is_dark", False):
        return False

    # Prefer room method if it exists (best place for custom per-room logic)
    has_lit_source = getattr(room, "has_lit_light_source", None)
    if callable(has_lit_source) and has_lit_source():
        return False

    # Fallback: scan room items and open boxes
    for item in getattr(room, "items", []):
        if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
            return False

    for box in getattr(room, "boxes", []):
        if getattr(box, "is_openable", False) and not getattr(box, "is_open", False):
            continue
        for item in getattr(box, "contents", []):
            if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                return False

    # Player inventory (carried lights illuminate the room)
    game = Game.get_instance()
    player = game.current_player
    if player is not None:
        for item in getattr(player.sack, "contents", []):
            if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                return False

    return True

def _dark_room_message(room: Room) -> str:
    return getattr(room, "dark_description", "It is pitch black. You can't see a thing.")


# ---------------------------------------------------------------------------
# Exit formatting helpers
# ---------------------------------------------------------------------------

# These constants belong to movement semantics, but rendering needs them
# for exit formatting. If you prefer, they can be imported from movement_verbs.
_DIRECTION_ORDER = {"up": 0, "down": 1, "north": 2, "south": 3, "east": 4, "west": 5}
_VERTICAL_DIRECTION_LABELS = {"up": "above", "down": "below"}


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

    vertical = [d for d in ordered if d in _VERTICAL_DIRECTION_LABELS]
    horizontal = [d for d in ordered if d not in _VERTICAL_DIRECTION_LABELS]

    phrases: list[str] = []
    if vertical:
        phrases.append(_join_with_and([_direction_phrase(d) for d in vertical]))
    if horizontal:
        phrases.append(_join_with_and([_direction_phrase(d) for d in horizontal]))

    if len(ordered) == 1:
        return f"There is an exit {phrases[0]}."

    return f"There are exits {_join_with_and(phrases)}."
