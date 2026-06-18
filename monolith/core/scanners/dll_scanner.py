from __future__ import annotations

import ctypes
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


def probe_hllapi_dlls(exe_path: str = "", profile_path: str = "", pid: int | None = None) -> list[dict]:
    roots = [
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
        Path.cwd(),
    ]
    for path in (exe_path, profile_path):
        if path:
            roots.append(Path(path).parent)

    found: list[dict] = []
    seen: set[str] = set()
    for root in roots:
        if root.exists():
            _scan_root(root, found, seen)
    if pid:
        _scan_memory_maps(pid, found, seen)
    return found


def try_load_dll(path: str) -> tuple[str, str]:
    try:
        ctypes.WinDLL(path)
        return "Candidate", "DLL loaded successfully with ctypes.WinDLL."
    except OSError as exc:
        return "Candidate", f"DLL found but could not be loaded: {exc}"
    except Exception as exc:
        return "Error", str(exc)


def _scan_root(root: Path, found: list[dict], seen: set[str]) -> None:
    names = {name.lower() for name in KNOWN_HLLAPI_DLLS}
    try:
        for current, dirs, files in os.walk(root):
            if Path(current).relative_to(root).parts and len(Path(current).relative_to(root).parts) > 3:
                dirs[:] = []
            for file_name in files:
                if file_name.lower() in names:
                    path = str(Path(current) / file_name)
                    key = path.lower()
                    if key not in seen:
                        seen.add(key)
                        found.append({"name": file_name, "path": path})
    except (OSError, ValueError):
        return


def _scan_memory_maps(pid: int, found: list[dict], seen: set[str]) -> None:
    try:
        import psutil

        proc = psutil.Process(pid)
        for mapped in proc.memory_maps():
            path = getattr(mapped, "path", "") or ""
            name = Path(path).name.lower()
            if name in {item.lower() for item in KNOWN_HLLAPI_DLLS} and path.lower() not in seen:
                seen.add(path.lower())
                found.append({"name": Path(path).name, "path": path})
    except Exception:
        return
