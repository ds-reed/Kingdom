# session.py

from dataclasses import dataclass
from pathlib import Path
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Room

@dataclass
class GameActionState:
    current_room: "Room | None" = None
    player_name: str | None = None
    score: int = 0

@dataclass
class SessionPrefs:
    save_directory: Path = Path("saves")
    last_save_filename: str = "quicksave.json"
    player_name: str | None = None          # set once prompted
    default_filename_template: str = "{name}.json"

    def remember_save(self, path: Path | str):
        path = Path(path)
        self.save_directory = path.parent
        self.last_save_filename = path.name

# Single instances
_action_state: GameActionState | None = None
_prefs: SessionPrefs | None = None

def init_session(
    initial_room: "Room | None" = None,
    player_name: str | None = None,
    save_path: Path | None = None,
) -> None:
    global _action_state, _prefs
    _action_state = GameActionState(
        current_room=initial_room,
        player_name=player_name,
    )
    _prefs = SessionPrefs(
        save_directory=save_path.parent if save_path else Path("saves"),
        last_save_filename=save_path.name if save_path else "quicksave.json",
        player_name=player_name,
    )

def get_action_state() -> GameActionState:
    if _action_state is None:
        raise RuntimeError("Action state not initialized")
    return _action_state

def set_action_state(new_state: GameActionState) -> None:
    global _action_state
    _action_state = new_state

def set_prefs(new_prefs: SessionPrefs) -> None:
    global _prefs
    _prefs = new_prefs  

def get_prefs() -> SessionPrefs:
    if _prefs is None:
        raise RuntimeError("Session preferences not initialized")
    return _prefs

def reset_all_state() -> None:
    global _action_state, _prefs
    _action_state = None
    _prefs = None
    # or reinitialize with defaults if preferred