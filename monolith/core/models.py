from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


TARGET_TYPES = ["Terminal Emulator", "Website", "Desktop Application"]
ACTION_TYPES = ["Click", "Type", "Extract Text"]
STEP_STATUSES = ["Pending", "Passed", "Failed", "Skipped", "Needs Manual Review"]


@dataclass
class CapturedTarget:
    target_type: str
    adapter: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def label(self) -> str:
        metadata = self.metadata
        for key in ("text", "name", "automation_id", "css_selector", "terminal_action", "description"):
            value = metadata.get(key)
            if value:
                return str(value)
        return "Captured Target"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandshakeStep:
    step_number: int
    action: str
    status: str = "Pending"
    captured_target: Optional[CapturedTarget] = None
    sample_input: str = ""
    extracted_text: str = ""
    test_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "action": self.action,
            "status": self.status,
            "sample_input": self.sample_input,
            "target": self.captured_target.to_dict() if self.captured_target else None,
            "extracted_text": self.extracted_text,
            "test_result": {
                "passed": self.status == "Passed",
                "message": self.test_message,
            },
        }


@dataclass
class HandshakeRecipe:
    monolith_version: str = "V2"
    target_type: str = ""
    adapter: str = ""
    status: str = "Pending"
    steps: list[HandshakeStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "monolith_version": self.monolith_version,
            "target_type": self.target_type,
            "adapter": self.adapter,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "notes": self.notes,
        }


@dataclass
class TargetWindow:
    title: str = ""
    hwnd: Optional[int] = None
    class_name: str = ""
    process_name: str = ""
    pid: Optional[int] = None
    exe_path: str = ""

    def label(self) -> str:
        title = self.title or "Untitled"
        proc = f" - {self.process_name}" if self.process_name else ""
        return f"{title}{proc}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionProfile:
    path: str = ""
    extension: str = ""
    product_guess: str = "Unknown"
    backend_guess: str = "Unknown"
    confidence: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AdapterDetection:
    adapter: str = "Manual row/column guidance"
    confidence: str = "low"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
