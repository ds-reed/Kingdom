from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from kingdom.language.interpreter import InterpretedCommand


class CommandStatus(Enum):
    SUCCESS = auto()
    MISSING_TARGET = auto()
    MISSING_PREP_TARGET = auto()
    INVALID_TARGET = auto()
    NOT_AVAILABLE = auto()
    PRECONDITION_FAILED = auto()
    BLOCKED = auto()
    NO_OP = auto()
    ERROR = auto()


class RenderMode(Enum):
    NORMALIZE = auto()
    RAW = auto()


@dataclass
class CommandOutcome:
    status: CommandStatus
    verb: str
    command: "InterpretedCommand | None"
    message: str
    code: str | None = None
    details: Dict[str, Any] = field(default_factory=dict)
    effects: List[str] = field(default_factory=list)
    render_mode: RenderMode = RenderMode.NORMALIZE


def make_outcome(
    *,
    status: CommandStatus,
    verb: str,
    command: "InterpretedCommand | None",
    message: str,
    code: str | None = None,
    details: Dict[str, Any] | None = None,
    effects: List[str] | None = None,
    render_mode: RenderMode = RenderMode.NORMALIZE,
) -> CommandOutcome:
    return CommandOutcome(
        status=status,
        verb=verb,
        command=command,
        message=message,
        code=code,
        details=details or {},
        effects=effects or [],
        render_mode=render_mode,
    )
