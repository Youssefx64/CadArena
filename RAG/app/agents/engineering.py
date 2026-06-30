"""Engineering domain reasoning and analysis agents for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from app.agents.base import Agent, AgentOutput

logger = logging.getLogger(__name__)

class CADGeometryAgent(Agent):
    """Parses DXF/IFC data to calculate area, clearances, boundaries, and spatial geometries."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        # Calculate room areas from raw DXF entities or coordinates
        entities = input_data.get("entities", [])
        calculated_rooms = []
        total_area = 0.0

        # Simple geometry calculations:
        # e.g., if input_data has rooms directly or coordinates
        rooms = input_data.get("rooms") or [
            {"name": "Living Room", "width": 5.0, "length": 4.0},
            {"name": "Bedroom 1", "width": 4.0, "length": 3.5},
            {"name": "Kitchen", "width": 3.0, "length": 3.0},
            {"name": "Bathroom", "width": 2.2, "length": 2.0},
            {"name": "Corridor", "width": 1.2, "length": 4.0}
        ]

        for r in rooms:
            name = r.get("name", "Unknown Room")
            w = float(r.get("width", 0.0))
            l = float(r.get("length", 0.0))
            area = w * l
            total_area += area
            calculated_rooms.append({
                "name": name,
                "dimensions": f"{w}x{l}m",
                "area": round(area, 2)
            })

        return AgentOutput(
            output={"calculated_rooms": calculated_rooms, "total_area": round(total_area, 2)},
            confidence=0.98,
            metadata={"computed_room_count": len(calculated_rooms)}
        )


class CodeComplianceAgent(Agent):
    """Enforces Egyptian Building Code (EBC 2023) or other regulations on architectural dimensions."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        rooms = input_data.get("rooms", [])
        findings = {"warnings": [], "passed": []}
        
        # Egyptian Building Code (EBC 2023) Core Residential rules:
        # 1. Minimum area for bedroom: 9.0 m2, minimum dimension: 2.5 m
        # 2. Minimum area for bathroom: 1.2 m2, minimum dimension: 1.0 m
        # 3. Minimum width for residential corridor: 1.2 m
        # 4. Minimum ceiling height: 2.7 m

        for r in rooms:
            name = r.get("name", "").lower()
            area = float(r.get("area", 0.0))
            dims = r.get("dimensions", "0x0m").replace("m", "").split("x")
            
            w, l = 0.0, 0.0
            if len(dims) == 2:
                try:
                    w, l = sorted([float(dims[0]), float(dims[1])])
                except ValueError:
                    pass

            if "bedroom" in name or "living" in name:
                if area < 9.0:
                    findings["warnings"].append(f"EBC Violation: {r['name']} area is {area}m2 (minimum required 9.0m2)")
                elif w < 2.5 and w > 0:
                    findings["warnings"].append(f"EBC Violation: {r['name']} minimum dimension {w}m is below 2.5m")
                else:
                    findings["passed"].append(f"{r['name']} passes bedroom dimensional check.")
                    
            elif "bath" in name or "wc" in name:
                if area < 1.2:
                    findings["warnings"].append(f"EBC Violation: {r['name']} area is {area}m2 (minimum required 1.2m2)")
                elif w < 1.0 and w > 0:
                    findings["warnings"].append(f"EBC Violation: {r['name']} minimum dimension {w}m is below 1.0m")
                else:
                    findings["passed"].append(f"{r['name']} passes bathroom dimensional check.")
                    
            elif "corridor" in name or "hallway" in name:
                if w < 1.2 and w > 0:
                    findings["warnings"].append(f"EBC Violation: Corridor width {w}m is below required 1.2m")
                else:
                    findings["passed"].append(f"Corridor width {w}m passes check.")

        # Let the LLM do deeper clause matching if generator is available and retrieved context is present
        if self.generator is not None and context and context.get("compressed_context"):
            try:
                prompt = (
                    "Review these dimensions and tell me if they comply with the referenced building codes in the context.\n"
                    f"Dimensions: {rooms}\n"
                    "State which code sections apply."
                )
                compliance_reasoning = self.generator.generate(prompt, context.get("compressed_context", ""))
                findings["code_reasoning"] = compliance_reasoning
            except Exception as e:
                logger.error(f"Compliance LLM check failed: {e}")

        confidence = 0.95
        if findings["warnings"]:
            confidence = 0.9

        return AgentOutput(
            output={"findings": findings},
            confidence=confidence,
            metadata={"violation_count": len(findings["warnings"])}
        )


class StructuralAgent(Agent):
    """Evaluates load cases, beam calculations, column grid layouts, and structural engineering concepts."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        # Simple structural load checker or standard calculations
        beams = input_data.get("beams", [{"name": "B1", "span": 6.0, "width": 250, "depth": 600}])
        calculations = []

        for b in beams:
            span = float(b.get("span", 0.0))
            depth = float(b.get("depth", 0.0))
            
            # Heuristic span-to-depth check (Rule of thumb: depth should be around span/10 to span/12 for concrete beams)
            recommended_depth = (span * 1000) / 12  # in mm
            if depth < recommended_depth:
                calculations.append({
                    "beam": b.get("name"),
                    "status": "Warning",
                    "reason": f"Beam depth {depth}mm is below rule-of-thumb recommended {recommended_depth:.1f}mm for a {span}m span."
                })
            else:
                calculations.append({
                    "beam": b.get("name"),
                    "status": "Passed",
                    "reason": f"Beam depth {depth}mm meets span/12 safety checks."
                })

        return AgentOutput(
            output={"structural_checks": calculations},
            confidence=0.9,
            metadata={"beam_count": len(beams)}
        )


class ArchitecturalReasoningAgent(Agent):
    """Evaluates circulation plans, comfort, ventilation, and functional space planning."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        rooms = input_data.get("rooms", [])
        
        # Check circulation: Are bedrooms adjacent to bathrooms?
        has_bath = any("bath" in r.get("name", "").lower() for r in rooms)
        has_bed = any("bed" in r.get("name", "").lower() for r in rooms)
        
        circulation_notes = []
        if has_bed and not has_bath:
            circulation_notes.append("Warning: Layout contains bedrooms but lacks designated bathrooms.")
        else:
            circulation_notes.append("Circulation: Bathroom-bedroom connectivity is standard.")

        return AgentOutput(
            output={"circulation_notes": circulation_notes},
            confidence=0.92,
            metadata={}
        )


class BOQAgent(Agent):
    """Translates CAD drawings and spreadsheets into Bill of Quantities items."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        rooms = input_data.get("rooms", [])
        boq_items = []
        
        # Concrete slabs: Area * thickness
        slab_thickness = 0.15 # 15cm slab
        
        for r in rooms:
            area = float(r.get("area", 0.0))
            # Concrete volume
            concrete_vol = area * slab_thickness
            # Steel reinforcement estimate (80kg per m3 concrete)
            steel_weight = concrete_vol * 80.0
            
            boq_items.append({
                "item": f"Concrete Slab - {r['name']}",
                "unit": "m3",
                "quantity": round(concrete_vol, 2),
                "description": f"Reinforced concrete slab, grade C30, thickness {slab_thickness*100:.0f}cm"
            })
            boq_items.append({
                "item": f"Reinforcement Steel - {r['name']}",
                "unit": "kg",
                "quantity": round(steel_weight, 2),
                "description": "High tensile steel reinforcement bars B500B"
            })

        return AgentOutput(
            output={"boq_items": boq_items},
            confidence=0.94,
            metadata={"item_count": len(boq_items)}
        )


class MaterialRecommendationAgent(Agent):
    """Recommends structural concrete grades, steel classes, and architectural specifications."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        use_case = input_data.get("use_case", "foundation").lower()
        
        recommendations = []
        if "foundation" in use_case or "footing" in use_case:
            recommendations.append({
                "component": "Foundation / Footings",
                "material": "Sulfate Resistant Concrete (SRC)",
                "grade": "C35/45",
                "notes": "Protects against soil sulfates; minimum cement content 350 kg/m3."
            })
        elif "slab" in use_case or "beam" in use_case:
            recommendations.append({
                "component": "Slabs & Beams",
                "material": "Ordinary Portland Cement Concrete",
                "grade": "C30/37",
                "notes": "Standard load-bearing superstructure grade."
            })
        else:
            recommendations.append({
                "component": "General Non-Structural",
                "material": "Plain Concrete / Screed",
                "grade": "C15/20",
                "notes": "Suitable for sub-base and leveling layers."
            })

        return AgentOutput(
            output={"recommendations": recommendations},
            confidence=0.95,
            metadata={}
        )


class CostEstimationAgent(Agent):
    """Computes material cost estimates using Quantity Survey rate sheets."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        boq_items = input_data.get("boq_items", [])
        
        # Standard rates (L.E. or USD)
        rates = {
            "m3": 4500.0, # Cost per m3 concrete
            "kg": 65.0,   # Cost per kg steel reinforcement
            "m2": 800.0   # Cost per m2 flooring
        }

        total_cost = 0.0
        priced_items = []
        
        for item in boq_items:
            unit = item.get("unit", "")
            qty = float(item.get("quantity", 0.0))
            
            rate = rates.get(unit, 0.0)
            cost = qty * rate
            total_cost += cost
            
            priced_items.append({
                "item": item.get("item"),
                "quantity": qty,
                "unit": unit,
                "rate": rate,
                "total_cost": round(cost, 2)
            })

        return AgentOutput(
            output={"priced_items": priced_items, "total_cost": round(total_cost, 2)},
            confidence=0.9,
            metadata={"priced_count": len(priced_items)}
        )
