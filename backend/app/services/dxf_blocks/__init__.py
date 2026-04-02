from __future__ import annotations

from typing import Any


# Register all architectural block definitions into the drawing before any inserts are created.
def register_all_blocks(doc: Any) -> None:
    from .bedroom_blocks import register_bedroom_blocks
    from .bathroom_blocks import register_bathroom_blocks
    from .living_blocks import register_living_blocks
    from .kitchen_blocks import register_kitchen_blocks

    register_bedroom_blocks(doc)
    register_bathroom_blocks(doc)
    register_living_blocks(doc)
    register_kitchen_blocks(doc)
