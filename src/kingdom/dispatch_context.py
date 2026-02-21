"""Dispatch context paradigm for verb/action execution.

Kingdom routes commands through `Verb.execute`, which may optionally include a
`DispatchContext` object. That context is the shared runtime envelope for a
single command dispatch.

Design goals:
- Keep handlers decoupled from global singletons.
- Provide strongly-typed access to runtime collaborators.
- Make context evolution explicit (add fields here, not ad-hoc dict keys).

Usage model:
- `game`: global world object for room/player/world state.
- `state`: per-session action state (current room, hero name, etc).
- `confirm_callback` / `prompt_callback`: UI hooks for optional interaction.

Guideline:
- Handlers should prefer reading from `DispatchContext` rather than reaching
    directly into unrelated modules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from kingdom.actions import GameActionState
    from kingdom.models import Game


ConfirmCallback = Callable[[str], bool]
PromptCallback = Callable[[str], str]


@dataclass(slots=True)
class DispatchContext:
    game: "Game | None" = None
    state: "GameActionState | None" = None
    save_path: Path | None = None
    confirm_callback: ConfirmCallback | None = None
    prompt_callback: PromptCallback | None = None
