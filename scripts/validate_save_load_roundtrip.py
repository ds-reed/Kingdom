from __future__ import annotations

import sys
from pathlib import Path

sys.path.append("./src")

from kingdom.model.noun_model import World, Player, Room, Container, Item
from kingdom.model.game_init import init_session, get_action_state, setup_world
from kingdom.model.game_persistence import save_game, load_game


ROOM_FIELDS = [
    "name",
    "description",
    "visited",
    "is_dark",
    "has_water",
    "dark_description",
    "discover_points",
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
    "noun_name",
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


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]
    data_path = base_dir / "data" / "initial_state.json"
    save_path = base_dir / "data" / "roundtrip_validation.tmp.json"

    game = World.get_instance()
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
        visited=True,
        is_dark=True,
        has_water=True,
        dark_description="Pitch black sentinel room",
        discover_points=77,
    )
    sentinel_room.connections["west"] = anchor
    sentinel_room.hidden_directions.add("west")
    sentinel_room.swim_exits["east"] = anchor
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
        noun_name="rt_item",
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

    save_game(game, save_path)
    load_game(game, save_path)

    loaded_room = game.rooms.get("__roundtrip_room__")
    if loaded_room is None:
        print("FAIL: sentinel room missing after load")
        return 1

    loaded_container = next(
        (container for container in loaded_room.containers if container.canonical_name() == "rt_box"),
        None,
    )
    if loaded_container is None:
        print("FAIL: sentinel container missing after load")
        return 1

    loaded_item = next((item for item in loaded_room.items if item.noun_name == "rt_item"), None)
    if loaded_item is None:
        print("FAIL: sentinel item missing after load")
        return 1

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

    if sorted(sentinel_room.hidden_directions) != sorted(loaded_room.hidden_directions):
        mismatches.append(
            "Room.hidden_directions: "
            f"before={sorted(sentinel_room.hidden_directions)!r} "
            f"after={sorted(loaded_room.hidden_directions)!r}"
        )

    if save_path.exists():
        save_path.unlink()

    if mismatches:
        print("FAIL: save/load roundtrip mismatches detected")
        for mismatch in mismatches:
            print(f" - {mismatch}")
        return 1

    print("PASS: save/load roundtrip preserves all tracked Room/Container/Item constructor fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
