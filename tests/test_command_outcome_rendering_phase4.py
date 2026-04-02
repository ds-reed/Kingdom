from __future__ import annotations

from kingdom.engine import exception_handling
from kingdom.language.outcomes import CommandOutcome, CommandStatus, RenderMode
from kingdom.rendering.command_results import format_command_outcome


class _DummyGame:
    def __init__(self):
        self.current_room = object()
        self.world = None
        self.end_room = object()
        self.continue_after_win = True


class _DummyWorld:
    def __init__(self):
        self.end_room = object()


class _DummyCommand:
    def __init__(self):
        self.verb = None


def test_format_command_outcome_normalize_strips_outer_blank_lines_and_trailing_spaces():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="\n  Hello world.   \nSecond line.   \n\n",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "  Hello world.\nSecond line."


def test_format_command_outcome_raw_bypasses_normalization():
    message = "\n  Already Rendered   \n"
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message=message,
        render_mode=RenderMode.RAW,
    )

    assert format_command_outcome(outcome) == message


def test_process_command_prints_formatted_outcome(monkeypatch):
    printed: list[str] = []
    dummy_game = _DummyGame()
    dummy_world = _DummyWorld()

    monkeypatch.setattr(exception_handling, "parse", lambda raw, lexicon: ["parsed"])
    monkeypatch.setattr(exception_handling, "interpret", lambda parsed, world, lexicon: [_DummyCommand()])
    monkeypatch.setattr(
        exception_handling,
        "execute",
        lambda cmd, world, raw: CommandOutcome(
            status=CommandStatus.SUCCESS,
            verb="test",
            command=None,
            message="\nTrim me.   \n",
            render_mode=RenderMode.NORMALIZE,
        ),
    )
    monkeypatch.setattr(exception_handling, "get_game", lambda: dummy_game)
    monkeypatch.setattr(exception_handling.ui, "print", lambda *args, **kwargs: printed.append(" ".join(str(arg) for arg in args)))

    should_quit, recovery_mode, output = exception_handling.process_command(
        raw_command="look",
        world=dummy_world,
        lexicon=object(),
        recovery_mode=False,
    )

    assert (should_quit, recovery_mode, output) == (False, False, None)
    assert printed == ["Trim me."]
