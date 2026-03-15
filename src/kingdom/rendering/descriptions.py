# kingdom/renderer.py

from typing import Sequence
import re

from kingdom.model.noun_model import Room, Item, Container
from kingdom.model.direction_model import DIRECTIONS
from kingdom.model.game_model import get_game
import kingdom.rendering.textutils as tu



_WALL_PATTERN = re.compile(
    r"\bon\s+(?:the|a|an)?\s*(?:\w+\s+){0,2}?wall\b",   # heuristic pattern to detect wall-mounted items based on their display name
    re.IGNORECASE
)


class RoomRenderer:
    """
    Pure presentation logic for describing rooms, items, containers, and exits.
    Produces semantic text; UI layer decides how to display it.
    """


    def describe_room(self, room: Room, look=False) -> list[str]:

        if self.is_dark_room(room):
            return [self.dark_room_message(room)]

        game = get_game()
        lines: list[str] = []

        # Room description
        if (room.found and not look) or not room.description:
            lines.append(f"You are in {room.name}.")
        else:
            lines.append(f"You are {room.description}")

        # Items and containers
        visible_items = [i for i in room.items if getattr(i, "is_visible", True)]
        visible_containers = [c for c in room.containers if getattr(c, "is_visible", True)]


        #update discover score - checks if first time seeing and if so updates score metrics
        game.update_discover_score(room)
        for item in visible_items:
            game.update_discover_score(item)
        for container in visible_containers:
            game.update_discover_score(container)

        wall_items = []
        floor_items = []
        ceiling_items = []
        special_structures = []

        # --- CLASSIFY ALL ITEMS FIRST ---
        fixtures = []

        for item in visible_items:
            name = item.stateful_name()

            # 0. Fixtures override everything
            if self.classify_fixture(name):
                fixtures.append(item)
                continue

            # 1. Special structures (doors, trapdoors, hatches)
            special = self.classify_special_structure(name)
            if special == "wall":
                wall_items.append((item, name, None))
                continue
            elif special == "floor":
                special_structures.append(item)
                continue
            elif special == "ceiling":
                ceiling_items.append(item)
                continue

            # 2. Regex-based wall detection
            is_wall, cleaned, phrase = self.extract_wall_phrase(item.display_name().lower())
            if is_wall:
                wall_items.append((item, cleaned, phrase))
            else:
                floor_items.append(item)


        floor_line = self.group_floor_items(floor_items)
        if floor_line:
            lines.append(floor_line)

        # --- RENDER SPECIAL STRUCTURES ---
        for s in special_structures:
            presence = self.describe_presence(s)
            if presence:
                lines.append(presence)

        # --- RENDER CONTAINERS ---
        for c in visible_containers:
            presence = self.describe_presence(c)
            if presence:
                lines.append(presence)

        # --- RENDER FIXTURES ---
        for f in fixtures:
            presence = self.describe_presence(f)
            if presence:
                lines.append(presence)
            
        # --- RENDER WALL ITEMS ---
        wall_line = self.group_wall_items(wall_items)
        if wall_line:
            lines.append(wall_line)

        # --- RENDER CEILING ITEMS ---
        ceiling_line = self.group_ceiling_items(ceiling_items)
        if ceiling_line:
            lines.append(ceiling_line)

        # --- RENDER EXITS ---
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
        game = get_game()
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        if container.is_openable and not container.is_open:
            return f"You see {container.display_name()} is closed."
        if not container.contents:
            return f"You see {container.display_name()} is empty."
        names = []
        for item in container.contents:
            game.update_discover_score(item)            #update discovery score for items inside container when looking inside
            names.append(item.display_name())
        result = ", ".join(names)
        return f"Inside {container.display_name()} you see: {result}."
    

    # ----------------------------------------------------------------------
    # Darkness logic
    # ----------------------------------------------------------------------

    def is_dark_room(self, room: Room) -> bool:
        """Return True if the room is effectively dark."""
        try:
            player = get_game().current_player
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
    
    #----------------------------------------------------------------------
    # Exit description logic
    #----------------------------------------------------------------------


    _VERTICAL_LABELS = {"up": "above", "down": "below"}

    def direction_phrase(self, direction: str) -> str:
        # Vertical directions get special labels
        if direction in self._VERTICAL_LABELS:
            return self._VERTICAL_LABELS[direction]
        # Everything else is direction-agnostic
        return direction

    def build_visible_exits_text(self, exits: Sequence[tuple[str, str, object]]) -> str:
        # Extract direction strings
        directions = [direction for _, direction, _ in exits if isinstance(direction, str)]
        if not directions:
            return "There are no visible exits."

        # order exits in directionRegistry order 

        ordered  = DIRECTIONS.sort_directions(directions)

        # Partition into vertical and non-vertical
        vertical = [d for d in ordered if d in self._VERTICAL_LABELS]
        horizontal = [d for d in ordered if d not in self._VERTICAL_LABELS]

        # Build phrases
        phrases = []

        if vertical:
            # "above and below"
            v_phrase = tu.join_with_and([self.direction_phrase(d) for d in vertical])
            phrases.append(v_phrase)

        if horizontal:
            # "north, south, east and west"
            h_phrase = tu.join_with_and([self.direction_phrase(d) for d in horizontal])
            phrases.append(f"to the {h_phrase}")

        # Single exit
        if len(ordered) == 1:
            return f"There is an exit {phrases[0]}."

        # Multiple exits
        return f"There are exits {tu.join_with_and(phrases)}."

    
    #----------------------------------------------------------------------
    # Item description logic and heuristics for better narative structure
    #----------------------------------------------------------------------

    def extract_wall_phrase(self, text: str):
        """
        Returns (is_wall_item, cleaned_text, matched_phrase or None)
        """
        m = _WALL_PATTERN.search(text)
        if not m:
            return False, text, None

        matched = m.group(0)
        # Remove the matched phrase cleanly
        cleaned = (text[:m.start()] + text[m.end():]).strip()
        # Remove doubled spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return True, cleaned, matched


    def describe_presence(self, obj):
        name = obj.stateful_name()

        # Wall items handled separately
        is_wall, cleaned, phrase = self.extract_wall_phrase(name.lower())
        if is_wall:
            return None  # grouped later

        # Containers
        if isinstance(obj, Container):
            return tu.terminate(tu.capitalize_first(
                f"{tu.add_indefinite_article(name)} sits nearby"
            ))

        # Trapdoor heuristic
        lname = name.lower()
        if "trapdoor" in lname or "trap door" in lname:
            return tu.terminate(tu.capitalize_first(
                f"{tu.add_indefinite_article(name)} lies set into the floor"
            ))
        
        #room fixtures (anchored, embedded, fixed, bolted, mounted, set into, etc.) get their own special phrasing to avoid sounding like loose items
        if self.classify_fixture(name):
            return tu.terminate(tu.capitalize_first(name))


        # Default loose item
        return tu.terminate(tu.capitalize_first(
            f"{tu.add_indefinite_article(name)} is here"
        ))


    def group_floor_items(self, items):
        if not items:
            return None

        if len(items) == 1:
            name = tu.add_indefinite_article(items[0].stateful_name())
            return tu.terminate(f"On the floor of the room lies {name}")

        names = [tu.add_indefinite_article(i.stateful_name()) for i in items]
        joined = tu.join_with_and(names)
        return tu.terminate(f"Scattered around the room are {joined}")


    def group_wall_items(self, wall_items):
        if not wall_items:
            return None

        # Use cleaned names
        names = [cleaned for (_, cleaned, _) in wall_items]
        joined = tu.join_with_and(names)

        if len(wall_items) == 1:
            return tu.terminate(
                f"On a nearby wall you can see {joined}"
            )
        else:
            return tu.terminate(
                f"On the walls around the room you can see {joined}"
            )


    def classify_special_structure(self, name: str):              # later we will make doors their own class and will be tied to a direction and location.
        """
        Returns one of: 'wall', 'floor', 'ceiling', or None.
        """
        lname = name.lower()

        if "door" in lname and "trap" not in lname:
            return "wall"

        if "trapdoor" in lname or "trap door" in lname:
            return "floor"

        if "hatch" in lname:
            return "ceiling"

        return None
    
    def classify_fixture(self, name: str):
        lname = name.lower()

        fixture_keywords = [
            "anchored", "embedded", "bolted", "mounted",
            "set into", "driven into", "fixed into", "firmly anchored",
            "tied", "attached", "secured"   # NEW
        ]

        return any(kw in lname for kw in fixture_keywords)



    def group_ceiling_items(self, items):
        if not items:
            return None

        names = [tu.add_indefinite_article(i.stateful_name()) for i in items]
        joined = tu.join_with_and(names)

        if len(items) == 1:
            return tu.terminate(f"High above you, {joined} is set into the ceiling")
        else:
            return tu.terminate(f"High above you, {joined} are set into the ceiling")
        


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

