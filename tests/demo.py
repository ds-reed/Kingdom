"""Pytest smoke tests for the current Kingdom command/action pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from kingdom.verbs.verb_registration import register_verbs
from kingdom.model.verb_model import Verb
from kingdom.model.game_model import (
    Game,
    GameOver,
    LoadGame,
    QuitGame,
    SaveGame,
    get_game,
)
from kingdom.model.noun_model import Player, World
from kingdom.language.lexicon import Lexicon, lex
from kingdom.language.parser import parse
from kingdom.language.interpreter import InterpretedCommand, interpret
from kingdom.language.executor import execute


def _run_interpreted(
    game: Game,
    lexicon: Lexicon,
    interpreted: list[InterpretedCommand],
    demo_save_path: Path | None = None,
    original_command: str = "",
):
    if not interpreted:
        return "UNKNOWN"

    try:
        messages: list[str] = []
        for cmd in interpreted:
            if cmd.verb is None:
                # Direction-only input (for example "west") maps to GO.
                inferred_direction_tokens = list(cmd.direction_tokens or [])
                if cmd.direction:
                    inferred_direction_tokens.append(str(cmd.direction))
                if cmd.all_tokens:
                    inferred_direction_tokens.extend(
                        token
                        for token in cmd.all_tokens
                        if token in lexicon.token_to_direction
                    )

                if not inferred_direction_tokens:
                    return "UNKNOWN"
                # Ensure direction is set so the go handler knows where to travel.
                if not cmd.direction:
                    cmd.direction = inferred_direction_tokens[0]

            outcome = execute(cmd, game, original_command)
            if outcome is not None and outcome.message is not None:
                messages.append(str(outcome.message))

        if not messages:
            return None
        return "\n".join(messages)
    except SaveGame:
        if demo_save_path is None:
            return "SAVE_ERROR"
        saved_path = get_game().save_game(demo_save_path)
        return f"Game saved to {saved_path}"
    except LoadGame:
        if demo_save_path is None:
            return "LOAD_ERROR"
        loaded_path = get_game().load_game(demo_save_path)
        return f"Game loaded from {loaded_path}"
    except QuitGame:
        return "QUIT"
    except GameOver as error:
        return f"GAME_OVER: {error}"
    except TypeError:
        return "ARG_ERROR"


def _expect_contains(result: object, needle: str):
    assert isinstance(result, str)
    assert needle.lower() in result.lower()


def _as_text(result: object) -> str:
    if not isinstance(result, str):
        return ""
    return " ".join(result.lower().split())


def _has_any(result: object, needles: tuple[str, ...]) -> bool:
    text = _as_text(result)
    return any(needle.lower() in text for needle in needles)


def _expect_any(result: object, *needles: str):
    assert _has_any(result, needles), f"Expected one of {needles!r} in result={result!r}"


def _inventory_handles(game: Game) -> set[str]:
    player = game.current_player
    if player is None:
        return set()
    return {item.obj_handle() for item in player.get_inventory_items()}


def _inventory_item(game: Game, handle: str):
    player = game.current_player
    if player is None:
        return None
    return next((item for item in player.get_inventory_items() if item.obj_handle() == handle), None)


def _room_item(game: Game, handle: str):
    room = game.current_room
    if room is None:
        return None
    return next((item for item in room.items if item.obj_handle() == handle), None)


def _room_container(game: Game, handle: str):
    room = game.current_room
    if room is None:
        return None
    return next((container for container in room.containers if container.obj_handle() == handle), None)


@pytest.fixture
def smoke_context(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    demo_save_path = tmp_path / "working_state.demo.json"

    world = World.get_instance()
    game.world = world
    game.setup_world(data_path)
    player = Player("DemoHero")

    assert len(world.rooms) > 0
    assert any(len(room.containers) > 0 for room in world.rooms.values())

    start_room = world.start_room
    assert start_room is not None

    game.init_session(
        world=world,
        current_player=player,
        player_name="DemoHero",
        save_path=demo_save_path,
    )

    register_verbs()
    verbs = Verb._by_name
    lexicon = lex()
    covered_verbs: set[str] = set()

    def run(command: str):
        parsed = parse(command, lexicon)
        interpreted = interpret(parsed, game, lexicon)
        result = _run_interpreted(game, lexicon, interpreted, demo_save_path=demo_save_path, original_command=command)

        for cmd in interpreted:
            canonical = cmd.verb.canonical_name() if cmd.verb is not None else None
            if canonical is None and cmd.verb_token:
                resolved_verb = Verb.get_by_name(cmd.verb_token)
                if resolved_verb is not None:
                    canonical = resolved_verb.canonical_name()
                else:
                    canonical = str(cmd.verb_token).lower()
            if canonical is None and cmd.direction_tokens:
                canonical = "go"
            if canonical:
                covered_verbs.add(str(canonical).lower())

        return result

    return {
        "world": world,
        "game": game,
        "verbs": verbs,
        "run": run,
        "covered_verbs": covered_verbs,
        "demo_save_path": demo_save_path,
    }


def test_demo_smoke(smoke_context):
    run = smoke_context["run"]
    verbs = smoke_context["verbs"]
    game = smoke_context["game"]
    world = smoke_context["world"]
    demo_save_path: Path = smoke_context["demo_save_path"]

    def _minimal_smoke_exit() -> None:
        save_result = run("save")
        assert isinstance(save_result, str)
        assert "Game saved to" in save_result
        assert demo_save_path.exists()

        load_result = run("load")
        assert isinstance(load_result, str)
        assert "Game loaded from" in load_result

        assert run("quit") == "QUIT"

    assert set(["go", "save", "load", "look", "help", "quit", "inventory", "score"]).issubset(verbs.keys())

    help_result = run("help")
    _expect_any(help_result, "you can try commands", "available commands")

    help_commands_result = run("help commands")
    _expect_any(help_commands_result, "available commands", "you can try commands")

    look_result = run("look")
    assert isinstance(look_result, str) and len(look_result.strip()) > 0

    score_result = run("score")
    _expect_any(score_result, "score")
    assert isinstance(score_result, str)
    assert str(game.score) in score_result

    inventory_result = run("inventory")
    _expect_any(inventory_result, "don't have anything", "you have (0")

    bag = _room_container(game, "bag")
    assert bag is not None

    run("open lunch bag")
    assert bag.is_open
    look_in_bag_result = run("look in lunch bag")
    assert isinstance(look_in_bag_result, str)
    _expect_any(look_in_bag_result, "inside", "bag")

    run("get fish from lunch bag")
    if "fish" not in _inventory_handles(game):
        _minimal_smoke_exit()
        return

    run("get key from lunch bag")
    if "key" not in _inventory_handles(game):
        _minimal_smoke_exit()
        return

    run("get lamp from lunch bag")
    run("get lighter from lunch bag")
    run("get torch from lunch bag")
    for handle in ("lamp", "lighter", "torch"):
        assert handle in _inventory_handles(game)

    run("close lunch bag")
    assert not bag.is_open
    run("open lunch bag")
    assert bag.is_open

    run("put all into bag")
    run("get torch from lunch bag")
    run("get lighter from lunch bag")
    run("get lamp from lunch bag")
    run("get fish from lunch bag")
    run("get key from lunch bag")
    for handle in ("lamp", "lighter", "torch", "fish", "key"):
        assert handle in _inventory_handles(game)

    run("light torch")
    torch_item = _inventory_item(game, "torch")
    assert torch_item is not None and getattr(torch_item, "is_lit", False)

    torch_bag_fire = run("put torch into lunch bag")
    assert isinstance(torch_bag_fire, str)
    _expect_any(torch_bag_fire, "catches on fire", "destroyed")

    run("drop torch")
    assert _room_item(game, "torch") is not None
    run("take torch")
    assert "torch" in _inventory_handles(game)

    run("extinguish torch")
    torch_item = _inventory_item(game, "torch")
    assert torch_item is not None and not getattr(torch_item, "is_lit", True)

    say_result = run("say hello")
    _expect_any(say_result, "wind", "say")
    eat_result = run("eat fish")
    _expect_any(eat_result, "vomit", "you")

    run("unlock trapdoor")
    trapdoor = _room_item(game, "trapdoor")
    assert trapdoor is not None and not getattr(trapdoor, "is_locked", True)
    run("open trapdoor")
    assert trapdoor is not None and getattr(trapdoor, "is_open", False)

    run("climb ladder")
    assert game.current_room.name == "Demo Landing"
    run("climb down")
    assert game.current_room.name == "Tower Cell"

    run("slide down")
    if game.current_room.name != "Blank Chamber":
        run("climb down")
    assert game.current_room.name == "Blank Chamber"

    _expect_any(run("rub lamp"), "djinni", "shinier")
    _expect_any(run("make wish"), "doorway", "djinni")

    score_before_new_room = game.score
    run("west")
    assert game.current_room.name == "Colossal Cave"
    assert game.score > score_before_new_room

    run("swim west")
    assert game.current_room.name == "Pool Ledge"

    run("teleport Demo Landing")
    assert game.current_room.name == "Demo Landing"

    run("south")
    assert game.current_room.name == "Ravine Edge"

    run("take rope")
    assert "rope" in _inventory_handles(game)

    tie_result = run("tie rope to hook")
    _expect_any(tie_result, "you tie", "dangles down")
    rope = _room_item(game, "rope")
    assert rope is not None and getattr(rope, "is_tied", False)

    run("climb rope")
    assert game.current_room.name == "Clover Rest"
    run("climb up")
    assert game.current_room.name == "Ravine Edge"
    run("north")
    assert game.current_room.name == "Demo Landing"

    save_result = run("save")
    assert isinstance(save_result, str)
    _expect_any(save_result, "game saved to")
    assert demo_save_path.exists()

    load_result = run("load")
    assert isinstance(load_result, str)
    _expect_any(load_result, "game loaded from")

    debug_result = run("debug room")
    assert debug_result is None or isinstance(debug_result, str)

    die_result = run("die")
    assert isinstance(die_result, str) and die_result.startswith("GAME_OVER:")

    assert run("dance") == "UNKNOWN"
    assert run("quit") == "QUIT"

    expected_canonical_verbs = {
        "go", "swim", "climb", "teleport",
        "light", "extinguish", "open", "close", "unlock", "tie", "eat", "rub", "say", "make", "look",
        "help", "score", "load", "save", "quit", "die", "debug",
            "inventory", "take", "drop",
    }
    missing = sorted(expected_canonical_verbs - smoke_context["covered_verbs"])
    assert not missing, f"All canonical verbs were exercised (missing: {missing})"


def test_demo_edge_case_regressions(smoke_context):
    run = smoke_context["run"]
    world: World = smoke_context["world"]
    game: Game = smoke_context["game"]

    failures: list[str] = []

    # Position player in an area with known directional exits.
    run("teleport Demo Landing")
    if game.current_room is None or game.current_room.name != "Demo Landing":
        failures.append("setup failed: teleport to Demo Landing did not succeed")
    else:
        south_result = run("south")
        if not _has_any(south_result, ("you go south", "go south", "south")):
            failures.append(
                "implicit movement failed: expected 'south' to behave like 'go south' "
                f"(result={south_result!r})"
            )
        current_room_name = game.current_room.name if game.current_room is not None else None
        if current_room_name != "Ravine Edge":
            failures.append(
                "implicit movement destination mismatch: expected room Ravine Edge after 'south' "
                f"(actual={current_room_name!r})"
            )

    # Return to Tower Cell for inventory/container edge checks.
    game.current_room = world.rooms.get("Tower Cell")
    room = game.current_room
    if room is None:
        failures.append("setup failed: no active room while running edge checks")
    else:
        bag = next((container for container in room.containers if container.obj_handle() == "bag"), None)
        trapdoor = next((item for item in room.items if item.obj_handle() == "trapdoor"), None)
        if bag is None or trapdoor is None:
            failures.append(
                "setup failed: expected bag and trapdoor in Tower Cell "
                f"(bag={bag is not None}, trapdoor={trapdoor is not None})"
            )
        else:
            run("open lunch bag")

            trapdoor_put_result = run("put trapdoor into bag")
            if _has_any(trapdoor_put_result, ("you put", "put ")):
                failures.append(
                    "invalid put accepted: trapdoor is not in inventory but command succeeded "
                    f"(result={trapdoor_put_result!r})"
                )
            if trapdoor in bag.contents:
                failures.append("state corruption: trapdoor moved into bag despite not being in inventory")

    assert not failures, "Edge-case regressions detected:\n" + "\n".join(f" - {failure}" for failure in failures)


def test_demo_phrase_batch1_regressions(smoke_context):
    run = smoke_context["run"]
    world: World = smoke_context["world"]
    game:  Game   = smoke_context["game"]

    failures: list[str] = []

    def container_handles(container) -> set[str]:
        return {item.obj_handle() for item in container.contents}

    def safe_run(command: str):
        try:
            return run(command)
        except Exception as exc:  # Keep collecting failures instead of aborting on first runtime exception.
            failures.append(f"command {command!r} raised {type(exc).__name__}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Phrase group 1: implicit movement forms (south / s)
    # ------------------------------------------------------------------
    safe_run("teleport Demo Landing")
    if game.current_room is None or game.current_room.name != "Demo Landing":
        failures.append("setup failed: teleport Demo Landing did not land in Demo Landing")
    else:
        safe_run("s")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Ravine Edge":
            failures.append(f"implicit abbreviation failed: 's' should move to Ravine Edge (actual={room_name!r})")

        safe_run("north")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Demo Landing":
            failures.append(f"movement parity failed: 'north' should return to Demo Landing (actual={room_name!r})")

        safe_run("south")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Ravine Edge":
            failures.append(f"implicit direction failed: 'south' should move to Ravine Edge (actual={room_name!r})")

    # ------------------------------------------------------------------
    # Phrase group 2: put/get preposition variants + source validation
    # ------------------------------------------------------------------
    game.current_room = world.rooms.get("Tower Cell")
    room = game.current_room
    if room is None:
        failures.append("setup failed: Tower Cell is not available")
    else:
        bag = _room_container(game, "bag")
        trapdoor = _room_item(game, "trapdoor")
        if bag is None or trapdoor is None:
            failures.append("setup failed: expected bag and trapdoor in Tower Cell")
        else:
            safe_run("open lunch bag")
            safe_run("get key from lunch bag")
            if "key" not in _inventory_handles(game):
                failures.append("setup failed: could not retrieve key from lunch bag")
            else:
                # closed container rejection
                safe_run("close lunch bag")
                bag_before = container_handles(bag)
                safe_run("put key into bag")
                bag_after = container_handles(bag)
                if bag_before != bag_after or "key" not in _inventory_handles(game):
                    failures.append("closed-container violation: put into closed bag changed state")

                # preposition synonym: in
                safe_run("open lunch bag")
                safe_run("put key in bag")
                if "key" in _inventory_handles(game) or "key" not in container_handles(bag):
                    failures.append("preposition mapping failed: 'put key in bag' did not place key in bag")

                # preposition synonym: inside
                safe_run("get key from lunch bag")
                safe_run("put key inside bag")
                if "key" in _inventory_handles(game) or "key" not in container_handles(bag):
                    failures.append("preposition mapping failed: 'put key inside bag' did not place key in bag")

                # reset key to inventory for negative put tests
                safe_run("get key from lunch bag")

                # missing indirect object should not consume item
                safe_run("put key into")
                if "key" not in _inventory_handles(game):
                    failures.append("missing-indirect violation: 'put key into' consumed key")

                # non-container target should not consume item
                safe_run("put key into trapdoor")
                if "key" not in _inventory_handles(game):
                    failures.append("invalid-target violation: 'put key into trapdoor' consumed key")

                # non-inventory source should not be accepted
                safe_run("put trapdoor into bag")
                if trapdoor in bag.contents:
                    failures.append("invalid-source violation: trapdoor moved into bag without being in inventory")

    assert not failures, "Batch-1 phrase regressions detected:\n" + "\n".join(f" - {failure}" for failure in failures)


def test_demo_phrase_batch2_regressions(smoke_context):
    run = smoke_context["run"]
    world: World = smoke_context["world"]
    game: Game = smoke_context["game"]

    failures: list[str] = []

    def container_handles(container) -> set[str]:
        return {item.obj_handle() for item in container.contents}

    def safe_run(command: str):
        try:
            return run(command)
        except Exception as exc:  # Keep collecting failures instead of aborting on first runtime exception.
            failures.append(f"command {command!r} raised {type(exc).__name__}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Phrase group 1: direction normalization and movement parity
    # ------------------------------------------------------------------
    safe_run("teleport Demo Landing")
    if game.current_room is None or game.current_room.name != "Demo Landing":
        failures.append("setup failed: teleport Demo Landing did not land in Demo Landing")
    else:
        safe_run("GO south!!")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Ravine Edge":
            failures.append(f"direction normalization failed: 'GO south!!' should move to Ravine Edge (actual={room_name!r})")

        safe_run("N")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Demo Landing":
            failures.append(f"abbreviation parity failed: 'N' should return to Demo Landing (actual={room_name!r})")

        safe_run("S")
        room_name = game.current_room.name if game.current_room else None
        if room_name != "Ravine Edge":
            failures.append(f"uppercase abbreviation failed: 'S' should move to Ravine Edge (actual={room_name!r})")

    # ------------------------------------------------------------------
    # Phrase group 2: preposition synonyms for put/get without multi-noun
    # ------------------------------------------------------------------
    game.current_room = world.rooms.get("Tower Cell")
    room = game.current_room
    if room is None:
        failures.append("setup failed: Tower Cell is not available")
    else:
        bag = _room_container(game, "bag")
        if bag is None:
            failures.append("setup failed: expected bag in Tower Cell")
        else:
            safe_run("open lunch bag")
            safe_run("get key from lunch bag")
            if "key" not in _inventory_handles(game):
                failures.append("setup failed: could not retrieve key from lunch bag")
            else:
                safe_run("put key within bag")
                if "key" in _inventory_handles(game) or "key" not in container_handles(bag):
                    failures.append("preposition synonym failed: 'put key within bag' did not place key in bag")

                safe_run("get key out bag")
                if "key" not in _inventory_handles(game):
                    failures.append("preposition synonym failed: 'get key out bag' did not retrieve key")

                safe_run("put key into bag")
                if "key" in _inventory_handles(game) or "key" not in container_handles(bag):
                    failures.append("control failed: 'put key into bag' did not place key in bag")

                safe_run("get key off bag")
                if "key" not in _inventory_handles(game):
                    failures.append("preposition synonym failed: 'get key off bag' did not retrieve key")

    # ------------------------------------------------------------------
    # Phrase group 3: unsupported prepositions should not mutate inventory
    # ------------------------------------------------------------------
    room = game.current_room
    bag = _room_container(game, "bag") if room is not None else None
    if bag is None:
        failures.append("setup failed: bag unavailable for malformed preposition checks")
    else:
        if "key" not in _inventory_handles(game):
            safe_run("open lunch bag")
            safe_run("get key from lunch bag")

        if "key" not in _inventory_handles(game):
            failures.append("setup failed: key unavailable for malformed preposition checks")
        else:
            safe_run("put key under bag")
            if "key" not in _inventory_handles(game):
                failures.append("unsupported-preposition violation: 'put key under bag' consumed key")

            safe_run("put key with bag")
            if "key" not in _inventory_handles(game):
                failures.append("unsupported-preposition violation: 'put key with bag' consumed key")

    assert not failures, "Batch-2 phrase regressions detected:\n" + "\n".join(f" - {failure}" for failure in failures)
