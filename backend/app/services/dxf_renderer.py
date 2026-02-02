import ezdxf
from pathlib import Path
from app.schemas.geometry import Point


def draw_rectangle(points: list[Point], file_path: Path):
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    msp.add_lwpolyline(
        [(p.x, p.y) for p in points],
        close=True
    )

    doc.saveas(file_path)
