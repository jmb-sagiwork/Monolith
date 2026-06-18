from __future__ import annotations

from monolith.core.models import AdapterResult, TargetWindow


def test_uia(window: TargetWindow) -> AdapterResult:
    if not window.hwnd:
        return AdapterResult("UI Automation", "Unavailable", "low", "No selected window handle.")
    try:
        from pywinauto import Application

        app = Application(backend="uia").connect(handle=window.hwnd, timeout=3)
        target = app.window(handle=window.hwnd)
        descendants = target.descendants()
        title = target.window_text() or window.title
        notes = f"Connected to '{title}'. Controls visible: {len(descendants)}."
        return AdapterResult("UI Automation", "Available", "medium", notes)
    except Exception as exc:
        return AdapterResult("UI Automation", "Error", "low", str(exc))
