from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kingdom.model.game_init import init_session, reset_all_state, setup_world
from kingdom.model.game_persistence import load_game, save_game
from kingdom.model.noun_model import Player, World


def _find_room(world: World, room_name: str):
    room = world.rooms.get(room_name)
    assert room is not None, f"Room not found: {room_name}"
    return room


def _find_container(room, container_name: str):
    for container in room.containers:
        if container.name == container_name:
            return container
    assert False, f"Container not found in {room.name}: {container_name}"


def _bootstrap_world(save_path: Path) -> World:
    reset_all_state()
    world = World()
    setup_world(world, "data/initial_state.json")

    start_room = _find_room(world, world.start_room_name)
    player = Player("TestHero")
    init_session(
        world=world,
        current_player=player,
        initial_room=start_room,
        player_name=player.name,
        save_path=save_path,
    )
    return world


def test_removed_items_do_not_reappear_and_empty_container_stays_empty(tmp_path: Path) -> None:
    save_path = tmp_path / "container_state_roundtrip.json"

    world = _bootstrap_world(save_path)

    tower_cell = _find_room(world, "Tower Cell")
    lunch_bag = _find_container(tower_cell, "lunch bag")

    initial_names = [item.name for item in lunch_bag.contents]
    assert len(initial_names) > 0

    removed_item = lunch_bag.contents[0]
    removed_name = removed_item.name
    lunch_bag.remove_item(removed_item)

    assert removed_name not in [item.name for item in lunch_bag.contents]
    assert len(lunch_bag.contents) == len(initial_names) - 1

    save_game(world, save_path)
    load_game(world, save_path)

    tower_cell_after_first_load = _find_room(world, "Tower Cell")
    lunch_bag_after_first_load = _find_container(tower_cell_after_first_load, "lunch bag")

    assert removed_name not in [item.name for item in lunch_bag_after_first_load.contents]

    for item in list(lunch_bag_after_first_load.contents):
        lunch_bag_after_first_load.remove_item(item)

    assert lunch_bag_after_first_load.contents == []

    save_game(world, save_path)
    load_game(world, save_path)

    tower_cell_after_second_load = _find_room(world, "Tower Cell")
    lunch_bag_after_second_load = _find_container(tower_cell_after_second_load, "lunch bag")

    assert lunch_bag_after_second_load.contents == []


def test_initially_empty_container_stays_empty_after_save_load(tmp_path: Path) -> None:
    save_path = tmp_path / "empty_container_roundtrip.json"

    world = _bootstrap_world(save_path)

    pool_ledge = _find_room(world, "Pool Ledge")
    wardrobe = _find_container(pool_ledge, "wardrobe")

    assert wardrobe.contents == []

    save_game(world, save_path)
    load_game(world, save_path)

    pool_ledge_after_load = _find_room(world, "Pool Ledge")
    wardrobe_after_load = _find_container(pool_ledge_after_load, "wardrobe")

    assert wardrobe_after_load.contents == []
