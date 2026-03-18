# kingdom/renderer.py

from turtle import clear
from typing import Sequence
import re

from kingdom.model.noun_model import Room, Item, Container
from kingdom.model.direction_model import DIRECTIONS
from kingdom.model.game_model import get_game
from kingdom.GUI.UI import ui
import kingdom.rendering.textutils as tu



_WALL_PATTERN = re.compile(
    r"\bon\s+(?:the|a|an)?\s*(?:\w+\s+){0,2}?wall\b",   # heuristic pattern to detect wall-mounted items based on their display name
    re.IGNORECASE
)

_WALL_ADJ_PATTERN = re.compile(r"\bwall\s+\w+", re.IGNORECASE)



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
            lines.extend(self.describe_room_concise(room))
            lines.append("")
        else:
            lines.extend(self.describe_room_verbose(room))
            lines.append("")

        return lines

    def describe_room_concise(self, room: Room) -> list[str]:
        game = get_game()
        room = game.current_room 
        lines: list[str] = []
        lines.append(f"You are in {room.name}.")
        lines.append("")

        # Items and containers (concise description only)
        visible_items = [i for i in room.items if getattr(i, "is_visible", True)]
        visible_containers = [c for c in room.containers if getattr(c, "is_visible", True)]
        for container in visible_containers:
            if container.is_transparent:
                visible_items.extend(container.contents)

        all_visible_objects = []

        for item in visible_items:
            all_visible_objects.append(("item", item))

        for container in visible_containers:
            all_visible_objects.append(("container", container))

        # Sort by render_priority (higher first)
        all_visible_objects.sort(
            key=lambda pair: (getattr(pair[1], "render_priority", 0) or 0),
            reverse=True
        )

        if all_visible_objects:
            lines.append("You see:")
            for _kind, obj in all_visible_objects:
                lines.append(F"-  {obj.stateful_name()}")

        
        #now exits

        exits = room.get_all_exits(movement_type="all", visible_only=True)
        if exits:
            lines.append("")
            lines.append("Available exits:")  
            for _, direction, _ in exits:
                if isinstance(direction, str):
                    lines.append(f"- {direction}")

        
        return lines

    def describe_room_verbose(self, room: Room) -> list[str]:

        game = get_game()
        lines: list[str] = []

        lines.append(f"You are {room.description}")
        lines.append("")


        # Items and containers
        visible_items = [i for i in room.items if getattr(i, "is_visible", True)]
        visible_containers = [c for c in room.containers if getattr(c, "is_visible", True)]

        #update discover score - checks if first time seeing and if so updates score metrics
        game.update_discover_score(room)
        for item in visible_items:
            game.update_discover_score(item)
        for container in visible_containers:
            game.update_discover_score(container)


        # --- PRIORITY SORTING -------------------------------------------------

        # Combine items and containers into a single sequence for ordering
        all_visible_objects = []

        for item in visible_items:
            all_visible_objects.append(("item", item))

        for container in visible_containers:
            all_visible_objects.append(("container", container))

        # Sort by render_priority (higher first)
        all_visible_objects.sort(
            key=lambda pair: (getattr(pair[1], "render_priority", 0) or 0),
            reverse=True
        )

        # --- BUCKET PRIORITIES -------------------------------------------------
        BUCKET_PRIORITY = {
            "floor": 0,
            "special": 1,
            "container": 2,
            "fixture": 3,
            "wall": 4,
            "ceiling": 5,
        }

        # This will hold tuples of (bucket_name, object_or_description)
        render_entries = []



        # --- CLASSIFY ALL OBJECTS IN PRIORITY ORDER  ---------------------
        wall_items = []          # renamed from wall_items for clarity in next block

        for kind, obj in all_visible_objects:
            name = obj.stateful_name()

            # If the object has an authored location_description, treat it as a special structure
            # (this stays first — it's the intended override)
            if getattr(obj, "location_description", None):
                render_entries.append(("special", obj))
                continue

            # 0. Fixtures 
            if self.classify_fixture(name):
                render_entries.append(("fixture", obj))
                continue

            # 1. Special structures (doors, trapdoors, hatches)
            special = self.classify_special_structure(name)
            if special == "wall":
                wall_items.append((obj, name, None))
                continue
            elif special == "floor":
                render_entries.append(("special", obj))
                continue
            elif special == "ceiling":
                render_entries.append(("ceiling", obj))
                continue

            # 2. Regex-based wall detection  
            is_wall, cleaned, phrase = self.extract_wall_phrase(name)  # ← no .lower() anymore
            if is_wall:
                wall_items.append((obj, cleaned, phrase))
                continue

            # 3. Containers get their own bucket
            if kind == "container":
                render_entries.append(("container", obj))
                continue

            # 4. Default: floor item
            render_entries.append(("floor", obj))

        # --- GROUPED WALL ITEMS ------------------------------------------------
        wall_max_pri = 0
        if wall_items:
            # Respect render_priority even for grouped walls (the highest one wins)
            wall_max_pri = max(
                (getattr(obj, "render_priority", 0) or 0 for obj, _, _ in wall_items),
                default=0
            )

            # Enhanced names — transparent containers now show contents inline!
            enhanced_names = []
            for obj, cleaned, _ in wall_items:
                if (isinstance(obj, Container) and
                    getattr(obj, "is_transparent", False) and
                    obj.contents):
                    inner = tu.join_with_and(
                        [tu.add_indefinite_article(i.stateful_name()) for i in obj.contents]
                    )
                    enhanced = f"{cleaned} holding {inner}"
                else:
                    enhanced = cleaned
                enhanced_names.append(enhanced)

            joined = tu.join_with_and(enhanced_names)

            if len(wall_items) == 1:
                wall_text = tu.terminate(f"On a nearby wall you can see {joined}")
            else:
                wall_text = tu.terminate(f"On the walls around the room you can see {joined}")

            render_entries.append(("wall", wall_text))

        queue = []

        for bucket, obj in render_entries:
            bucket_pri = BUCKET_PRIORITY[bucket]

            if isinstance(obj, str):
                # grouped lines
                combined = bucket_pri
                if bucket == "wall":
                    combined = (wall_max_pri * 100) + bucket_pri   # ← now respects render_priority
                queue.append((combined, obj))
                continue

            item_pri = getattr(obj, "render_priority", 0) or 0
            combined = (item_pri * 100) + bucket_pri

            queue.append((combined, obj))

        for pri, obj in queue:
            if not isinstance(obj, str):
                obj_name = obj.stateful_name()
        # Now sort
        queue.sort(key=lambda x: x[0], reverse=True)

        for pri, obj in queue:
            if not isinstance(obj, str):
                obj_name = obj.stateful_name()

        # Now render
        for _, entry in queue:
            if isinstance(entry, str):
                lines.append(entry)
                lines.append("")
            else:
                text = self.describe_presence(entry)
                if text:
                    lines.append(text)
                    lines.append("")


        # --- RENDER EXITS ------------------------------------------------------
        exits = room.get_all_exits(movement_type="all", visible_only=True)
        exits_text = self.build_visible_exits_text(exits)
        if exits_text:
            lines.append(exits_text)

        return lines

    def describe_item(self, room: Room, item: Item) -> str:
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        desc = getattr(item, "examine_description", None)
        if desc:
            return desc
        return f"You look at {item.stateful_name()} carefully."
    
    
    def describe_container(self, room: Room, container: Container) -> str:
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        desc = getattr(container, "examine_description", None)
        if desc:
            return desc
        return f"You look at {container.stateful_name()} carefully. There might be something interesting inside."
    

    def describe_container_contents(self, room: Room, container: Container) -> str:
        game = get_game()
        if self.is_dark_room(room):
            return self.dark_room_message(room)
        if container.is_openable and not container.is_open:
            return f"You see {container.stateful_name()} is closed."
        if not container.contents:
            return f"You see {container.stateful_name()} is empty."
        names = []
        for item in container.contents:
            game.update_discover_score(item)            #update discovery score for items inside container when looking inside
            names.append(item.stateful_name())
        result = ", ".join(names)
        return f"You see: {result}."
    

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
        msg = getattr(room, "dark_description", None)
        return msg or "It is pitch black. You can't see a thing."

    
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
        # 1. Phrase-based wall detection ("on the wall", etc.)
        m = _WALL_PATTERN.search(text)
        if m:
            phrase = m.group(0)
            cleaned = text.replace(phrase, "").strip()
            return True, cleaned, phrase

        # 2. Adjective-based wall detection ("wall sconce", "wall bracket")
        m2 = _WALL_ADJ_PATTERN.search(text)
        if m2:
            phrase = m2.group(0)
            cleaned = text.strip()
            return True, cleaned, phrase

        # 3. No wall cue
        return False, text, None

    def describe_presence(self, obj):
        name = obj.stateful_name()


        # Author-provided location_description overrides *location heuristics*
        # but we still apply other transformations (like transparent container contents).
        loc = getattr(obj, "location_description", None)

        # Containers get special treatment first — this is the "other transformation"
        # the user specifically wanted to preserve even when loc is provided.
        if isinstance(obj, Container):
            # Transparent containers show contents inline
            if getattr(obj, "is_transparent", False) and obj.contents:
                inner = tu.join_with_and(
                    [tu.add_indefinite_article(i.stateful_name()) for i in obj.contents]
                )
                if loc:
                    # Author loc provides the positioning verb; we append the contents
                    # transformation so it still shows. Example:
                    # "A glass box rests on the altar holding a ruby and a key"
                    full_phrase = f"{name} {loc} holding {inner}"
                else:
                    full_phrase = f"{name} holding {inner}"

                return tu.terminate(
                    tu.capitalize_first(
                        tu.add_indefinite_article(full_phrase)
                    )
                )

            # Normal opaque containers — loc overrides the "sits nearby" heuristic
            if loc:
                full_phrase = f"{name} {loc}"
            else:
                full_phrase = f"{name} sits nearby"

            return tu.terminate(
                tu.capitalize_first(
                    tu.add_indefinite_article(full_phrase)
                )
            )

        # === Non-containers below here ===

        # Wall items handled separately 
        is_wall, cleaned, phrase = self.extract_wall_phrase(name.lower())
        if is_wall:
            return None  # grouped later


        # Author-provided loc overrides ALL remaining location heuristics
        # (trapdoor, fixture, default "is here").
        if loc:
            return tu.terminate(
                tu.capitalize_first(
                    tu.add_indefinite_article(f"{name} {loc}")
                )
            )

        # Trapdoor heuristic
        lname = name.lower()
        if "trapdoor" in lname or "trap door" in lname:
            return tu.terminate(tu.capitalize_first(
                f"{tu.add_indefinite_article(name)} is set into the floor"
            ))
        
        # Room fixtures (anchored, embedded, etc.)
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
        Returns one of: 'wall', 'floor', 'ceiling', "door", or None.
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
    return renderer.describe_room(room, look=look)

def render_item(room, item) -> list[str] | None:
    return(renderer.describe_item(room, item))

def render_container(room, item) -> list[str] | None:
    return(renderer.describe_container(room, item))

def render_container_contents(room, container) -> list[str] | None:
    return(renderer.describe_container_contents(room, container))

