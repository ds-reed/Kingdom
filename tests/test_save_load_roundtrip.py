from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kingdom.model.game_init import get_action_state, init_session, reset_all_state, setup_world
from kingdom.model.game_persistence import load_game, save_game
from kingdom.model.noun_model import Container, Item, Player, Room, World


ROOM_FIELDS = [
    "name",
    "description",
    "found",
    "discover_points",
    "is_climbable",
]

CONTAINER_FIELDS = [
    "name",
    "handle",
    "description",
    "capacity",
    "is_openable",
    "is_open",
    "opened_state_description",
    "closed_state_description",
    "open_action_description",
    "close_action_description",
    "is_lockable",
    "is_locked",
    "unlock_key",
    "locked_description",
    "open_exit_direction",
    "open_exit_destination",
    "examine_string",
]

ITEM_FIELDS = [
    "name",
    "is_gettable",
    "refuse_string",
    "presence_string",
    "handle",
    "is_openable",
    "is_open",
    "opened_state_description",
    "closed_state_description",
    "lit_state_description",
    "unlit_state_description",
    "open_action_description",
    "close_action_description",
    "examine_string",
    "open_exit_direction",
    "open_exit_destination",
    "is_lockable",
    "is_locked",
    "unlock_key",
    "locked_state_description",
    "unlocked_state_description",
    "unlockable_description",
    "is_edible",
    "is_verbally_interactive",
    "is_lightable",
    "is_lit",
    "can_ignite",
    "ignite_success_string",
    "is_rubbable",
    "is_rubbed",
    "rubbed_state_description",
    "rub_success_string",
    "trigger_room",
    "too_heavy_to_swim",
    "eat_refuse_string",
    "eaten_success_string",
    "get_refuse_string",
    "special_handlers",
]


def _norm(value):
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, set):
        return sorted(value)
    return value


def _compare_fields(entity_name: str, before_obj, after_obj, fields: list[str]) -> list[str]:
    mismatches: list[str] = []
    for field in fields:
        before_value = _norm(getattr(before_obj, field, None))
        after_value = _norm(getattr(after_obj, field, None))
        if before_value != after_value:
            mismatches.append(
                f"{entity_name}.{field}: before={before_value!r} after={after_value!r}"
            )
    return mismatches


def test_save_load_roundtrip_preserves_tracked_room_container_item_fields(tmp_path: Path) -> None:
    reset_all_state()

    base_dir = Path(__file__).resolve().parents[1]
    data_path = base_dir / "data" / "initial_state.json"
    save_path = tmp_path / "roundtrip_validation.tmp.json"

    game = World()
    setup_world(game, data_path)

    player = Player("RoundtripHero")

    start_room = game.rooms.get(game.start_room_name)
    init_session(
        world=game,
        current_player=player,
        initial_room=start_room,
        player_name=player.name,
        save_path=save_path,
    )
    get_action_state().score = 123

    anchor = next(iter(game.rooms.values()))

    sentinel_room = Room(
        name="__roundtrip_room__",
        description="Roundtrip validation room",
        found=True,
        discover_points=77,
    )
    sentinel_room.connections["west"] = anchor
    sentinel_room.hidden_directions.add("west")
    sentinel_room.swim_exits["east"] = anchor
    sentinel_room.climb_exits["down"] = anchor
    sentinel_room.is_climbable = True
    game.rooms[sentinel_room.name] = sentinel_room

    sentinel_container = Container(
        name="Roundtrip Box",
        handle="rt_box",
        description="A sentinel box sits here.",
        capacity=3,
        is_openable=True,
        is_open=True,
        opened_state_description="The sentinel box is open.",
        closed_state_description="The sentinel box is closed.",
        open_action_description="You open the sentinel box.",
        close_action_description="You close the sentinel box.",
        is_lockable=True,
        is_locked=True,
        unlock_key="rt_key",
        locked_description="The sentinel box is locked tight.",
        open_exit_direction="down",
        open_exit_destination=anchor.name,
        examine_string="A carefully instrumented box.",
    )
    sentinel_room.add_container(sentinel_container)

    sentinel_item = Item(
        name="Roundtrip Item",
        is_gettable=False,
        refuse_string="You may not take the sentinel item.",
        presence_string="A sentinel item glows here.",
        handle="rt_item",
        is_openable=True,
        is_open=True,
        opened_state_description="It is open.",
        closed_state_description="It is closed.",
        lit_state_description="It is lit.",
        unlit_state_description="It is unlit.",
        open_action_description="You open it.",
        close_action_description="You close it.",
        examine_string="Highly instrumented test item.",
        open_exit_direction="up",
        open_exit_destination=anchor.name,
        is_lockable=True,
        is_locked=True,
        unlock_key="rt_item_key",
        locked_state_description="Locked item.",
        unlocked_state_description="Unlocked item.",
        unlockable_description="Needs a specific key.",
        is_edible=True,
        is_verbally_interactive=True,
        is_lightable=True,
        is_lit=True,
        can_ignite=True,
        ignite_success_string="Ignited.",
        is_rubbable=True,
        is_rubbed=True,
        rubbed_state_description="Rubbed smooth.",
        rub_success_string="You rub the item.",
        trigger_room=sentinel_room.name,
        too_heavy_to_swim=True,
        eat_refuse_string="Do not eat this.",
        eaten_success_string="Crunch.",
        get_refuse_string="No getting this one.",
        special_handlers={"rub": "rub_lamp", "eat": "eat_fish"},
    )
    sentinel_room.add_item(sentinel_item)

    # These room flags are world-data invariants; validate they survive save/load for existing rooms.
    invariant_snapshot_before = {
        room_name: (room.is_dark, room.has_water, room.dark_description)
        for room_name, room in game.rooms.items()
    }

    save_game(game, save_path)

    # Loader currently expects lowercase room collection keys.
    with save_path.open("r", encoding="utf-8") as saved_file:
        saved_data = json.load(saved_file)
    saved_sentinel_room = next(
        room for room in saved_data["rooms"] if room.get("name") == "__roundtrip_room__"
    )
    assert "containers" in saved_sentinel_room, "saved room payload must use lowercase 'containers'"
    assert "features" in saved_sentinel_room, "saved room payload must use lowercase 'features'"

    load_game(game, save_path)

    invariant_snapshot_after = {
        room_name: (room.is_dark, room.has_water, room.dark_description)
        for room_name, room in game.rooms.items()
    }
    for room_name, before_values in invariant_snapshot_before.items():
        assert invariant_snapshot_after.get(room_name) == before_values, (
            f"Invariant mismatch for {room_name}: "
            f"before={before_values!r} after={invariant_snapshot_after.get(room_name)!r}"
        )

    loaded_room = game.rooms.get("__roundtrip_room__")
    assert loaded_room is not None, "sentinel room missing after load"

    loaded_container = next(
        (container for container in loaded_room.containers if container.obj_handle() == "rt_box"),
        None,
    )
    assert loaded_container is not None, "sentinel container missing after load"

    loaded_item = next((item for item in loaded_room.items if item.obj_handle() == "rt_item"), None)
    assert loaded_item is not None, "sentinel item missing after load"

    mismatches: list[str] = []
    mismatches.extend(_compare_fields("Room", sentinel_room, loaded_room, ROOM_FIELDS))
    mismatches.extend(_compare_fields("Container", sentinel_container, loaded_container, CONTAINER_FIELDS))
    mismatches.extend(_compare_fields("Item", sentinel_item, loaded_item, ITEM_FIELDS))

    before_connections = {k: v.name for k, v in sentinel_room.connections.items()}
    after_connections = {k: v.name for k, v in loaded_room.connections.items()}
    if before_connections != after_connections:
        mismatches.append(
            f"Room.connections: before={before_connections!r} after={after_connections!r}"
        )

    before_swim = {k: v.name for k, v in sentinel_room.swim_exits.items()}
    after_swim = {k: v.name for k, v in loaded_room.swim_exits.items()}
    if before_swim != after_swim:
        mismatches.append(
            f"Room.swim_exits: before={before_swim!r} after={after_swim!r}"
        )

    before_climb = {k: v.name for k, v in sentinel_room.climb_exits.items()}
    after_climb = {k: v.name for k, v in loaded_room.climb_exits.items()}
    if before_climb != after_climb:
        mismatches.append(
            f"Room.climb_exits: before={before_climb!r} after={after_climb!r}"
        )

    if sorted(sentinel_room.hidden_directions) != sorted(loaded_room.hidden_directions):
        mismatches.append(
            "Room.hidden_directions: "
            f"before={sorted(sentinel_room.hidden_directions)!r} "
            f"after={sorted(loaded_room.hidden_directions)!r}"
        )

    assert not mismatches, "save/load roundtrip mismatches detected:\n" + "\n".join(
        f" - {mismatch}" for mismatch in mismatches
    )
