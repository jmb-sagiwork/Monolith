from __future__ import annotations

import time

from monolith.core.models import AdapterResult, TargetWindow


def test_clipboard(window: TargetWindow, root=None) -> AdapterResult:
    if not window.hwnd:
        return AdapterResult("Clipboard Copy", "Unavailable", "low", "No selected window handle.")
    try:
        import win32con
        import win32gui

        previous = _clipboard_get(root)
        win32gui.SetForegroundWindow(window.hwnd)
        time.sleep(0.2)
        win32gui.SendMessage(window.hwnd, win32con.WM_COPY, 0, 0)
        time.sleep(0.3)
        captured = _clipboard_get(root)
        if previous is not None:
            _clipboard_set(previous, root)
        if captured and captured != previous:
            return AdapterResult("Clipboard Copy", "Available", "low", f"Captured {len(captured)} character(s).")
        return AdapterResult("Clipboard Copy", "Unavailable", "low", "No new clipboard text captured.")
    except Exception as exc:
        return AdapterResult("Clipboard Copy", "Error", "low", str(exc))


def _clipboard_get(root=None) -> str | None:
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception:
        if root is None:
            return None
        try:
            return root.clipboard_get()
        except Exception:
            return None


def _clipboard_set(value: str, root=None) -> None:
    try:
        import pyperclip

        pyperclip.copy(value)
    except Exception:
        if root is not None:
            root.clipboard_clear()
            root.clipboard_append(value)
