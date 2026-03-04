# kingdom/renderer.py

from typing import Sequence
from kingdom.model.noun_model import Room, Item, Box
from kingdom.model.game_init import get_action_state


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

        if not room.description:
            desc = f"You are in {room.name}."
        else:            
            desc = f"You are {room.description}"

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
        if room.visited or not room.description:
            lines.append(f"You are in {room.name}.")
        else:            
            lines.append(f"You are {room.description}")

        # Items
        if room.items:
            names = ", ".join(item.display_name() for item in room.items)
            lines.append(f"You see {names}")

        # Boxes
        if room.boxes:
            names = ", ".join(box.display_name() for box in room.boxes)
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
        return f"You look at {item.display_name()} carefully."

    def describe_box_contents(self, box: Box) -> str:
        """Return a description of a box's contents."""
        if box.is_openable and not box.is_open:
            return f"You see {box.display_name()} is closed."
        if not box.contents:
            return f"You see {box.display_name()} is empty."
        names = ", ".join(item.display_name() for item in box.contents)
        return f"Inside {box.display_name()} you see: {names}."

    # ----------------------------------------------------------------------
    # Darkness logic
    # ----------------------------------------------------------------------

    def is_dark_room(self, room: Room) -> bool:
        """Return True if the room is effectively dark."""
        try:
            player = get_action_state().current_player
        except RuntimeError:
            player = None

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


def render_current_room(state, display=True, clear=False):

    room = state.current_room
    if room is None:
        return
    
    renderer = RoomRenderer()
    lines = renderer.room_display_lines(room)

    return lines



