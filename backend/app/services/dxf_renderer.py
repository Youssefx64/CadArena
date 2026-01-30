import ezdxf
from app.schemas.geometry import Point

def draw_rectangle(points: list[Point], filename: str):
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    msp.add_lwpolyline(
        [(p.x, p.y) for p in points],
        close=True
    )

    doc.saveas(filename)