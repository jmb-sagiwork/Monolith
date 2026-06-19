from __future__ import annotations

from monolith.core.models import TargetWindow


def inspect_window(window: TargetWindow) -> dict:
    if not window.hwnd:
        return {"available": False, "message": "No selected window."}
    try:
        import win32gui

        children = []

        def collect(hwnd: int, _: object) -> None:
            if len(children) >= 20:
                return
            children.append({"class_name": win32gui.GetClassName(hwnd), "text": win32gui.GetWindowText(hwnd)})

        win32gui.EnumChildWindows(window.hwnd, collect, None)
        return {"available": True, "children": children, "message": f"Child controls found: {len(children)}"}
    except Exception as exc:
        return {"available": False, "message": str(exc)}
