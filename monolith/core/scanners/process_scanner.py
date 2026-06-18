from __future__ import annotations

import subprocess


KNOWN_EMULATOR_PROCESSES = [
    "mystyle.exe",
    "pcsws.exe",
    "pcscm.exe",
    "r2win.exe",
    "reflection.exe",
    "extra.exe",
    "rumba.exe",
    "bzmd.exe",
    "bluezone.exe",
    "wfica32.exe",
]


def scan_processes() -> list[dict]:
    try:
        import psutil

        rows = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = proc.info
                rows.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name") or "",
                        "exe": info.get("exe") or "",
                    }
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return rows
    except Exception:
        return _scan_processes_tasklist()


def likely_emulator_processes(processes: list[dict]) -> list[dict]:
    known = {name.lower() for name in KNOWN_EMULATOR_PROCESSES}
    return [proc for proc in processes if (proc.get("name") or "").lower() in known]


def _scan_processes_tasklist() -> list[dict]:
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return []
    rows = []
    for line in result.stdout.splitlines():
        parts = [part.strip('"') for part in line.split('","')]
        if len(parts) >= 2:
            rows.append({"name": parts[0], "pid": _safe_int(parts[1]), "exe": ""})
    return rows


def _safe_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
