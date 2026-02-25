# kingdom/renderer.py

from typing import Sequence
from kingdom.models import Game, Room, Item, Box
from kingdom.UI import UI


class RoomRenderer:
    """
    Pure presentation logic for describing rooms, items, boxes, and exits.
    Produces semantic text; UI layer decides how to display it.
    """

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def describe_room(self, room: Room) -> str:
        """Return a one-paragraph description of the room."""
        if room is None:
            return "You are nowhere."

        if self.is_dark_room(room):
            return self.dark_room_message(room)

        desc = room.description.strip() if room.description else room.name
        exits = room.available_directions(visible_only=True)
        exits_text = self.build_visible_exits_text(exits)

        # Items and boxes (presence text)
        presence = []
        for obj in [*room.items, *room.boxes]:
            text = obj.get_presence_text()
            if text:
                presence.append(text)

        presence_text = " ".join(presence)
        if presence_text:
            return f"{desc} {presence_text} {exits_text}".strip()

        return f"{desc} {exits_text}".strip()

    def room_display_lines(self, room: Room) -> list[str]:
        """Return a list of lines for UI rendering."""
        if self.is_dark_room(room):
            return [self.dark_room_message(room)]

        lines: list[str] = []

        # Room description
        if room.description:
            lines.append(room.description)

        # Items
        if room.items:
            names = ", ".join(item.name for item in room.items)
            lines.append(f"You see {names}")

        # Boxes
        if room.boxes:
            names = ", ".join(box.name for box in room.boxes)
            lines.append(f"There is {names} here.")

        # Exits
        exits = room.available_directions(visible_only=True)
        exits_text = self.build_visible_exits_text(exits)
        if exits_text:
            lines.append(exits_text)

        return lines

    def describe_item(self, item: Item) -> str:
        """Return a description of an item when the player LOOKs at it."""
        desc = getattr(item, "description", None)
        if desc:
            return desc
        return f"You look at {item.get_noun_name()} carefully."

    def describe_box_contents(self, box: Box) -> str:
        """Return a description of a box's contents."""
        if box.is_openable and not box.is_open:
            return f"The {box.get_noun_name()} is closed."
        if not box.contents:
            return f"The {box.get_noun_name()} is empty."
        names = ", ".join(item.name for item in box.contents)
        return f"Inside the {box.get_noun_name()} you see: {names}."

    # ----------------------------------------------------------------------
    # Darkness logic
    # ----------------------------------------------------------------------

    def is_dark_room(self, room: Room) -> bool:
        """Return True if the room is effectively dark."""
        game = Game.get_instance()
        player = game.current_player

        if not getattr(room, "is_dark", False):
            return False

        # Room-specific override
        has_lit = getattr(room, "has_lit_light_source", None)
        if callable(has_lit) and has_lit():
            return False

        # Room items
        for item in room.items:
            if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                return False

        # Boxes (only open ones)
        for box in room.boxes:
            if box.is_openable and not box.is_open:
                continue
            for item in box.contents:
                if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                    return False

        # Player inventory
        if player:
            for item in player.sack.contents:
                if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                    return False

        return True

    def dark_room_message(self, room: Room) -> str:
        return getattr(room, "dark_description",
                       "It is pitch black. You can't see a thing.")

    # ----------------------------------------------------------------------
    # Exit formatting
    # ----------------------------------------------------------------------

    _DIRECTION_ORDER = {"up": 0, "down": 1, "north": 2, "south": 3, "east": 4, "west": 5}
    _VERTICAL_LABELS = {"up": "above", "down": "below"}

    def order_directions(self, directions: Sequence[str]) -> list[str]:
        return sorted(directions, key=lambda d: self._DIRECTION_ORDER.get(d, 99))

    def join_with_and(self, parts: Sequence[str]) -> str:
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        return f"{', '.join(parts[:-1])}, and {parts[-1]}"

    def direction_phrase(self, direction: str) -> str:
        if direction in self._VERTICAL_LABELS:
            return self._VERTICAL_LABELS[direction]
        return f"to the {direction}"

    def build_visible_exits_text(self, directions: Sequence[str]) -> str:
        ordered = self.order_directions(directions)
        if not ordered:
            return "There are no visible exits."

        vertical = [d for d in ordered if d in self._VERTICAL_LABELS]
        horizontal = [d for d in ordered if d not in self._VERTICAL_LABELS]

        phrases = []
        if vertical:
            phrases.append(self.join_with_and([self.direction_phrase(d) for d in vertical]))
        if horizontal:
            phrases.append(self.join_with_and([self.direction_phrase(d) for d in horizontal]))

        if len(ordered) == 1:
            return f"There is an exit {phrases[0]}."

        return f"There are exits {self.join_with_and(phrases)}."


def render_current_room(state, clear=False):

    room = state.current_room
    if room is None:
        return
    
    ui = UI(
        confirm=None,
        prompt=None,
        save_path=None,
        load_path=None,
        game=None
    )

    renderer = RoomRenderer()
    lines = renderer.room_display_lines(room)

    ui.render_room(lines, clear=clear)



