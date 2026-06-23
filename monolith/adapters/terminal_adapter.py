from __future__ import annotations

import time

from monolith.adapters.clipboard_adapter import clipboard_available
from monolith.adapters.hllapi_detector import detect_hllapi
from monolith.adapters.win32_adapter import inspect_window
from monolith.core.models import AdapterDetection, CapturedTarget, TargetWindow
from monolith.scanners.process_scanner import likely_emulator_processes, scan_processes
from monolith.scanners.profile_scanner import guess_profile, scan_profiles
from monolith.scanners.window_scanner import scan_windows


TERMINAL_KEYS = ["Enter", "Tab", "PF1", "PF2", "PF3", "PF4", "PF5", "PF6", "PF7", "PF8", "PF9", "PF10", "PF11", "PF12"]


class TerminalAdapter:
    def detect(self, selected_window: TargetWindow | None, session_file: str = "", root=None) -> tuple[AdapterDetection, dict]:
        processes = scan_processes()
        windows = scan_windows(processes)
        profiles = scan_profiles()
        profile_guess = guess_profile(session_file) if session_file else {}
        roots = [session_file]
        if selected_window and selected_window.exe_path:
            roots.append(selected_window.exe_path)
        hllapi = detect_hllapi(roots)
        win32 = inspect_window(selected_window) if selected_window else {"available": False}
        clipboard = clipboard_available(root)

        if hllapi["available"]:
            detection = AdapterDetection("HLLAPI / EHLLAPI", hllapi["confidence"], {"dlls": hllapi["dlls"]})
        elif clipboard:
            detection = AdapterDetection("Clipboard screen copy", "medium", {})
        elif win32.get("available"):
            detection = AdapterDetection("UIA / Win32", "medium", win32)
        else:
            detection = AdapterDetection("Manual row/column guidance", "low", {})

        details = {
            "windows": [window.to_dict() for window in windows],
            "processes": likely_emulator_processes(processes),
            "profiles": profiles,
            "profile_guess": profile_guess,
            "hllapi": hllapi,
            "clipboard_available": clipboard,
            "win32": win32,
        }
        return detection, details

    def read_screen_preview(self) -> str:
        return (
            "Screen preview is not available from the detected adapter yet.\n"
            "Use manual row/column capture, or validate HLLAPI/EHLLAPI support in generated code."
        )

    def build_target(self, action: str, metadata: dict) -> CapturedTarget:
        return CapturedTarget("Terminal Emulator", "Terminal Adapter", metadata)

    def test_step(self, action: str, metadata: dict, sample_input: str = "") -> tuple[str, str, str]:
        if action == "Extract Text":
            if metadata.get("row") and metadata.get("column") and metadata.get("length"):
                return "Needs Manual Review", "Terminal extraction region saved for developer validation.", ""
            return "Failed", "Missing row, column, or length for terminal extraction.", ""
        if action == "Type":
            if metadata.get("row") and metadata.get("column") and sample_input:
                ok, message = self._focus_terminal(metadata)
                if not ok:
                    return "Failed", message, ""
                sent, send_message = self._send_text(sample_input)
                if sent:
                    return (
                        "Passed",
                        "Typed sample input into the focused terminal window. "
                        "Row/column were saved for the recipe but not enforced without a full HLLAPI cursor-position implementation.",
                        "",
                    )
                return "Failed", send_message, ""
            return "Failed", "Missing terminal row/column or sample input.", ""
        ok, message = self._focus_terminal(metadata)
        if not ok:
            return "Failed", message, ""
        sent, send_message = self._send_terminal_action(metadata.get("terminal_action", "Enter"))
        if sent:
            return "Passed", f"Sent terminal action: {metadata.get('terminal_action', 'Enter')}.", ""
        return "Failed", send_message, ""

    def _focus_terminal(self, metadata: dict) -> tuple[bool, str]:
        hwnd = (metadata.get("window") or {}).get("hwnd")
        if not hwnd:
            return False, "No terminal window handle was saved with this step. Click Refresh Windows, save the target again, then retest."
        try:
            import win32con
            import win32gui

            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.25)
            return True, "Terminal window focused."
        except Exception as exc:
            return False, f"Could not focus terminal window: {exc}"

    def _send_text(self, text: str) -> tuple[bool, str]:
        try:
            from pywinauto.keyboard import send_keys

            send_keys(text, with_spaces=True, pause=0.02)
            return True, "Text sent."
        except Exception as exc:
            return False, f"Could not type into terminal window: {exc}"

    def _send_terminal_action(self, action: str) -> tuple[bool, str]:
        key_map = {
            "Enter": "{ENTER}",
            "Tab": "{TAB}",
            "PF1": "{F1}",
            "PF2": "{F2}",
            "PF3": "{F3}",
            "PF4": "{F4}",
            "PF5": "{F5}",
            "PF6": "{F6}",
            "PF7": "{F7}",
            "PF8": "{F8}",
            "PF9": "{F9}",
            "PF10": "{F10}",
            "PF11": "{F11}",
            "PF12": "{F12}",
        }
        try:
            from pywinauto.keyboard import send_keys

            send_keys(key_map.get(action, "{ENTER}"), pause=0.02)
            return True, "Terminal action sent."
        except Exception as exc:
            return False, f"Could not send terminal action: {exc}"
