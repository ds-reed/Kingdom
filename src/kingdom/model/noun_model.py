from __future__ import annotations

import json
from pathlib import Path


def _normalize_tokens(text: str) -> list[str]:
    return [token for token in str(text).strip().lower().split() if token]


def _derive_noun_name(text: str) -> str:
    tokens = _normalize_tokens(text)
    if not tokens:
        return ""
    articles = {"a", "an", "the"}
    if tokens[0] in articles and len(tokens) > 1:
        tokens = tokens[1:]
    return tokens[-1]


class Noun:
    """Parent class for all game world entities (items, boxes, rooms)."""

    all_nouns = []

    def __init__(self):
        Noun.all_nouns.append(self)

    def get_name(self):
        return self.name

    def get_noun_name(self):
        noun_name = getattr(self, "noun_name", None)
        if noun_name:
            return str(noun_name)
        return _derive_noun_name(self.get_name())

    def get_descriptive_phrase(self):
        phrase = getattr(self, "descriptive_phrase", None)
        if phrase:
            return str(phrase)
        return self.get_name()

    def matches_reference(self, reference: str) -> bool:
        candidate = " ".join(_normalize_tokens(reference))
        if not candidate:
            return False

        descriptive = " ".join(_normalize_tokens(self.get_descriptive_phrase()))
        noun_name = " ".join(_normalize_tokens(self.get_noun_name()))
        return candidate in {descriptive, noun_name}

    def get_presence_text(self):
        return f"There is {self.name} here."

    def on_unlock(self, words):
        return None

    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        return True, None

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in getattr(self, "behavior_handlers", []):
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return None

    @classmethod
    def by_name(cls, name: str, *, exact: bool = False) -> "Noun | None":
        name_lower = name.lower().strip()
        if not name_lower:
            return None

        for noun in cls.all_nouns:
            if exact:
                if noun.get_name().lower() == name_lower:
                    return noun
            else:
                if noun.matches_reference(name):
                    return noun
        return None


class DirectionRegistry:
    def __init__(self):
        self.canonical = set()
        self.aliases = {}
        self.reverse = {}

    def register(self, canonical: str, *, synonyms=None, reverse=None):
        canonical = canonical.lower().strip()
        self.canonical.add(canonical)

        if synonyms:
            for synonym in synonyms:
                self.aliases[synonym.lower().strip()] = canonical

        if reverse:
            reverse = reverse.lower().strip()
            self.reverse[canonical] = reverse
            self.reverse[reverse] = canonical
            self.canonical.add(reverse)

    def to_canonical(self, token: str) -> str:
        token = token.lower().strip()
        return self.aliases.get(token, token)

    def reverse_of(self, canonical: str) -> str | None:
        canonical = canonical.lower().strip()
        return self.reverse.get(canonical)

    def is_direction(self, token: str) -> bool:
        return self.to_canonical(token) in self.canonical

    def all_directions(self):
        return sorted(self.canonical)


DIRECTIONS = DirectionRegistry()


class DirectionNoun(Noun):
    def __init__(self, reference_name: str, canonical_direction: str):
        super().__init__()
        self.name = reference_name
        self._noun_name = reference_name
        self.canonical_direction = canonical_direction

    def matches_reference(self, reference: str) -> bool:
        ref = reference.lower().strip()
        canon = DIRECTIONS.to_canonical(ref)
        return canon == self.canonical_direction

    def canonical_name(self):
        return self.canonical_direction

    def noun_name(self):
        return self._noun_name

    _direction_nouns_by_reference: dict[str, "DirectionNoun"] = {}
    _direction_nouns_by_canonical: dict[str, list["DirectionNoun"]] = {}

    def ensure_direction_nouns():
        if DirectionNoun._direction_nouns_by_reference:
            return

        for canonical in DIRECTIONS.canonical:
            direction_noun = DirectionNoun(canonical, canonical)
            DirectionNoun._direction_nouns_by_reference[canonical] = direction_noun
            DirectionNoun._direction_nouns_by_canonical.setdefault(canonical, []).append(direction_noun)

        for alias, canonical in DIRECTIONS.aliases.items():
            direction_noun = DirectionNoun(alias, canonical)
            DirectionNoun._direction_nouns_by_reference[alias] = direction_noun
            DirectionNoun._direction_nouns_by_canonical.setdefault(canonical, []).append(direction_noun)

    def get_direction_noun(token: str) -> "DirectionNoun | None":
        DirectionNoun.ensure_direction_nouns()
        token = token.lower().strip()
        return DirectionNoun._direction_nouns_by_reference.get(token)

    def get_direction_nouns_for_available_exits(room) -> list["DirectionNoun"]:
        DirectionNoun.ensure_direction_nouns()
        if room is None:
            return []

        nouns: list[DirectionNoun] = []
        for canonical in room.available_directions(visible_only=True):
            canonical = canonical.lower().strip()
            nouns.extend(DirectionNoun._direction_nouns_by_canonical.get(canonical, []))

        return nouns


class Item(Noun):
    all_items = []
    _by_name = {}

    @classmethod
    def get_by_name(cls, name: str) -> "Item | None":
        if not name:
            return None
        key = str(name).strip().lower()
        return cls._by_name.get(key)

    def __init__(
        self,
        name,
        is_gettable=True,
        refuse_string=None,
        presence_string=None,
        noun_name=None,
        is_openable=False,
        is_open=False,
        opened_state_description=None,
        closed_state_description=None,
        lit_state_description=None,
        unlit_state_description=None,
        open_action_description=None,
        close_action_description=None,
        examine_string=None,
        open_exit_direction=None,
        open_exit_destination=None,
        is_lockable=False,
        is_locked=False,
        unlock_key=None,
        locked_state_description=None,
        unlocked_state_description=None,
        unlockable_description=None,
        is_edible=False,
        is_verbally_interactive=False,
        is_lightable=False,
        is_lit=False,
        can_ignite=False,
        ignite_success_string=None,
        is_rubbable=False,
        is_rubbed=False,
        rubbed_state_description=None,
        rub_success_string=None,
        trigger_room=None,
        too_heavy_to_swim=False,
        eat_refuse_string=None,
        eaten_success_string=None,
        get_refuse_string=None,
        special_handlers=None,
    ):
        super().__init__()
        self.name = str(name).strip()
        self.descriptive_phrase = self.name
        self.noun_name = str(noun_name).strip().lower() if noun_name else _derive_noun_name(self.name)
        searchkey = self.noun_name.lower()
        if searchkey in Item._by_name:
            print(f"Warning: duplicate item name '{searchkey}' — overwriting previous")
        Item._by_name[searchkey] = self
        self.current_box = None
        self.is_broken = False
        self.is_gettable = is_gettable
        self.refuse_string = refuse_string or f"You can't pick up {self.name}"
        self.presence_string = presence_string
        self.is_openable = bool(is_openable)
        self.is_open = bool(is_open)
        self.opened_state_description = opened_state_description
        self.closed_state_description = closed_state_description
        self.lit_state_description = lit_state_description
        self.unlit_state_description = unlit_state_description
        self.open_action_description = open_action_description
        self.close_action_description = close_action_description
        self.examine_string = examine_string
        self.open_exit_direction = (
            str(open_exit_direction).strip().lower()
            if open_exit_direction is not None and str(open_exit_direction).strip()
            else None
        )
        self.open_exit_destination = (
            str(open_exit_destination).strip()
            if open_exit_destination is not None and str(open_exit_destination).strip()
            else None
        )
        self.is_lockable = bool(is_lockable)
        self.is_locked = bool(is_locked)
        self.unlock_key = (
            str(unlock_key).strip().lower()
            if unlock_key is not None and str(unlock_key).strip()
            else None
        )
        self.locked_state_description = locked_state_description
        self.unlocked_state_description = unlocked_state_description
        self.unlockable_description = unlockable_description
        self.is_edible = bool(is_edible)
        self.is_verbally_interactive = bool(is_verbally_interactive)
        self.is_lightable = bool(is_lightable)
        self.is_lit = bool(is_lit)
        self.can_ignite = bool(can_ignite)
        self.ignite_success_string = ignite_success_string
        self.is_rubbable = bool(is_rubbable)
        self.is_rubbed = bool(is_rubbed)
        self.rubbed_state_description = rubbed_state_description
        self.rub_success_string = rub_success_string
        self.trigger_room = str(trigger_room).strip() if trigger_room is not None and str(trigger_room).strip() else None
        self.too_heavy_to_swim = bool(too_heavy_to_swim)
        self.eat_refuse_string = eat_refuse_string
        self.eaten_success_string = eaten_success_string
        self.get_refuse_string = get_refuse_string
        self.is_verbally_interactive = bool(is_verbally_interactive)
        self.special_handlers = special_handlers or {}
        Item.all_items.append(self)

    def get_presence_text(self):
        if self.is_lockable and self.is_locked and self.locked_state_description:
            return self.locked_state_description
        if self.is_openable:
            if self.is_open and self.opened_state_description:
                return self.opened_state_description
            if not self.is_open and self.closed_state_description:
                return self.closed_state_description
        if self.is_lightable:
            if self.is_lit and self.lit_state_description:
                return self.lit_state_description
            if not self.is_lit and self.unlit_state_description:
                return self.unlit_state_description
        if self.presence_string:
            return self.presence_string
        return f"There is {self.name} here."

    def _remove_from_known_containers(self, dispatch_context: object | None = None) -> bool:
        if self.current_box is not None:
            if self in self.current_box.contents:
                self.current_box.contents.remove(self)
                self.current_box = None
                return True
            self.current_box = None

        from . import models as model_api

        state = getattr(dispatch_context, "state", None)
        if state is None:
            try:
                state = model_api.get_action_state()
            except RuntimeError:
                return False

        if state is not None and getattr(state, "current_room", None) is not None:
            room = state.current_room
            if self in room.items:
                room.items.remove(self)
                return True

            for box in room.boxes:
                if self in box.contents:
                    box.contents.remove(self)
                    return True

        player = getattr(state, "current_player", None)

        if player is not None and self in player.sack.contents:
            player.sack.contents.remove(self)
            return True

        return False

    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        if verb_name == "take" and not self.is_gettable:
            return False, self.refuse_string
        if verb_name == "eat":
            return True, None
        return super().can_handle_verb(verb_name, *args, **kwargs)

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in self.behavior_handlers:
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return super().handle_verb(verb_name, *args, **kwargs)

    def canonical_name(self):
        return getattr(self, "noun_name", None) or self.name

    def display_name(self):
        return self.name


class Box(Noun):
    all_boxes = []
    _by_name = {}

    def __init__(
        self,
        canonical_name,
        box_name,
        capacity=None,
        presence_string=None,
        is_openable=False,
        is_open=False,
        opened_state_description=None,
        closed_state_description=None,
        open_action_description=None,
        close_action_description=None,
        is_lockable=False,
        is_locked=False,
        unlock_key=None,
        locked_description=None,
        open_exit_direction=None,
        open_exit_destination=None,
        examine_string=None,
    ):
        super().__init__()
        self.noun_name = canonical_name
        self.box_name = box_name
        self.name = box_name
        self.contents = []
        self.capacity = capacity
        searchkey = self.noun_name.lower()
        if searchkey in Box._by_name:
            print(f"Warning: duplicate item name '{searchkey}' — overwriting previous")
        Box._by_name[searchkey] = self
        self.presence_string = presence_string
        self.is_openable = bool(is_openable)
        self.is_open = bool(is_open)
        self.opened_state_description = opened_state_description
        self.closed_state_description = closed_state_description
        self.open_action_description = open_action_description
        self.close_action_description = close_action_description
        self.examine_string = examine_string
        self.is_lockable = bool(is_lockable)
        self.is_locked = bool(is_locked)
        self.unlock_key = (
            str(unlock_key).strip().lower()
            if unlock_key is not None and str(unlock_key).strip()
            else None
        )
        self.locked_description = locked_description
        self.open_exit_direction = (
            str(open_exit_direction).strip().lower()
            if open_exit_direction is not None and str(open_exit_direction).strip()
            else None
        )
        self.open_exit_destination = (
            str(open_exit_destination).strip()
            if open_exit_destination is not None and str(open_exit_destination).strip()
            else None
        )
        Box.all_boxes.append(self)
        Box._by_name[self.noun_name.lower()] = self

    def __repr__(self):
        cls = self.__class__.__name__
        contents = [item.name for item in self.contents]
        return f"<{cls} name={self.name!r} open={self.is_open} contents={contents}>"

    def get_presence_text(self):
        if self.is_lockable and self.is_locked and self.locked_description:
            return self.locked_description
        if self.is_openable:
            if self.is_open and self.opened_state_description:
                return self.opened_state_description
            if not self.is_open and self.closed_state_description:
                return self.closed_state_description
        if self.presence_string:
            return self.presence_string
        return f"There is {self.box_name} here."

    def add_item(self, item):
        if item is None:
            print("ERROR: add_item received None")
            return
        if self.capacity is not None and len(self.contents) >= self.capacity:
            print(f"ERROR: Cannot add {item.name} to {self.box_name} - capacity reached")
            return
        if item.current_box == self:
            print(f"ERROR: {item.name} is already in {self.box_name}")
            return

        if item.current_box is not None:
            item.current_box.contents.remove(item)

        self.contents.append(item)
        item.current_box = self

        return

    def has_item(self, item) -> bool:
        return item in self.contents

    def remove_item(self, item):
        if item in self.contents:
            self.contents.remove(item)
            item.current_box = None
            return

    def canonical_name(self):
        return getattr(self, "noun_name")

    def display_name(self):
        return self.box_name


class Player:
    """A player character who can collect items in their sack (max 10 items)."""

    def __init__(self, name):
        self.name = name
        self.sack = Box(
            canonical_name="inventory",
            box_name=f"{name}'s sack",
            capacity=10,
        )

    def add_to_sack(self, item):
        return self.sack.add_item(item)

    def remove_from_sack(self, item):
        return self.sack.remove_item(item)

    def has_item(self, item) -> bool:
        return self.sack.has_item(item)

    def get_inventory_items(self):
        return self.sack.contents

    def canonical_name(self):
        return self.name.lower()

    def display_name(self):
        return self.name


class Room(Noun):
    all_rooms = []
    DIRECTIONS = []
    _by_name = {}

    def __init__(self, name, description, visited=False, is_dark=False, has_water=False, dark_description=None, discover_points=10):
        super().__init__()
        self.name = name
        self.description = description
        self.visited = bool(visited)
        self.is_dark = bool(is_dark)
        self.has_water = bool(has_water)
        self.dark_description = dark_description or None
        self.discover_points = max(0, discover_points)
        self.swim_exits: dict[str, "Room"] = {}
        searchkey = self.name.lower()
        if searchkey in Room._by_name:
            print(f"Warning: duplicate room name '{searchkey}' — overwriting previous")
        Room._by_name[searchkey] = self
        self.items = []
        self.boxes = []
        self.connections = {}
        self.hidden_directions = set()
        self.minigame = None
        Room.all_rooms.append(self)
        Room._by_name[self.name.lower()] = self

    def __repr__(self):
        items_str = [it.name for it in self.items if it is not None]
        boxes_str = [b.box_name for b in self.boxes]
        connections_str = {direction: room.name for direction, room in self.connections.items()}
        return (
            f"Room({self.name}, desc='{self.description}', visited={self.visited}, is_dark={self.is_dark}, has_water={self.has_water}, items={items_str}, "
            f"boxes={boxes_str}, connections={connections_str}, hidden_directions={sorted(self.hidden_directions)})"
        )

    def add_item(self, item) -> bool:
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")
        return True

    def add_box(self, box) -> bool:
        if not isinstance(box, Box):
            raise TypeError("Room.add_box expects a Box instance")
        self.boxes.append(box)
        return True

    def remove_item(self, item) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def remove_box(self, box) -> bool:
        if box in self.boxes:
            self.boxes.remove(box)
            return True
        return False

    def has_item(self, item) -> bool:
        return item in self.items

    def has_box(self, box) -> bool:
        return box in self.boxes

    def find_containing_box(self, item) -> "Box | None":
        for box in self.boxes:
            if item in box.contents:
                return box
        return None

    def add_direction(self, direction):
        if not isinstance(direction, str):
            raise TypeError("direction must be a string")
        if direction == "":
            raise ValueError("direction cannot be empty")
        if direction not in Room.DIRECTIONS:
            Room.DIRECTIONS.append(direction)
        return direction

    def connect_room(self, direction, room, visible=True):
        if not isinstance(room, Room):
            raise TypeError("connect_room expects a Room instance")
        registered_direction = self.add_direction(direction)
        self.connections[registered_direction] = room
        if visible:
            self.hidden_directions.discard(registered_direction)
        else:
            self.hidden_directions.add(registered_direction)

    def get_connection(self, direction):
        return self.connections.get(direction)

    def is_exit_visible(self, direction):
        canonical_direction = self.add_direction(direction)
        if canonical_direction not in self.connections:
            return False
        return canonical_direction not in self.hidden_directions

    def set_exit_visibility(self, direction, visible=True):
        canonical_direction = self.add_direction(direction)
        if canonical_direction not in self.connections:
            return False

        if visible:
            self.hidden_directions.discard(canonical_direction)
        else:
            self.hidden_directions.add(canonical_direction)
        return True

    def can_go(self, direction):
        return self.get_connection(direction) is not None

    def available_directions(self, visible_only=False):
        directions = sorted(self.connections.keys())
        if not visible_only:
            return directions
        return [direction for direction in directions if direction not in self.hidden_directions]

    def has_lit_is_lightable(self):
        for item in self.items:
            if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                return True

        for box in self.boxes:
            if box.is_openable and not box.is_open:
                continue
            for item in box.contents:
                if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                    return True

        return False

    def move(self, direction):
        destination = self.get_connection(direction)
        if destination is None:
            raise ValueError(f"No connection from {self.name} via '{direction}'")
        return destination

    def get_description(self):
        return self.description

    def set_minigame(self, func):
        self.minigame = func

    def play_minigame(self, *args, **kwargs):
        if callable(self.minigame):
            return self.minigame(*args, **kwargs)
        return None

    def canonical_name(self):
        return getattr(self, "noun_name", None) or self.name.lower()

    def display_name(self):
        return self.name


class Feature(Noun):
    all_features = []

    def __init__(self, name: str, noun_name: str, examine_string: str | None = None):
        super().__init__()
        self.name = name.strip()
        self.noun_name = noun_name.strip().lower()
        self.examine_string = examine_string
        Feature.all_features.append(self)

    def get_presence_text(self):
        return None

    def handle_verb(self, verb_name: str, *args, **kwargs):
        if verb_name == "examine" and self.examine_string:
            return self.examine_string
        return f"You can't do that to {self.name}."


class World(Noun):
    _instance = None

    def __init__(self):
        super().__init__()
        self.name = "World"
        self.boxes = []
        self.rooms = []
        self.start_room_name = None
        self.start_room = None
        self.state = None
        World._instance = self

    @property
    def current_player(self):
        if self.state is None:
            return None
        return self.state.current_player

    @current_player.setter
    def current_player(self, player):
        if self.state is not None:
            self.state.current_player = player

    def __repr__(self):
        return (
            f"World(\n"
            f"  rooms={list(self.rooms.keys())},\n"
            f"  current_player={self.current_player!r},\n"
            f"  start_room={self.start_room_name!r},\n"
            f")"
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = World()
        return cls._instance

    def set_world(self, boxes, rooms):
        self.boxes = boxes
        self.rooms = rooms

    def set_current_player(self, player):
        self.current_player = player

    def require_player(self, missing_message: str = "No hero is active yet.", return_error: bool = False) -> "Player | str":
        player = self.current_player
        if player is not None:
            return player

        if return_error:
            return missing_message

        raise RuntimeError(missing_message)

    def get_all_nouns(self):
        return Noun.all_nouns

    def find_item_in_game(self, noun_name: str) -> tuple["Room | None", "Item | None"]:
        for room in self.rooms.values():
            for item in room.items:
                if getattr(item, "noun_name", None) == noun_name:
                    return room, item
        return None, None

    def move_item_between_rooms(self, item: "Item", from_room: "Room", to_room: "Room") -> None:
        if item in from_room.items:
            from_room.items.remove(item)

        if item not in to_room.items:
            to_room.items.append(item)

    def setup_world(self, source):
        if isinstance(source, (str, Path)):
            with open(source, "r") as file:
                data = json.load(file)
        elif isinstance(source, dict):
            data = source
        else:
            raise TypeError("setup_world expects a filepath or a dict")

        Room.all_rooms.clear()
        Box.all_boxes.clear()
        Item.all_items.clear()
        Noun.all_nouns.clear()
        Room._by_name = {}
        Box._by_name = {}
        Item._by_name = {}

        from . import models as model_api

        model_api._load_directions(data)
        DirectionNoun.ensure_direction_nouns()

        Room.DIRECTIONS = DIRECTIONS.canonical

        if isinstance(data, dict):
            boxes = model_api._construct_boxes(data.get("boxes", []))
            rooms = model_api._construct_rooms(data.get("rooms", []))
        else:
            rooms = []
            boxes = []

        self.set_world(boxes, rooms)
        self.rooms = {room.name: room for room in rooms}
        start_room_name = data.get("start_room")
        self.start_room_name = start_room_name

        return boxes, self.rooms

    def load_game(self, filepath) -> Path:
        target = Path(filepath).expanduser()
        if not target.suffix:
            target = target.with_suffix(".json")
        if not target.is_file():
            raise RuntimeError(f"Save file not found: {target}")

        try:
            with target.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid save file format: {target} ({error})") from error
        except OSError as error:
            raise RuntimeError(f"Unable to read save file: {target} ({error})") from error

        player_data = data.pop("player", None)
        current_room_name = data.get("current_room")
        player_name = player_data.get("name", "Hero") if player_data else "Hero"

        from . import models as model_api

        action_state = model_api.get_action_state()
        action_state.player_name = player_name

        if action_state.current_player is None:
            action_state.current_player = Player(player_name)
        self.setup_world(data)

        player = action_state.current_player
        if player is None:
            raise RuntimeError("No hero is active yet.")

        player.sack.contents.clear()
        if player_data:
            for item_json in player_data.get("inventory", []):
                item = model_api._construct_item_from_spec(item_json)
                player.sack.add_item(item)

        if current_room_name and current_room_name in self.rooms:
            model_api.get_action_state().current_room = self.rooms[current_room_name]

        model_api.get_action_state().score = int(data.get("score", 0))

        return target

    def save_game(self, filepath) -> Path:
        target = Path(filepath).expanduser()
        if not target.suffix:
            target = target.with_suffix(".json")
        if target.name == "initial_state.json":
            raise RuntimeError("Refusing to overwrite initial_state.json")
        target.parent.mkdir(parents=True, exist_ok=True)

        from . import models as model_api
        action_state = model_api.get_action_state()
        player = action_state.current_player

        payload = {
            "player": {
                "name": player.name,
                "inventory": [model_api._serialize_item(item) for item in player.sack.contents],
            }
            if player
            else None,
            "current_room": action_state.current_room.name,
            "start_room": self.start_room_name,
            "score": int(action_state.score),
            "rooms": [],
        }

        for room in self.rooms.values():
            room_payload = {
                "name": room.name,
                "description": room.description,
                "visited": room.visited,
                "items": [model_api._serialize_item(item) for item in room.items],
                "boxes": [],
                "connections": {direction: destination.name for direction, destination in room.connections.items()},
                "swim_exits": {direction: destination.name for direction, destination in room.swim_exits.items()},
                "hidden_directions": list(room.hidden_directions),
                "is_dark": room.is_dark,
                "has_water": room.has_water,
                "dark_description": room.dark_description,
                "discover_points": room.discover_points,
            }

            for box in room.boxes:
                room_payload["boxes"].append(model_api._serialize_box(box))

            payload["rooms"].append(room_payload)

        try:
            with target.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=4)
        except OSError as error:
            raise RuntimeError(f"Unable to write save file: {target} ({error})") from error

        return target

    def create_state_verbs(self):
        from kingdom.model.verb_model import Verb

        def save_action(path):
            self.save_game(path)
            return f"Game saved to {path}"

        def load_action(path):
            self.load_game(path)
            return f"Game loaded from {path}"

        return Verb("save", save_action), Verb("load", load_action)


# Backward-compatibility alias; remove after call sites fully migrate.
Game = World
