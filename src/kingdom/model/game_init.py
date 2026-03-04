"""World state intialization and management

Handles world loading, serialization, and runtime entity management.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, Optional
from enum import Enum, auto
from dataclasses import dataclass, fields as dataclass_fields
from kingdom.model.noun_model import (
    Noun,
    DirectionNoun,
    Item,
    Container,
    Player,
    Room,
    Feature,
    World,
)


@dataclass
class GameActionState:
    game: World | None = None
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
        game=world,
        current_player=resolved_player,
        current_room=initial_room,
        player_name=resolved_player_name,
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

    world = getattr(new_state, "game", None)
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


class GameOver(Exception):
    pass

class QuitGame(Exception):
    pass

class SaveGame(Exception):
    pass

class LoadGame(Exception):
    pass

            
def _construct_item_from_spec(item_spec) -> "Item":
    if isinstance(item_spec, str):
        return Item(item_spec)

    if not isinstance(item_spec, dict):
        raise TypeError("Item spec must be a dict")

    normalized = dict(item_spec)

    init_field_names = {f.name for f in dataclass_fields(Item) if f.init}
    constructor_kwargs = {
        key: value
        for key, value in normalized.items()
        if key in init_field_names
    }

    return Item(**constructor_kwargs)





#----- functions for constructing objects from JSON data -----

def _construct_containers(data):
    """Construct Container objects from loaded JSON data list.

    Expects `data` to be a list of dicts with keys like 'name', 'description', 'items', etc.
    """
    Container.all_containers.clear()           # Clear for clean load
    Container._by_name.clear()

    for entry in data:
        container = _construct_container_from_spec(entry)

        # Add contained items
        for item_spec in entry.get("items", []):
            new_item = _construct_item_from_spec(item_spec)
            container.add_item(new_item)

    return Container.all_containers


def _construct_container_from_spec(container_spec) -> "Container":
    if isinstance(container_spec, str):
        return Container(name=container_spec)

    if not isinstance(container_spec, dict):
        raise TypeError("Container spec must be a dict")

    init_field_names = {f.name for f in dataclass_fields(Container) if f.init}

    normalized = dict(container_spec)
    if "name" not in normalized:
        if normalized.get("box_name"):
            normalized["name"] = normalized["box_name"]
        elif normalized.get("canonical_name"):
            normalized["name"] = normalized["canonical_name"]

    if "handle" not in normalized and normalized.get("canonical_name"):
        normalized["handle"] = normalized["canonical_name"]

    constructor_kwargs = {
        key: value
        for key, value in normalized.items()
        if key in init_field_names
    }

    return Container(**constructor_kwargs)

def _construct_rooms(data):
    """Construct Room objects from loaded JSON data list.

    Each room dict should have 'name', 'description', optional 'items', optional 'Container', and optional 'connections'.
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
        # Add Containers to the room
        for container_data in entry.get("Container", []):
            container = _construct_container_from_spec(container_data)

            for item_spec in container_data.get("items", []):
                item_obj = _construct_item_from_spec(item_spec)
                container.add_item(item_obj)

            room.add_container(container) 

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

