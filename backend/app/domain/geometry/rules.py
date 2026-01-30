WALL_THICKNESS = 0.2  # meters

def validate_rectangle(width: float, height: float):
    if width <= 0 or height <= 0:
        raise ValueError("Invalid rectangle dimensions")

    if width < 2 or height < 2:
        raise ValueError("Room too small")
