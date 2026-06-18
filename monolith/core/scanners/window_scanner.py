from __future__ import annotations

from monolith.core.models import TargetWindow


LIKELY_TITLE_TERMS = [
    "Session",
    "MyStyle",
    "Reflection",
    "Rumba",
    "BlueZone",
    "Personal Communications",
    "IBM",
    "AS400",
    "Mainframe",
    "Citrix",
]


def scan_windows(processes: list[dict] | None = None) -> list[TargetWindow]:
    try:
        import win32gui
        import win32process
    except Exception:
        return []

    process_by_pid = {proc.get("pid"): proc for proc in processes or []}
    windows: list[TargetWindow] = []

    def collect(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            pid = None
        proc = process_by_pid.get(pid, {})
        try:
            class_name = win32gui.GetClassName(hwnd)
        except Exception:
            class_name = ""
        windows.append(
            TargetWindow(
                title=title,
                hwnd=hwnd,
                class_name=class_name,
                process_name=proc.get("name", ""),
                pid=pid,
                exe_path=proc.get("exe", ""),
            )
        )

    win32gui.EnumWindows(collect, None)
    windows.sort(key=lambda item: (0 if is_likely_window(item) else 1, item.title.lower()))
    return windows


def is_likely_window(window: TargetWindow) -> bool:
    haystack = f"{window.title} {window.process_name} {window.class_name}".lower()
    return any(term.lower() in haystack for term in LIKELY_TITLE_TERMS)
