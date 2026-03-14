"""World state intialization and management

Handles world loading, serialization, and runtime entity management.
"""

from __future__ import annotations
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
        self.action_state: GameActionState | None = None
        self.prefs: SessionPrefs | None = None

    def init_session(self, world=None, current_player=None, initial_room=None,
                     player_name=None, save_path=None):

        resolved_player = current_player
        resolved_player_name = player_name or getattr(resolved_player, "name", None)

        self.action_state = GameActionState(
            world=world,
            current_player=resolved_player,
            current_room=initial_room,
            player_name=resolved_player_name,
            lexicon=None,
            score=0,
        )

        self.prefs = SessionPrefs(
            save_directory=save_path.parent if save_path else Path("saves"),
            last_save_filename=save_path.name if save_path else "quicksave.json",
            player_name=resolved_player_name,
        )

    def get_action_state(self):
        if self.action_state is None:
            raise RuntimeError("Action state not initialized")
        return self.action_state

    def set_action_state(self, new_state):
        self.action_state = new_state

    def get_prefs(self):
        if self.prefs is None:
            raise RuntimeError("Session preferences not initialized")
        return self.prefs

    def set_prefs(self, new_prefs):
        self.prefs = new_prefs

    def reset_all_state(self):
        self.action_state = None
        self.prefs = None

        Container.all_containers.clear()
        Noun.all_nouns.clear()
        Noun._by_name = {}



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


def get_game() -> Game:
    return _game


def init_session(
    world: World | None = None,
    current_player: Player | None = None,
    initial_room: Room | None = None,
    player_name: str | None = None,
    save_path: Path | None = None,
) -> None:
    global _game

    resolved_player = current_player
    resolved_player_name = player_name or getattr(resolved_player, "name", None)

    _game.action_state = GameActionState(
        world=world,
        current_player=resolved_player,
        current_room=initial_room,
        player_name=resolved_player_name,
        lexicon=None,
        score=0,
    )

    _game.prefs = SessionPrefs(
        save_directory=save_path.parent if save_path else Path("saves"),
        last_save_filename=save_path.name if save_path else "quicksave.json",
        player_name=resolved_player_name,
    )



_game = Game()

def init_session(*args, **kwargs):
    return _game.init_session(*args, **kwargs)

#def get_action_state():
#    return _game.get_action_state()

def set_action_state(new_state):
    return _game.set_action_state(new_state)

def get_prefs():
    return _game.get_prefs()

def set_prefs(new_prefs):
    return _game.set_prefs(new_prefs)

def reset_all_state():
    return _game.reset_all_state()



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

