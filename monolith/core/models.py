from dataclasses import dataclass, field, asdict
from typing import Optional


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

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SessionProfile:
    path: str = ""
    extension: str = ""
    product_guess: str = "Unknown"
    backend_guess: str = "Unknown"
    confidence: str = "unknown"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdapterResult:
    name: str
    status: str
    confidence: str
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanResult:
    product_guess: str = "Unknown"
    launcher_guess: str = "Unknown"
    backend_guess: str = "Unknown"
    best_adapter: str = "Unknown"
    selected_window: TargetWindow = field(default_factory=TargetWindow)
    selected_profile: SessionProfile = field(default_factory=SessionProfile)
    adapters: list[AdapterResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["adapters"] = [adapter.to_dict() for adapter in self.adapters]
        return data
