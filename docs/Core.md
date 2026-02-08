Core Status Summary (Simple English)

Where We Are Now
- API /generate-dxf works with a structured DesignIntent JSON.
- Rooms can be fully deterministic by providing origin for each room.
- Walls are single-line segments; door/window gaps are cut from walls.
- Doors support hinge and swing; swing can be "in" or "out".
- Windows are rendered as openings on wall segments.
- Boundary walls are also cut where openings touch the outer frame.
- Input validation is stricter so bad JSON returns 400 errors, not 500.

What Is Still Missing
- Automatic layout rules that make good floor plans without fixed origins.
- More stable “defaults” when the JSON is incomplete or ambiguous.
- A formal JSON schema and test suite for all edge cases.
- Better planning logic for corridors, stairs, and adjacency goals.
- Packaging and deployment checklist for production.

How To Add AI/LLMs (Simple Pipeline)
1. User prompt -> LLM outputs DesignIntent JSON only.
2. Validate JSON strictly (types, required fields, ranges).
3. Normalize JSON (fill defaults like door width, hinge, swing).
4. If origins are missing, run deterministic planner with clear rules.
5. Generate DXF with the existing pipeline.
6. If validation fails, return a clear error message to the user.

Practical Suggestions
- Keep a fixed JSON schema and force the LLM to follow it.
- Use a “planner fallback” only when origins are missing.
- For openings, always require: room_name + wall + (offset or cut_start/cut_end).
- Default door swing to "in" if not provided.
- Add a small library of layout templates the LLM can choose from.
