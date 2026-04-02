from dataclasses import dataclass

from app.schemas.geometry import Point
from app.services import dxf_room_renderer as renderer_module
from app.services.dxf_room_renderer import DXFRoomRenderer, draw_furniture


@dataclass(frozen=True)
class _RoomStub:
    name: str
    room_type: str
    width: float
    height: float


class _DummyModelSpace:
    def __init__(self) -> None:
        self.blockrefs: list[tuple[str, tuple[float, float], dict]] = []
        self.polylines: list[tuple[list[tuple[float, float]], dict]] = []
        self.mtexts: list[tuple[str, dict]] = []

    def add_blockref(self, name: str, insert: tuple[float, float], dxfattribs: dict) -> None:
        self.blockrefs.append((name, insert, dxfattribs))

    def add_lwpolyline(self, points, close: bool, dxfattribs: dict) -> None:
        _ = close
        self.polylines.append((list(points), dxfattribs))

    def add_mtext(self, text: str, dxfattribs: dict) -> None:
        self.mtexts.append((text, dxfattribs))


def _rectangle_segment_pairs(width: float, height: float, offset: float = 0.075) -> list[tuple[Point, Point]]:
    return [
        (Point(x=0.0, y=-offset), Point(x=width, y=-offset)),
        (Point(x=0.0, y=offset), Point(x=width, y=offset)),
        (Point(x=0.0, y=height - offset), Point(x=width, y=height - offset)),
        (Point(x=0.0, y=height + offset), Point(x=width, y=height + offset)),
        (Point(x=-offset, y=0.0), Point(x=-offset, y=height)),
        (Point(x=offset, y=0.0), Point(x=offset, y=height)),
        (Point(x=width - offset, y=0.0), Point(x=width - offset, y=height)),
        (Point(x=width + offset, y=0.0), Point(x=width + offset, y=height)),
    ]


def test_living_room_sofa_is_centered_on_longest_wall_and_tv_opposite() -> None:
    msp = _DummyModelSpace()
    room = _RoomStub(name="Living Room", room_type="living_room", width=6.0, height=4.0)

    draw_furniture(msp, room, 0.0, 0.0, door_wall=None)

    sofa = next(item for item in msp.blockrefs if item[0] == "SOFA_3SEAT")
    assert abs(sofa[1][0] - ((6.0 - 2.20) / 2.0)) < 1e-6
    assert abs(sofa[1][1] - 0.15) < 1e-6

    table = next(item for item in msp.blockrefs if item[0] == "COFFEE_TABLE")
    assert table[1][1] > sofa[1][1]
    assert msp.polylines


def test_bedroom_without_door_places_bed_on_top_wall_centered() -> None:
    msp = _DummyModelSpace()
    room = _RoomStub(name="Bedroom", room_type="bedroom", width=4.0, height=4.0)

    draw_furniture(msp, room, 0.0, 0.0, door_wall=None)

    bed = next(item for item in msp.blockrefs if item[0] in {"BED_DOUBLE", "BED_SINGLE"})
    assert abs(bed[1][0] - 2.80) < 1e-6
    assert abs(bed[1][1] - 3.85) < 1e-6


def test_kitchen_switches_between_single_wall_and_l_shape() -> None:
    single_msp = _DummyModelSpace()
    single_room = _RoomStub(name="Kitchen Small", room_type="kitchen", width=2.4, height=3.0)
    draw_furniture(single_msp, single_room, 0.0, 0.0, door_wall="bottom")
    single_sink_count = sum(1 for item in single_msp.blockrefs if item[0] == "KITCHEN_SINK_DOUBLE")

    lshape_msp = _DummyModelSpace()
    lshape_room = _RoomStub(name="Kitchen Large", room_type="kitchen", width=3.2, height=3.0)
    draw_furniture(lshape_msp, lshape_room, 0.0, 0.0, door_wall="bottom")
    lshape_sink_count = sum(1 for item in lshape_msp.blockrefs if item[0] == "KITCHEN_SINK_DOUBLE")

    assert single_sink_count == 1
    assert lshape_sink_count >= 2


def test_bathroom_shower_appears_only_when_room_is_large_enough() -> None:
    small_msp = _DummyModelSpace()
    small_room = _RoomStub(name="Bathroom Small", room_type="bathroom", width=1.7, height=2.0)
    draw_furniture(small_msp, small_room, 0.0, 0.0, door_wall="bottom")
    assert not any(item[0] == "SHOWER_TRAY" for item in small_msp.blockrefs)

    large_msp = _DummyModelSpace()
    large_room = _RoomStub(name="Bathroom Large", room_type="bathroom", width=2.0, height=2.0)
    draw_furniture(large_msp, large_room, 0.0, 0.0, door_wall="bottom")
    assert any(item[0] == "SHOWER_TRAY" for item in large_msp.blockrefs)


def test_resolve_furniture_preset_uses_room_type() -> None:
    assert DXFRoomRenderer._resolve_furniture_preset("Family Space", room_type="living") == "living_room"
    assert DXFRoomRenderer._resolve_furniture_preset("Guest Room", room_type="bedroom") == "bedroom"
    assert DXFRoomRenderer._resolve_furniture_preset("Main Bath", room_type="bathroom") == "bathroom"


def test_renderer_initializes_professional_white_sheet_headers_and_layers() -> None:
    renderer = DXFRoomRenderer()
    assert renderer.doc.header["$INSUNITS"] == 6
    assert renderer.doc.header["$MEASUREMENT"] == 1
    assert renderer.doc.layers.get("WALLS").lineweight == 50
    assert renderer.doc.layers.get("BORDER").lineweight == 70
    assert renderer.doc.layers.get("FURNITURE_BEDROOM").color == 252


def test_wall_segments_render_as_const_width_wall_polylines() -> None:
    renderer = DXFRoomRenderer()

    renderer.draw_wall_segments(
        [
            (Point(x=0.0, y=0.925), Point(x=4.0, y=0.925)),
            (Point(x=0.0, y=1.075), Point(x=4.0, y=1.075)),
        ]
    )

    wall_polylines = [
        entity for entity in renderer.msp if entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "WALLS"
    ]
    assert len(wall_polylines) == 1
    assert abs(wall_polylines[0].dxf.const_width - 0.20) < 1e-6


def test_draw_room_label_adds_centered_text_and_bathroom_hatch() -> None:
    renderer = DXFRoomRenderer()
    renderer.draw_boundary_segments(_rectangle_segment_pairs(4.0, 3.0))

    renderer.draw_room_label("Bathroom", Point(x=2.0, y=1.5), room_type="bathroom")

    texts = [entity.dxf.text for entity in renderer.msp if entity.dxftype() == "TEXT"]
    assert "BATHROOM" in texts
    assert '13\'-1" x 9\'-10"' in texts
    assert any(entity.dxftype() == "HATCH" and entity.dxf.layer == "HATCH" for entity in renderer.msp)


def test_draw_room_dimensions_is_a_compatibility_no_op() -> None:
    renderer = DXFRoomRenderer()
    before = len(list(renderer.msp))

    renderer.draw_room_dimensions("3.00m x 4.00m", Point(x=1.5, y=1.5))

    assert len(list(renderer.msp)) == before


def test_save_adds_exterior_dimensions_border_and_title(monkeypatch, tmp_path) -> None:
    renderer = DXFRoomRenderer()
    renderer.draw_boundary_segments(_rectangle_segment_pairs(6.0, 4.0))
    target_path = tmp_path / "layout_test.dxf"
    monkeypatch.setattr(renderer_module, "generate_dxf_filename", lambda prefix="layout": target_path)

    saved_path = renderer.save()

    assert saved_path == target_path
    assert target_path.exists()
    assert any(entity.dxftype() == "DIMENSION" and entity.dxf.layer == "DIMENSIONS" for entity in renderer.msp)
    assert any(entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "BORDER" for entity in renderer.msp)
    assert any(entity.dxftype() == "TEXT" and entity.dxf.text == "FLOOR PLAN" for entity in renderer.msp)
