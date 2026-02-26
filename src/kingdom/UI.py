"""
User Interface level

This module formats rooms, exits, items, boxes, and dark-room behavior.
It depends on game models and terminal_style, but NOT on actions or verbs.

"""

from typing import Any, Sequence
from kingdom.models import Game, Room, Item, Box
from kingdom.terminal_style import trs80_clear_and_show_room, trs80_print, TRS80_WHITE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# kingdom/ui.py

class UI:
    def __init__(self, confirm, prompt, save_path, load_path, game):
        self.confirm = confirm
        self.prompt = prompt
        self.save_path = save_path
        self.load_path = load_path
        self.game = game

    def _prompt_for_path(self, action_label: str, default_path: str) -> str:
        # Show a nice prompt with default in brackets
        prompt_text = f"{action_label} file [{default_path}]: "
        response = self.prompt(prompt_text)

        # Accept default on blank input
        response = response.strip()
        if not response:
            return default_path

        return response

    def request_save(self):
        if self.game is None:
            return "No game is active yet."

        if self.save_path is None:
            return "No save path is configured."

        if not self.confirm("Save game?"):
            return "Save cancelled."

        path = self._prompt_for_path("Save", self.save_path)

        self.game.save_world(path)

        return f"Game saved to {path}."

    def request_load(self):
        if self.game is None:
            return "No game is active yet."

        if self.load_path is None:
            return "No load path is configured."

        # Confirm
        if not self.confirm("Load game?"):
            return "Load cancelled."

        # Prompt for path
        path = self._prompt_for_path("Load", self.load_path)

        # Load world
        self.game.load_world(path)

        return f"Game loaded from {path}."
    
    def request_quit(self):
        if self.confirm("Quit without saving? "):
           return True # Confirmed
        return False # Cancelled
    
    
    def render_room(self, lines: list[str], clear: bool = True):
        trs80_clear_and_show_room(lines, clear=clear)

   
