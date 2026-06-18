from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Callable


class AppLogger:
    def __init__(self, callback: Callable[[str], None] | None = None) -> None:
        self.callback = callback
        self.lines: list[str] = []
        self.lock = Lock()
        self.log_path = Path("output/logs/monolith.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def set_callback(self, callback: Callable[[str], None]) -> None:
        self.callback = callback

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def warn(self, message: str) -> None:
        self._write("WARN", message)

    def error(self, message: str) -> None:
        self._write("ERROR", message)

    def _write(self, level: str, message: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {level} - {message}"
        with self.lock:
            self.lines.append(line)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        if self.callback:
            self.callback(line)
