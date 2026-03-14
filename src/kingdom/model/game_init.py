"""World state intialization and management

Handles world loading, serialization, and runtime entity management.
"""

from __future__ import annotations
from collections import deque
import json
from pathlib import Path
from dataclasses import dataclass, fields as dataclass_fields
from kingdom.model.direction_model import DIRECTIONS 
from kingdom.model.noun_model import (
    Noun,
    Item,
    Feature,
    Container,
    Player,
    Room,
    World,
)


class Game:
    def __init__(self):

        # Core session state
        self.world: World | None = None
        self.current_player: Player | None = None
        self.player_name: str | None = None
        self.current_room: Room | None = None

        # game data fields
        self.lexicon: "Lexicon" | None = None
        self.prefs: SessionPrefs | None = None

        # Persistent metrics (saved/loaded)
        self.rooms_found: int = 0
        self.items_found: int = 0
        self.score: int = 0

        # Ephemeral metrics (reset on load)
        self.rooms_found_since_load: int = 0
        self.items_found_since_load: int = 0
        self.score_since_load: int = 0
        self.recent_commands: deque[str] = deque(maxlen=10)


    def init_session(
        self,
        world=None,
        current_player=None,
        player_name=None,
        initial_room=None,
        save_path=None,
    ):
        # Core session state
        self.world = world
        self.current_player = current_player
        self.player_name = player_name
        self.current_room = initial_room
        self.score = 0

        # Preferences
        self.prefs = SessionPrefs(
            save_directory=save_path.parent if save_path else Path("saves"),
            last_save_filename=save_path.name if save_path else "quicksave.json",
            player_name=self.player_name,
        )

        # Persistent metrics (new playthrough starts fresh)
        self.rooms_found = 0
        self.items_found = 0
        self.score = 0

        # Ephemeral metrics (reset on new session)
        self.rooms_found_since_load = 0
        self.items_found_since_load = 0
        self.score_since_load = 0

        self.recent_commands.clear()


        # Rebuild noun layer for this world
    #   if self.world:
    #       self.lexicon.reset_nouns(self.world)




    def get_prefs(self):
        if self.prefs is None:
            raise RuntimeError("Session preferences not initialized")
        return self.prefs

    def set_prefs(self, new_prefs):
        self.prefs = new_prefs

    def reset_all_state(self):
        # Reset session-level fields
        self.world = None
        self.current_player = None
        self.player_name = None
        self.current_room = None
        self.score = 0

        self.rooms_found = 0
        self.items_found = 0
        self.rooms_found_since_load = 0
        self.items_found_since_load = 0
        self.score_since_load = 0
        self.recent_commands.clear()

        # Reset prefs
        self.prefs = None

        # Reset global noun/container registries
        Container.all_containers.clear()
        Noun.all_nouns.clear()
        Noun._by_name = {}



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


def get_game() -> Game:
    return _game



# Global game instance
_game = Game()


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


    _load_directions(data)

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
        container = construct_from_spec(entry, Container)

        # Add contained items
        for item_spec in entry.get("items", []):
            container.add_item(_construct_item_from_spec(item_spec))

    return Container.all_containers


def _construct_feature_from_spec(spec):
    return construct_from_spec(spec, Feature)
 

def _construct_rooms(data):
    rooms = []

    # Phase 1: Construct all rooms
    for entry in data:
        room = construct_from_spec(entry, Room)
        rooms.append(room)


    # Phase 2: Populate rooms
    for entry, room in zip(data, rooms):
        for item_spec in entry.get("items", []):
            room.items.append(_construct_item_from_spec(item_spec))

        for container_data in entry.get("containers", []):
            container = _construct_container_from_spec(container_data)
            for item_spec in container_data.get("items", []):
                container.add_item(_construct_item_from_spec(item_spec))
            room.add_container(container)

        for feature_data in entry.get("features", []):
            room.add_feature(_construct_feature_from_spec(feature_data))


    # Phase 3: Resolve unified exits
    room_by_name = {room.name: room for room in rooms}

    for entry, room in zip(data, rooms):
        exits_block = entry.get("exits", {})
        _resolve_unified_exits(room, exits_block, room_by_name)

    return rooms

def _resolve_unified_exits(room, exits_block, room_by_name):
    for movement_type, movement_dict in exits_block.items():
        for direction, exit_obj in movement_dict.items():
            dest_name = exit_obj.get("destination")
            dest_room = room_by_name.get(dest_name) if dest_name else None

            room.add_exit(
                movement_type=movement_type,
                direction=direction,
                destination=dest_room,
                is_visible=exit_obj.get("is_visible", True),
                is_passable=exit_obj.get("is_passable", True),
                refuse_string=exit_obj.get("refuse_string"),
                go_refuse_string=exit_obj.get("go_refuse_string")
            )

