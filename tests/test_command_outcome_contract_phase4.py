from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.executor import CommandOutcome, CommandStatus, RenderMode, execute
from kingdom.language.interpreter import InterpretedCommand, interpret
from kingdom.language.lexicon import lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Player, World


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def phase4_context(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    world = World.get_instance()
    game.world = world
    game.setup_world(data_path)

    player = Player("Phase4Tester")
    game.init_session(
        world=world,
        current_player=player,
        player_name="Phase4Tester",
        save_path=tmp_path / "phase4.tmp.json",
    )

    register_verbs()
    lexicon = lex()

    return {
        "game": game,
        "lexicon": lexicon,
    }


def _execute_one(command: str, ctx: dict) -> CommandOutcome:
    parsed = parse(command, ctx["lexicon"])
    interpreted = interpret(parsed, ctx["game"], ctx["lexicon"])
    assert len(interpreted) == 1
    return execute(interpreted[0], ctx["game"], command)


def _execute_sequence(commands: list[str], ctx: dict) -> CommandOutcome:
    outcome: CommandOutcome | None = None
    for command in commands:
        outcome = _execute_one(command, ctx)
    assert outcome is not None
    return outcome


def test_execute_unknown_verb_returns_structured_invalid_target(phase4_context):
    outcome = _execute_one("lool", phase4_context)

    assert outcome.status == CommandStatus.INVALID_TARGET
    assert outcome.code == "unknown_verb"
    assert outcome.render_mode == RenderMode.NORMALIZE
    assert "don't know" in outcome.message.lower()


def test_execute_look_returns_structured_success_outcome(phase4_context):
    outcome = _execute_one("look", phase4_context)

    assert outcome.status == CommandStatus.SUCCESS
    assert outcome.code == "look_room"
    assert outcome.render_mode == RenderMode.RAW
    assert isinstance(outcome.message, str)


def test_execute_accepts_structured_command_outcome_from_verb():
    class DummyVerb:
        def canonical_name(self):
            return "dummy"

        def execute(self, cmd=None):
            return CommandOutcome(
                status=CommandStatus.SUCCESS,
                verb="",
                command=None,
                message="already rendered output",
                code="dummy",
                render_mode=RenderMode.RAW,
            )

    dummy_command = InterpretedCommand(
        verb=DummyVerb(),
        verb_token="dummy",
        all_tokens=["dummy"],
        verb_source="explicit",
    )

    outcome = execute(dummy_command, World.get_instance(), "dummy")

    assert outcome.status == CommandStatus.SUCCESS
    assert outcome.code == "dummy"
    assert outcome.render_mode == RenderMode.RAW
    assert outcome.verb == "dummy"
    assert outcome.command is dummy_command


def test_execute_rejects_legacy_string_result_from_verb():
    class LegacyVerb:
        def canonical_name(self):
            return "legacy"

        def execute(self, cmd=None):
            return "old string contract"

    legacy_command = InterpretedCommand(
        verb=LegacyVerb(),
        verb_token="legacy",
        all_tokens=["legacy"],
        verb_source="explicit",
    )

    with pytest.raises(TypeError, match="expected CommandOutcome"):
        execute(legacy_command, World.get_instance(), "legacy")


@pytest.mark.parametrize(
    ("command", "expected_status", "expected_code"),
    [
        ("take", CommandStatus.MISSING_TARGET, "missing_direct_target"),
        ("get unicorn", CommandStatus.NOT_AVAILABLE, "direct_target_not_here"),
    ],
)
def test_execute_returns_expected_structured_statuses_for_simple_failures(
    phase4_context,
    command: str,
    expected_status: CommandStatus,
    expected_code: str,
):
    outcome = _execute_one(command, phase4_context)

    assert outcome.status == expected_status
    assert outcome.code == expected_code
    assert outcome.render_mode == RenderMode.NORMALIZE


def test_execute_take_from_closed_container_returns_precondition_failed(phase4_context):
    outcome = _execute_one("get all from lunch bag", phase4_context)

    assert outcome.status == CommandStatus.PRECONDITION_FAILED
    assert outcome.code == "source_container_closed"
    assert outcome.render_mode == RenderMode.NORMALIZE


def test_execute_open_non_openable_item_returns_blocked(phase4_context):
    outcome = _execute_sequence(["open lunch bag", "get lamp from lunch bag", "open lamp"], phase4_context)

    assert outcome.status == CommandStatus.BLOCKED
    assert outcome.code == "open_not_allowed"
    assert outcome.render_mode == RenderMode.NORMALIZE


def test_execute_getting_owned_item_returns_no_op(phase4_context):
    outcome = _execute_sequence(["open lunch bag", "get lamp from lunch bag", "get lamp"], phase4_context)

    assert outcome.status == CommandStatus.NO_OP
    assert outcome.code == "already_in_inventory"
    assert outcome.render_mode == RenderMode.NORMALIZE
