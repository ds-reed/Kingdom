"""Smoke-test demo for the current Kingdom command/action pipeline."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from kingdom.model.noun_model import World, Player, DirectionNoun
from kingdom.model.game_init import QuitGame, SaveGame, LoadGame, GameOver
from kingdom.model.game_init import GameActionState, init_session, get_action_state
from kingdom.model.game_persistence import save_game, load_game
from kingdom.language.lexicon.verb_registry import build_verb_registry
from kingdom.parser import resolve_command
from kingdom.UI import UI


def _iter_known_noun_names(game: World):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.get_descriptive_phrase()
        yield noun.get_noun_name()


def _iter_local_target_candidates(game: World, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for container in state.current_room.containers:
            yield container
            if not container.is_openable or container.is_open:
                for item in container.contents:
                    yield item

    player = game.require_player(return_error=True)
    if not isinstance(player, str):
        for item in player.sack.contents:
            yield item


def _resolve_target_noun(game: World, state: GameActionState, resolved_command) -> object | None:
    noun_matches = resolved_command.parse.nouns
    if not noun_matches:
        return None

    local_candidates = list(_iter_local_target_candidates(game, state))
    for noun_match in noun_matches:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                return candidate

    return None


def _run_command(game: World, state: GameActionState, verbs, command, demo_save_path: Path | None = None):
    resolved_command = resolve_command(
        command,
        known_verbs=verbs.keys(),
        known_nouns=_iter_known_noun_names(game),
    )
    if resolved_command is None:
        return "UNKNOWN"

    verb_word = resolved_command.verb
    args = tuple(resolved_command.args)
    target_noun = _resolve_target_noun(game, state, resolved_command)

    verb = verbs.get(verb_word)
    if verb is None:
        return "UNKNOWN"

    try:
        return verb.execute(target_noun, args)
    except SaveGame:
        if demo_save_path is None:
            return "SAVE_ERROR"
        saved_path = save_game(game, demo_save_path)
        return f"Game saved to {saved_path}"
    except LoadGame:
        if demo_save_path is None:
            return "LOAD_ERROR"
        loaded_path = load_game(game, demo_save_path)
        return f"Game loaded from {loaded_path}"
    except QuitGame:
        return "QUIT"
    except GameOver as error:
        return f"GAME_OVER: {error}"
    except TypeError:
        return "ARG_ERROR"


def _expect(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def _expect_contains(result, needle: str, message: str):
    _expect(isinstance(result, str) and needle.lower() in result.lower(), message)


def demo():
    """Run deterministic smoke tests for core gameplay flows."""
    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    demo_save_path = PROJECT_ROOT / "data" / "working_state.demo.json"

    game = World.get_instance()
    game.setup_world(data_path)
    player = Player("DemoHero")

    _expect(len(game.rooms) > 0, "World loads rooms")
    _expect(any(len(room.containers) > 0 for room in game.rooms.values()), "World loads containers")

    start_room = game.rooms.get(game.start_room_name) if isinstance(game.rooms, dict) else None
    _expect(start_room is not None, "Start room resolves from world data")

    init_session(world=game, current_player=player, initial_room=start_room, player_name="DemoHero", save_path=demo_save_path)
    action_state = get_action_state()

    ui = UI()

    verbs = build_verb_registry()
    covered_verbs: set[str] = set()

    def run(command: str):
        resolved = resolve_command(
            command,
            known_verbs=verbs.keys(),
            known_nouns=_iter_known_noun_names(game),
        )
        result = _run_command(game, action_state, verbs, command, demo_save_path=demo_save_path)
        if resolved is not None:
            canonical = verbs[resolved.verb].name
            covered_verbs.add(canonical)
        return result

    _expect(
        set(["go", "save", "load", "look", "help", "quit", "inventory", "score"]).issubset(verbs.keys()),
        "Core verbs are registered",
    )

    help_result = run("help")
    _expect(isinstance(help_result, str) and "You can try commands like:" in help_result, "help command returns default help text")

    help_commands_result = run("help commands")
    _expect(isinstance(help_commands_result, str) and "Available commands:" in help_commands_result, "help commands returns command listing")

    look_result = run("look")
    _expect(isinstance(look_result, str) and len(look_result.strip()) > 0, "look command describes current room")

    score_result = run("score")
    _expect(isinstance(score_result, str) and "Your current score is:" in score_result, "score command returns score text")

    inventory_result = run("inventory")
    _expect(isinstance(inventory_result, str) and "don't have anything" in inventory_result.lower(), "inventory reports empty inventory")

    # --- Special handler: open bean ---
    open_bean_result = run("open bean")
    _expect_contains(open_bean_result, "you reached me", "open bean triggers special handler")

    # --- Container interactions + inventory verbs ---
    _expect_contains(run("open lunch bag"), "open", "open container works")
    look_in_bag_result = run("look in lunch bag")
    _expect(
        isinstance(look_in_bag_result, str)
        and "inside" in look_in_bag_result.lower()
        and "lunch bag" in look_in_bag_result.lower(),
        "look in container shows contents",
    )

    _expect_contains(run("take fish"), "you take", "take fish from open container")
    _expect_contains(run("take key"), "you take", "take key from open container")
    _expect_contains(run("take lamp"), "you take", "take lamp from open container")
    _expect_contains(run("take lighter"), "you take", "take lighter from open container")
    _expect_contains(run("take torch"), "you take", "take torch from room")
    _expect_contains(run("close lunch bag"), "close", "close container works")
    _expect_contains(run("drop torch"), "you drop", "drop command works")
    _expect_contains(run("take torch"), "you take", "take command works after drop")

    # --- State-changing verbs ---
    _expect_contains(run("light torch"), "you light", "light command works with ignition source")
    _expect_contains(run("extinguish torch"), "you extinguish", "extinguish command works")
    _expect_contains(run("say hello"), "wind", "say command executes generic path")
    eat_fish_result = run("eat fish")
    _expect_contains(eat_fish_result, "vomit", "eat fish triggers special handler")

    _expect_contains(run("unlock trapdoor"), "you unlock", "unlock command works with key")
    _expect_contains(run("open trapdoor"), "passage leading down", "opening trapdoor reveals exit")

    # --- GO (explicit and implicit) ---
    _expect_contains(run("go down"), "you go down", "explicit go command works")
    _expect(action_state.current_room.name == "Blank Chamber", "go down lands in Blank Chamber")

    rub_lamp_result = run("rub lamp")
    _expect_contains(rub_lamp_result, "imposing djinni", "rub lamp in trigger room summons djinni")

    make_wish_result = run("make wish")
    _expect_contains(make_wish_result, "places a doorway in the west wall", "make wish triggers djinni special handler")

    _expect_contains(run("west"), "you go west", "implicit direction movement works")
    _expect(action_state.current_room.name == "Colossal Cave", "west exit from djinni wish is active")

    # --- Swim command at real swim exit ---
    _expect_contains(run("swim west"), "you swim west", "swim works in watery room with swim exit")
    _expect(action_state.current_room.name == "Pool Ledge", "swim west lands in Pool Ledge")

    # --- Teleport hidden verb ---
    teleport_result = run("teleport Demo Landing")
    _expect_contains(teleport_result, "you teleport", "teleport command works")
    _expect(action_state.current_room.name == "Demo Landing", "teleport moves to requested room")

    # --- Save/Load verbs ---
    save_result = run("save")
    _expect("Game saved to" in save_result, "save command writes demo save file")
    _expect(demo_save_path.exists(), "Demo save file exists")

    load_result = run("load")
    _expect("Game loaded from" in load_result, "load command restores from demo save file")

    # --- DEBUG / DIE hidden verbs ---
    debug_result = run("debug room")
    _expect(debug_result is None or isinstance(debug_result, str), "debug command executes without crashing")

    die_result = run("die")
    _expect(isinstance(die_result, str) and die_result.startswith("GAME_OVER:"), "die command raises game over")

    unknown_result = run("dance")
    _expect(unknown_result == "UNKNOWN", "Unknown commands are detected")

    quit_result = run("quit")
    _expect(quit_result == "QUIT", "quit command returns QUIT sentinel")

    expected_canonical_verbs = {
        "go", "swim", "teleport",
        "light", "extinguish", "open", "close", "unlock", "eat", "rub", "say", "make", "look",
        "help", "score", "load", "save", "quit", "die", "debug",
        "inventory", "take", "drop",
    }
    missing = sorted(expected_canonical_verbs - covered_verbs)
    _expect(not missing, f"All canonical verbs were exercised (missing: {missing})")

    print("\nAll demo smoke tests passed.")


if __name__ == "__main__":
    demo()
