from __future__ import annotations

from pathlib import Path


EXTENSION_RULES = {
    ".rsf": {"product_guess": "Reflection for IBM", "backend_guess": "IBM AS/400 / iSeries / Mainframe", "confidence": "high"},
    ".ws": {"product_guess": "IBM Personal Communications", "backend_guess": "IBM AS/400 / iSeries / Mainframe", "confidence": "high"},
    ".edp": {"product_guess": "Extra! / Attachmate", "backend_guess": "IBM host or terminal session", "confidence": "medium"},
    ".rd3x": {"product_guess": "Reflection Desktop", "backend_guess": "IBM host or terminal session", "confidence": "medium"},
    ".rd5x": {"product_guess": "Reflection Desktop", "backend_guess": "IBM host or terminal session", "confidence": "medium"},
}


def guess_profile(path: str) -> dict:
    extension = Path(path).suffix.lower()
    rule = EXTENSION_RULES.get(extension, {})
    return {
        "path": path,
        "extension": extension,
        "product_guess": rule.get("product_guess", "Unknown"),
        "backend_guess": rule.get("backend_guess", "Unknown"),
        "confidence": rule.get("confidence", "unknown"),
    }


def scan_profiles() -> list[dict]:
    roots = [Path.home() / "Desktop", Path.home() / "Documents", Path.cwd()]
    found: list[dict] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        try:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in EXTENSION_RULES:
                    key = str(path.resolve()).lower()
                    if key not in seen:
                        seen.add(key)
                        found.append(guess_profile(str(path)))
        except OSError:
            continue
    return found
