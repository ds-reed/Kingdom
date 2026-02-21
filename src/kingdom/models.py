import json
import inspect
from pathlib import Path
from typing import Iterable

from kingdom.item_behaviors import get_default_item_behavior_ids, resolve_item_behaviors


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


def _serialize_item(item: "Item") -> dict:
    payload = {
        "name": item.name,
        "noun_name": item.get_noun_name(),
    }

    if not item.pickupable:
        payload["pickupable"] = False

    default_refusal = f"You can't pick up {item.name}"
    if item.refuse_string and item.refuse_string != default_refusal:
        payload["refuse_string"] = item.refuse_string

    if item.presence_string:
        payload["presence_string"] = item.presence_string

    if getattr(item, "openable", False):
        payload["openable"] = True

    if getattr(item, "is_open", False):
        payload["is_open"] = True

    if getattr(item, "open_description", None):
        payload["open_description"] = item.open_description

    if getattr(item, "closed_description", None):
        payload["closed_description"] = item.closed_description

    if getattr(item, "open_exit_direction", None):
        payload["open_exit_direction"] = item.open_exit_direction

    if getattr(item, "open_exit_destination", None):
        payload["open_exit_destination"] = item.open_exit_destination

    if getattr(item, "close_hides_exit", False):
        payload["close_hides_exit"] = True

    if getattr(item, "lockable", False):
        payload["lockable"] = True

    if getattr(item, "is_locked", False):
        payload["is_locked"] = True

    if getattr(item, "unlock_key", None):
        payload["unlock_key"] = item.unlock_key

    if getattr(item, "locked_description", None):
        payload["locked_description"] = item.locked_description

    if getattr(item, "edible", False):
        payload["edible"] = True

    if getattr(item, "light_source", False):
        payload["light_source"] = True

    if getattr(item, "is_lit", False):
        payload["is_lit"] = True

    if getattr(item, "eat_refuse_string", None):
        payload["eat_refuse_string"] = item.eat_refuse_string

    if getattr(item, "eat_success_string", None):
        payload["eat_success_string"] = item.eat_success_string

    if getattr(item, "eat_missing_string", None):
        payload["eat_missing_string"] = item.eat_missing_string

    behavior_ids = getattr(item, "explicit_behavior_ids", None)
    if behavior_ids:
        payload["behaviors"] = list(behavior_ids)

    return payload


def _serialize_box(box: "Box") -> dict:
    payload = {
        "box_name": box.box_name,
        "items": [_serialize_item(item) for item in box.contents],
    }

    if box.presence_string:
        payload["presence_string"] = box.presence_string

    if getattr(box, "openable", False):
        payload["openable"] = True

    if getattr(box, "is_open", False):
        payload["is_open"] = True

    if getattr(box, "open_description", None):
        payload["open_description"] = box.open_description

    if getattr(box, "closed_description", None):
        payload["closed_description"] = box.closed_description

    if getattr(box, "lockable", False):
        payload["lockable"] = True

    if getattr(box, "is_locked", False):
        payload["is_locked"] = True

    if getattr(box, "unlock_key", None):
        payload["unlock_key"] = box.unlock_key

    if getattr(box, "locked_description", None):
        payload["locked_description"] = box.locked_description

    return payload


def _construct_item_from_spec(item_spec) -> "Item":
    if isinstance(item_spec, str):
        return Item(item_spec)

    refuse_string = item_spec.get("refuse_string")
    if refuse_string is None:
        refuse_string = item_spec.get("refusal_string")

    presence_string = item_spec.get("presence_string")
    if presence_string is None:
        presence_string = item_spec.get("presence")

    return Item(
        item_spec.get("name"),
        pickupable=item_spec.get("pickupable", True),
        refuse_string=refuse_string,
        presence_string=presence_string,
        noun_name=item_spec.get("noun_name"),
        openable=item_spec.get("openable", False),
        is_open=item_spec.get("is_open", False),
        open_description=item_spec.get("open_description"),
        closed_description=item_spec.get("closed_description"),
        open_exit_direction=item_spec.get("open_exit_direction"),
        open_exit_destination=item_spec.get("open_exit_destination"),
        close_hides_exit=item_spec.get("close_hides_exit", False),
        lockable=item_spec.get("lockable", False),
        is_locked=item_spec.get("is_locked", False),
        unlock_key=item_spec.get("unlock_key"),
        locked_description=item_spec.get("locked_description"),
        edible=item_spec.get("edible", False),
        light_source=item_spec.get("light_source", False),
        is_lit=item_spec.get("is_lit", False),
        eat_refuse_string=item_spec.get("eat_refuse_string"),
        eat_success_string=item_spec.get("eat_success_string"),
        eat_missing_string=item_spec.get("eat_missing_string"),
        behavior_ids=item_spec.get("behaviors") or item_spec.get("behavior_ids"),
    )

DIRECTION_ALIASES = {
    "north": ("n",),
    "south": ("s",),
    "east": ("e",),
    "west": ("w",),
    "up": ("u", "above"),
    "down": ("d", "below"),
}

_DIRECTION_NOUNS_BY_REFERENCE: dict[str, "DirectionNoun"] = {}
_DIRECTION_NOUNS_BY_CANONICAL: dict[str, list["DirectionNoun"]] = {}


class Noun:
    """Parent class for all game world entities (items, boxes, rooms)."""
    all_nouns = []  # Class variable to track every noun created

    def __init__(self):
        Noun.all_nouns.append(self)

    def get_name(self):
        """Return the name of this noun."""
        return self.name

    def get_noun_name(self):
        """Return the short handle name for this noun (e.g., 'carrot')."""
        noun_name = getattr(self, "noun_name", None)
        if noun_name:
            return str(noun_name)
        return _derive_noun_name(self.get_name())

    def get_descriptive_phrase(self):
        """Return the longer descriptive phrase for this noun."""
        phrase = getattr(self, "descriptive_phrase", None)
        if phrase:
            return str(phrase)
        return self.get_name()

    def matches_reference(self, reference: str) -> bool:
        """Return True if input text refers to this noun by phrase or handle name."""
        candidate = " ".join(_normalize_tokens(reference))
        if not candidate:
            return False

        descriptive = " ".join(_normalize_tokens(self.get_descriptive_phrase()))
        noun_name = " ".join(_normalize_tokens(self.get_noun_name()))
        return candidate in {descriptive, noun_name}

    def get_presence_text(self):
        """Default sentence used when this noun is noticed in a room."""
        return f"There is {self.name} here."

    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        """Return whether this noun allows handling the given verb.

        Default behavior allows all verbs and provides no refusal text.
        """
        return True, None

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        """Optionally handle a verb directly on this noun.

        Return a string when handled; return None to fall back to verb action.
        """
        return None

class Verb(Noun):
    """A verb paired with an action function.
    
    Verbs are used to define actions that can be performed in the game.
    Each verb has a name and an associated callable that implements the action.
    """
    all_verbs = []  # Class variable to track every verb created

    def __init__(self, verb, action, synonyms: Iterable[str] | None = None, hidden: bool = False):
        """Initialize a Verb.
        
        Args:
            verb: The verb name (e.g., 'take', 'drop', 'examine')
            action: A callable that performs the action
            synonyms: Optional list of alternate verb spellings/phrases
            hidden: If True, omit this verb from help/listing output
        """
        super().__init__()
        normalized_verb = str(verb).strip().lower()
        self.name = normalized_verb  # Noun uses 'name'
        self.verb = normalized_verb
        self.action = action
        self._accepts_target = self._detect_target_support(action)
        self._accepts_dispatch_context = self._detect_dispatch_context_support(action)
        self.hidden = bool(hidden)
        self.synonyms = tuple(
            sorted(
                {
                    normalized
                    for synonym in (synonyms or [])
                    if (normalized := str(synonym).strip().lower()) and normalized != normalized_verb
                }
            )
        )
        Verb.all_verbs.append(self)    

    @staticmethod
    def _detect_target_support(action) -> bool:
        try:
            signature = inspect.signature(action)
        except (TypeError, ValueError):
            return False

        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                return True
            if parameter.name == "target":
                return True
        return False

    @staticmethod
    def _detect_dispatch_context_support(action) -> bool:
        try:
            signature = inspect.signature(action)
        except (TypeError, ValueError):
            return False

        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                return True
            if parameter.name == "dispatch_context":
                return True
        return False

    def all_names(self):
        return (self.verb, *self.synonyms)
    
    def execute(self, *args, target=None, dispatch_context: dict | None = None, **kwargs):
        """Execute this verb with optional noun double-dispatch."""
        if target is not None:
            can_handle, refusal_message = target.can_handle_verb(
                self.verb,
                *args,
                dispatch_context=dispatch_context,
            )
            if not can_handle:
                return refusal_message or f"You can't {self.verb} that."

            handled_result = target.handle_verb(
                self.verb,
                *args,
                dispatch_context=dispatch_context,
            )
            if handled_result is not None:
                return handled_result

        if not callable(self.action):
            raise TypeError(f"Action for verb '{self.verb}' is not callable")

        if target is not None and self._accepts_target:
            kwargs = dict(kwargs)
            kwargs["target"] = target

        if dispatch_context is not None and self._accepts_dispatch_context:
            kwargs = dict(kwargs)
            kwargs["dispatch_context"] = dispatch_context

        return self.action(*args, **kwargs)
    
    def __repr__(self):
        if self.synonyms:
            return f"Verb({self.verb}, synonyms={list(self.synonyms)})"
        return f"Verb({self.verb})"


class DirectionNoun(Noun):
    """Noun representation of a direction token (e.g., north, n)."""

    def __init__(self, reference_name: str, canonical_direction: str):
        super().__init__()
        self.name = reference_name
        self.noun_name = reference_name
        self.descriptive_phrase = canonical_direction
        self.canonical_direction = canonical_direction

    def matches_reference(self, reference: str) -> bool:
        candidate = " ".join(_normalize_tokens(reference))
        if not candidate:
            return False
        return candidate in {self.name, self.noun_name, self.canonical_direction}

    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        if verb_name != "":
            return super().can_handle_verb(verb_name, *args, **kwargs)

        dispatch_context = kwargs.get("dispatch_context") or {}
        state = dispatch_context.get("state")
        current_room = getattr(state, "current_room", None)
        if current_room is None:
            return False, "There is nowhere to go."

        if self.canonical_direction not in current_room.available_directions():
            return False, f"You can't go {self.canonical_direction} from here."

        return True, None

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        if verb_name != "":
            return super().handle_verb(verb_name, *args, **kwargs)

        dispatch_context = kwargs.get("dispatch_context") or {}
        move_direction = dispatch_context.get("move_direction")
        if callable(move_direction):
            return move_direction(self.canonical_direction)
        return None


def ensure_direction_nouns() -> dict[str, DirectionNoun]:
    """Create direction nouns once and return reference-token lookup."""
    if _DIRECTION_NOUNS_BY_REFERENCE:
        return _DIRECTION_NOUNS_BY_REFERENCE

    for canonical, aliases in DIRECTION_ALIASES.items():
        _DIRECTION_NOUNS_BY_CANONICAL[canonical] = []
        for reference_name in (canonical, *aliases):
            direction_noun = DirectionNoun(reference_name, canonical)
            _DIRECTION_NOUNS_BY_REFERENCE[reference_name] = direction_noun
            _DIRECTION_NOUNS_BY_CANONICAL[canonical].append(direction_noun)

    return _DIRECTION_NOUNS_BY_REFERENCE


def get_direction_nouns_for_available_exits(room: "Room | None") -> list[DirectionNoun]:
    """Return direction noun tokens valid for the current room exits."""
    ensure_direction_nouns()
    if room is None:
        return []

    nouns: list[DirectionNoun] = []
    for direction in room.available_directions():
        nouns.extend(_DIRECTION_NOUNS_BY_CANONICAL.get(str(direction).lower(), []))
    return nouns

class Item(Noun):
    all_items = []  # Class variable to track every item created

    def __init__(
        self,
        name,
        pickupable=True,
        refuse_string=None,
        presence_string=None,
        noun_name=None,
        openable=False,
        is_open=False,
        open_description=None,
        closed_description=None,
        open_exit_direction=None,
        open_exit_destination=None,
        close_hides_exit=False,
        lockable=False,
        is_locked=False,
        unlock_key=None,
        locked_description=None,
        edible=False,
        light_source=False,
        is_lit=False,
        eat_refuse_string=None,
        eat_success_string=None,
        eat_missing_string=None,
        behavior_ids=None,
    ):
        super().__init__()
        self.name = str(name).strip()
        self.descriptive_phrase = self.name
        self.noun_name = str(noun_name).strip().lower() if noun_name else _derive_noun_name(self.name)
        explicit_behavior_ids = tuple(str(identifier).strip() for identifier in (behavior_ids or []) if str(identifier).strip())
        default_behavior_ids = get_default_item_behavior_ids(self.noun_name)
        combined_behavior_ids = tuple(dict.fromkeys((*default_behavior_ids, *explicit_behavior_ids)))
        self.explicit_behavior_ids = explicit_behavior_ids
        self.behavior_ids = combined_behavior_ids
        self.behavior_handlers = resolve_item_behaviors(self.behavior_ids)
        self.current_box = None
        self.is_broken = False
        self.pickupable = pickupable
        self.refuse_string = refuse_string or f"You can't pick up {self.name}"
        self.presence_string = presence_string
        self.openable = bool(openable)
        self.is_open = bool(is_open)
        self.open_description = open_description
        self.closed_description = closed_description
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
        self.close_hides_exit = bool(close_hides_exit)
        self.lockable = bool(lockable)
        self.is_locked = bool(is_locked)
        self.unlock_key = (
            str(unlock_key).strip().lower()
            if unlock_key is not None and str(unlock_key).strip()
            else None
        )
        self.locked_description = locked_description
        self.edible = bool(edible)
        self.light_source = bool(light_source)
        self.is_lit = bool(is_lit)
        self.eat_refuse_string = eat_refuse_string
        self.eat_success_string = eat_success_string
        self.eat_missing_string = eat_missing_string
        Item.all_items.append(self)

    def get_presence_text(self):
        if self.lockable and self.is_locked and self.locked_description:
            return self.locked_description
        if self.openable:
            if self.is_open and self.open_description:
                return self.open_description
            if not self.is_open and self.closed_description:
                return self.closed_description
        if self.presence_string:
            return self.presence_string
        return f"There is {self.name} here."

    def _remove_from_known_containers(self, dispatch_context: dict | None = None) -> bool:
        if self.current_box is not None:
            if self in self.current_box.contents:
                self.current_box.contents.remove(self)
                self.current_box = None
                return True
            self.current_box = None

        if not dispatch_context:
            return False

        state = dispatch_context.get("state")
        game = dispatch_context.get("game")

        if state is not None and getattr(state, "current_room", None) is not None:
            room = state.current_room
            if self in room.items:
                room.items.remove(self)
                return True

            for box in room.boxes:
                if self in box.contents:
                    box.contents.remove(self)
                    return True

        if game is not None:
            player = getattr(game, "current_player", None)
            if player is not None and self in player.sack.contents:
                player.sack.contents.remove(self)
                return True

        return False

    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        if verb_name == "take" and not self.pickupable:
            return False, self.refuse_string
        if verb_name == "eat":
            return True, None
        return super().can_handle_verb(verb_name, *args, **kwargs)

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        if verb_name != "eat":
            return super().handle_verb(verb_name, *args, **kwargs)

        dispatch_context = kwargs.get("dispatch_context")

        for handler in self.behavior_handlers:
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return super().handle_verb(verb_name, *args, **kwargs)

    def __repr__(self):
        """Controls how the item looks when printed in a list."""
        status = " [BROKEN]" if self.is_broken else ""
        return f"'{self.name}{status}'"

class Box(Noun):
    all_boxes = []  # Class variable to track every box created

    def __init__(
        self,
        box_name,
        capacity=None,
        presence_string=None,
        openable=False,
        is_open=False,
        open_description=None,
        closed_description=None,
        lockable=False,
        is_locked=False,
        unlock_key=None,
        locked_description=None,
    ):
        super().__init__()
        self.name = box_name  # Noun uses 'name'
        self.box_name = box_name
        self.contents = []
        self.capacity = capacity  # None = unlimited
        self.presence_string = presence_string
        self.openable = bool(openable)
        self.is_open = bool(is_open)
        self.open_description = open_description
        self.closed_description = closed_description
        self.lockable = bool(lockable)
        self.is_locked = bool(is_locked)
        self.unlock_key = (
            str(unlock_key).strip().lower()
            if unlock_key is not None and str(unlock_key).strip()
            else None
        )
        self.locked_description = locked_description
        Box.all_boxes.append(self)

    def get_presence_text(self):
        if self.lockable and self.is_locked and self.locked_description:
            return self.locked_description
        if self.openable:
            if self.is_open and self.open_description:
                return self.open_description
            if not self.is_open and self.closed_description:
                return self.closed_description
        if self.presence_string:
            return self.presence_string
        return f"There is {self.box_name} here."

    def add_item(self, item, announce=True):
        """The King claims an item. If it's in another box, he seizes it."""
        if self.capacity is not None and len(self.contents) >= self.capacity:
            if announce:
                print(f"KING {self.box_name}: The box is full!")
            return

        if item.current_box == self:
            if announce:
                print(f"KING {self.box_name}: I already own {item.name}!")
            return

        # Handle the move logic (Seizing from another box)
        if item.current_box is not None:
            if announce:
                print(f"KING {self.box_name}: Seizing {item.name} from {item.current_box.box_name}!")
            item.current_box.contents.remove(item)

        # Update states
        self.contents.append(item)
        item.current_box = self
        if announce:
            print(f"KING {self.box_name}: {item.name} has been added to the treasury.")

    def __repr__(self):
        return f"Box({self.box_name}, contents={self.contents})"

class Robber:
    def __init__(self, name):
        self.name = name
        # Composition: The Robber HAS a Box (his sack)
        self.sack = Box(f"{name}'s Sack")

    def steal(self, from_container, item):
        """The robber takes a specific item object from a box or room."""
        # Determine which type of container we're dealing with
        if isinstance(from_container, Box):
            contents = from_container.contents
            container_name = from_container.box_name
        elif isinstance(from_container, Room):
            contents = from_container.items
            container_name = from_container.name
        else:
            raise TypeError("from_container must be a Box or Room")

        assert item in contents, f"{item.name} isn't even in {container_name}!"

        # Check if item is pickupable
        if not item.pickupable:
            print(f"!!! {self.name} tries to steal from {container_name}...")
            print(f"{item.refuse_string}")
            return

        print(f"!!! {self.name} sneaks into {container_name}...")
        contents.remove(item)
        self.sack.add_item(item)

        # The 'Careless' part: 50% chance to break it during the theft
        import random
        if random.random() > 0.5:
            self.break_item(item)

    def break_item(self, item):
        item.is_broken = True
        print(f"CRACK! {self.name} was careless and broke {item.name}!")


class Player:
    """A player character who can collect items in their sack (max 10 items)."""
    def __init__(self, name):
        self.name = name
        self.sack = Box(f"{name}'s Sack", capacity=10)

    def take(self, from_container, item):
        """The player takes an item from a box or room."""
        # Determine which type of container we're dealing with
        if isinstance(from_container, Box):
            contents = from_container.contents
            container_name = from_container.box_name
        elif isinstance(from_container, Room):
            contents = from_container.items
            container_name = from_container.name
        else:
            raise TypeError("from_container must be a Box or Room")

        assert item in contents, f"{item.name} isn't even in {container_name}!"

        # Check if item is pickupable
        if not item.pickupable:
            print(f"{self.name} tries to pick up {item.name}...")
            print(f"{item.refuse_string}")
            return

        # Check sack capacity
        if len(self.sack.contents) >= self.sack.capacity:
            print(f"{self.name}'s sack is full (max {self.sack.capacity} items)!")
            return

        print(f"{self.name} takes {item.name} from {container_name}.")
        contents.remove(item)
        self.sack.contents.append(item)
        item.current_box = self.sack

    def drop(self, item):
        """The player drops an item from their sack."""
        if item not in self.sack.contents:
            print(f"{self.name} doesn't have {item.name}!")
            return
        print(f"{self.name} drops {item.name}.")
        self.sack.contents.remove(item)
        item.current_box = None


class Room(Noun):
    """A simple Room that can hold `Item` objects and connect to other rooms.

    Adapted from the Castle example; uses the project's `Item` class.
    """
    all_rooms = []  # Class variable to track every room created
    DIRECTIONS = ["north", "south", "east", "west", "up", "down"]

    def __init__(self, name, description, visited=False, is_dark=False, dark_description=None):
        super().__init__()
        self.name = name
        self.description = description
        self.visited = bool(visited)
        self.is_dark = bool(is_dark)
        self.dark_description = dark_description or "It is too dark to see anything."
        self.items = []  # list[Item]
        self.boxes = []  # list[Box]
        self.connections = {}
        self.minigame = None
        Room.all_rooms.append(self)

    def add_item(self, item):
        """Add an Item instance or create one from a string name."""
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")

    def add_box(self, box):
        """Add a Box instance to this room."""
        if not isinstance(box, Box):
            raise TypeError("Room.add_box expects a Box instance")
        self.boxes.append(box)

    def add_direction(self, direction):
        if not isinstance(direction, str):
            raise TypeError("direction must be a string")
        if direction == "":
            raise ValueError("direction cannot be empty")
        if direction not in Room.DIRECTIONS:
            Room.DIRECTIONS.append(direction)
        return direction

    def connect_room(self, direction, room):
        if not isinstance(room, Room):
            raise TypeError("connect_room expects a Room instance")
        registered_direction = self.add_direction(direction)
        self.connections[registered_direction] = room

    def get_connection(self, direction):
        return self.connections.get(direction)

    def can_go(self, direction):
        return self.get_connection(direction) is not None

    def available_directions(self):
        return sorted(self.connections.keys())

    def has_lit_light_source(self):
        for item in self.items:
            if getattr(item, "light_source", False) and getattr(item, "is_lit", False):
                return True

        for box in self.boxes:
            if box.openable and not box.is_open:
                continue
            for item in box.contents:
                if getattr(item, "light_source", False) and getattr(item, "is_lit", False):
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

    def __repr__(self):
        items_str = [it.name for it in self.items]
        boxes_str = [b.box_name for b in self.boxes]
        connections_str = {direction: room.name for direction, room in self.connections.items()}
        return (
            f"Room({self.name}, desc='{self.description}', visited={self.visited}, is_dark={self.is_dark}, items={items_str}, "
            f"boxes={boxes_str}, connections={connections_str})"
        )


class Game(Noun):
    """The Game world itself - a special noun that represents the overall game state.
    
    The Game noun is always instantiated and manages the kingdom's boxes, rooms,
    and current player. Unlike other nouns, it is not loaded from JSON.
    """
    _instance = None  # Singleton pattern
    
    def __init__(self):
        super().__init__()
        self.name = "Game"
        self.boxes = []
        self.rooms = []
        self.current_player = None
        Game._instance = self
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton Game instance."""
        if cls._instance is None:
            cls._instance = Game()
        return cls._instance
    
    def set_world(self, boxes, rooms):
        """Set the kingdom boxes and rooms."""
        self.boxes = boxes
        self.rooms = rooms
    
    def set_current_player(self, player):
        """Set the current player character."""
        self.current_player = player
    
    def get_all_nouns(self):
        """Get all nouns in the game world (boxes, items, rooms, players, etc)."""
        return Noun.all_nouns

    def setup_world(self, filepath):
        """Load and construct world state from a JSON file."""
        with open(filepath, 'r') as file:
            data = json.load(file)

        if isinstance(data, dict):
            boxes = _construct_boxes(data.get('boxes', []))
            rooms = _construct_rooms(data.get('rooms', []))
        else:
            boxes = _construct_boxes(data)
            rooms = []

        self.set_world(boxes, rooms)
        return boxes, rooms

    def load_world(self, filepath):
        """Load previously saved world state from a JSON file."""
        return self.setup_world(filepath)

    def save_world(self, filepath):
        """Save current world state to JSON."""
        target = Path(filepath)
        if target.name == "initial_state.json":
            raise RuntimeError("Refusing to overwrite initial_state.json")

        payload = {
            'boxes': [],
            'rooms': []
        }

        for box in self.boxes:
            payload['boxes'].append(_serialize_box(box))

        for room in self.rooms:
            room_payload = {
                'name': room.name,
                'description': room.description,
                'visited': room.visited,
                'items': [_serialize_item(item) for item in room.items],
                'boxes': [],
                'connections': {
                    direction: destination.name
                    for direction, destination in room.connections.items()
                },
            }

            if getattr(room, 'is_dark', False):
                room_payload['is_dark'] = True
            dark_description = getattr(room, 'dark_description', None)
            if dark_description and dark_description != "It is too dark to see anything.":
                room_payload['dark_description'] = dark_description

            for box in room.boxes:
                room_payload['boxes'].append(_serialize_box(box))

            payload['rooms'].append(room_payload)

        with open(filepath, 'w') as file:
            json.dump(payload, file, indent=4)

    def create_state_verbs(self):
        """Create save/load verbs bound to this Game instance."""

        def save_action(path):
            self.save_world(path)
            return f"Game saved to {path}"

        def load_action(path):
            self.load_world(path)
            return f"Game loaded from {path}"

        return Verb("save", save_action), Verb("load", load_action)


def _construct_boxes(data):
    """Construct Box and Item objects from loaded JSON data list.

    Expects `data` to be a list of dicts with keys 'box_name' and 'items'.
    Each item can be a string or a dict with 'name', 'pickupable', 'refuse_string'.
    """
    Box.all_boxes.clear()  # Clear existing boxes for a clean load
    for entry in data:
        new_box = Box(
            entry["box_name"],
            presence_string=entry.get("presence_string"),
            openable=entry.get("openable", False),
            is_open=entry.get("is_open", False),
            open_description=entry.get("open_description"),
            closed_description=entry.get("closed_description"),
            lockable=entry.get("lockable", False),
            is_locked=entry.get("is_locked", False),
            unlock_key=entry.get("unlock_key"),
            locked_description=entry.get("locked_description"),
        )
        for item_spec in entry.get("items", []):
            new_item = _construct_item_from_spec(item_spec)
            new_box.add_item(new_item, announce=False)
    return Box.all_boxes



def _construct_rooms(data):
    """Construct Room objects from loaded JSON data list.

    Each room dict should have 'name', 'description', optional 'items', optional 'boxes', and optional 'connections'.
    Items can be strings or dicts with 'name', 'pickupable', 'refuse_string'.
    """
    Room.all_rooms.clear()  # Clear existing rooms for a clean load
    pending_connections = []
    for entry in data:
        room = Room(
            entry.get("name"),
            entry.get("description", ""),
            visited=entry.get("visited", False),
            is_dark=entry.get("is_dark", False),
            dark_description=entry.get("dark_description"),
        )
        # Add items to the room
        for item_spec in entry.get("items", []):
            room.items.append(_construct_item_from_spec(item_spec))
        # Add boxes to the room
        for box_data in entry.get("boxes", []):
            box = Box(
                box_data.get("box_name"),
                presence_string=box_data.get("presence_string"),
                openable=box_data.get("openable", False),
                is_open=box_data.get("is_open", False),
                open_description=box_data.get("open_description"),
                closed_description=box_data.get("closed_description"),
                lockable=box_data.get("lockable", False),
                is_locked=box_data.get("is_locked", False),
                unlock_key=box_data.get("unlock_key"),
                locked_description=box_data.get("locked_description"),
            )
            for item_spec in box_data.get("items", []):
                item_obj = _construct_item_from_spec(item_spec)
                box.add_item(item_obj, announce=False)
            room.add_box(box)

        pending_connections.append((room, entry.get("connections", {})))

    room_by_name = {room.name: room for room in Room.all_rooms}
    for room, raw_connections in pending_connections:
        if isinstance(raw_connections, dict):
            iterable = raw_connections.items()
            for direction, destination_name in iterable:
                destination_room = room_by_name.get(destination_name)
                if destination_room is not None:
                    room.connect_room(direction, destination_room)
        elif isinstance(raw_connections, list):
            for connection in raw_connections:
                if isinstance(connection, dict):
                    direction = connection.get("direction")
                    destination_name = connection.get("room")
                    if direction and destination_name:
                        destination_room = room_by_name.get(destination_name)
                        if destination_room is not None:
                            room.connect_room(direction, destination_room)
                elif isinstance(connection, str):
                    destination_room = room_by_name.get(connection)
                    if destination_room is not None:
                        room.connect_room(connection, destination_room)

    return Room.all_rooms

