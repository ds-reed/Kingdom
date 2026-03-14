from __future__ import annotations

import json
from pathlib import Path 

from . import game_init as model_api
from .noun_model import Player, Item
from .direction_model import DIRECTIONS


def _serialize_directions() -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}

    for canonical in sorted(DIRECTIONS.get_all_directions()):
        synonyms = sorted(DIRECTIONS.get_synonyms(canonical))

        entry: dict[str, object] = {}
        reverse = DIRECTIONS.get_reverse(canonical)
        if reverse is not None:
            entry["reverse"] = reverse
        if synonyms:
            entry["synonyms"] = synonyms
        payload[canonical] = entry

    return payload


def load_game(world, filepath) -> Path:
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

    action_state = model_api.get_game().action_state
    action_state.player_name = player_name

    if action_state.current_player is None:
        action_state.current_player = Player(player_name)
    model_api.setup_world(world, data)

    player = action_state.current_player
    if player is None:
        raise RuntimeError("No hero is active yet.")

    player.sack.contents.clear()
    if player_data:
        for item_json in player_data.get("inventory", []):
            item = model_api._construct_item_from_spec(item_json)
            player.sack.add_item(item)

    if current_room_name and current_room_name in world.rooms:
        model_api.get_game().action_state.current_room = world.rooms[current_room_name]

    model_api.get_game().action_state.score = int(data.get("score", 0))

    return target


def save_game(world, filepath) -> Path:
    target = Path(filepath).expanduser()
    if not target.suffix:
        target = target.with_suffix(".json")
    if target.name == "initial_state.json":
        raise RuntimeError("Refusing to overwrite initial_state.json")
    target.parent.mkdir(parents=True, exist_ok=True)

    action_state = model_api.get_game().action_state
    player = action_state.current_player

    payload = {
        "directions": _serialize_directions(),
        "player": {
            "name": player.name,
            "inventory": [Item._serialize_item(item) for item in player.sack.contents],
        }
        if player
        else None,
        "current_room": action_state.current_room.name,
        "start_room": world.start_room_name,
        "score": int(action_state.score),
        "rooms": [],
    }

    for room in world.rooms.values():
        payload["rooms"].append(room.to_dict())


    try:
        with target.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)
    except OSError as error:
        raise RuntimeError(f"Unable to write save file: {target} ({error})") from error

    return target
