from __future__ import annotations


def clipboard_available(root=None) -> bool:
    try:
        import pyperclip

        pyperclip.paste()
        return True
    except Exception:
        if root is None:
            return False
        try:
            root.clipboard_get()
            return True
        except Exception:
            return False
