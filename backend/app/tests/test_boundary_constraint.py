from app.schemas.room import Room
from app.schemas.geometry import Point, RectangleGeometry
from app.domain.constraints.boundary import is_room_inside_boundary


def main():
    boundary = RectangleGeometry(
        type="rectangle",
        width=30,
        height=50,
        origin=Point(x=0, y=0)
    )

    room_inside = Room(
        name="Living",
        room_type="living",
        width=10,
        height=8,
        origin=Point(x=5, y=5)
    )

    room_outside = Room(
        name="Bedroom",
        room_type="bedroom",
        width=10,
        height=8,
        origin=Point(x=25, y=45)
    )

    print("Inside room valid:",
          is_room_inside_boundary(room_inside, boundary))

    print("Outside room valid:",
          is_room_inside_boundary(room_outside, boundary))


if __name__ == "__main__":
    main()
