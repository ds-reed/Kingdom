from __future__ import annotations

import pytest

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


def test_format_command_outcome_enforces_terminal_dot_policy():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="wait..\nno....\nok...",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "Wait.\nNo...\nOk..."


def test_format_command_outcome_applies_articles_to_non_plural_bullets_without_forcing_periods():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="- cigarettes\n- lighter\n- key",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "- Cigarettes\n- A lighter\n- A key"


def test_format_command_outcome_strips_period_after_colon_and_preserves_header():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="you have (3 items):.\n- cigarettes\n- lighter\n- key",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "You have (3 items):\n- Cigarettes\n- A lighter\n- A key"


def test_format_command_outcome_applies_conservative_article_normalization():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="you get fish..",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "You get a fish."


def test_format_command_outcome_strips_period_after_question_mark():
    """A period (or run of periods) after ? or ! is spurious and must be removed."""
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="Are you sure?.",
        render_mode=RenderMode.NORMALIZE,
    )
    assert format_command_outcome(outcome) == "Are you sure?"


def test_format_command_outcome_strips_multiple_periods_after_question_mark():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="Are you sure?..",
        render_mode=RenderMode.NORMALIZE,
    )
    assert format_command_outcome(outcome) == "Are you sure?"


def test_format_command_outcome_strips_period_after_exclamation():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="Stop!.",
        render_mode=RenderMode.NORMALIZE,
    )
    assert format_command_outcome(outcome) == "Stop!"


def test_format_command_outcome_no_article_before_locative_adverb():
    """'from somewhere ahead' must not become 'from the somewhere ahead'."""
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="The air carries faint echoes from somewhere ahead.",
        render_mode=RenderMode.NORMALIZE,
    )
    assert format_command_outcome(outcome) == "The air carries faint echoes from somewhere ahead."


def test_format_command_outcome_no_article_before_gerund_action_phrase():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="Something is holding you back from climbing down.",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "Something is holding you back from climbing down."


def test_format_command_outcome_does_not_capitalize_inner_you_phrase():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message="You have a feeling of accomplishment as you rub the lamp. It looks shinier now.",
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == "You have a feeling of accomplishment as you rub the lamp. It looks shinier now."


def test_format_command_outcome_preserves_infinitive_phrases_and_direction_bullets():
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message=(
            "The Victrola shudders violently and begins to play.\n"
            "The haunting magical melody swells and seems to fill the room.\n"
            "Available exits:\n"
            "- East"
        ),
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == (
        "The Victrola shudders violently and begins to play.\n"
        "The haunting magical melody swells and seems to fill the room.\n"
        "Available exits:\n"
        "- East"
    )


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("you take fish.", "You take a fish."),
        ("you drop fish into lunch bag.", "You drop a fish into the lunch bag."),
        ("you can't get a greasy brown lunch bag.", "You can't get the greasy brown lunch bag."),
        ("you take the lamp from table.", "You take the lamp from the table."),
        ("you can't put things into lunch bag!", "You can't put things into the lunch bag!"),
        ("you don't see any chest here to take from.", "You don't see any chest here to take from."),
    ],
)
def test_format_command_outcome_validates_article_normalization_on_verb_feedback(message, expected):
    outcome = CommandOutcome(
        status=CommandStatus.SUCCESS,
        verb="test",
        command=None,
        message=message,
        render_mode=RenderMode.NORMALIZE,
    )

    assert format_command_outcome(outcome) == expected
