"""Core game models and world state.

Defines Noun, Item, Box, Room, Player, Game, and related helpers.
Handles world loading, serialization, and runtime entity management.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, Optional
from enum import Enum, auto
from dataclasses import dataclass


@dataclass
class GameActionState:
    game: Game | None = None
    current_player: Player | None = None
    current_room: Room | None = None
    player_name: str | None = None
    score: int = 0


@dataclass
class SessionPrefs:
    save_directory: Path = Path("saves")
    last_save_filename: str = "quicksave.json"
    player_name: str | None = None
    default_filename_template: str = "{name}.json"

    def remember_save(self, path: Path | str):
        path = Path(path)
        self.save_directory = path.parent
        self.last_save_filename = path.name


_action_state: GameActionState | None = None
_prefs: SessionPrefs | None = None


def init_session(
    game: Game | None = None,
    current_player: Player | None = None,
    initial_room: Room | None = None,
    player_name: str | None = None,
    save_path: Path | None = None,
) -> None:
    global _action_state, _prefs

    resolved_player = current_player

    resolved_player_name = player_name or getattr(resolved_player, "name", None)
    
    _action_state = GameActionState(
        game=game,
        current_player=resolved_player,
        current_room=initial_room,
        player_name=resolved_player_name,
        score=0,
    )

    if game is not None:
        game.state = _action_state

    _prefs = SessionPrefs(
        save_directory=save_path.parent if save_path else Path("saves"),
        last_save_filename=save_path.name if save_path else "quicksave.json",
        player_name=resolved_player_name,
    )


def get_action_state() -> GameActionState:
    if _action_state is None:
        raise RuntimeError("Action state not initialized")
    return _action_state


def set_action_state(new_state: GameActionState) -> None:
    global _action_state
    _action_state = new_state


def set_prefs(new_prefs: SessionPrefs) -> None:
    global _prefs
    _prefs = new_prefs


def get_prefs() -> SessionPrefs:
    if _prefs is None:
        raise RuntimeError("Session preferences not initialized")
    return _prefs


def reset_all_state() -> None:
    global _action_state, _prefs
    _action_state = None
    _prefs = None




class GameOver(Exception):
    pass

class QuitGame(Exception):
    pass

class SaveGame(Exception):
    pass

class LoadGame(Exception):
    pass

class LocationType(Enum):
    """Where an item can physically be in the game world."""
    INVENTORY     = auto()   # directly in player's sack/inventory
    ROOM_FLOOR    = auto()   # loose on the room floor
    BOX_IN_ROOM   = auto()   # the box/container itself is present in the room
    INSIDE_BOX    = auto()   # inside a box (or other container)

@dataclass(frozen=True)
class ItemLocation:
    """Precise, type-safe description of an item's location."""
    type: LocationType
    container: Optional['Box'] = None   # only relevant for INSIDE_BOX

    def is_accessible(self) -> bool:
        """Quick default rule — override or extend per verb if needed."""
        match self.type:
            case LocationType.INVENTORY | LocationType.ROOM_FLOOR | LocationType.BOX_IN_ROOM:
                return True
            case LocationType.INSIDE_BOX:
                # Assuming Box has .is_open (bool) or similar
                return self.container is not None and self.container.is_open
            case _:
                return False

    def describe(self) -> str:
        """Human-readable phrase for messages."""
        match self.type:
            case LocationType.INVENTORY:
                return "in your inventory"
            case LocationType.ROOM_FLOOR:
                return "here on the ground"
            case LocationType.BOX_IN_ROOM:
                return "here (as a container)"
            case LocationType.INSIDE_BOX if self.container:
                return f"inside the {self.container.display_name()}"
            case _:
                return "somewhere strange"
            

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

    default_refusal = f"You can't pick up {item.name}"
    if item.refuse_string and item.refuse_string != default_refusal:
        payload["refuse_string"] = item.refuse_string

    if not item.is_gettable:
        payload["is_gettable"] = False

    if item.get_refuse_string and item.get_refuse_string != default_refusal:
        payload["get_refuse_string"] = item.get_refuse_string

    if item.presence_string:
        payload["presence_string"] = item.presence_string

    if getattr(item, "is_openable", False):
        payload["is_openable"] = True

    if getattr(item, "is_open", False):
        payload["is_open"] = True

    if getattr(item, "opened_state_description", None):
        payload["opened_state_description"] = item.opened_state_description

    if getattr(item, "closed_state_description", None):
        payload["closed_state_description"] = item.closed_state_description

    if getattr(item, "lit_state_description", None):
        payload["lit_state_description"] = item.lit_state_description

    if getattr(item, "unlit_state_description", None):
        payload["unlit_state_description"] = item.unlit_state_description

    if getattr(item, "open_action_description", None):
        payload["open_action_description"] = item.open_action_description

    if getattr(item, "close_action_description", None):
        payload["close_action_description"] = item.close_action_description

    if getattr(item, "examine_string", None):
        payload["examine_string"] = item.examine_string

    if getattr(item, "open_exit_direction", None):
        payload["open_exit_direction"] = item.open_exit_direction

    if getattr(item, "open_exit_destination", None):
        payload["open_exit_destination"] = item.open_exit_destination

    if getattr(item, "is_lockable", False):
        payload["is_lockable"] = True

    if getattr(item, "is_locked", False):
        payload["is_locked"] = True

    if getattr(item, "unlock_key", None):
        payload["unlock_key"] = item.unlock_key

    if getattr(item, "locked_state_description", None):
        payload["locked_state_description"] = item.locked_state_description
    
    if getattr(item, "unlocked_state_description", None):
        payload["unlocked_state_description"] = item.unlocked_state_description
    
    if getattr(item, "unlockable_description", None):
        payload["unlockable_description"] = item.unlockable_description
    
    if getattr(item, "is_edible", False):
        payload["is_edible"] = True

    if getattr(item, "is_lightable", False):
        payload["is_lightable"] = True

    if getattr(item, "is_verbally_interactive", False):
        payload["is_verbally_interactive"] = True

    if getattr(item, "is_lit", False):
        payload["is_lit"] = True
    
    if getattr(item, "can_ignite", False):
        payload["can_ignite"] = True   

    if getattr(item, "ignite_success_string", None):
        payload["ignite_success_string"] = item.ignite_success_string

    if getattr(item, "eat_refuse_string", None):
        payload["eat_refuse_string"] = item.eat_refuse_string

    if getattr(item, "eaten_success_string", None):
        payload["eaten_success_string"] = item.eaten_success_string

    if getattr(item, "get_refuse_string", None):
        payload["get_refuse_string"] = item.get_refuse_string

    if getattr(item, "is_rubbable", False):
        payload["is_rubbable"] = True

    if getattr(item, "is_rubbed", False):
        payload["is_rubbed"] = True

    if getattr(item, "rub_success_string", None):
        payload["rub_success_string"] = item.rub_success_string

    if getattr(item, "rubbed_state_description", None):
        payload["rubbed_state_description"] = item.rubbed_state_description

    if getattr(item, "too_heavy_to_swim", False):
        payload["too_heavy_to_swim"] = True

    if getattr(item, "trigger_room", None):
        payload["trigger_room"] = item.trigger_room

    special_handlers = getattr(item, "special_handlers", None)
    if special_handlers:
        payload["special_handlers"] = dict(special_handlers)

    return payload


def _serialize_box(box: "Box") -> dict:
    payload = {
        "canonical_name": box.canonical_name(), 
        "box_name": box.box_name,
        "items": [_serialize_item(item) for item in box.contents],
    }

    if box.presence_string:
        payload["presence_string"] = box.presence_string

    if box.capacity is not None:
        payload["capacity"] = box.capacity

    if getattr(box, "is_openable", False):
        payload["is_openable"] = True

    if getattr(box, "is_open", False):
        payload["is_open"] = True

    if getattr(box, "opened_state_description", None):
        payload["opened_state_description"] = box.opened_state_description

    if getattr(box, "closed_state_description", None):
        payload["closed_state_description"] = box.closed_state_description

    if getattr(box, "open_action_description", None):
        payload["open_action_description"] = box.open_action_description

    if getattr(box, "close_action_description", None):
        payload["close_action_description"] = box.close_action_description

    if getattr(box, "examine_string", None):
        payload["examine_string"] = box.examine_string

    if getattr(box, "is_lockable", False):
        payload["is_lockable"] = True

    if getattr(box, "is_locked", False):
        payload["is_locked"] = True

    if getattr(box, "unlock_key", None):
        payload["unlock_key"] = box.unlock_key

    if getattr(box, "locked_description", None):
        payload["locked_description"] = box.locked_description

    if getattr(box, "open_exit_direction", None):
        payload["open_exit_direction"] = box.open_exit_direction

    if getattr(box, "open_exit_destination", None):
        payload["open_exit_destination"] = box.open_exit_destination

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

    item = Item(
        item_spec.get("name"),
        is_gettable=item_spec.get("is_gettable", True),
        refuse_string=refuse_string,
        presence_string=presence_string,
        noun_name=item_spec.get("noun_name"),
        is_openable=item_spec.get("is_openable", False),
        is_open=item_spec.get("is_open", False),
        opened_state_description=item_spec.get("opened_state_description"),
        closed_state_description=item_spec.get("closed_state_description"),
        lit_state_description=item_spec.get("lit_state_description"),
        unlit_state_description=item_spec.get("unlit_state_description"),
        open_action_description=item_spec.get("open_action_description"),
        close_action_description=item_spec.get("close_action_description"),
        examine_string=item_spec.get("examine_string"),
        open_exit_direction=item_spec.get("open_exit_direction"),
        open_exit_destination=item_spec.get("open_exit_destination"),
        is_lockable=item_spec.get("is_lockable", False),
        is_locked=item_spec.get("is_locked", False),
        unlock_key=item_spec.get("unlock_key"),
        unlockable_description=item_spec.get("unlockable_description"),
        unlocked_state_description=item_spec.get("unlocked_state_description"),
        locked_state_description=item_spec.get("locked_state_description"),
        is_edible=item_spec.get("is_edible", False),
        is_verbally_interactive=item_spec.get("is_verbally_interactive", False),
        is_lightable=item_spec.get("is_lightable", False),
        is_lit=item_spec.get("is_lit", False),
        can_ignite=item_spec.get("can_ignite", False),
        ignite_success_string=item_spec.get("ignite_success_string"),
        is_rubbable=item_spec.get("is_rubbable", False),
        is_rubbed=item_spec.get("is_rubbed", False),
        rub_success_string=item_spec.get("rub_success_string"),
        rubbed_state_description=item_spec.get("rubbed_state_description"),
        trigger_room=item_spec.get("trigger_room"),
        too_heavy_to_swim=item_spec.get("too_heavy_to_swim", False),
        eat_refuse_string=item_spec.get("eat_refuse_string"),
        eaten_success_string=item_spec.get("eaten_success_string"),
        get_refuse_string=item_spec.get("get_refuse_string"),
        special_handlers=item_spec.get("special_handlers"),
    )

    return item 

class Verb:
    """A verb paired with a handler method.

    Verbs know:
      - their name
      - their synonyms
      - their handler function
      - how to perform noun-side overrides (double dispatch)
    """

    all_verbs = []

    def __init__(self, name, action, synonyms=None, hidden=False):
        self.name = str(name).strip().lower()
        self.action = action
        self.hidden = bool(hidden)

        # Normalize synonyms
        self.synonyms = tuple(
            sorted(
                {
                    s.strip().lower()
                    for s in (synonyms or [])
                    if s.strip().lower() != self.name
                }
            )
        )

        Verb.all_verbs.append(self)

    def all_names(self):
        return (self.name, *self.synonyms)

    def execute(self, target, words):
        """Execute this verb with noun override + handler fallback."""

        # 1. Noun override: on_<verb>
        if target is not None:
            override = getattr(target, f"on_{self.name}", None)
            if callable(override):
                result = override(words)
                if result is not None:
                    return result

        # 2. Handler fallback
        return self.action(target, words)

    def __repr__(self):
        if self.synonyms:
            return f"Verb({self.name}, synonyms={list(self.synonyms)})"
        return f"Verb({self.name})"


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
    
        
    def on_unlock(self, words):
        return None


    def can_handle_verb(self, verb_name: str, *args, **kwargs) -> tuple[bool, str | None]:
        """Return whether this noun allows handling the given verb.

        Default behavior allows all verbs and provides no refusal text.
        """
        return True, None

    def handle_verb(self, verb_name: str, *args, **kwargs) -> str | None:
        dispatch_context = kwargs.get("dispatch_context")

        for handler in getattr(self, "behavior_handlers", []):
            handled_result = handler(self, verb_name, args, dispatch_context)
            if handled_result is not None:
                return handled_result

        return None

    @classmethod
    def by_name(cls, name: str, *, exact: bool = False) -> 'Noun | None':
        """
        Find a noun by name, noun_name, or descriptive phrase.
        Returns first match or None.
        
        exact=True → only matches exact get_name()
        """
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
        self.aliases = {}          # alias -> canonical
        self.reverse = {}          # canonical -> canonical reverse

    def register(self, canonical: str, *, synonyms=None, reverse=None):
        canonical = canonical.lower().strip()
        self.canonical.add(canonical)

        if synonyms:
            for s in synonyms:
                self.aliases[s.lower().strip()] = canonical

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
    """
    Minimal noun representation of a direction token.
    No verb-handling logic; parser handles implicit GO.
    """

    def __init__(self, reference_name: str, canonical_direction: str):
        super().__init__()
        self.name = reference_name
        self._noun_name = reference_name
        self.canonical_direction = canonical_direction

    def matches_reference(self, reference: str) -> bool:
        """
        A direction noun matches if the reference token canonicalizes
        to the same canonical direction.
        """
        ref = reference.lower().strip()
        canon = DIRECTIONS.to_canonical(ref)
        return canon == self.canonical_direction

    def canonical_name(self):
        return self.canonical_direction
    
    def noun_name(self):
        return self._noun_name
    
    # ----------------------------------------------------------------------
    # Registry-driven direction noun generation
    # ----------------------------------------------------------------------

    _direction_nouns_by_reference: dict[str, DirectionNoun] = {}
    _direction_nouns_by_canonical: dict[str, list[DirectionNoun]] = {}


    def ensure_direction_nouns():
        """
        Build direction nouns from the DirectionRegistry.
        """
        global _direction_nouns_by_reference, _direction_nouns_by_canonical

        if DirectionNoun._direction_nouns_by_reference:
            return
        
        # Build nouns for canonical directions
        for canonical in DIRECTIONS.canonical:
            dn = DirectionNoun(canonical, canonical)
            DirectionNoun._direction_nouns_by_reference[canonical] = dn
            DirectionNoun._direction_nouns_by_canonical.setdefault(canonical, []).append(dn)

        # Build nouns for aliases
        for alias, canonical in DIRECTIONS.aliases.items():
            dn = DirectionNoun(alias, canonical)
            DirectionNoun._direction_nouns_by_reference[alias] = dn
            DirectionNoun._direction_nouns_by_canonical.setdefault(canonical, []).append(dn)


    def get_direction_noun(token: str) -> DirectionNoun | None:
        """
        Return a DirectionNoun for a token if it is a known direction.
        """
        DirectionNoun.ensure_direction_nouns()
        token = token.lower().strip()
        return DirectionNoun._direction_nouns_by_reference.get(token)


    def get_direction_nouns_for_available_exits(room) -> list[DirectionNoun]:
        """
        Return direction nouns corresponding to the exits available in the room.
        Useful for parser hints, autocompletion, etc.
        """
        DirectionNoun.ensure_direction_nouns()
        if room is None:
            return []

        nouns: list[DirectionNoun] = []
        for canonical in room.available_directions(visible_only=True):
            canonical = canonical.lower().strip()
            nouns.extend(DirectionNoun._direction_nouns_by_canonical.get(canonical, []))

        return nouns


class Item(Noun):
    all_items = []  # Class variable to track every item created
    _by_name = {}                     # name → Item 

    @classmethod
    def get_by_name(cls, name: str) -> 'Item | None':
        """Look up item by name (case-insensitive)"""
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

        state = getattr(dispatch_context, "state", None)
        if state is None:
            try:
                state = get_action_state()
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
    all_boxes = []  # Class variable to track every box created
    _by_name = {}                     # name → Box

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
        self.capacity = capacity  # None = unlimited
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
            return # no room in box
        if item.current_box == self:
            print(f"ERROR: {item.name} is already in {self.box_name}")
            return # already in this box

        # Handle the move logic (moving from another box)
        if item.current_box is not None:
            item.current_box.contents.remove(item)

        # Update states
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
            capacity=10
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
    # A Room that can hold `Item` objects and connect to other Rooms.
  
    all_rooms = []  # Class variable to track every room created
    DIRECTIONS = []  # Class variable to track all directions used across rooms
    _by_name = {}                     # name → Room 


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
        self.items = []  # list[Item]
        self.boxes = []  # list[Box]
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
        """Add an Item instance or create one from a string name."""
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")
        return True

    def add_box(self, box) -> bool:
        """Add a Box instance to this room."""
        if not isinstance(box, Box):
            raise TypeError("Room.add_box expects a Box instance")
        self.boxes.append(box)
        return True
    
    def remove_item(self, item) -> bool:
        """Remove an Item instance from this room."""
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def remove_box(self, box) -> bool:
        """Remove a Box instance from this room."""
        if box in self.boxes:
            self.boxes.remove(box)
            return True
        return False
    
    def has_item(self, item) -> bool:
        """Check if an Item instance is in this room."""
        return item in self.items
    
    def has_box(self, box) -> bool:
        """Check if a Box instance is in this room."""
        return box in self.boxes
    
    def find_containing_box(self, item) -> Box | None:
        """Return the Box instance that contains the given Item, or None if not found."""
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
    # rooms currently only have "name"
        return getattr(self, "noun_name", None) or self.name.lower()

    def display_name(self):
        return self.name



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
        self.start_room_name = None
        self.start_room = None
        self.state = None
        Game._instance = self

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
            f"Game(\n"
            f"  rooms={list(self.rooms.keys())},\n"
            f"  current_player={self.current_player!r},\n"
            f"  start_room={self.start_room_name!r},\n"
            f")"
        )


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

    def require_player(self, missing_message: str = "No hero is active yet.", return_error: bool = False) -> "Player | str":
        """Return current player or report a meaningful missing-player condition.

        Args:
            missing_message: Message used when no active player exists.
            return_error: When True, return missing_message instead of raising.
        """
        player = self.current_player
        if player is not None:
            return player

        if return_error:
            return missing_message

        raise RuntimeError(missing_message)
    
    def get_all_nouns(self):
        """Get all nouns in the game world (boxes, items, rooms, players, etc)."""
        return Noun.all_nouns
    

    def find_item_in_game(self, noun_name: str) -> tuple["Room | None", "Item | None"]:
        """
        Search all rooms for an item by noun_name.
        Returns (room, item) or (None, None) if not found.
        """
        for room in self.rooms.values():
            for item in room.items:  # items is a list[Item]
                if getattr(item, "noun_name", None) == noun_name:
                    return room, item
        return None, None


    def move_item_between_rooms(
        self,
        item: "Item",
        from_room: "Room",
        to_room: "Room"
    ) -> None:
        """
        Move an item from one room to another.
        Works with the current list-based room.items structure.
        """
        # Remove from old room
        if item in from_room.items:
            from_room.items.remove(item)

        # Add to new room
        if item not in to_room.items:
            to_room.items.append(item)
            

    def setup_world(self, source):
        """ Build the world from either: 
            - a filepath (Path), or 
            - a pre-loaded JSON dict """ 
        if isinstance(source, (str, Path)): 
            with open(source, 'r') as file: 
                data = json.load(file) 
        elif isinstance(source, dict): 
            data = source 
        else: 
            raise TypeError("setup_world expects a filepath or a dict")
# clear existing world state before loading new one
# need to also clear dictionaries that track nouns by name
# don't clear player we are keeping the same player instance across world loads
        Room.all_rooms.clear()
        Box.all_boxes.clear()
        Item.all_items.clear()
        Noun.all_nouns.clear()
        Room._by_name = {}
        Box._by_name = {}
        Item._by_name = {}

        _load_directions(data) 
        DirectionNoun.ensure_direction_nouns()

        Room.DIRECTIONS = DIRECTIONS.canonical

        if isinstance(data, dict):
            boxes = _construct_boxes(data.get('boxes', []))
            rooms = _construct_rooms(data.get('rooms', []))
        else:
            rooms = []

        self.set_world(boxes, rooms)
        self.rooms = { room.name: room for room in rooms }     #convert room list to a dictionary for easy lookup by name
        start_room_name = data.get("start_room")
        start_room = self.rooms
        self.start_room_name = start_room_name

        return boxes, self.rooms


    def load_game(self, filepath) -> Path:
        target = Path(filepath).expanduser()
        if not target.suffix:
            target = target.with_suffix(".json")
        if not target.is_file():
            raise RuntimeError(f"Save file not found: {target}")

        try:
            with target.open('r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid save file format: {target} ({e})") from e
        except OSError as e:
            raise RuntimeError(f"Unable to read save file: {target} ({e})") from e

        # --- 1. Peel off the player block ---
        player_data = data.pop("player", None)

        # --- 2. Extract current room name BEFORE setup_world ---
        current_room_name = data.get("current_room")

        # --- 3. Update player name ---
        if player_data:
            player_name = player_data.get("name", "Hero")
        else:
            player_name = "Hero"

        action_state = get_action_state()
        action_state.player_name = player_name

        if action_state.current_player is None:
            action_state.current_player = Player(player_name)

        self.current_player = action_state.current_player
        # change to saved player name, but keep same player object which is persistent across world loads

        # --- 4. Build the world ---
        self.setup_world(data)

        # --- 5. Restore player inventory ---
        player = self.require_player(return_error=True)
        if isinstance(player, str):
            raise RuntimeError(player)

        player.sack.contents.clear() # Clear existing inventory before loading new one
        if player_data:
            for item_json in player_data.get("inventory", []):
                item = _construct_item_from_spec(item_json)
                player.sack.add_item(item)

        # --- 6. Restore current room ---
        if current_room_name and current_room_name in self.rooms:
            get_action_state().current_room = self.rooms[current_room_name]

        # --- 7. Restore score ---
        get_action_state().score = int(data.get("score", 0))

        return target


####### need to update to save "directions" ######
    def save_game(self, filepath) -> Path:
        """Save current world state to JSON."""
        target = Path(filepath).expanduser()
        if not target.suffix:
            target = target.with_suffix(".json")
        if target.name == "initial_state.json":
            raise RuntimeError("Refusing to overwrite initial_state.json")
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            'player': { 'name': self.current_player.name, 
            'inventory': [_serialize_item(item)  for item in self.current_player.sack.contents]} if self.current_player else None,
            'current_room': (get_action_state().current_room.name),
            'start_room': self.start_room_name,
            'score': int(get_action_state().score),
            'rooms': []
        }

        for room in self.rooms.values():
            room_payload = {
                'name': room.name,
                'description': room.description,
                'visited': room.visited,
                'items': [_serialize_item(item) for item in room.items],
                'boxes': [],
                'connections': {
                    direction: destination.name
                    for direction, destination in room.connections.items()},
                'swim_exits': {
                    direction: destination.name
                    for direction, destination in room.swim_exits.items()},
                'hidden_directions': list(room.hidden_directions),
                'is_dark': room.is_dark,
                'has_water': room.has_water,
                'dark_description': room.dark_description,
                'discover_points': room.discover_points,
            }

            for box in room.boxes:
                room_payload['boxes'].append(_serialize_box(box))

            payload['rooms'].append(room_payload)

        try:
            with target.open('w', encoding='utf-8') as file:
                json.dump(payload, file, indent=4)
        except OSError as e:
            raise RuntimeError(f"Unable to write save file: {target} ({e})") from e

        return target

    def create_state_verbs(self):
        """Create save/load verbs bound to this Game instance."""

        def save_action(path):
            self.save_game(path)
            return f"Game saved to {path}"

        def load_action(path):
            self.load_game(path)
            return f"Game loaded from {path}"

        return Verb("save", save_action), Verb("load", load_action)




#----- functions for constructing objects from JSON data -----

def _load_directions(json_data):
    directions = json_data.get("directions", {})
    for canonical, info in directions.items():
        DIRECTIONS.register(
            canonical,
            synonyms=info.get("aliases", []),
            reverse=info.get("reverse")
        )

def _construct_boxes(data):
    """Construct Box and Item objects from loaded JSON data list.

    Expects `data` to be a list of dicts with keys 'box_name' and 'items'.
    Each item can be a string or a dict with 'name', 'is_gettable', 'refuse_string'.
    """
    Box.all_boxes.clear()  # Clear existing boxes for a clean load
    for entry in data:
        new_box = Box(
            entry["canonical_name"], # canonical_name (parser-facing)
            entry["box_name"], # box_name (display-facing)
            capacity=entry.get("capacity"),
            presence_string=entry.get("presence_string"),
            is_openable=entry.get("is_openable", False),
            is_open=entry.get("is_open", False),
            open_action_description=entry.get("open_action_description"),
            close_action_description=entry.get("close_action_description"),
            open_exit_direction=entry.get("open_exit_direction"),
            open_exit_destination=entry.get("open_exit_destination"),
            examine_string=entry.get("examine_string"),
            opened_state_description=entry.get("opened_state_description"),
            closed_state_description=entry.get("closed_state_description"),
            is_lockable=entry.get("is_lockable", False),
            is_locked=entry.get("is_locked", False),
            unlock_key=entry.get("unlock_key"),
            locked_description=entry.get("locked_description"),
        )
        for item_spec in entry.get("items", []):
            new_item = _construct_item_from_spec(item_spec)
            new_box.add_item(new_item)
    return Box.all_boxes



def _construct_rooms(data):
    """Construct Room objects from loaded JSON data list.

    Each room dict should have 'name', 'description', optional 'items', optional 'boxes', and optional 'connections'.
    Items can be strings or dicts with 'name', 'is_gettable', 'refuse_string'.
    """
    Room.all_rooms.clear()  # Clear existing rooms for a clean load
    pending_connections = []
    for entry in data:
        room = Room(
            entry.get("name"),
            entry.get("description", ""),
            visited=entry.get("visited", False),
            is_dark=entry.get("is_dark", False),
            has_water=entry.get("has_water", False),
            dark_description=entry.get("dark_description"),
            discover_points=entry.get("discover_points", 10),
        )        
        # Add items to the room
        for item_spec in entry.get("items", []):
            room.items.append(_construct_item_from_spec(item_spec))
        # Add boxes to the room
        for box_data in entry.get("boxes", []):
            box = Box(
                canonical_name=box_data.get("canonical_name"),
                box_name=box_data.get("box_name"),
                capacity=box_data.get("capacity"),
                presence_string=box_data.get("presence_string"),
                is_openable=box_data.get("is_openable", False),
                is_open=box_data.get("is_open", False),
                opened_state_description=box_data.get("opened_state_description"),
                closed_state_description=box_data.get("closed_state_description"),
                open_action_description=box_data.get("open_action_description"),
                close_action_description=box_data.get("close_action_description"),
                open_exit_direction=box_data.get("open_exit_direction"),
                open_exit_destination=box_data.get("open_exit_destination"),
                is_lockable=box_data.get("is_lockable", False),
                is_locked=box_data.get("is_locked", False),
                unlock_key=box_data.get("unlock_key"),
                locked_description=box_data.get("locked_description"),
                examine_string=box_data.get("examine_string"),
            )
            for item_spec in box_data.get("items", []):
                item_obj = _construct_item_from_spec(item_spec)
                box.add_item(item_obj)
            room.add_box(box)
        room.swim_exits = entry.get("swim_exits", {})

        hidden_directions = entry.get("hidden_directions", entry.get("hidden_exits", []))
        pending_connections.append((room, entry.get("connections", {}), hidden_directions))

    room_by_name = {room.name: room for room in Room.all_rooms}
    for room, raw_connections, hidden_exits in pending_connections:
        if isinstance(raw_connections, dict):
            iterable = raw_connections.items()
            for direction, destination_name in iterable:
                visible = True
                target_name = destination_name
                if isinstance(destination_name, dict):
                    target_name = destination_name.get("room")
                    visible = bool(destination_name.get("visible", True))
                destination_room = room_by_name.get(target_name)
                if destination_room is not None:
                    room.connect_room(direction, destination_room, visible=visible)
        elif isinstance(raw_connections, list):
            for connection in raw_connections:
                if isinstance(connection, dict):
                    direction = connection.get("direction")
                    destination_name = connection.get("room")
                    visible = bool(connection.get("visible", True))
                    if direction and destination_name:
                        destination_room = room_by_name.get(destination_name)
                        if destination_room is not None:
                            room.connect_room(direction, destination_room, visible=visible)
                elif isinstance(connection, str):
                    destination_room = room_by_name.get(connection)
                    if destination_room is not None:
                        room.connect_room(connection, destination_room)

        if isinstance(hidden_exits, list):
            for direction in hidden_exits:
                if isinstance(direction, str):
                    room.set_exit_visibility(direction, visible=False)
        # ------------------------------------------------------------
        # Resolve swim_exits into Room objects
        # ------------------------------------------------------------
        raw_swim_exits = getattr(room, "swim_exits", {})
        resolved_swim_exits = {}

        for direction, dest_name in raw_swim_exits.items():
            dest_room = room_by_name.get(dest_name)
            if dest_room:
                resolved_swim_exits[direction] = dest_room
            else:
                print(f"DEBUG: Swim exit destination '{dest_name}' not found for room '{room.name}'.")

        room.swim_exits = resolved_swim_exits

    return Room.all_rooms

