from __future__ import annotations

from dataclasses import dataclass, field, fields
from os import name
from typing import Any, Optional, List, Dict, ClassVar, Iterator
from kingdom.utilities import normalize_key
from kingdom.model.direction_model import DIRECTIONS

def _normalize_tokens(text: str) -> list[str]:
    return [token for token in str(text).strip().lower().split() if token]

def _derive_handle(text: str) -> str:
    tokens = _normalize_tokens(text)
    if not tokens:
        return ""
    articles = {"a", "an", "the"}
    if tokens[0] in articles and len(tokens) > 1:
        tokens = tokens[1:]
    return tokens[-1]

from dataclasses import MISSING, fields

class PersistRule:
    def __init__(self, field):
        self.name = field.name
        self.init = field.init
        self.rule = field.metadata.get("persist", "non_default")
        self.parent = field.metadata.get("persist_if_parent")

        # Correct handling of default_factory vs default
        if field.default_factory is not MISSING:
            # Create a fresh default value for comparison
            self.default = field.default_factory()
        else:
            self.default = field.default

    def should_serialize(self, obj, value):
        # Skip runtime-only fields
        if not self.init:
            return False

        # Parent-dependent persistence
        if self.parent:
            if getattr(obj, self.parent, False):
                return True

        # Explicit rules
        if self.rule == "always":
            return True

        if self.rule == "if_set":
            return value is not None

        # Default rule: non-default
        if value is None:
            return False

        if value == self.default:
            return False

        return True


def serialize_non_default(obj):
    payload = {}
    for f in fields(obj):
        rule = PersistRule(f)
        value = getattr(obj, f.name)
        if rule.should_serialize(obj, value):
            payload[f.name] = value
    return payload

@dataclass
class Exit:
    movement_type: str = field(metadata={"persist": False})
    direction: str = field(metadata={"persist": False})
    destination: "Room" = field(metadata={"persist": False})

    # Mutable state
    is_visible: bool = field(default=True, metadata={"persist": "non_default"})
    is_passable: bool = field(default=True, metadata={"persist": "non_default"})
    refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    go_refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})

    # Runtime-only (example)
    # temp_flag: bool = field(default=False, metadata={"persist": False})


    def set_existing(self, name, value):
        if not hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")
        setattr(self, name, value)



@dataclass(init=False)
class Noun:
    """Parent class for all game world entities (items, containers, rooms)."""

    all_nouns: ClassVar[List["Noun"]] = []
    _by_name: ClassVar[Dict[str, "Noun"]] = {}

    def __init__(self):
        self._register_noun()
    
    def __repr__(self):
        return f"Noun(canonical_name={self.canonical_name()}, display_name={self.display_name()}, obj_handle={self.obj_handle()})"

    def _register_noun(self) -> None:
        Noun.all_nouns.append(self)

        for key in self._registry_keys():
            Noun._by_name[key] = self

    def _registry_keys(self) -> list[str]:
        canonical_key = normalize_key(self.canonical_name())
        return [canonical_key] if canonical_key else []

    def _normalized_identity_tokens(self) -> list[str]:
        return [
            " ".join(_normalize_tokens(self.canonical_name())),
            " ".join(_normalize_tokens(self.display_name())),
            " ".join(_normalize_tokens(self.obj_handle())),
        ]
    

    def set_existing(self, name, value):
        if not hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")
        setattr(self, name, value)



    # ───────────────────────────────────────────────
    # Noun interface methods
    # ───────────────────────────────────────────────

    def canonical_name(self) -> str:
        return self.name

    def display_name(self) -> str:
        return self.description

    def obj_handle(self) -> str:
        return self.handle
    
    def synonym_names(self) -> list[str]:
        return self.synonyms  
    
    def stateful_name(self):
        # Start with the base description
        desc = self.description or self.display_name()

        # Lit/unlit
        if getattr(self, "is_lit", False) and getattr(self, "lit_state_description", None):
            desc = self.lit_state_description

        # Open/closed
        if getattr(self, "is_openable", False):
            if getattr(self, "is_open", False) and getattr(self, "opened_state_description", None):
                desc = self.opened_state_description
            elif not getattr(self, "is_open", False) and getattr(self, "closed_state_description", None):
                desc = self.closed_state_description

        # Locked/unlocked
        if getattr(self, "is_lockable", False):
            if getattr(self, "is_locked", False) and getattr(self, "locked_state_description", None):
                desc = self.locked_state_description
            elif not getattr(self, "is_locked", False) and getattr(self, "unlocked_state_description", None):
                desc = self.unlocked_state_description

        # Rubbed
        if getattr(self, "is_rubbed", False) and getattr(self, "rubbed_state_description", None):
            desc = self.rubbed_state_description

        # Tied/attached
        if getattr(self, "is_tied_to_description", None):
            desc = f"{desc}, {self.is_tied_to_description}"

        # Normalize (lowercase, remove trailing period)
        desc = desc.strip()
        if desc.endswith("."):
            desc = desc[:-1]
        desc = desc.lower()

        return desc


    @classmethod
    def get_by_name(cls, name: str) -> "Noun | None":
        candidate = normalize_key(name)
        if not candidate:
            return None

        noun = Noun._by_name.get(candidate)
        if noun is None:
            return None

        if cls is Noun or isinstance(noun, cls):
            return noun

        return None

    @classmethod
    def get_all(cls):
        for noun in cls._by_name.values():
            yield noun

    @classmethod
    def iter_by_type(cls, class_name: str) -> Iterator["Noun"]:
        target = str(class_name).strip().lower() if class_name else ""
        if not target:
            return
        for noun in cls._by_name.values():
            if noun.get_class_name().lower() == target:
                yield noun

    @classmethod
    def get_typed_by_name(cls, name: str, class_name: str) -> "Noun | None":
        candidate = normalize_key(name)
        if not candidate:
            return None

        typed_match = None
        for noun in cls.iter_by_type(class_name):
            if normalize_key(noun.canonical_name()) == candidate:
                typed_match = noun
                break

        if typed_match is not None:
            return typed_match

        return None

    @classmethod
    def get_class_name(cls) -> str :
        return cls.__name__


    def matches_reference(self, reference: str) -> bool:
        candidate = " ".join(_normalize_tokens(reference))
        if not candidate:
            return False

        return candidate in self._normalized_identity_tokens()

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in getattr(self, "behavior_handlers", []):
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return None

    @classmethod
    def by_name(cls, name: str, *, exact: bool = False) -> "Noun | None":
        candidate = " ".join(_normalize_tokens(name))
        if not candidate:
            return None

        direct = cls._by_name.get(candidate)
        if direct is not None:
            return direct

        for noun in cls.all_nouns:
            if exact:
                if " ".join(_normalize_tokens(noun.canonical_name())) == candidate:
                    return noun
            else:
                if noun.matches_reference(name):
                    return noun
        return None
    
    def set_existing(self, name, value):
        if not hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")
        setattr(self, name, value)



@dataclass
class Item(Noun):
    # ------------------------------------------------------------
    # Persistent fields (world-defined capabilities & properties)
    # ------------------------------------------------------------
    # These come from world JSON and do not change during gameplay.
    # Metadata controls how they appear in world JSON. Save files
    # always store the current value, regardless of metadata.

    # Identity & lexicon
    name: str = field(metadata={"persist": "always"})
    description: Optional[str] = field(default=None, metadata={"persist": "always"})
    handle: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    synonyms: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    adjectives: list[str] = field(default_factory=list, metadata={"persist": "non_default"})

    # Take interaction
    is_takeable: bool = field(default=True, metadata={"persist": "non_default"})
    take_refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})

    # Open/close mechanics
    is_openable: bool = field(default=False, metadata={"persist": "non_default"})
    is_open: bool = field(default=False, metadata={"persist": "non_default"})
    opened_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})
    closed_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})
    open_action_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})
    close_action_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})
    examine_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    open_exit_direction: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})
    open_exit_type: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_openable"})

    # Lock/unlock mechanics
    is_lockable: bool = field(default=False, metadata={"persist": "non_default", })
    is_locked: bool = field(default=False, metadata={"persist": "non_default", "persist_if_parent": "is_lockable"})
    unlock_key: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lockable"})
    locked_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lockable"})
    unlocked_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lockable"})
    unlockable_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lockable"})

    # Light/extinguish mechanics
    is_lightable: bool = field(default=False, metadata={"persist": "non_default"})
    is_lit: bool = field(default=False, metadata={"persist": "non_default"})
    lit_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lightable"})
    unlit_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_lightable"})
    can_ignite: bool = field(default=False, metadata={"persist": "non_default"})
    ignite_success_string: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "can_ignite"})
    is_flamable: bool = field(default=True, metadata={"persist": "non_default"})

    # Rub mechanics
    is_rubbable: bool = field(default=False, metadata={"persist": "non_default"})
    is_rubbed: bool = field(default=False, metadata={"persist": "non_default"})
    rubbed_state_description: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_rubbable"})
    rub_success_string: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_rubbable"})

    # Eating
    is_edible: bool = field(default=False, metadata={"persist": "non_default"})
    eat_refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_edible"})
    eaten_success_string: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "is_edible"})

    # Tieing
    is_tieable: bool = field(default=False, metadata={"persist": "non_default"})
    is_tied: bool = field(default=False, metadata={"persist": "non_default"})
    can_be_tied_to: bool = field(default=False, metadata={"persist": "non_default"})

    # Climbing
    is_climbable: bool = field(default=False, metadata={"persist": "non_default"})
    climb_directions: list[str] = field(default_factory=list, metadata={"persist": "non_default", "persist_if_parent": "is_climbable"})

    # Swimming
    too_heavy_to_swim: bool = field(default=False, metadata={"persist": "non_default"})

    # Speaking
    can_be_spoken_to: bool = field(default=False, metadata={"persist": "non_default"})
    speak_string: Optional[str] = field(default=None, metadata={"persist": "non_default", "persist_if_parent": "can_be_spoken_to"})

    # Visibility
    is_visible: bool = field(default=True, metadata={"persist": "non_default"}) 

    # Broken state
    is_broken: bool = field(default=False, metadata={"persist": "non_default"})

    # Special handling
    trigger_room: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    special_handlers: Dict[str, str] = field(default_factory=dict, metadata={"persist": "non_default"})


    # ------------------------------------------------------------
    # Runtime-only fields (never saved)
    # ------------------------------------------------------------
    # These are pointers or ephemeral state reconstructed automatically.
    current_container: "Container | None" = field(default=None, init=False)

    def __post_init__(self):
        self.description = self.description or self.name

        # Set parser handle: explicit → derived → fallback
        self.handle = normalize_key(self.handle or self.name)

        super().__init__()

        self.open_exit_direction = (
            str(self.open_exit_direction).strip().lower()
            if self.open_exit_direction is not None and str(self.open_exit_direction).strip()
            else None
        )
        self.open_exit_type = (
            str(self.open_exit_type).strip()
            if self.open_exit_type is not None and str(self.open_exit_type).strip()
            else None
        )

        self.unlock_key = (
            str(self.unlock_key).strip().lower()
            if self.unlock_key is not None and str(self.unlock_key).strip()
            else None
        )


        if self.special_handlers is None:
            self.special_handlers = {}
        else:
            self.special_handlers = dict(self.special_handlers)

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in getattr(self, "behavior_handlers", []):
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return super().handle_verb(verb_name, *args, **kwargs)

    def to_dict(self) -> dict:
        """
        Metadata-driven persistence with a couple of legacy compatibility rules.
        """
        payload = serialize_non_default(self)

        if not payload.get("special_handlers"):
            payload.pop("special_handlers", None)

        return payload

    @classmethod
    def _serialize_item(cls, item: "Item") -> dict:
        if hasattr(item, "to_dict"):
            return item.to_dict()

        return {
            "name": getattr(item, "name", str(item)),
            "handle": getattr(item, "obj_handle", lambda: _derive_handle(str(item)))(),
        }



@dataclass
class Container(Noun):
    """
    A container that can hold items, be opened/closed, locked, etc.
    """
    all_containers: ClassVar[List["Container"]] = []
    # Required by noun class
    name: str = field(metadata={"persist": "always"})
    description: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    handle: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    synonyms: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    adjectives: list[str] = field(default_factory=list, metadata={"persist": "non_default"})


    # Normal optional fields
    found: bool = False
    capacity: Optional[int] = None
    is_openable: bool = False
    is_flamable: bool = True
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
    open_exit_type: Optional[str] = None
    examine_string: Optional[str] = None
    
    # Visibility
    is_visible: bool = field(default=True, metadata={"persist": "non_default"})   

    # Runtime state – never saved
    contents: List["Item"] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.description = self.description or self.name
        self.handle = normalize_key(self.handle or self.name)

        super().__init__()
        Container.all_containers.append(self)

    # ───────────────────────────────────────────────
    # Item interface methods
    # ───────────────────────────────────────────────

    def add_item(self, item):
        if item is None:
            return

        if self.capacity is not None and len(self.contents) >= self.capacity:
            return(f"Cannot add {item.name} to {self.name} - capacity reached)")

        self.contents.append(item)
        item.current_container = self

        return
    
    def all_items(self) -> list["Item"]:
        return list(self.contents)

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



@dataclass
class Player:
    """A player character who can collect items in their sack (max 10 items)."""

    name: str
    sack: Container = field(init=False)

    def __post_init__(self):
        self.name = str(self.name)
        self.sack = Container(
            name="inventory",
            description=f"{self.name}'s sack",
            capacity=10,
        )

    def display_name(self) -> str:
        return self.name

    def add_to_sack(self, item):
        return self.sack.add_item(item)
    
    def take_item_from_room(self, item, room):
        msg = self.sack.add_item(item)
        if msg: return msg
        room.remove_item(item)

    def drop_item_to_room(self, item, room):
        self.sack.remove_item(item)
        room.add_item(item)

    def put_item_into_container(self, item, container):
        msg = container.add_item(item)
        if msg: return msg
        self.sack.remove_item(item)

    def take_item_from_container(self, item, container):
        msg = self.sack.add_item(item)
        if msg: return msg
        container.remove_item(item)

    def remove_from_sack(self, item):
        return self.sack.remove_item(item)

    def has_item(self, item) -> bool:
        return self.sack.has_item(item)

    def get_inventory_items(self):
        return list(self.sack.contents)


@dataclass
class Room(Noun):

    # --- Persistent fields (from JSON) ---
    name: str = field(metadata={"persist": "always"})
    description: str = field(default="", metadata={"persist": "always"})
    handle: str = field(default=None, metadata={"persist": "non_default"})
    synonyms: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    adjectives: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    found: bool = field(default=False, metadata={"persist": "non_default"})
    is_dark: bool = field(default=False, metadata={"persist": "non_default"})
    dark_description: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    discover_points: int = field(default=10, metadata={"persist": "non_default"})
    has_water: bool = field(default=False, metadata={"persist": "non_default"})

    # Refuse strings for blocked exits
    refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    go_refuse_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})
 

    # --- Runtime-constructed fields (not in JSON) ---
    items: List["Item"] = field(default_factory=list, init=False)
    containers: List["Container"] = field(default_factory=list, init=False)
    features: List["Feature"] = field(default_factory=list, init=False)
    exits: Dict[str, Dict[str, Exit]] = field(default_factory=lambda: {"go": {}, "swim": {}, "climb": {}})


    def __post_init__(self):
        self.handle = normalize_key(self.handle or self.name)
        super().__init__()

    def __repr__(self):
        items_str = [it.name for it in self.items if it is not None]
        containers_str = [c.display_name() for c in self.containers]
        features_str = [f.display_name() for f in self.features]
        exits = [{mtype: list(exits.keys()) for mtype, exits in self.exits.items()}]
        return (
            f"Room({self.name}, desc='{self.description}', found={self.found}, is_dark={self.is_dark}, has_water={self.has_water}, items={items_str}, "
            f"containers={containers_str}, features={features_str}, exits={exits})"
        )

    def add_item(self, item):
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")

    def add_container(self, container):
        if not isinstance(container, Container):
            raise TypeError("Room.add_container expects a Container instance")
        self.containers.append(container)

    def add_feature(self, feature):
        if not isinstance(feature, Feature):
            raise TypeError("Room.add_feature expects a Feature instance")
        self.features.append(feature)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)

    def remove_container(self, container):
        if container in self.containers:
            self.containers.remove(container)
            return True

    def remove_feature(self, feature):
        if feature in self.features:
            self.features.remove(feature)

    def has_item(self, item) -> bool:
        return item in self.items
    
    def all_items(self) -> list["Item"]:
        all_items = list(self.items)
        return list(all_items)
    
    def has_container(self, container) -> bool:
        return container in self.containers

    def has_feature(self, feature) -> bool:
        return feature in self.features

    def find_containing_container(self, item) -> "Container | None":
        for container in self.containers:
            if item in container.contents:
                return container
        return None


# ---------- connection functions ------------------------

    def normalize_direction(self, direction):
        
        if not isinstance(direction, str):
            raise TypeError("direction must be a string")
        if direction == "":
            raise ValueError("direction cannot be empty")

        direction = direction.lower()

        # Ask the global direction registry for canonical form
        canonical =  DIRECTIONS.get_canonical(direction)

        if canonical is None:
            raise ValueError(f"Unknown direction '{direction}' in room '{self.name}'")
        return canonical

    def add_exit(
        self,
        movement_type,
        direction,
        destination=None,
        **overrides
    ):
        canonical = self.normalize_direction(direction)

        # Ensure movement type exists
        if movement_type not in self.exits:
            self.exits[movement_type] = {}

        # Build Exit with defaults
        exit_obj = Exit(
            movement_type=movement_type,
            direction=canonical,
            destination=destination
        )

        # Apply overrides safely
        for key, value in overrides.items():
            if hasattr(exit_obj, key):
                setattr(exit_obj, key, value)
            else:
                raise AttributeError(f"Unknown Exit attribute '{key}'")

        # Store it
        self.exits[movement_type][canonical] = exit_obj

        return exit_obj
    

    def get_exit(self, movement_type, direction) -> Optional[Exit]:
    
        return self.exits.get(movement_type, {}).get(direction)

    def get_all_exits(
        self,
        movement_type="all",
        visible_only=False,
        passable_only=False
    ) -> list[tuple[str, str, Exit] | tuple[str, Exit]]:

        # Validate movement_type
        if movement_type != "all" and movement_type not in self.exits:
            raise ValueError(f"Unknown movement type '{movement_type}' in room '{self.name}'")

        def include(exit_obj):
            if visible_only and not exit_obj.is_visible:
                return False
            if passable_only and not exit_obj.is_passable:
                return False
            return True

        # Collect exits across all movement types
        if movement_type == "all":
            all_exits = []
            for mtype, exits in self.exits.items():
                for direction, exit_obj in exits.items():
                    if include(exit_obj):
                        all_exits.append((mtype, direction, exit_obj))
            return all_exits

        # Single movement type
        exits = self.exits.get(movement_type, {})
        return [
            (direction, exit_obj)
            for direction, exit_obj in exits.items()
            if include(exit_obj)
        ]


# ---------------- end of connection functions -------------

    def has_lit_is_lightable(self) -> bool:
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

        # Remove empty persistent collections
        if not self.synonyms:
            payload.pop("synonyms", None)
        if not self.adjectives:
            payload.pop("adjectives", None)

        # Runtime collections
        if self.items:
            payload["items"] = [Item._serialize_item(item) for item in self.items]

        if self.containers:
            payload["containers"] = [c._serialize_container() for c in self.containers]

        if self.features:
            payload["features"] = [f.to_dict() for f in self.features]

        # Unified exits
        if any(self.exits[m] for m in self.exits):
            payload["exits"] = {}

            for movement_type, exits in self.exits.items():
                if not exits:
                    continue

                payload["exits"][movement_type] = {}

                for direction, exit_obj in exits.items():
                    entry = {
                        "destination": exit_obj.destination.name if exit_obj.destination else None,
                    }
                    if not exit_obj.is_visible:
                        entry["is_visible"] = False
                    if not exit_obj.is_passable:
                        entry["is_passable"] = False

                    if exit_obj.refuse_string is not None:
                        entry["refuse_string"] = exit_obj.refuse_string

                    if exit_obj.go_refuse_string is not None:
                        entry["go_refuse_string"] = exit_obj.go_refuse_string

                    payload["exits"][movement_type][direction] = entry

        return payload




@dataclass
class Feature(Noun):
    name: str = field(metadata={"persist": "always"})
    description: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    handle: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    examine_string: Optional[str] = field(default=None, metadata={"persist": "non_default"})
    synonyms: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    adjectives: list[str] = field(default_factory=list, metadata={"persist": "non_default"})
    found: bool = field(default=False, metadata={"persist": "non_default"})

    def __post_init__(self):
        self.name = str(self.name)
        self.description = self.description or self.name
        self.handle = normalize_key(self.handle or self.name)

        # Accept set/tuple inputs from tests or tooling, but keep persisted payload JSON-safe.
        if isinstance(self.synonyms, set):
            self.synonyms = sorted(str(value) for value in self.synonyms)
        elif self.synonyms is None:
            self.synonyms = []
        elif not isinstance(self.synonyms, list):
            self.synonyms = [str(value) for value in self.synonyms]

        if isinstance(self.adjectives, set):
            self.adjectives = sorted(str(value) for value in self.adjectives)
        elif self.adjectives is None:
            self.adjectives = []
        elif not isinstance(self.adjectives, list):
            self.adjectives = [str(value) for value in self.adjectives]

        super().__init__()

    def _normalized_identity_tokens(self) -> set[str]:
        return super()._normalized_identity_tokens() | set(self.synonyms)

    def to_dict(self) -> dict:
        payload = serialize_non_default(self)
        return payload



@dataclass
class World:
    _instance: ClassVar["World | None"] = None

    name: str = field(default="World")
    description: str = field(default="The game world.")
    containers: list = field(default_factory=list)
    rooms: dict | list = field(default_factory=dict)
    start_room_name: Optional[str] = None
    start_room: "Room | None" = None


    def __post_init__(self):
        World._instance = self

    def __repr__(self):
        return (
            f"World(\n"
            f"  rooms={list(self.rooms.keys())},\n"
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


    def find_item_in_game(self, name: str) -> tuple["Room | None", "Item | None"]:
        for room in self.rooms.values():
            for item in room.items:
                if getattr(item, "name", None) == name:
                    return room, item
        return None, None

    def move_item_between_rooms(self, item: "Item", from_room: "Room", to_room: "Room") -> None:
        if item in from_room.items:
            from_room.items.remove(item)

        if item not in to_room.items:
            to_room.items.append(item)


