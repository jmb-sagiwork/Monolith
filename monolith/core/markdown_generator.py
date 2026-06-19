from __future__ import annotations

from monolith.core.models import HandshakeRecipe


def generate_markdown(recipe: HandshakeRecipe) -> str:
    lines = [
        "# Monolith Handshake Summary",
        "",
        "## Target Type",
        "",
        recipe.target_type or "Unknown",
        "",
        "## Adapter",
        "",
        recipe.adapter or "Unknown",
        "",
        "## Overall Status",
        "",
        recipe.status,
        "",
        "## Steps",
        "",
    ]
    for step in recipe.steps:
        target = step.captured_target.label() if step.captured_target else "Not captured"
        lines.extend(
            [
                f"### Step {step.step_number} - {step.action}",
                "",
                f"Status: {step.status}  ",
                f"Target: {target}  ",
            ]
        )
        if step.sample_input:
            lines.append(f"Sample Input: {step.sample_input}  ")
        if step.extracted_text:
            lines.append(f"Extracted Text: {step.extracted_text}  ")
        if step.test_message:
            lines.append(f"Message: {step.test_message}  ")
        lines.append("")
    lines.extend(
        [
            "## Developer Notes",
            "",
            "This handshake was generated from a user-driven test.",
            "Selectors and target objects should be validated by the developer before production use.",
            "No screenshots or OCR artifacts were captured by Monolith V2.",
            "",
        ]
    )
    return "\n".join(lines)
