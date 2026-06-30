from copy import deepcopy

from app.services.design_parser.layout_planner import DeterministicLayoutPlanner
from app.services.design_parser.opening_planner import DeterministicOpeningPlanner
from app.services.design_parser.quality_gate import ArchitecturalQualityGate


def _compliant_payload() -> tuple[dict, dict]:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
            {"name": "Main Corridor", "room_type": "corridor", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }
    layout, meta = DeterministicLayoutPlanner().plan_with_metadata(extracted)
    planned = DeterministicOpeningPlanner().plan(
        extracted_payload=extracted,
        layout_payload=layout,
    )
    metrics = dict(meta["topology_metrics"])
    metrics["total_score"] = 0.95
    metrics["selected_topology"] = meta["selected_topology"]
    return planned, metrics


def test_quality_gate_passes_compliant_planned_layout() -> None:
    planned, metrics = _compliant_payload()

    report = ArchitecturalQualityGate().evaluate(
        planned_payload=planned,
        metrics_payload=metrics,
        strict_openings=True,
    )

    assert report.passed is True
    assert report.score == 0.95
    assert report.grade in {"A", "B"}
    assert report.code_profile == "EBC_RESIDENTIAL_V1"
    assert report.hard_failures == []


def test_quality_gate_rejects_ebc_dimension_failure() -> None:
    planned, metrics = _compliant_payload()
    bedroom = next(room for room in planned["rooms"] if room["room_type"] == "bedroom")
    bedroom["width"] = 2.0

    report = ArchitecturalQualityGate().evaluate(
        planned_payload=planned,
        metrics_payload=metrics,
        strict_openings=True,
    )

    assert report.passed is False
    assert any("ebc_dimension" in failure for failure in report.hard_failures)


def test_quality_gate_rejects_low_score() -> None:
    planned, metrics = _compliant_payload()
    metrics["total_score"] = 0.79

    report = ArchitecturalQualityGate().evaluate(
        planned_payload=planned,
        metrics_payload=metrics,
        strict_openings=True,
    )

    assert report.passed is False
    assert "quality_score_below_threshold:0.790<min:0.800" in report.hard_failures


def test_quality_gate_rejects_shared_bathroom_with_multiple_doors() -> None:
    planned, metrics = _compliant_payload()
    bathroom_door = next(
        opening
        for opening in planned["openings"]
        if opening["type"] == "door" and opening["room_name"] == "Bathroom"
    )
    planned["openings"].append(deepcopy(bathroom_door))

    report = ArchitecturalQualityGate().evaluate(
        planned_payload=planned,
        metrics_payload=metrics,
        strict_openings=True,
    )

    assert report.passed is False
    assert "bathroom_multiple_doors:Bathroom:2" in report.hard_failures


def test_quality_gate_rejects_bathroom_used_as_bedroom_passage() -> None:
    planned = {
        "boundary": {"width": 16.0, "height": 10.0},
        "rooms": [
            {
                "name": "Bathroom",
                "room_type": "bathroom",
                "width": 8.77,
                "height": 2.30,
                "origin": {"x": 7.23, "y": 7.70},
            },
            {
                "name": "Bedroom 2",
                "room_type": "bedroom",
                "width": 4.39,
                "height": 7.70,
                "origin": {"x": 11.61, "y": 0.0},
            },
            {
                "name": "Main Corridor",
                "room_type": "corridor",
                "width": 1.2,
                "height": 10.0,
                "origin": {"x": 6.03, "y": 0.0},
            },
        ],
        "openings": [
            {
                "type": "door",
                "room_name": "Bedroom 2",
                "wall": "top",
                "cut_start": {"x": 13.46, "y": 7.70},
                "cut_end": {"x": 14.16, "y": 7.70},
            },
            {
                "type": "door",
                "room_name": "Bathroom",
                "wall": "bottom",
                "cut_start": {"x": 13.46, "y": 7.70},
                "cut_end": {"x": 14.16, "y": 7.70},
            },
            {
                "type": "door",
                "room_name": "Bathroom",
                "wall": "left",
                "cut_start": {"x": 7.23, "y": 8.50},
                "cut_end": {"x": 7.23, "y": 9.20},
            },
            {
                "type": "door",
                "room_name": "Main Corridor",
                "wall": "right",
                "cut_start": {"x": 7.23, "y": 8.50},
                "cut_end": {"x": 7.23, "y": 9.20},
            },
        ],
    }

    report = ArchitecturalQualityGate().evaluate(
        planned_payload=planned,
        metrics_payload={"total_score": 0.95, "selected_topology": "regression"},
        strict_openings=True,
    )

    assert report.passed is False
    assert "bathroom_multiple_doors:Bathroom:2" in report.hard_failures
    assert "forbidden_door_pair:Bathroom:Bedroom 2" in report.hard_failures
