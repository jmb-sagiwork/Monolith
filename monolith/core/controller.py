from __future__ import annotations

import json
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from monolith.core.adapters.clipboard_adapter import test_clipboard
from monolith.core.adapters.hllapi_adapter import test_hllapi
from monolith.core.adapters.uia_adapter import test_uia
from monolith.core.adapters.win32_adapter import test_win32
from monolith.core.logger import AppLogger
from monolith.core.models import AdapterResult, ScanResult, SessionProfile, TargetWindow
from monolith.core.scanners.dll_scanner import probe_hllapi_dlls
from monolith.core.scanners.process_scanner import likely_emulator_processes, scan_processes
from monolith.core.scanners.profile_scanner import guess_profile, scan_profiles
from monolith.core.scanners.window_scanner import is_likely_window, scan_windows


class MonolithController:
    def __init__(self, root, view_callbacks: dict[str, Callable]) -> None:
        self.root = root
        self.callbacks = view_callbacks
        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.logger = AppLogger(self._queue_log)
        self.windows: list[TargetWindow] = []
        self.profiles: list[SessionProfile] = []
        self.processes: list[dict] = []
        self.found_dlls: list[dict] = []
        self.scan_result = ScanResult()

    def start(self) -> None:
        self.root.after(100, self._drain_queue)
        self.run_thread(self.light_discovery)

    def run_thread(self, work: Callable[[], None]) -> None:
        threading.Thread(target=work, daemon=True).start()

    def light_discovery(self) -> None:
        self.logger.info("Starting light discovery scan.")
        self.processes = scan_processes()
        likely_processes = likely_emulator_processes(self.processes)
        for proc in likely_processes:
            self.logger.info(f"Found emulator process: {proc.get('name')} ({proc.get('pid')})")
        self.windows = scan_windows(self.processes)
        self.profiles = scan_profiles()
        selected = next((item for item in self.windows if is_likely_window(item)), self.windows[0] if self.windows else TargetWindow())
        selected_profile = self.profiles[0] if self.profiles else SessionProfile()
        self.scan_result.selected_window = selected
        self.scan_result.selected_profile = selected_profile
        self._apply_profile_guess(selected_profile)
        self._apply_launcher_guess(likely_processes, selected)
        self.queue.put(("discovery", None))
        self.logger.info(f"Visible windows found: {len(self.windows)}")
        self.logger.info(f"Session/profile files found: {len(self.profiles)}")

    def refresh_windows(self) -> None:
        self.run_thread(self._refresh_windows)

    def _refresh_windows(self) -> None:
        self.processes = scan_processes()
        self.windows = scan_windows(self.processes)
        self.queue.put(("windows", None))
        self.logger.info(f"Window list refreshed: {len(self.windows)} visible windows.")

    def select_profile(self, path: str) -> None:
        self.scan_result.selected_profile = guess_profile(path)
        self._apply_profile_guess(self.scan_result.selected_profile)
        self.queue.put(("result", self.scan_result))
        self.logger.info(f"Selected profile: {path}")

    def select_window_by_index(self, index: int) -> None:
        if 0 <= index < len(self.windows):
            self.scan_result.selected_window = self.windows[index]
            self.queue.put(("result", self.scan_result))
            self.logger.info(f"Selected window: {self.windows[index].label()}")

    def start_scan(self) -> None:
        self.run_thread(self._start_scan)

    def _start_scan(self) -> None:
        self.logger.info("Starting deeper handshake scan.")
        window = self.scan_result.selected_window
        profile = self.scan_result.selected_profile
        self.found_dlls = probe_hllapi_dlls(window.exe_path, profile.path, window.pid)
        adapters = [
            test_win32(window),
            test_uia(window),
            test_hllapi(self.found_dlls),
            AdapterResult("COM / ActiveX", "Unavailable", "low", "Future placeholder for Reflection automation."),
        ]
        self.scan_result.adapters = adapters
        self.scan_result.best_adapter = recommend_best_adapter(self.scan_result)
        self.queue.put(("result", self.scan_result))
        self.logger.info(f"Known HLLAPI DLL candidates found: {len(self.found_dlls)}")
        self.logger.info(f"Recommended adapter: {self.scan_result.best_adapter}")

    def test_uia(self) -> None:
        self.run_thread(lambda: self._single_adapter(test_uia(self.scan_result.selected_window)))

    def probe_dlls(self) -> None:
        self.run_thread(self._probe_dlls)

    def _probe_dlls(self) -> None:
        window = self.scan_result.selected_window
        profile = self.scan_result.selected_profile
        self.found_dlls = probe_hllapi_dlls(window.exe_path, profile.path, window.pid)
        self._single_adapter(test_hllapi(self.found_dlls))

    def test_clipboard(self) -> None:
        self.run_thread(lambda: self._single_adapter(test_clipboard(self.scan_result.selected_window, self.root)))

    def _single_adapter(self, adapter: AdapterResult) -> None:
        existing = [item for item in self.scan_result.adapters if item.name != adapter.name]
        existing.append(adapter)
        self.scan_result.adapters = existing
        self.scan_result.best_adapter = recommend_best_adapter(self.scan_result)
        self.queue.put(("result", self.scan_result))
        self.logger.info(f"{adapter.name}: {adapter.status} - {adapter.notes}")

    def export_report(self) -> None:
        Path("output/reports").mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now()
        path = Path("output/reports") / f"monolith_report_{timestamp:%Y%m%d_%H%M%S}.json"
        payload = self.scan_result.to_dict()
        payload["timestamp"] = timestamp.isoformat()
        payload["logs"] = self.logger.lines
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.logger.info(f"Exported report: {path}")
        self.queue.put(("exported", str(path)))

    def _apply_profile_guess(self, profile: SessionProfile) -> None:
        if profile.path:
            self.scan_result.product_guess = profile.product_guess
            self.scan_result.backend_guess = profile.backend_guess

    def _apply_launcher_guess(self, likely_processes: list[dict], selected: TargetWindow) -> None:
        name = (selected.process_name or "").lower()
        if name == "mystyle.exe" or any((proc.get("name") or "").lower() == "mystyle.exe" for proc in likely_processes):
            self.scan_result.launcher_guess = "MyStyle / Internal Wrapper"
        elif selected.process_name:
            self.scan_result.launcher_guess = selected.process_name
        elif likely_processes:
            self.scan_result.launcher_guess = likely_processes[0].get("name") or "Unknown"

    def _queue_log(self, line: str) -> None:
        self.queue.put(("log", line))

    def _drain_queue(self) -> None:
        while True:
            try:
                event, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            if event == "log":
                self.callbacks["log"](payload)
            elif event in {"discovery", "windows"}:
                self.callbacks["windows"](self.windows, self.scan_result.selected_window)
                self.callbacks["profiles"](self.profiles, self.scan_result.selected_profile)
                self.callbacks["result"](self.scan_result)
            elif event == "result":
                self.callbacks["result"](payload)
            elif event == "exported":
                self.callbacks["exported"](payload)
        self.root.after(100, self._drain_queue)


def recommend_best_adapter(scan_result: ScanResult) -> str:
    names = [
        adapter.name
        for adapter in scan_result.adapters
        if adapter.status.lower() in ["available", "candidate"]
    ]
    if "HLLAPI / EHLLAPI" in names:
        return "HLLAPI / EHLLAPI"
    if "COM / ActiveX" in names:
        return "COM / ActiveX"
    if "UI Automation" in names:
        return "UI Automation"
    if "Clipboard Copy" in names:
        return "Clipboard Copy"
    return "OCR / Image Fallback"
