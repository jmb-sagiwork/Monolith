from __future__ import annotations

import os
from pathlib import Path


KNOWN_HLLAPI_DLLS = [
    "pcshll32.dll",
    "pcsapi32.dll",
    "ehlapi32.dll",
    "ehllapi.dll",
    "whllapi.dll",
    "hllapi32.dll",
]


def scan_hllapi_dlls(extra_roots: list[str] | None = None) -> list[dict]:
    roots = [Path("C:/Program Files"), Path("C:/Program Files (x86)"), Path.cwd()]
    for item in extra_roots or []:
        if item:
            roots.append(Path(item).parent if Path(item).suffix else Path(item))
    found: list[dict] = []
    seen: set[str] = set()
    names = {name.lower() for name in KNOWN_HLLAPI_DLLS}
    for root in roots:
        if not root.exists():
            continue
        try:
            for current, dirs, files in os.walk(root):
                rel_parts = Path(current).relative_to(root).parts
                if len(rel_parts) > 3:
                    dirs[:] = []
                for file_name in files:
                    if file_name.lower() in names:
                        path = str(Path(current) / file_name)
                        if path.lower() not in seen:
                            seen.add(path.lower())
                            found.append({"name": file_name, "path": path})
        except (OSError, ValueError):
            continue
    return found
