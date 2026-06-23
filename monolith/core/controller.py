from __future__ import annotations

import os
import queue
import threading
import time
from pathlib import Path
from typing import Callable

from monolith.adapters.desktop_uia_adapter import DesktopUIAAdapter
from monolith.adapters.terminal_adapter import TERMINAL_KEYS, TerminalAdapter
from monolith.adapters.website_playwright_adapter import WebsitePlaywrightAdapter
from monolith.core.exporter import export_handshake
from monolith.core.logger import AppLogger
from monolith.core.models import CapturedTarget, HandshakeRecipe, HandshakeStep, TargetWindow
from monolith.core.step_manager import StepManager


class MonolithController:
    def __init__(self, root, callbacks: dict[str, Callable]) -> None:
        self.root = root
        self.callbacks = callbacks
        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.logger = AppLogger(self._queue_log)
        self.step_manager = StepManager()
        self.target_type = "Terminal Emulator"
        self.adapter_name = "Manual row/column guidance"
        self.current_target: CapturedTarget | None = None
        self.selected_window: TargetWindow | None = None
        self.session_file = ""
        self.website_url = ""
        self.export_folder: Path | None = None
        self.website = WebsitePlaywrightAdapter()
        self.desktop = DesktopUIAAdapter()
        self.terminal = TerminalAdapter()
        self.desktop_windows: list[TargetWindow] = []
        self.terminal_detection_done = False

    def start(self) -> None:
        self.root.after(100, self._drain_queue)
        self.logger.info("Monolith V2 started.")
        self.emit_state()

    def set_target_type(self, target_type: str) -> None:
        self.target_type = target_type
        self.current_target = None
        if target_type == "Website":
            self.adapter_name = "Playwright"
        elif target_type == "Desktop Application":
            self.adapter_name = "UI Automation"
        else:
            self.adapter_name = "Manual row/column guidance"
            self.terminal_detection_done = False
        self.logger.info(f"{target_type} mode selected.")
        self.emit_state()

    def open_website(self, url: str) -> None:
        self.website_url = url.strip()
        self._run(lambda: self._open_website(self.website_url))

    def _open_website(self, url: str) -> None:
        if not url:
            self.logger.warn("Website URL is required.")
            return
        ok, message = self.website.open_browser(url)
        self.logger.info(message) if ok else self.logger.error(message)
        self.queue.put(("website_status", {"status": "Open" if ok else "Error", "url": self.website.current_url or url}))

    def start_website_catch(self) -> None:
        self._run(self._start_website_catch)

    def _start_website_catch(self) -> None:
        self.logger.info("Website catch mode started. Click an element in the controlled browser.")
        try:
            self.current_target = self.website.start_catch_mode()
            self.logger.info("Website element captured.")
            self.queue.put(("captured", self.current_target))
        except Exception as exc:
            self.logger.error(str(exc))

    def stop_website_catch(self) -> None:
        self.website.stop_catch_mode()
        self.logger.info("Website catch mode stopped.")

    def refresh_desktop_windows(self) -> None:
        self._run(self._refresh_desktop_windows)

    def _refresh_desktop_windows(self) -> None:
        self.desktop_windows = self.desktop.list_windows()
        if self.desktop_windows and self.selected_window is None:
            self.selected_window = self.desktop_windows[0]
        self.logger.info(f"Desktop windows found: {len(self.desktop_windows)}")
        self.queue.put(("windows", self.desktop_windows))

    def select_window(self, index: int) -> None:
        if 0 <= index < len(self.desktop_windows):
            self.selected_window = self.desktop_windows[index]
            self.logger.info(f"Selected window: {self.selected_window.label()}")
            self.emit_state()

    def catch_desktop_target(self) -> None:
        self._run(self._catch_desktop_target)

    def _catch_desktop_target(self) -> None:
        self.logger.info("Desktop catch armed. Hover over the target object and press F9.")
        try:
            self.current_target = self.desktop.catch_under_mouse_f9(self.selected_window)
            self.logger.info("Desktop UIA target captured.")
            self.queue.put(("captured", self.current_target))
        except Exception as exc:
            self.logger.error(str(exc))

    def detect_terminal_adapter(self) -> None:
        self._run(self._detect_terminal_adapter)

    def _detect_terminal_adapter(self) -> None:
        detection, details = self.terminal.detect(self.selected_window, self.session_file, self.root)
        self.adapter_name = detection.adapter
        self.terminal_detection_done = True
        self.logger.info(f"Terminal adapter detected: {detection.adapter} ({detection.confidence})")
        self.queue.put(("terminal_detection", {"detection": detection.to_dict(), "details": details}))
        self.emit_state()

    def select_session_file(self, path: str) -> None:
        self.session_file = path
        self.logger.info(f"Selected session file: {path}")
        self.emit_state()

    def read_terminal_preview(self) -> None:
        self.queue.put(("terminal_preview", self.terminal.read_screen_preview()))
        self.logger.info("Terminal screen preview requested.")

    def catch_terminal_target(self, action: str, metadata: dict) -> None:
        self.current_target = self.terminal.build_target(action, metadata)
        self.logger.info(f"Manual terminal target saved: {self.current_target.label()}.")
        self.queue.put(("captured", self.current_target))

    def add_step(self, action: str, sample_input: str = "") -> None:
        try:
            step = self.step_manager.add_step(action, self.current_target, sample_input)
            self.logger.info(f"Added step {step.step_number}: {action}.")
            self.emit_state()
        except Exception as exc:
            self.logger.error(str(exc))

    def delete_step(self, index: int) -> None:
        self.step_manager.delete_step(index)
        self.logger.info("Deleted selected step.")
        self.emit_state()

    def move_step_up(self, index: int) -> int:
        new_index = self.step_manager.move_up(index)
        self.emit_state()
        return new_index

    def move_step_down(self, index: int) -> int:
        new_index = self.step_manager.move_down(index)
        self.emit_state()
        return new_index

    def test_selected_step(self, index: int) -> None:
        step = self.step_manager.get(index)
        if not step:
            self.logger.warn("No selected step to test.")
            return
        self._run(lambda: self._test_step(step))

    def test_full_handshake(self) -> None:
        self._run(self._test_full_handshake)

    def _test_full_handshake(self) -> None:
        if not self.step_manager.steps:
            self.logger.warn("No steps to test.")
            return
        for step in self.step_manager.steps:
            self._test_step(step, emit=False)
        self.emit_state()
        recipe = self._recipe()
        passed = sum(1 for step in recipe.steps if step.status == "Passed")
        failed = sum(1 for step in recipe.steps if step.status == "Failed")
        review = sum(1 for step in recipe.steps if step.status == "Needs Manual Review")
        if recipe.status == "Passed":
            self.logger.info("Full handshake passed.")
            self.queue.put(("full_passed", {"target_type": recipe.target_type, "steps": len(recipe.steps), "adapter": recipe.adapter}))
        else:
            self.logger.warn("Full handshake completed with issues.")
            self.queue.put(("full_issues", {"passed": passed, "failed": failed, "review": review}))

    def _test_step(self, step: HandshakeStep, emit: bool = True) -> None:
        if step.action in {"Click", "Type"}:
            self._countdown(step.action)
        status, message, extracted = self._dispatch_step_test(step)
        self.step_manager.update_status(step, status, message, extracted)
        self.logger.info(f"Step {step.step_number} {step.action}: {status} - {message}")
        if emit:
            self.emit_state()

    def _dispatch_step_test(self, step: HandshakeStep) -> tuple[str, str, str]:
        if self.target_type == "Website":
            return self.website.test_step(step.action, step.captured_target, step.sample_input)
        if self.target_type == "Desktop Application":
            return self.desktop.test_step(step.action, step.captured_target, step.sample_input)
        metadata = step.captured_target.metadata if step.captured_target else {}
        return self.terminal.test_step(step.action, metadata, step.sample_input)

    def _countdown(self, action: str) -> None:
        for second in range(5, 0, -1):
            self.logger.info(f"{action} test in {second}...")
            time.sleep(1)
        self.logger.info("Running test now...")

    def export_outputs(self) -> None:
        self._run(self._export_outputs)

    def _export_outputs(self) -> None:
        recipe = self._recipe()
        folder = export_handshake(recipe)
        self.export_folder = folder
        self.logger.info(f"Exported handshake outputs: {folder}")
        self.queue.put(("exported", str(folder)))

    def open_export_folder(self) -> None:
        if self.export_folder:
            os.startfile(self.export_folder)

    def _recipe(self) -> HandshakeRecipe:
        recipe = HandshakeRecipe(
            target_type=self.target_type,
            adapter=self.adapter_name,
            status=self.step_manager.overall_status(),
            steps=self.step_manager.steps,
            notes=[self.website_url] if self.target_type == "Website" and self.website_url else [],
        )
        return recipe

    def emit_state(self) -> None:
        self.queue.put(("state", self._recipe()))

    def _run(self, work: Callable[[], None]) -> None:
        threading.Thread(target=work, daemon=True).start()

    def _queue_log(self, line: str) -> None:
        self.queue.put(("log", line))

    def _drain_queue(self) -> None:
        while True:
            try:
                event, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            callback = self.callbacks.get(event)
            if callback:
                callback(payload)
        self.root.after(100, self._drain_queue)
