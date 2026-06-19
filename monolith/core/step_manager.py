from __future__ import annotations

from monolith.core.models import ACTION_TYPES, CapturedTarget, HandshakeStep


class StepManager:
    def __init__(self) -> None:
        self.steps: list[HandshakeStep] = []

    def add_step(self, action: str, target: CapturedTarget | None, sample_input: str = "") -> HandshakeStep:
        if action not in ACTION_TYPES:
            raise ValueError(f"Unsupported action type: {action}")
        step = HandshakeStep(
            step_number=len(self.steps) + 1,
            action=action,
            captured_target=target,
            sample_input=sample_input,
        )
        self.steps.append(step)
        self._renumber()
        return step

    def delete_step(self, index: int) -> None:
        if 0 <= index < len(self.steps):
            del self.steps[index]
            self._renumber()

    def move_up(self, index: int) -> int:
        if index > 0:
            self.steps[index - 1], self.steps[index] = self.steps[index], self.steps[index - 1]
            self._renumber()
            return index - 1
        return index

    def move_down(self, index: int) -> int:
        if 0 <= index < len(self.steps) - 1:
            self.steps[index + 1], self.steps[index] = self.steps[index], self.steps[index + 1]
            self._renumber()
            return index + 1
        return index

    def get(self, index: int) -> HandshakeStep | None:
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def update_status(self, step: HandshakeStep, status: str, message: str, extracted_text: str = "") -> None:
        step.status = status
        step.test_message = message
        if extracted_text:
            step.extracted_text = extracted_text

    def overall_status(self) -> str:
        if not self.steps:
            return "Pending"
        if all(step.status == "Passed" for step in self.steps):
            return "Passed"
        if any(step.status in {"Failed", "Needs Manual Review"} for step in self.steps):
            return "Partial"
        return "Pending"

    def _renumber(self) -> None:
        for index, step in enumerate(self.steps, start=1):
            step.step_number = index
