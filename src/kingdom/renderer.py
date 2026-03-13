# kingdom/renderer.py

from typing import Sequence
from kingdom.model.noun_model import Room, Item, Container
from kingdom.model.game_init import get_action_state


class RoomRenderer:
    """
    Pure presentation logic for describing rooms, items, containers, and exits.
    Produces semantic text; UI layer decides how to display it.
    """


    def describe_room(self, room: Room, look=False) -> list[str]:   
        """Return a list of lines for UI rendering."""
        if self.is_dark_room(room):
            return [self.dark_room_message(room)]

        lines: list[str] = []

        # Room description
    
        if (room.found and not look) or not room.description:
            lines.append(f"You are in {room.name}.")
        else:            
            lines.append(f"You are {room.description}")

        # Items
        visible_items = [item for item in room.items if getattr(item, "is_visible", True)]
        if visible_items:
            names = ", ".join(item.display_name() for item in visible_items)
            lines.append(f"You see {names}")

        # Containers
        visible_containers = [c for c in room.containers if getattr(c, "is_visible", True)]
        if visible_containers:
            names = ", ".join(container.display_name() for container in visible_containers)
            if len(visible_containers) == 1:
                lines.append(f"You see {names} here.")
            else:
                lines.append(f"There are {names} here.")

        # Exits
        exits = room.get_all_exits(movement_type="all", visible_only=True)
        exits_text = self.build_visible_exits_text(exits)
        if exits_text:
            lines.append(exits_text)

        return lines

    def describe_item(self, room: Room, item: Item) -> str:
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        desc = getattr(item, "examine_string", None)
        if desc:
            return desc
        return f"You look at {item.display_name()} carefully."
    
    def describe_container(self, room: Room, container: Container) -> str:
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        desc = getattr(container, "examine_string", None)
        if desc:
            return desc
        return f"You look at {container.display_name()} carefully. There might be something interesting inside."

    def describe_container_contents(self, room: Room, container: Container) -> str:
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        if container.is_openable and not container.is_open:
            return f"You see {container.display_name()} is closed."
        if not container.contents:
            return f"You see {container.display_name()} is empty."
        names = ", ".join(item.display_name() for item in container.contents)
        return f"Inside {container.display_name()} you see: {names}."

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


        # Room items
        for item in room.items:
            if getattr(item, "is_lit", False):
                return False

        # Containers (only open ones)
        for container in room.containers:
            if container.is_openable and not container.is_open:
                continue
            for item in container.contents:
                if getattr(item, "is_lit", False):
                    return False

        # Player inventory
        if player:
            for item in player.sack.contents:
                if getattr(item, "is_lit", False):
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

    def build_visible_exits_text(self, exits: Sequence[tuple[str, str, object]]) -> str:
        directions: list[str] = []
        for movement_type, direction, exit_obj in exits:
            if isinstance(direction, str):
                directions.append(direction)

        ordered = self.order_directions(sorted(set(directions)))
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




# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

renderer = RoomRenderer()

def render_current_room(room, look=False) -> list[str] | None:
    return(renderer.describe_room(room, look=look))

def render_item(room, item) -> list[str] | None:
    return(renderer.describe_item(room, item))

def render_container(room, item) -> list[str] | None:
    return(renderer.describe_container(room, item))

def render_container_contents(room, container) -> list[str] | None:
    return(renderer.describe_container_contents(room, container))

