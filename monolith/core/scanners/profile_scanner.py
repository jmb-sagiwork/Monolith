from __future__ import annotations

import os
import sys
from pathlib import Path

from monolith.core.models import SessionProfile


EXTENSION_RULES = {
    ".rsf": {
        "product_guess": "Reflection for IBM",
        "backend_guess": "IBM AS/400 / iSeries / Mainframe",
        "confidence": "high",
    },
    ".ws": {
        "product_guess": "IBM Personal Communications",
        "backend_guess": "IBM AS/400 / iSeries / Mainframe",
        "confidence": "high",
    },
    ".edp": {
        "product_guess": "Extra! / Attachmate",
        "backend_guess": "IBM host or terminal session",
        "confidence": "medium",
    },
    ".rd3x": {
        "product_guess": "Reflection Desktop",
        "backend_guess": "IBM host or terminal session",
        "confidence": "medium",
    },
    ".rd5x": {
        "product_guess": "Reflection Desktop",
        "backend_guess": "IBM host or terminal session",
        "confidence": "medium",
    },
}


def guess_profile(path: str) -> SessionProfile:
    extension = Path(path).suffix.lower()
    rule = EXTENSION_RULES.get(extension, {})
    return SessionProfile(
        path=path,
        extension=extension,
        product_guess=rule.get("product_guess", "Unknown"),
        backend_guess=rule.get("backend_guess", "Unknown"),
        confidence=rule.get("confidence", "unknown"),
    )


def scan_profiles() -> list[SessionProfile]:
    roots = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.cwd(),
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3])),
    ]
    profiles: list[SessionProfile] = []
    seen: set[str] = set()
    extensions = tuple(EXTENSION_RULES)
    for root in roots:
        if not root.exists():
            continue
        try:
            for current, _, files in os.walk(root):
                for file_name in files:
                    path = Path(current) / file_name
                    if path.suffix.lower() in extensions:
                        key = str(path.resolve()).lower()
                        if key not in seen:
                            seen.add(key)
                            profiles.append(guess_profile(str(path)))
        except OSError:
            continue
    return profiles
