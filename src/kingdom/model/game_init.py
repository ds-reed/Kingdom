"""World state intialization and management

Handles world loading, serialization, and runtime entity management.
"""

from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, fields as dataclass_fields
from kingdom.model.direction_model import NewDirectionRegistry, NewDIRECTIONS
from kingdom.model.noun_model import (
    Noun,
    DIRECTIONS,
    DirectionNoun,
    Item,
    Feature,
    Container,
    Player,
    Room,
    World,
)


@dataclass
class GameActionState:
    world: World | None = None
    current_player: Player | None = None
    current_room: Room | None = None
    player_name: str | None = None
    lexicon: "Lexicon" | None = None
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
    world: World | None = None,
    current_player: Player | None = None,
    initial_room: Room | None = None,
    player_name: str | None = None,
    save_path: Path | None = None,
) -> None:
    global _action_state, _prefs

    resolved_player = current_player

    resolved_player_name = player_name or getattr(resolved_player, "name", None)
    
    _action_state = GameActionState(
        world=world,
        current_player=resolved_player,
        current_room=initial_room,
        player_name=resolved_player_name,
        lexicon=None,  # will be set after verb registration
        score=0,
    )

    if world is not None:
        world.state = _action_state

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

    world = getattr(new_state, "world", None)
    if world is not None:
        world.state = new_state


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

    # Keep noun registries clean across hard session resets.
    Container.all_containers.clear()
    Noun.all_nouns.clear()
    Noun._by_name = {}
    DirectionNoun._direction_nouns_by_reference = {}
    DirectionNoun._direction_nouns_by_canonical = {}


class GameOver(Exception):
    pass

class QuitGame(Exception):
    pass

class SaveGame(Exception):
    pass

class LoadGame(Exception):
    pass


def setup_world(world: World, source):
    if isinstance(source, (str, Path)):
        with open(source, "r") as file:
            data = json.load(file)
    elif isinstance(source, dict):
        data = source
    else:
        raise TypeError("setup_world expects a filepath or a dict")

    # Clear all registries before reconstructing world entities.
    Container.all_containers.clear()
    Noun.all_nouns.clear()
    Noun._by_name = {}
    DirectionNoun._direction_nouns_by_reference = {}
    DirectionNoun._direction_nouns_by_canonical = {}


    _load_directions(data)
    DirectionNoun.ensure_direction_nouns()
    Room.DIRECTIONS = DIRECTIONS.canonical

    if isinstance(data, dict):
        containers = _construct_containers(data.get("containers", []))
        rooms = _construct_rooms(data.get("rooms", []))
    else:
        containers = []
        rooms = []

    world.set_world(containers, rooms)
    world.rooms = {room.name: room for room in rooms}
    world.start_room_name = data.get("start_room")

    return containers, world.rooms


def _load_directions(json_data):
    directions = json_data.get("directions", {})
    for canonical, info in directions.items():
        DIRECTIONS.register(
            canonical,
            synonyms=info.get("synonyms", []),
            reverse=info.get("reverse"),
        )
        NewDIRECTIONS.register(         #only used for new parser right now, but will replace OLD DIRECTIONS later
            canonical,
            synonyms=info.get("synonyms", []),
            reverse=info.get("reverse"),  
        )



#----- functions for constructing objects from JSON data -----

def construct_from_spec(spec, cls, *, name_fallbacks=()):              # helper function for all constructors
    if isinstance(spec, str):
        return cls(spec)

    if not isinstance(spec, dict):
        raise TypeError(f"{cls.__name__} spec must be a dict")

    normalized = dict(spec)

    # Apply fallback names
    if "name" not in normalized:
        for fb in name_fallbacks:
            if fb in normalized:
                normalized["name"] = normalized[fb]
                break

    init_fields = {f.name for f in dataclass_fields(cls) if f.init}
    kwargs = {k: v for k, v in normalized.items() if k in init_fields}

    return cls(**kwargs)

            
def _construct_item_from_spec(spec):
    return construct_from_spec(spec, Item)


def _construct_container_from_spec(spec):
    return construct_from_spec(spec, Container)

def _construct_containers(data):                  #  construct each container and populate with with Items
    Container.all_containers.clear()

    for entry in data:
        container = _construct_container_from_spec(entry)

        # Add contained items
        for item_spec in entry.get("items", []):
            container.add_item(_construct_item_from_spec(item_spec))

    return Container.all_containers


def _construct_feature_from_spec(spec):
    return construct_from_spec(spec, Feature)
 





def _construct_rooms(data):
    """Construct Room objects from loaded JSON data list.

    Each room dict should have 'name', 'description', optional 'items', optional 'Container', and optional 'connections'.
    Items can be strings or dicts with 'name', 'is_takeable', 'refuse_string'.
    """
    rooms: list[Room] = []
    pending_connections = []
    for entry in data:
        room = Room(
            entry.get("name"),
            entry.get("description", ""),
            found=entry.get("found", False),
            is_dark=entry.get("is_dark", False),
            has_water=entry.get("has_water", False),
            climb_refuse_string=entry.get("climb_refuse_string"),
            up_refuse_string=entry.get("up_refuse_string"),
            down_refuse_string=entry.get("down_refuse_string"),
            east_refuse_string=entry.get("east_refuse_string"),
            west_refuse_string=entry.get("west_refuse_string"),
            north_refuse_string=entry.get("north_refuse_string"),
            south_refuse_string=entry.get("south_refuse_string"),
            dark_description=entry.get("dark_description"),
            discover_points=entry.get("discover_points", 10),
        )
        rooms.append(room)

        # Add items to the room
        for item_spec in entry.get("items", []):
            room.items.append(_construct_item_from_spec(item_spec))
        # Add Containers to the room
        for container_data in entry.get("containers", []):
            container = _construct_container_from_spec(container_data)

            for item_spec in container_data.get("items", []):
                item_obj = _construct_item_from_spec(item_spec)
                container.add_item(item_obj)

            room.add_container(container) 

        # Add Features to the room
        for feature_data in entry.get("features", entry.get("", [])):
            feature = _construct_feature_from_spec(feature_data)
            room.add_feature(feature)

        room.swim_exits = entry.get("swim_exits", {})
        room.climb_exits = entry.get("climb_exits", {})

        hidden_directions = entry.get("hidden_directions", entry.get("hidden_exits", []))
        pending_connections.append((room, entry.get("connections", {}), hidden_directions))

    # ------------------------------------------------------------
    # Connect rooms
    # ------------------------------------------------------------

    room_by_name = {room.name: room for room in rooms}
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
        # Resolve swim_exits 
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

        # ------------------------------------------------------------
        # Resolve climb_exits 
        # ------------------------------------------------------------
        raw_climb_exits = getattr(room, "climb_exits", {})
        resolved_climb_exits = {}

        for direction, dest_name in raw_climb_exits.items():
            dest_room = room_by_name.get(dest_name)
            if dest_room:
                resolved_climb_exits[direction] = dest_room
            else:
                print(f"DEBUG: Climb exit destination '{dest_name}' not found for room '{room.name}'.")

        room.climb_exits = resolved_climb_exits

    return rooms

