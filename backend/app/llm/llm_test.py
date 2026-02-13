import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SAMPLE_USER_PROMPT = """Generate a 2D floor plan layout with a total footprint of 20 units wide by 15 units high.

The layout is divided into two vertical sections:

1. Left Section (Public Zone) - x: 0 to 12:
- Living Room: Large area at the bottom. Dimensions: 12 wide x 9 high.
- Kitchen: Located directly above the Living Room. Dimensions: 12 wide x 6 high.

2. Right Section (Private Zone) - x: 12 to 20:
- Master Bedroom: Located at the top-right corner. Dimensions: 8 wide x 6 high.
- Bathroom: Located in the middle, directly below the Master Bedroom. Dimensions: 8 wide x 4 high.
- Guest Bedroom: Located at the bottom-right corner. Dimensions: 8 wide x 5 high.

3. Openings (Doors & Windows):
- Main Entrance: In the Living Room, on the bottom wall (centered).
- Internal Doors:
  - Opening between Living Room and Kitchen.
  - Door connecting Living Room to Guest Bedroom.
  - Door connecting Living Room to Bathroom.
  - Door connecting Kitchen to Master Bedroom.
- Windows:
  - Kitchen: Top wall.
  - Living Room: Left wall and Bottom wall.
  - Master Bedroom: Right wall.
  - Guest Bedroom: Right wall.

Ensure all rooms fit perfectly within the 20x15 boundary."""


def _read_user_prompt(args: argparse.Namespace) -> str:
    if args.sample:
        return SAMPLE_USER_PROMPT

    if args.prompt is not None:
        return args.prompt.strip()

    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8").strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    return SAMPLE_USER_PROMPT


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--sample", action="store_true")
    source.add_argument("-p", "--prompt", type=str)
    source.add_argument("-f", "--file", type=str)
    args = parser.parse_args()

    user_prompt = _read_user_prompt(args)
    try:
        from app.llm.compiler import prompt_to_json

        result = prompt_to_json(user_prompt)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
