from __future__ import annotations

from datetime import datetime

from monolith.core.models import HandshakeRecipe


def generate_recipe(recipe: HandshakeRecipe) -> dict:
    data = recipe.to_dict()
    data["created_at"] = datetime.now().isoformat(timespec="seconds")
    return data
