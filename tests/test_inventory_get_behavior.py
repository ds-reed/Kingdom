from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from kingdom.language.executor import execute
from kingdom.language.interpreter import InterpretedCommand
from kingdom.language.interpreter import interpret
from kingdom.language.lexicon import lex
from kingdom.language.parser import parse
from kingdom.model.game_model import Game, get_game
from kingdom.model.noun_model import Feature, Player, World
from kingdom.engine.verbs.verb_registration import register_verbs


def _run_command(game: Game, command: str) -> str:
    lexicon = lex()
    parsed = parse(command, lexicon)
    interpreted = interpret(parsed, game, lexicon)
    if not interpreted:
        return "UNKNOWN"

    messages: list[str] = []
    for cmd in interpreted:
        outcome = execute(cmd, game, command)
        if outcome is not None and outcome.message is not None:
            messages.append(str(outcome.message))

    return "\n".join(messages)


def test_get_all_skips_open_container_contents_but_get_single_pulls_from_open_container() -> None:
    game = get_game()
    game.reset_all_state()

    world = World()
    game.world = world
    game.setup_world(PROJECT_ROOT / "data" / "initial_state.json")

    player = Player("InventoryHero")
    game.init_session(
        world=world,
        current_player=player,
        player_name=player.name,
    )
    register_verbs()
    room = game.current_room

    bag = next((container for container in room.containers if container.obj_handle() == "bag"), None)
    assert bag is not None

    open_result = _run_command(game, "open lunch bag")
    assert isinstance(open_result, str)
    assert "bag" in open_result.lower()
    assert bag.is_open

    inventory_handles_before_get_all = {item.obj_handle() for item in player.get_inventory_items()}

    get_all_result = _run_command(game, "get all")
    assert "you get" in get_all_result.lower()

    inventory_handles_after_get_all = {item.obj_handle() for item in player.get_inventory_items()}
    bag_handles_after_get_all = {item.obj_handle() for item in bag.contents}

    # Room-level takeables are still picked up by get all.
    assert len(inventory_handles_after_get_all) > len(inventory_handles_before_get_all)
    # Open-container contents should not be pulled by get all.
    assert "fish" not in inventory_handles_after_get_all
    assert "fish" in bag_handles_after_get_all

    get_fish_result = _run_command(game, "get fish")
    assert "you see no fish here" in get_fish_result.lower()

    get_fish_from_bag_result = _run_command(game, "get fish from lunch bag")
    assert "you get" in get_fish_from_bag_result.lower() and "fish" in get_fish_from_bag_result.lower()

    inventory_handles_after_get_fish = {item.obj_handle() for item in player.get_inventory_items()}
    bag_handles_after_get_fish = {item.obj_handle() for item in bag.contents}

    # Opaque-container contents require an explicit source.
    assert "fish" in inventory_handles_after_get_fish
    assert "fish" not in bag_handles_after_get_fish


def test_get_feature_returns_custom_refusal_without_crashing() -> None:
    game = get_game()
    game.reset_all_state()

    world = World()
    game.world = world
    game.setup_world(PROJECT_ROOT / "data" / "initial_state.json")

    player = Player("InventoryHero")
    game.init_session(
        world=world,
        current_player=player,
        player_name=player.name,
    )
    register_verbs()

    bench = Feature(
        "bench",
        description="a broken bench",
        handle="bench",
        take_refuse_description="The bench is too heavy for you to take.",
    )
    game.current_room.add_feature(bench)

    result = _run_command(game, "get bench")

    assert isinstance(result, str)
    assert "too heavy" in result.lower()


def test_get_feature_without_custom_refusal_uses_generic_message() -> None:
    game = get_game()
    game.reset_all_state()

    world = World()
    game.world = world
    game.setup_world(PROJECT_ROOT / "data" / "initial_state.json")

    player = Player("InventoryHero")
    game.init_session(
        world=world,
        current_player=player,
        player_name=player.name,
    )
    register_verbs()

    statue = Feature("statue", description="a marble statue", handle="statue")
    game.current_room.add_feature(statue)

    result = _run_command(game, "get statue")

    assert isinstance(result, str)
    assert "you can't get" in result.lower()


def test_take_uses_roles_source_when_prep_phrases_are_absent() -> None:
    game = get_game()
    game.reset_all_state()

    world = World()
    game.world = world
    game.setup_world(PROJECT_ROOT / "data" / "initial_state.json")

    player = Player("InventoryHero")
    game.init_session(
        world=world,
        current_player=player,
        player_name=player.name,
    )
    register_verbs()

    bag = next((container for container in game.current_room.containers if container.obj_handle() == "bag"), None)
    assert bag is not None
    bag.is_open = True

    lexicon = lex()
    parsed = parse("get fish from lunch bag", lexicon)
    interpreted = interpret(parsed, game, lexicon)
    assert len(interpreted) == 1

    original = interpreted[0]
    cmd_without_prep = InterpretedCommand(
        verb=original.verb,
        verb_token=original.verb_token,
        all_tokens=original.all_tokens,
        verb_source=original.verb_source,
        direct=original.direct,
        direct_object_token=original.direct_object_token,
        prep_phrases=[],
        roles=dict(original.roles),
        direction=original.direction,
        direction_tokens=original.direction_tokens,
        modifier_tokens=original.modifier_tokens,
    )

    outcome = execute(cmd_without_prep, game, "get fish from lunch bag")

    assert outcome.status.name == "SUCCESS"
    assert "you get" in (outcome.message or "").lower()
    assert "fish" in (outcome.message or "").lower()
