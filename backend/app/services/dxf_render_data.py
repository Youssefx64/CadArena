"""Convert a DXF file into structured render JSON for the canvas viewer."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import ezdxf


def extract_render_data(dxf_path: str | Path) -> dict[str, Any]:
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    layers: dict[str, dict[str, Any]] = {}
    for layer in doc.layers:
        layers[layer.dxf.name] = {
            "color": _aci_to_hex(layer.color),
            "visible": True,
        }

    entities: list[dict[str, Any]] = []
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for entity in msp:
        dxf_type = entity.dxftype()
        layer_name = entity.dxf.get("layer", "0")

        if layer_name not in layers:
            layers[layer_name] = {"color": "#000000", "visible": True}

        entry = _convert_entity(entity, dxf_type, layer_name)
        if entry is None:
            continue

        entities.append(entry)
        _update_extents(entry, min_x, min_y, max_x, max_y)
        ex = _entity_extents(entry)
        if ex:
            min_x = min(min_x, ex[0])
            min_y = min(min_y, ex[1])
            max_x = max(max_x, ex[2])
            max_y = max(max_y, ex[3])

    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0

    return {
        "layers": layers,
        "extents": {
            "minX": round(min_x, 4),
            "minY": round(min_y, 4),
            "maxX": round(max_x, 4),
            "maxY": round(max_y, 4),
        },
        "entities": entities,
    }


def _convert_entity(entity, dxf_type: str, layer_name: str) -> dict[str, Any] | None:
    color = _resolve_entity_color(entity)

    if dxf_type == "LINE":
        return {
            "type": "line",
            "layer": layer_name,
            "color": color,
            "start": [round(entity.dxf.start.x, 4), round(entity.dxf.start.y, 4)],
            "end": [round(entity.dxf.end.x, 4), round(entity.dxf.end.y, 4)],
            "lineweight": entity.dxf.get("lineweight", -1),
        }

    if dxf_type == "LWPOLYLINE":
        points = []
        width = 0.0
        for x, y, _start_w, _end_w, _bulge in entity.get_points(format="xyseb"):
            points.append([round(x, 4), round(y, 4)])
            if _start_w > width:
                width = _start_w
        const_w = entity.dxf.get("const_width", 0.0)
        if const_w > width:
            width = const_w
        return {
            "type": "lwpolyline",
            "layer": layer_name,
            "color": color,
            "points": points,
            "width": round(width, 4),
            "closed": entity.closed,
        }

    if dxf_type == "ARC":
        return {
            "type": "arc",
            "layer": layer_name,
            "color": color,
            "center": [round(entity.dxf.center.x, 4), round(entity.dxf.center.y, 4)],
            "radius": round(entity.dxf.radius, 4),
            "startAngle": round(entity.dxf.start_angle, 4),
            "endAngle": round(entity.dxf.end_angle, 4),
        }

    if dxf_type == "CIRCLE":
        return {
            "type": "circle",
            "layer": layer_name,
            "color": color,
            "center": [round(entity.dxf.center.x, 4), round(entity.dxf.center.y, 4)],
            "radius": round(entity.dxf.radius, 4),
        }

    if dxf_type == "TEXT":
        insert = entity.dxf.get("insert", (0, 0, 0))
        return {
            "type": "text",
            "layer": layer_name,
            "color": color,
            "text": entity.dxf.get("text", ""),
            "position": [round(insert[0], 4), round(insert[1], 4)],
            "height": round(entity.dxf.get("height", 0.25), 4),
            "rotation": round(entity.dxf.get("rotation", 0.0), 4),
        }

    if dxf_type == "MTEXT":
        insert = entity.dxf.get("insert", (0, 0, 0))
        return {
            "type": "text",
            "layer": layer_name,
            "color": color,
            "text": entity.text or "",
            "position": [round(insert[0], 4), round(insert[1], 4)],
            "height": round(entity.dxf.get("char_height", 0.25), 4),
            "rotation": round(entity.dxf.get("rotation", 0.0), 4),
        }

    if dxf_type == "INSERT":
        insert = entity.dxf.get("insert", (0, 0, 0))
        return {
            "type": "insert",
            "layer": layer_name,
            "color": color,
            "blockName": entity.dxf.get("name", ""),
            "position": [round(insert[0], 4), round(insert[1], 4)],
            "rotation": round(entity.dxf.get("rotation", 0.0), 4),
            "xscale": round(entity.dxf.get("xscale", 1.0), 4),
            "yscale": round(entity.dxf.get("yscale", 1.0), 4),
        }

    if dxf_type == "HATCH":
        paths = []
        try:
            for path in entity.paths:
                if hasattr(path, "vertices"):
                    verts = [[round(v[0], 4), round(v[1], 4)] for v in path.vertices]
                    if verts:
                        paths.append(verts)
        except Exception:
            pass
        if not paths:
            return None
        return {
            "type": "hatch",
            "layer": layer_name,
            "color": color,
            "paths": paths,
        }

    if dxf_type == "DIMENSION":
        try:
            points = []
            text_pos = None
            text_val = ""
            if hasattr(entity, "dxf"):
                defpoint = entity.dxf.get("defpoint", None)
                defpoint2 = entity.dxf.get("defpoint2", None)
                defpoint3 = entity.dxf.get("defpoint3", None)
                text_pos_raw = entity.dxf.get("text_midpoint", None)
                text_val = entity.dxf.get("text", "") or ""
                if defpoint2:
                    points.append([round(defpoint2[0], 4), round(defpoint2[1], 4)])
                if defpoint3:
                    points.append([round(defpoint3[0], 4), round(defpoint3[1], 4)])
                if text_pos_raw:
                    text_pos = [round(text_pos_raw[0], 4), round(text_pos_raw[1], 4)]
                if defpoint and not text_pos:
                    text_pos = [round(defpoint[0], 4), round(defpoint[1], 4)]
            return {
                "type": "dimension",
                "layer": layer_name,
                "color": color,
                "points": points,
                "textPosition": text_pos,
                "text": text_val,
            }
        except Exception:
            return None

    return None


_ACI_COLORS = {
    0: "#000000", 1: "#FF0000", 2: "#FFFF00", 3: "#00FF00",
    4: "#00FFFF", 5: "#0000FF", 6: "#FF00FF", 7: "#000000",
    8: "#808080", 9: "#C0C0C0",
}


def _aci_to_hex(color_index: int) -> str:
    if color_index in _ACI_COLORS:
        return _ACI_COLORS[color_index]
    if 0 <= color_index <= 255:
        return "#000000"
    return "#000000"


def _resolve_entity_color(entity) -> str:
    color = entity.dxf.get("color", 256)
    if color == 256:
        return "#bylayer"
    if color == 0:
        return "#byblock"
    return _aci_to_hex(color)


def _update_extents(entry, min_x, min_y, max_x, max_y):
    pass


def _entity_extents(entry: dict[str, Any]) -> tuple[float, float, float, float] | None:
    t = entry["type"]
    if t == "line":
        xs = [entry["start"][0], entry["end"][0]]
        ys = [entry["start"][1], entry["end"][1]]
        return min(xs), min(ys), max(xs), max(ys)
    if t == "lwpolyline" and entry["points"]:
        xs = [p[0] for p in entry["points"]]
        ys = [p[1] for p in entry["points"]]
        return min(xs), min(ys), max(xs), max(ys)
    if t == "arc" or t == "circle":
        cx, cy = entry["center"]
        r = entry["radius"]
        return cx - r, cy - r, cx + r, cy + r
    if t == "text":
        px, py = entry["position"]
        h = entry.get("height", 0.25)
        return px, py, px + h * 5, py + h
    if t == "hatch" and entry["paths"]:
        xs = [p[0] for path in entry["paths"] for p in path]
        ys = [p[1] for path in entry["paths"] for p in path]
        if xs:
            return min(xs), min(ys), max(xs), max(ys)
    return None
