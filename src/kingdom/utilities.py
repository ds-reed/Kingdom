"""Session logging and stream utilities.

Provides TeeStream for multi-stream output and session log management helpers.
Used for logging game sessions and managing terminal output.
"""
from datetime import datetime
from pathlib import Path
from typing import TextIO
import sys
import kingdom.terminal_style as terminal_style
import argparse



class TeeStream:
    def __init__(self, *streams: TextIO):
        self._streams = streams

    def write(self, data: str) -> None:
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

class SessionLogger:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.log_file: TextIO | None = None
        self.original_stdout: TextIO | None = None
        self.original_stderr: TextIO | None = None

    def start(self) -> None:
        logs_dir = self.base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_path = logs_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        self.log_file = log_path.open("w", encoding="utf-8", buffering=1)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = TeeStream(sys.stdout, self.log_file)
        sys.stderr = TeeStream(sys.stderr, self.log_file)

    def stop(self) -> None:
        if self.log_file:
            sys.stdout = self.original_stdout  # type: ignore
            sys.stderr = self.original_stderr  # type: ignore
            self.log_file.close()


import os
import sys
import subprocess
from pathlib import Path


def ensure_terminal_session() -> bool:
    """Ensure the game is running inside a real terminal on Windows.

    Returns True if execution should continue in this process.
    Returns False if a new terminal session was spawned and this process should exit.
    """
    if not _is_windows():
        return True

    if _already_in_real_terminal():
        return True

    if _already_relaunched():
        return True

    _relaunch_in_terminal()
    return False


# ───────────────────────────────────────────────────────────────────────────────
# Helper functions for terminal session management and relaunching on Windows.
# ───────────────────────────────────────────────────────────────────────────────

def _is_windows() -> bool:
    return os.name == "nt"


def _already_in_real_terminal() -> bool:
    """Check whether stdin, stdout, stderr are attached to a real TTY."""
    streams = (sys.stdin, sys.stdout, sys.stderr)
    return all(getattr(s, "isatty", lambda: False)() for s in streams)


def _already_relaunched() -> bool:
    """Detect whether this process is the relaunched terminal session."""
    return os.environ.get("KINGDOM_TERMINAL_RELAUNCHED") == "1"


def _python_executable_for_terminal() -> Path:
    """Return python.exe (not pythonw.exe) to ensure a terminal is created."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        return exe.with_name("python.exe")
    return exe


def _relaunch_in_terminal() -> None:
    """Spawn a new Windows terminal window and run this script inside it."""
    script_path = Path(__file__).resolve()
    working_dir = script_path.parent

    python_exe = _python_executable_for_terminal()

    # Escape single quotes for PowerShell
    wd = str(working_dir).replace("'", "''")
    py = str(python_exe).replace("'", "''")
    script = str(script_path).replace("'", "''")

    # PowerShell command:
    #   - mark this as the relaunched session
    #   - cd to the script directory
    #   - run python script
    ps_command = (
        "$env:KINGDOM_TERMINAL_RELAUNCHED='1'; "
        f"Set-Location -LiteralPath '{wd}'; "
        f"& '{py}' '{script}'"
    )

    # Launch a new terminal window running PowerShell
    subprocess.Popen(
        [
            "cmd",
            "/c",
            "start",
            '"Kingdom TRS-80"',
            "powershell",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_command,
        ]
    )


def init_terminal_mode(args):
    if args is None:
        args = parse_args()
    terminal_style.ACTIVE_TERMINAL_MODE = args.mode

# ───────────────────────────────────────────────────────────────────────────────
# Gene utilities for Kingdom functions and classes.
# ───────────────────────────────────────────────────────────────────────────────

def normalize_key(text: str) -> str:
    """Normalize a string for dictionary look-up."""

    DETERMINERS = {"the", "a", "an"}

    if not text:
        return ""
    key = text.lower().split()
    if key and key[0] in DETERMINERS:
        key = key[1:]
    return " ".join(key)

    