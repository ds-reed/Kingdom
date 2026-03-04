from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field, fields
from typing import Any, Optional, List, Dict, ClassVar



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
    """Parent class for all game world entities (items, containers, rooms)."""

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


def _load_directions(json_data):
    directions = json_data.get("directions", {})
    for canonical, info in directions.items():
        DIRECTIONS.register(
            canonical,
            synonyms=info.get("aliases", []),
            reverse=info.get("reverse"),
        )


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


@dataclass
class Item(Noun):
    all_items: ClassVar[List["Item"]] = []
    _by_name: ClassVar[Dict[str, "Item"]] = {}

    name: str = field(metadata={"persist": "always"})
    is_gettable: bool = True
    refuse_string: Optional[str] = field(default=None, metadata={"persist": "if_set"})
    presence_string: Optional[str] = field(default=None, metadata={"persist": "if_set"})
    noun_name: Optional[str] = field(default=None, metadata={"persist": "always"})
    is_openable: bool = False
    is_open: bool = field(default=False, metadata={"persist_if_parent": "is_openable"})
    opened_state_description: Optional[str] = None
    closed_state_description: Optional[str] = None
    lit_state_description: Optional[str] = None
    unlit_state_description: Optional[str] = None
    open_action_description: Optional[str] = None
    close_action_description: Optional[str] = None
    examine_string: Optional[str] = None
    open_exit_direction: Optional[str] = None
    open_exit_destination: Optional[str] = None
    is_lockable: bool = False
    is_locked: bool = field(default=False, metadata={"persist_if_parent": "is_lockable"})
    unlock_key: Optional[str] = None
    locked_state_description: Optional[str] = None
    unlocked_state_description: Optional[str] = None
    unlockable_description: Optional[str] = None
    is_edible: bool = False
    is_verbally_interactive: bool = False
    is_lightable: bool = False
    is_lit: bool = field(default=False, metadata={"persist_if_parent": "is_lightable"})
    can_ignite: bool = False
    ignite_success_string: Optional[str] = None
    is_rubbable: bool = False
    is_rubbed: bool = False
    rubbed_state_description: Optional[str] = None
    rub_success_string: Optional[str] = None
    trigger_room: Optional[str] = None
    too_heavy_to_swim: bool = False
    eat_refuse_string: Optional[str] = None
    eaten_success_string: Optional[str] = None
    get_refuse_string: Optional[str] = None
    special_handlers: Dict[str, str] = field(default_factory=dict, metadata={"persist": "if_set"})

    # Runtime fields
    current_container: "Container | None" = field(default=None, init=False)
    is_broken: bool = field(default=False, init=False)
    descriptive_phrase: str = field(default="", init=False)

    def __post_init__(self):
        super().__init__()

        self.name = str(self.name).strip()
        self.descriptive_phrase = self.name
        self.noun_name = str(self.noun_name).strip().lower() if self.noun_name else _derive_noun_name(self.name)

        searchkey = self.noun_name.lower()
        if searchkey in Item._by_name:
            print(f"Warning: duplicate item name '{searchkey}' - overwriting previous")
        Item._by_name[searchkey] = self

        self.is_gettable = bool(self.is_gettable)
        self.refuse_string = self.refuse_string or f"You can't pick up {self.name}"
        self.is_openable = bool(self.is_openable)
        self.is_open = bool(self.is_open)

        self.open_exit_direction = (
            str(self.open_exit_direction).strip().lower()
            if self.open_exit_direction is not None and str(self.open_exit_direction).strip()
            else None
        )
        self.open_exit_destination = (
            str(self.open_exit_destination).strip()
            if self.open_exit_destination is not None and str(self.open_exit_destination).strip()
            else None
        )

        self.is_lockable = bool(self.is_lockable)
        self.is_locked = bool(self.is_locked)
        self.unlock_key = (
            str(self.unlock_key).strip().lower()
            if self.unlock_key is not None and str(self.unlock_key).strip()
            else None
        )

        self.is_edible = bool(self.is_edible)
        self.is_verbally_interactive = bool(self.is_verbally_interactive)
        self.is_lightable = bool(self.is_lightable)
        self.is_lit = bool(self.is_lit)
        self.can_ignite = bool(self.can_ignite)
        self.is_rubbable = bool(self.is_rubbable)
        self.is_rubbed = bool(self.is_rubbed)
        self.trigger_room = str(self.trigger_room).strip() if self.trigger_room is not None and str(self.trigger_room).strip() else None
        self.too_heavy_to_swim = bool(self.too_heavy_to_swim)

        if self.special_handlers is None:
            self.special_handlers = {}
        else:
            self.special_handlers = dict(self.special_handlers)

        Item.all_items.append(self)

    @classmethod
    def get_by_name(cls, name: str) -> "Item | None":
        if not name:
            return None
        key = str(name).strip().lower()
        return cls._by_name.get(key)

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


    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        if verb_name == "take" and not self.is_gettable:
            return False, self.refuse_string
        if verb_name == "eat":
            return True, None
        return super().can_handle_verb(verb_name, *args, **kwargs)

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in getattr(self, "behavior_handlers", []):
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return super().handle_verb(verb_name, *args, **kwargs)

    def canonical_name(self):
        return getattr(self, "noun_name", None) or self.name

    def display_name(self):
        return self.name

    def to_dict(self) -> dict:
        """
        Metadata-driven persistence with a couple of legacy compatibility rules.
        """
        payload = serialize_non_default(self)

        default_refusal = f"You can't pick up {self.name}"
        if payload.get("refuse_string") == default_refusal:
            payload.pop("refuse_string", None)

        if payload.get("get_refuse_string") == default_refusal:
            payload.pop("get_refuse_string", None)

        if not payload.get("special_handlers"):
            payload.pop("special_handlers", None)

        return payload

    @classmethod
    def _serialize_item(cls, item: "Item") -> dict:
        if hasattr(item, "to_dict"):
            return item.to_dict()

        return {
            "name": getattr(item, "name", str(item)),
            "noun_name": getattr(item, "get_noun_name", lambda: str(item))(),
        }

  

def serialize_non_default(obj: Any) -> dict:
    """
    Serialize dataclass fields according to persistence rules.
    - Skips runtime fields (init=False)
    - Uses metadata: "always", "if_set", "persist_if_parent", default=non_default
    """
    payload = {}
    for f in fields(obj):
        if f.init is False:
            continue

        value = getattr(obj, f.name)
        persist_rule = f.metadata.get("persist", "non_default")
        parent_field = f.metadata.get("persist_if_parent")

        # Save if parent is True (even if value == default)
        if parent_field:
            parent_value = getattr(obj, parent_field, False)
            if parent_value is True:
                payload[f.name] = value
                continue

        if persist_rule == "always":
            payload[f.name] = value
            continue

        if persist_rule == "if_set":
            if value is not None:
                payload[f.name] = value
            continue

        # Default: omit None / False / default value
        if value is None:
            continue
        if isinstance(value, bool) and not value:
            continue
        if value == f.default:
            continue

        payload[f.name] = value

    return payload


@dataclass
class Container(Noun):
    """
    A container that can hold items, be opened/closed, locked, etc.
    """
    all_containers: ClassVar[List["Container"]] = []
    _by_name: ClassVar[Dict[str, "Container"]] = {}

    # Required: what the player sees / reads in text
    name: str = field(metadata={"persist": "always"})

    # Optional override: parser/search key (stable, lowercase)
    # Auto-derived from name if missing
    handle: Optional[str] = field(default=None, metadata={"persist": "if_set"})

    # Legacy field (preserved but unused; will be removed later)
    noun_name: str = field(init=False)

    # Optional long text for examine/look
    description: Optional[str] = field(default=None, metadata={"persist": "if_set"})

    # Normal optional fields
    capacity: Optional[int] = None
    is_openable: bool = False
    is_open: bool = field(default=False, metadata={"persist_if_parent": "is_openable"})
    opened_state_description: Optional[str] = None
    closed_state_description: Optional[str] = None
    open_action_description: Optional[str] = None
    close_action_description: Optional[str] = None
    is_lockable: bool = False
    is_locked: bool = field(default=False, metadata={"persist_if_parent": "is_lockable"})
    unlock_key: Optional[str] = None
    locked_description: Optional[str] = None
    open_exit_direction: Optional[str] = None
    open_exit_destination: Optional[str] = None
    examine_string: Optional[str] = None  

    # Runtime state – never saved
    contents: List["Item"] = field(default_factory=list, init=False)

    def __post_init__(self):
        super().__init__()

        # Legacy support (remove later)
        self.noun_name = self.name

        # Set parser handle: explicit → derived → fallback
        self.handle = (
            self.handle
            or _derive_noun_name(self.name)
            or self.name.lower()
        )

        # Register using parser-friendly handle (lowercased)
        searchkey = self.handle.lower()
        if searchkey in Container._by_name:
            print(f"Warning: duplicate handle '{searchkey}' — overwriting previous")
        Container._by_name[searchkey] = self
        Container.all_containers.append(self)

    # ───────────────────────────────────────────────
    # Noun interface methods
    # ───────────────────────────────────────────────

    def get_name(self) -> str:
        """Legacy - will be removed in favor of canonical_name"""
        return self.name

    def display_name(self) -> str:
        """What the player sees in text / inventory"""
        return self.description or self.name

    def canonical_name(self) -> str:
        """Stable parser / lookup key"""
        return self.handle
    
    # ───────────────────────────────────────────────
    # Item interface methods
    # ───────────────────────────────────────────────

    def add_item(self, item):
        if item is None:
            print("ERROR: add_item received None")
            return

        if self.capacity is not None and len(self.contents) >= self.capacity:
            print(f"ERROR: Cannot add {item.name} to {self.name} - capacity reached")
            return

        if item.current_container == self:
            print(f"ERROR: {item.name} is already in {self.name}")
            return

        if item.current_container is not None:
            item.current_container.contents.remove(item)

        self.contents.append(item)
        item.current_container = self

        return

    def has_item(self, item) -> bool:
        return item in self.contents

    def remove_item(self, item):
        if item in self.contents:
            self.contents.remove(item)
            item.current_container = None
            return
        
    # ───────────────────────────────────────────────
    # Serialization
    # ───────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Convert to dict for saving.
        Fully automatic + one special case for contents → items.
        """
        payload = serialize_non_default(self)

        if self.contents:
            serialized_items = []
            for item in self.contents:
                if hasattr(item, "to_dict"):
                    serialized_items.append(item.to_dict())
                else:
                    serialized_items.append(Item._serialize_item(item))
            payload["items"] = serialized_items


        return payload
    
    def _serialize_container(self) -> dict:
        return self.to_dict()



class Player:
    """A player character who can collect items in their sack (max 10 items)."""

    def __init__(self, name):
        self.name = name
        self.sack = Container(
            name="inventory",
            description=f"{name}'s sack",
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


@dataclass
class Room(Noun):
    all_rooms: ClassVar[List["Room"]] = []
    DIRECTIONS: ClassVar[list[str] | set[str]] = []
    _by_name: ClassVar[Dict[str, "Room"]] = {}

    name: str = field(metadata={"persist": "always"})
    description: str = field(default="", metadata={"persist": "always"})
    visited: bool = False
    is_dark: bool = False
    has_water: bool = False
    dark_description: Optional[str] = None
    discover_points: int = 10

    swim_exits: Dict[str, "Room"] = field(default_factory=dict, init=False)
    items: List["Item"] = field(default_factory=list, init=False)
    containers: List["Container"] = field(default_factory=list, init=False)
    connections: Dict[str, "Room"] = field(default_factory=dict, init=False)
    hidden_directions: set[str] = field(default_factory=set, init=False)

    def __post_init__(self):
        super().__init__()

        self.name = str(self.name)
        self.description = str(self.description)
        self.visited = bool(self.visited)
        self.is_dark = bool(self.is_dark)
        self.has_water = bool(self.has_water)
        self.dark_description = self.dark_description or None
        self.discover_points = max(0, int(self.discover_points))

        searchkey = self.name.lower()
        if searchkey in Room._by_name:
            print(f"Warning: duplicate room name '{searchkey}' — overwriting previous")
        Room._by_name[searchkey] = self
        Room.all_rooms.append(self)

    def __repr__(self):
        items_str = [it.name for it in self.items if it is not None]
        containers_str = [c.display_name() for c in self.containers]
        connections_str = {direction: room.name for direction, room in self.connections.items()}
        return (
            f"Room({self.name}, desc='{self.description}', visited={self.visited}, is_dark={self.is_dark}, has_water={self.has_water}, items={items_str}, "
            f"containers={containers_str}, connections={connections_str}, hidden_directions={sorted(self.hidden_directions)})"
        )

    def add_item(self, item) -> bool:
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")
        return True

    def add_container(self, container) -> bool:
        if not isinstance(container, Container):
            raise TypeError("Room.add_container expects a Container instance")
        self.containers.append(container)
        return True

    def remove_item(self, item) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def remove_container(self, container) -> bool:
        if container in self.containers:
            self.containers.remove(container)
            return True
        return False

    def has_item(self, item) -> bool:
        return item in self.items

    def has_container(self, container) -> bool:
        return container in self.containers

    def find_containing_container(self, item) -> "Container | None":
        for container in self.containers:
            if item in container.contents:
                return container
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

    def available_directions(self, visible_only=False):
        directions = sorted(self.connections.keys())
        if not visible_only:
            return directions
        return [direction for direction in directions if direction not in self.hidden_directions]

    def has_lit_is_lightable(self):
        for item in self.items:
            if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                return True

        for container in self.containers:
            if container.is_openable and not container.is_open:
                continue
            for item in container.contents:
                if getattr(item, "is_lightable", False) and getattr(item, "is_lit", False):
                    return True

        return False

    def to_dict(self) -> dict:
        payload = serialize_non_default(self)

        payload.setdefault("name", self.name)
        payload.setdefault("description", self.description)
        payload["visited"] = bool(self.visited)
        payload["is_dark"] = bool(self.is_dark)
        payload["has_water"] = bool(self.has_water)
        payload["dark_description"] = self.dark_description
        payload["discover_points"] = int(self.discover_points)

        payload["items"] = [Item._serialize_item(item) for item in self.items]
        payload["Container"] = [container._serialize_container() for container in self.containers]
        payload["connections"] = {
            direction: destination.name
            for direction, destination in self.connections.items()
        }
        payload["swim_exits"] = {
            direction: destination.name if hasattr(destination, "name") else str(destination)
            for direction, destination in self.swim_exits.items()
        }
        payload["hidden_directions"] = list(self.hidden_directions)

        return payload

    def _serialize_room(self) -> dict:
        return self.to_dict()

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
        self.containers = []
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

    def set_world(self, containers, rooms):
        self.containers = containers
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

        # Clear all registries
        Room.all_rooms.clear()
        Container.all_containers.clear()      
        Item.all_items.clear()
        Noun.all_nouns.clear()

        # Reset lookup dictionaries
        Room._by_name = {}
        Container._by_name = {}                     #
        Item._by_name = {}


        from . import game_init as model_api

        _load_directions(data)
        DirectionNoun.ensure_direction_nouns()

        Room.DIRECTIONS = DIRECTIONS.canonical

        if isinstance(data, dict):
            containers = model_api._construct_containers(data.get("Container", []))   
            rooms = model_api._construct_rooms(data.get("rooms", []))
        else:
            containers = []
            rooms = []

        # Pass containers to set_world
        self.set_world(containers, rooms)
        self.rooms = {room.name: room for room in rooms}
        start_room_name = data.get("start_room")
        self.start_room_name = start_room_name

        return containers, self.rooms
    

# Backward-compatibility alias; remove after call sites fully migrate.
Game = World
