"""
User Interface level

This module formats rooms, exits, items, boxes, and dark-room behavior.
It depends on game models and terminal_style, but NOT on actions or verbs.

"""

from typing import Any, Sequence
from kingdom.models import Game, Room, Item, Box
from kingdom.terminal_style import trs80_clear_and_show_room, trs80_print, TRS80_WHITE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# kingdom/ui.py

class UI:
    def __init__(self, confirm, prompt, render, save_path, load_path, game):
        self.confirm = confirm
        self.prompt = prompt
        self.render = render
        self.save_path = save_path
        self.load_path = load_path
        self.game = game

    def _prompt_for_path(self, action_label: str, default_path: str) -> str:
        # Show a nice prompt with default in brackets
        prompt_text = f"{action_label} file [{default_path}]: "
        response = self.prompt(prompt_text)

        # Accept default on blank input
        response = response.strip()
        if not response:
            return default_path

        return response

    def request_save(self):
        if self.game is None:
            return "No game is active yet."

        if self.save_path is None:
            return "No save path is configured."

        if not self.confirm("Save game?"):
            return "Save cancelled."

        path = self._prompt_for_path("Save", self.save_path)

        self.game.save_world(path)

        return f"Game saved to {path}."

    def request_load(self):
        if self.game is None:
            return "No game is active yet."

        if self.load_path is None:
            return "No load path is configured."

        # Confirm
        if not self.confirm("Load game?"):
            return "Load cancelled."

        # Prompt for path
        path = self._prompt_for_path("Load", self.load_path)

        # Load world
        self.game.load_world(path)

        return f"Game loaded from {path}."





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


def _describe_room(room: Room) -> str:
    """
    Long-form room description used by EXAMINE ROOM.
    """
    if _is_dark_room(room):
        return _dark_room_message(room)

    exits = room.available_directions(visible_only=True)
    visible_text = [obj.get_presence_text() for obj in [*room.items, *room.boxes]]
    exits_text = _build_visible_exits_text(exits)
    long_description = room.description.strip() if room.description else room.name

    if visible_text:
        return f"{long_description} {' '.join(visible_text)} {exits_text}"
    return f"{long_description} {exits_text}"


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
