from __future__ import annotations

import time

from monolith.core.models import CapturedTarget, TargetWindow
from monolith.scanners.process_scanner import scan_processes
from monolith.scanners.window_scanner import scan_windows


MANUAL_CHECK = "Text could not be extracted through UI Automation. Please verify manually or choose another readable control."


class DesktopUIAAdapter:
    def list_windows(self) -> list[TargetWindow]:
        return scan_windows(scan_processes())

    def catch_under_mouse_f9(self, selected_window: TargetWindow | None = None, timeout: int = 20) -> CapturedTarget:
        try:
            import win32api
            from pywinauto import Desktop
        except Exception as exc:
            raise RuntimeError(f"Desktop capture dependencies unavailable: {exc}") from exc

        deadline = time.time() + timeout
        while time.time() < deadline:
            if win32api.GetAsyncKeyState(0x78) & 0x8000:
                x, y = win32api.GetCursorPos()
                element = Desktop(backend="uia").from_point(x, y)
                metadata = self._metadata(element, selected_window, x, y)
                return CapturedTarget("Desktop Application", "UI Automation", metadata)
            time.sleep(0.08)
        raise TimeoutError("F9 was not pressed before timeout.")

    def test_step(self, action: str, target: CapturedTarget | None, sample_input: str = "") -> tuple[str, str, str]:
        if not target:
            return "Failed", "No desktop target captured.", ""
        if action == "Click":
            return self._test_click(target)
        if action == "Type":
            return self._test_type(target, sample_input)
        return self._test_extract(target)

    def _test_click(self, target: CapturedTarget) -> tuple[str, str, str]:
        try:
            element = self._resolve(target)
            try:
                element.invoke()
            except Exception:
                element.click_input()
            return "Passed", "Desktop click test passed.", ""
        except Exception as exc:
            return "Failed", f"Desktop click failed: {exc}", ""

    def _test_type(self, target: CapturedTarget, sample_input: str) -> tuple[str, str, str]:
        if not sample_input:
            return "Failed", "Sample input is required for Type.", ""
        try:
            app_window = self._window(target)
            edit_controls = app_window.descendants(control_type="Edit")
            edit_controls_sorted = sorted(edit_controls, key=lambda c: (c.rectangle().top, c.rectangle().left))
            for edit in edit_controls_sorted:
                try:
                    existing_value = edit.get_value()
                except Exception:
                    existing_value = ""
                if existing_value.strip():
                    continue
                try:
                    edit.set_edit_text(sample_input)
                except Exception:
                    edit.click_input()
                    edit.type_keys(sample_input, with_spaces=True)
                return "Passed", "Desktop type test passed. Filled first empty textbox by visual order.", ""
            return "Needs Manual Review", "No empty textbox found to type into.", ""
        except Exception as exc:
            return "Failed", f"Desktop type failed: {exc}", ""

    def _test_extract(self, target: CapturedTarget) -> tuple[str, str, str]:
        try:
            element = self._resolve(target)
            text = ""
            try:
                text = element.window_text()
            except Exception:
                text = ""
            if not text:
                try:
                    text = element.get_value()
                except Exception:
                    text = ""
            if text:
                return "Passed", "Desktop extract test passed.", text
            return "Needs Manual Review", MANUAL_CHECK, ""
        except Exception as exc:
            return "Needs Manual Review", f"{MANUAL_CHECK} Details: {exc}", ""

    def _metadata(self, element, selected_window: TargetWindow | None, x: int, y: int) -> dict:
        rect = element.rectangle()
        metadata = {
            "window_title": selected_window.title if selected_window else "",
            "process_name": selected_window.process_name if selected_window else "",
            "pid": selected_window.pid if selected_window else None,
            "hwnd": selected_window.hwnd if selected_window else None,
            "control_type": getattr(element.element_info, "control_type", ""),
            "name": getattr(element.element_info, "name", ""),
            "automation_id": getattr(element.element_info, "automation_id", ""),
            "class_name": getattr(element.element_info, "class_name", ""),
            "bounding_rectangle": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
            "capture_point": {"x": x, "y": y},
            "value_pattern_available": self._pattern_available(element, "get_value"),
            "text_pattern_available": bool(getattr(element.element_info, "rich_text", False)),
            "parent_hierarchy": self._parents(element),
        }
        return metadata

    def _resolve(self, target: CapturedTarget):
        meta = target.metadata
        app_window = self._window(target)
        name = meta.get("name")
        control_type = meta.get("control_type")
        automation_id = meta.get("automation_id")
        if automation_id:
            return app_window.child_window(auto_id=automation_id, control_type=control_type)
        if name:
            return app_window.child_window(title=name, control_type=control_type)
        return app_window

    def _window(self, target: CapturedTarget):
        from pywinauto import Desktop

        title = target.metadata.get("window_title") or ".*"
        return Desktop(backend="uia").window(title_re=f".*{title}.*")

    def _pattern_available(self, element, attr: str) -> bool:
        return hasattr(element, attr)

    def _parents(self, element) -> list[dict]:
        parents = []
        try:
            parent = element.parent()
            while parent and len(parents) < 5:
                parents.append(
                    {
                        "name": getattr(parent.element_info, "name", ""),
                        "control_type": getattr(parent.element_info, "control_type", ""),
                        "class_name": getattr(parent.element_info, "class_name", ""),
                    }
                )
                parent = parent.parent()
        except Exception:
            pass
        return parents
