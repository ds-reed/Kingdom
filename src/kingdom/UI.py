"""
User Interface level

This module formats rooms, exits, items, boxes, and dark-room behavior.
It depends on game models and terminal_style, but NOT on actions or verbs.

"""

from pathlib import Path
from typing import Any, Sequence
from kingdom.terminal_style import tty_show_room, tty_print, tty_prompt, tty_clear_screen
from kingdom.models import get_prefs, SessionPrefs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# kingdom/ui.py

class UI:
    def __init__(self, game):
        self.game = game

    def clear_screen(self):
        tty_clear_screen()

    def print(self, *args, sep=" ", end="\n", **kwargs):
        """Thin wrapper — can later add coloring, logging, quiet mode, etc."""
        tty_print(*args, sep=sep, end=end, **kwargs)

    def prompt(self,  message, *, default=None, type_=str, validate=None) -> str:
        while True:
            value = tty_prompt(message)
            if not value and default is not None:
                return default
            if validate is None or validate(value):
                return value
            self.print("Invalid input, try again.")

    def confirm(self, question: str = "Continue? [y/n] ") -> bool:
        ans = tty_prompt(question).lower().strip()
        return ans in ("y", "yes", "1", "true")


    def _prompt_for_filename(self, action_label: str, default_filename: str) -> str:
        while True:
            prompt_text = f"{action_label} file [{default_filename}]: "
            response = tty_prompt(prompt_text).strip()
            if not response:
                return default_filename

            filename = Path(response).name
            if filename != response:
                self.print("Please enter a filename only (no folder path).")
                continue

            return filename


    def request_save(self) -> Path | None:

        if not self.confirm(question="Save game? (y/n): "):
            return None

        prefs = get_prefs()
        filename = self._prompt_for_filename("Save to", prefs.last_save_filename)
        path = Path(prefs.save_directory) / filename

        if not path.suffix:
            path = path.with_suffix(".json")

        return path


    def request_load(self) -> Path | None:

        if not self.confirm(question = "Load game? (y/n): "):
            return None

        prefs = get_prefs()
        filename = self._prompt_for_filename("Load from", prefs.last_save_filename)
        path = Path(prefs.save_directory) / filename

        if not path.suffix:
            path = path.with_suffix(".json")

        return path
    

    def request_quit(self) -> bool:
        if self.confirm(question = "Quit without saving? (y/n): "):
           return True
        return False

    
    def render_room(self, lines: list[str], clear: bool = True):
        tty_show_room(lines, clear=clear)


