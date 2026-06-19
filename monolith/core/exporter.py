from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from monolith.core.code_generator import generate_code
from monolith.core.markdown_generator import generate_markdown
from monolith.core.models import HandshakeRecipe
from monolith.core.recipe_generator import generate_recipe


def export_handshake(recipe: HandshakeRecipe) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = Path("output/handshakes") / stamp
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "handshake_recipe.json").write_text(
        json.dumps(generate_recipe(recipe), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (folder / "handshake_summary.md").write_text(generate_markdown(recipe), encoding="utf-8")
    (folder / "generated_handshake.py").write_text(generate_code(recipe), encoding="utf-8")
    return folder
