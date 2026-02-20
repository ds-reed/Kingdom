from datetime import datetime
from pathlib import Path
from typing import TextIO
import sys


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


def start_session_logging(base_dir: Path) -> tuple[TextIO, Path, TextIO, TextIO]:
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log_file = log_path.open("w", encoding="utf-8", buffering=1)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = TeeStream(sys.stdout, log_file)
    sys.stderr = TeeStream(sys.stderr, log_file)

    return log_file, log_path, original_stdout, original_stderr


def stop_session_logging(log_file: TextIO, original_stdout: TextIO, original_stderr: TextIO) -> None:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    log_file.close()