from app.schemas.room import Room
from app.schemas.geometry import Point
from app.domain.constraints.overlap import rooms_overlap


def main():
    room_a = Room(
        name="Living",
        room_type="living",
        width=10,
        height=8,
        origin=Point(x=0, y=0)
    )

    room_b = Room(
        name="Bedroom",
        room_type="bedroom",
        width=5,
        height=5,
        origin=Point(x=5, y=3)  # overlaps
    )

    room_c = Room(
        name="Kitchen",
        room_type="kitchen",
        width=5,
        height=5,
        origin=Point(x=15, y=0)  # no overlap
    )

    print("A overlaps B:", rooms_overlap(room_a, room_b))
    print("A overlaps C:", rooms_overlap(room_a, room_c))


if __name__ == "__main__":
    main()
