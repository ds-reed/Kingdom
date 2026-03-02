"""
User Interface level

This module formats rooms, exits, items, boxes, and dark-room behavior.
It depends on game models and terminal_style, but NOT on actions or verbs.

"""

from typing import Any, Sequence
from kingdom.terminal_style import tty_clear_and_show_room, tty_print, tty_prompt


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
        if self.game is None:
            return "ERROR - no game found."

        if self.game.save_path is None:
            return "ERROR - no save path is configured."

        if not self.confirm(question = "Save game? (y/n): "):
            return "Save cancelled."

        path = self._prompt_for_path("Save", self.game.save_path)

        self.game.save_world(path)

        return f"Game saved to {path}."

    def request_load(self):
        if self.game is None:
            return "ERROR - no game found."

        if self.game.load_path is None:
            return "ERROR - no load path is configured."

        # Confirm
        if not self.confirm(question = "Load game? (y/n): "):
            return "Load cancelled."

        # Prompt for path
        path = self._prompt_for_path("Load", self.game.load_path)

        # Load world
        self.game.load_world(path)

        return f"Game loaded from {path}."
    
    def request_quit(self):
        if self.confirm(question = "Quit without saving? (y/n): "):
           return "Goodbye! Thanks for playing Kingdom."
        return None
    
    
    def render_room(self, lines: list[str], clear: bool = True):
        tty_clear_and_show_room(lines, clear=clear)

   
