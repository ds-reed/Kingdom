#command_results.py

from kingdom.model.game_model import Game
from kingdom.language.outcomes import CommandOutcome, RenderMode
import kingdom.rendering.textutils as tu


def format_command_message(message: str | None) -> str:
    return tu.normalize_outcome_text(message)


def format_command_outcome(outcome: CommandOutcome | None) -> str:
    if outcome is None:
        return ""

    if outcome.render_mode == RenderMode.RAW:
        return outcome.message or ""

    return format_command_message(outcome.message)


def exit_message(game: Game) -> str:
    score = game.score
    score_since_load  = game.score_since_load
    items_found = game.items_found  
    items_found_since_load = game.items_found_since_load
    rooms_found = game.rooms_found
    rooms_found_since_load = game.rooms_found_since_load

    lines = [f"Thanks for playing Kingdom {game.player_name.capitalize()}!"]

    if score_since_load == 0:
        lines.append("We're sorry to see you go so soon.")
    else:
        lines.append(f"You earned {score_since_load} points since your last load, for a total score of {score}.")
        lines.append(f"You have found {items_found} items in total, including {items_found_since_load} since your last load.")
        lines.append(f"You have discovered {rooms_found} rooms in total, including {rooms_found_since_load} since your last load.")

    return "\n".join(lines)