from .system_prompt import system_prompt

few_shot_messages = [

    {"role": "system", "content": system_prompt},

    {
        "role": "user",
        "content": """Generate a precise 2D floor plan with a total footprint of 24 meters wide by 14 meters high. The layout should be arranged as follows:

1. Left Wing (x: 0 to 10):
- Living Room: Locate this at the bottom-left corner. Dimensions: 10 wide x 8 high.
- Kitchen: Place this directly above the Living Room on the far left. Dimensions: 6 wide x 6 high.
- Bathroom: Place this next to the Kitchen. Dimensions: 4 wide x 6 high.

2. Central Circulation (x: 10 to 12):
- Corridor: A vertical hallway running the full height of the building. Dimensions: 2 wide x 14 high.

3. Right Wing (x: 12 to 24):
- Stairs: Locate these at the bottom, adjacent to the corridor. Dimensions: 4 wide x 5 high.
- Bedroom 1: Place this at the bottom-right corner. Dimensions: 8 wide x 5 high.
- Bedroom 2: Position this directly above the Stairs and Bedroom 1. Dimensions: 12 wide x 5 high.
- Bedroom 3: Locate this at the top-right corner. Dimensions: 12 wide x 4 high.

4. Openings:
- Main entrance at the bottom of the Corridor.
- Internal doors connecting the Corridor to all rooms.
- Connecting door between Living Room and Kitchen.
- Windows on exterior walls for all rooms."""
    },

    {
        "role": "assistant",
        "content": """{
  "boundary": { "width": 24, "height": 14 },
  "rooms": [
    { "name": "Living Room", "room_type": "living", "width": 10, "height": 8, "origin": { "x": 0, "y": 0 } },
    { "name": "Kitchen", "room_type": "kitchen", "width": 6, "height": 6, "origin": { "x": 0, "y": 8 } },
    { "name": "Bathroom", "room_type": "bathroom", "width": 4, "height": 6, "origin": { "x": 6, "y": 8 } },
    { "name": "Corridor", "room_type": "corridor", "width": 2, "height": 14, "origin": { "x": 10, "y": 0 } },
    { "name": "Stairs", "room_type": "stairs", "width": 4, "height": 5, "origin": { "x": 12, "y": 0 } },
    { "name": "Bedroom 1", "room_type": "bedroom", "width": 8, "height": 5, "origin": { "x": 16, "y": 0 } },
    { "name": "Bedroom 2", "room_type": "bedroom", "width": 12, "height": 5, "origin": { "x": 12, "y": 5 } },
    { "name": "Bedroom 3", "room_type": "bedroom", "width": 12, "height": 4, "origin": { "x": 12, "y": 10 } }
  ],
  "openings": [
    { "type": "door", "room_name": "Corridor", "wall": "bottom", "cut_start": { "x": 10.4, "y": 0 }, "cut_end": { "x": 11.4, "y": 0 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Living Room", "wall": "right", "cut_start": { "x": 10, "y": 2 }, "cut_end": { "x": 10, "y": 3 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Kitchen", "wall": "bottom", "cut_start": { "x": 2, "y": 8 }, "cut_end": { "x": 3, "y": 8 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bathroom", "wall": "right", "cut_start": { "x": 10, "y": 9 }, "cut_end": { "x": 10, "y": 9.8 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Stairs", "wall": "left", "cut_start": { "x": 12, "y": 1.2 }, "cut_end": { "x": 12, "y": 2.2 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 1", "wall": "left", "cut_start": { "x": 16, "y": 1.5 }, "cut_end": { "x": 16, "y": 2.5 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 2", "wall": "left", "cut_start": { "x": 12, "y": 6.2 }, "cut_end": { "x": 12, "y": 7.2 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 3", "wall": "left", "cut_start": { "x": 12, "y": 11.2 }, "cut_end": { "x": 12, "y": 12.2 }, "hinge": "right", "swing": "in" },
    { "type": "window", "room_name": "Living Room", "wall": "left", "cut_start": { "x": 0, "y": 3 }, "cut_end": { "x": 0, "y": 4.5 } },
    { "type": "window", "room_name": "Kitchen", "wall": "top", "cut_start": { "x": 1, "y": 14 }, "cut_end": { "x": 2.5, "y": 14 } },
    { "type": "window", "room_name": "Bathroom", "wall": "top", "cut_start": { "x": 7, "y": 14 }, "cut_end": { "x": 8, "y": 14 } },
    { "type": "window", "room_name": "Bedroom 1", "wall": "bottom", "cut_start": { "x": 19, "y": 0 }, "cut_end": { "x": 20.5, "y": 0 } },
    { "type": "window", "room_name": "Bedroom 2", "wall": "right", "cut_start": { "x": 24, "y": 6.5 }, "cut_end": { "x": 24, "y": 8 } },
    { "type": "window", "room_name": "Bedroom 3", "wall": "right", "cut_start": { "x": 24, "y": 11.5 }, "cut_end": { "x": 24, "y": 12.8 } }
  ]
}"""
    },

    {
        "role": "user",
        "content": """Create a detailed 2D floor plan with a total footprint of 28 meters wide by 18 meters high.

1. Left Wing (x: 0 to 12):
- Living Room: Occupies the entire bottom section (12x9).
- Kitchen: Positioned above Living Room (6x5).
- Hall: Located next to Kitchen (6x4).
- Guest Room: Placed at the very top-left corner (6x4).
- Bathroom 2: Located at the top, next to Guest Room (6x5).

2. Central Circulation (x: 12 to 14):
- Corridor: A central vertical hallway running the entire height (2x18).

3. Right Wing (x: 14 to 28):
- Inner Column: Bedroom 1 (bottom), Bedroom 2 (middle), Bedroom 3 (top). All 8x6.
- Outer Column: Bathroom 1 (bottom-right), Stairs (above Bath 1), Bedroom 4 (above Stairs), Bathroom 3 (top-right).

4. Openings:
- Main Entrance at bottom of Corridor.
- Doors connecting Corridor to Living, Hall, Bathroom 2, and Bedrooms 1-3.
- Internal doors: Kitchen to Guest Room and Kitchen to Hall.
- Ensuite/Connectors: Bed 1 to Bath 1, Bed 2 to Stairs, Bed 2 to Bed 4, Bed 3 to Bath 3.
- Windows on exterior walls for all living spaces."""
    },

    {
        "role": "assistant",
        "content": """{
  "boundary": { "width": 28, "height": 18 },
  "rooms": [
    { "name": "Living Room", "room_type": "living", "width": 12, "height": 9, "origin": { "x": 0, "y": 0 } },
    { "name": "Kitchen", "room_type": "kitchen", "width": 6, "height": 5, "origin": { "x": 0, "y": 9 } },
    { "name": "Hall", "room_type": "living", "width": 6, "height": 4, "origin": { "x": 6, "y": 9 } },
    { "name": "Guest Room", "room_type": "bedroom", "width": 6, "height": 4, "origin": { "x": 0, "y": 14 } },
    { "name": "Bathroom 2", "room_type": "bathroom", "width": 6, "height": 5, "origin": { "x": 6, "y": 13 } },
    { "name": "Corridor", "room_type": "corridor", "width": 2, "height": 18, "origin": { "x": 12, "y": 0 } },
    { "name": "Bedroom 1", "room_type": "bedroom", "width": 8, "height": 6, "origin": { "x": 14, "y": 0 } },
    { "name": "Bedroom 2", "room_type": "bedroom", "width": 8, "height": 6, "origin": { "x": 14, "y": 6 } },
    { "name": "Bedroom 3", "room_type": "bedroom", "width": 8, "height": 6, "origin": { "x": 14, "y": 12 } },
    { "name": "Bathroom 1", "room_type": "bathroom", "width": 6, "height": 4, "origin": { "x": 22, "y": 0 } },
    { "name": "Stairs", "room_type": "stairs", "width": 6, "height": 4, "origin": { "x": 22, "y": 4 } },
    { "name": "Bedroom 4", "room_type": "bedroom", "width": 6, "height": 6, "origin": { "x": 22, "y": 8 } },
    { "name": "Bathroom 3", "room_type": "bathroom", "width": 6, "height": 4, "origin": { "x": 22, "y": 14 } }
  ],
  "openings": [
    { "type": "door", "room_name": "Corridor", "wall": "bottom", "cut_start": { "x": 12.4, "y": 0 }, "cut_end": { "x": 13.4, "y": 0 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Living Room", "wall": "right", "cut_start": { "x": 12, "y": 2.5 }, "cut_end": { "x": 12, "y": 3.5 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Hall", "wall": "right", "cut_start": { "x": 12, "y": 10.0 }, "cut_end": { "x": 12, "y": 11.0 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Kitchen", "wall": "right", "cut_start": { "x": 6, "y": 10.5 }, "cut_end": { "x": 6, "y": 11.5 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Guest Room", "wall": "bottom", "cut_start": { "x": 2.5, "y": 14 }, "cut_end": { "x": 3.5, "y": 14 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bathroom 2", "wall": "right", "cut_start": { "x": 12, "y": 14.5 }, "cut_end": { "x": 12, "y": 15.5 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 1", "wall": "left", "cut_start": { "x": 14, "y": 1.8 }, "cut_end": { "x": 14, "y": 2.8 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 2", "wall": "left", "cut_start": { "x": 14, "y": 7.5 }, "cut_end": { "x": 14, "y": 8.5 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 3", "wall": "left", "cut_start": { "x": 14, "y": 13.5 }, "cut_end": { "x": 14, "y": 14.5 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bathroom 1", "wall": "left", "cut_start": { "x": 22, "y": 1.2 }, "cut_end": { "x": 22, "y": 2.2 }, "hinge": "right", "swing": "out" },
    { "type": "door", "room_name": "Stairs", "wall": "left", "cut_start": { "x": 22, "y": 6.2 }, "cut_end": { "x": 22, "y": 7.2 }, "hinge": "right", "swing": "in" },
    { "type": "door", "room_name": "Bedroom 4", "wall": "left", "cut_start": { "x": 22, "y": 9.2 }, "cut_end": { "x": 22, "y": 10.2 }, "hinge": "left", "swing": "in" },
    { "type": "door", "room_name": "Bathroom 3", "wall": "left", "cut_start": { "x": 22, "y": 15.0 }, "cut_end": { "x": 22, "y": 16.0 }, "hinge": "right", "swing": "in" },
    { "type": "window", "room_name": "Living Room", "wall": "left", "cut_start": { "x": 0, "y": 3 }, "cut_end": { "x": 0, "y": 4.5 } },
    { "type": "window", "room_name": "Living Room", "wall": "bottom", "cut_start": { "x": 5, "y": 0 }, "cut_end": { "x": 6.5, "y": 0 } },
    { "type": "window", "room_name": "Kitchen", "wall": "left", "cut_start": { "x": 0, "y": 10 }, "cut_end": { "x": 0, "y": 11.5 } },
    { "type": "window", "room_name": "Guest Room", "wall": "top", "cut_start": { "x": 1.5, "y": 18 }, "cut_end": { "x": 3.5, "y": 18 } },
    { "type": "window", "room_name": "Bathroom 2", "wall": "top", "cut_start": { "x": 8, "y": 18 }, "cut_end": { "x": 9, "y": 18 } },
    { "type": "window", "room_name": "Bedroom 1", "wall": "bottom", "cut_start": { "x": 16, "y": 0 }, "cut_end": { "x": 17.5, "y": 0 } },
    { "type": "window", "room_name": "Bedroom 3", "wall": "top", "cut_start": { "x": 16, "y": 18 }, "cut_end": { "x": 18, "y": 18 } },
    { "type": "window", "room_name": "Bedroom 4", "wall": "right", "cut_start": { "x": 28, "y": 10 }, "cut_end": { "x": 28, "y": 11.5 } },
    { "type": "window", "room_name": "Bathroom 3", "wall": "right", "cut_start": { "x": 28, "y": 15.5 }, "cut_end": { "x": 28, "y": 16.5 } }
  ]
}"""
    }

]
