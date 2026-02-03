import math


def create_single_door_block(doc):
    if "DOOR_SINGLE" in doc.blocks:
        return

    block = doc.blocks.new(name="DOOR_SINGLE")

    # Door leaf
    block.add_line((0, 0), (1, 0))

    # Swing arc
    block.add_arc(center=(0, 0), radius=1, start_angle=0, end_angle=90)
