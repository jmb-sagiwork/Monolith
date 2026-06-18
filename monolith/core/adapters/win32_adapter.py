from __future__ import annotations

from monolith.core.models import AdapterResult, TargetWindow


def test_win32(window: TargetWindow) -> AdapterResult:
    if not window.hwnd:
        return AdapterResult("Win32 Window Read", "Unavailable", "low", "No selected window handle.")
    try:
        import win32gui

        count = 0
        samples: list[str] = []

        def collect(hwnd: int, _: object) -> None:
            nonlocal count
            count += 1
            if len(samples) < 5:
                text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                samples.append(f"{class_name}:{text}".strip(":"))

        win32gui.EnumChildWindows(window.hwnd, collect, None)
        notes = f"Child controls found: {count}."
        if samples:
            notes += " Samples: " + "; ".join(samples)
        return AdapterResult("Win32 Window Read", "Available", "medium", notes)
    except Exception as exc:
        return AdapterResult("Win32 Window Read", "Error", "low", str(exc))
