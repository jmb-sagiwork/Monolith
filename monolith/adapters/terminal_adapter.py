from __future__ import annotations

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
                return "Needs Manual Review", "Terminal input position and sample text saved for developer validation.", ""
            return "Failed", "Missing terminal row/column or sample input.", ""
        return "Needs Manual Review", f"Terminal action saved: {metadata.get('terminal_action', 'Enter')}", ""
