"""
DXF block definitions for reusable door symbols.

This module provides functions to create DXF blocks (reusable symbols)
for doors that can be inserted multiple times in a drawing.
"""

def create_single_door_block(doc):
    """
    Create a reusable door block in the DXF document.
    
    Creates a block definition with a door leaf line and swing arc.
    The block can be inserted multiple times with different positions/rotations.
    
    Args:
        doc: ezdxf document to add the block to.
    """
    # Skip if block already exists
    if "DOOR_SINGLE" in doc.blocks:
        return

    block = doc.blocks.new(name="DOOR_SINGLE")

    # Door leaf (line from hinge to end)
    block.add_line((0, 0), (1, 0))

    # Swing arc (90-degree arc showing door opening path)
    block.add_arc(center=(0, 0), radius=1, start_angle=0, end_angle=90)
