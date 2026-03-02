"""
User Interface level

This module formats rooms, exits, items, boxes, and dark-room behavior.
It depends on game models and terminal_style, but NOT on actions or verbs.

"""

from pathlib import Path
from typing import Any, Sequence
from kingdom.terminal_style import tty_clear_and_show_room, tty_print, tty_prompt
from kingdom.session import get_prefs, SessionPrefs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# kingdom/ui.py

class UI:
    def __init__(self, game):
        self.game = game

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


    def _prompt_for_path(self, action_label: str, default_path: str) -> str:
        # Show a nice prompt with default in brackets
        prompt_text = f"{action_label} file [{default_path}]: "
        response = tty_prompt(prompt_text)

        # Accept default on blank input
        response = response.strip()
        if not response:
            return default_path

        return response


    def request_save(self):

        if not self.confirm(question="Save game? (y/n): "):
            return "Save cancelled."

        prefs = get_prefs()
        last_save_path = Path(prefs.save_directory / prefs.last_save_filename)

        path_str = self._prompt_for_path("Save to", str(last_save_path))

        # Convert to Path and normalize
        path = Path(path_str)

        if not path.suffix:
            path = path.with_suffix(".json")

        # Make sure directory exists 
        path.parent.mkdir(parents=True, exist_ok=True)

        # Perform the save 
        self.game.save_world(path)

        # tell session prefs we used this location
        prefs.remember_save(path)

        return path


    def request_load(self):

        if not self.confirm(question = "Load game? (y/n): "):
            return "Load cancelled."

        prefs = get_prefs()
        last_save_path = Path(prefs.save_directory / prefs.last_save_filename)

        # default load from last save path
        path_str = self._prompt_for_path("Load from", str(last_save_path))
        path = Path(path_str)

        return path
    

    def request_quit(self) -> bool:
        if self.confirm(question = "Quit without saving? (y/n): "):
           return True
        return False

    
    def render_room(self, lines: list[str], clear: bool = True):
        tty_clear_and_show_room(lines, clear=clear)

   
