#IMPORTANT NOTE: Currently giving false positives, so use this as a starting point only for manual review.
#                In particular, it isn't aware of save/load game related attributes that are not in initial_state.json but are still relevant.


import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def _extract_loader_keys(models_text: str) -> dict[str, set[str]]:
    def function_block(function_name: str) -> str:
        pattern = re.compile(
            rf"^\s*def\s+{re.escape(function_name)}\b[\s\S]*?(?=^\s*def\s+|^class\s+|\Z)",
            re.MULTILINE,
        )
        match = pattern.search(models_text)
        return match.group(0) if match else ""

    get_key_re = re.compile(r"(\w+)\.get\(\s*(['\"])([^'\"]+)\2")
    pop_key_re = re.compile(r"(\w+)\.pop\(\s*(['\"])([^'\"]+)\2")

    def keys_for_var(block: str, variable_name: str) -> set[str]:
        out = set()
        for found_var, _quote, found_key in get_key_re.findall(block):
            if found_var == variable_name:
                out.add(found_key)
        for found_var, _quote, found_key in pop_key_re.findall(block):
            if found_var == variable_name:
                out.add(found_key)
        return out

    item_block = function_block("_construct_item_from_spec")
    boxes_block = function_block("_construct_boxes")
    rooms_block = function_block("_construct_rooms")
    setup_block = function_block("setup_world")
    load_block = function_block("load_world")

    return {
        "item": keys_for_var(item_block, "item_spec"),
        "box": keys_for_var(boxes_block, "entry") | keys_for_var(rooms_block, "box_data"),
        "room": keys_for_var(rooms_block, "entry"),
        "world": keys_for_var(setup_block, "data") | keys_for_var(load_block, "data"),
        "player": keys_for_var(load_block, "player_data"),
    }


def _collect_json_keys(payload: dict) -> dict[str, set[str]]:
    seen: dict[str, set[str]] = {
        "world": set(),
        "room": set(),
        "box": set(),
        "item": set(),
        "player": set(),
    }

    if not isinstance(payload, dict):
        return seen

    seen["world"].update(payload.keys())

    player = payload.get("player")
    if isinstance(player, dict):
        seen["player"].update(player.keys())

    def _collect_items(items):
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict):
                seen["item"].update(item.keys())

    def _collect_box(box):
        if not isinstance(box, dict):
            return
        seen["box"].update(box.keys())
        _collect_items(box.get("items", []))

    for box in payload.get("boxes", []) if isinstance(payload.get("boxes"), list) else []:
        _collect_box(box)

    rooms = payload.get("rooms")
    if isinstance(rooms, list):
        for room in rooms:
            if not isinstance(room, dict):
                continue
            seen["room"].update(room.keys())
            _collect_items(room.get("items", []))
            for room_box in room.get("boxes", []) if isinstance(room.get("boxes"), list) else []:
                _collect_box(room_box)

    if isinstance(player, dict):
        _collect_items(player.get("inventory", []))

    return seen


def _collect_attr_defs(models_text: str) -> dict[str, set[str]]:
    class_targets = {"Item", "Room", "Player", "Game"}
    class_blocks = {}
    current = None
    lines = models_text.splitlines()

    for line in lines:
        m = re.match(r'^\s*class\s+(\w+)\b', line)
        if m:
            current = m.group(1)
            if current in class_targets:
                class_blocks[current] = []
            continue
        if current in class_targets:
            if re.match(r'^\S', line):
                current = None
            else:
                class_blocks[current].append(line)

    attr_defs: dict[str, set[str]] = defaultdict(set)
    attr_re = re.compile(r'\bself\.(\w+)\s*=')
    for cls, block_lines in class_blocks.items():
        block = "\n".join(block_lines)
        for attr_name in attr_re.findall(block):
            attr_defs[cls].add(attr_name)
    return attr_defs


def main() -> int:

    print("IMPORTANT NOTE: This script is currently giving false positives, so use this as a starting point only for manual review.")
    print("                In particular, it isn't aware of save/load game related attributes that are not in initial_state.json but are still relevant.")
    parser = argparse.ArgumentParser(
        description="Find likely obsolete JSON keys and model attributes."
    )
    parser.add_argument(
        "json_files",
        nargs="*",
        help="JSON files to inspect (defaults to data/initial_state.json if present).",
    )
    args = parser.parse_args()

    root = Path(".").resolve()
    src = root / "src" / "kingdom"
    models = src / "models.py"

    if not models.exists():
        print(f"ERROR: models.py not found at {models}")
        return 1

    models_text = models.read_text(encoding="utf-8", errors="ignore")

    json_paths: list[Path] = []
    if args.json_files:
        json_paths = [Path(p).resolve() for p in args.json_files]
    else:
        default_candidates = [
            root / "data" / "initial_state.json",
            root / "data" / "working_state.json",
            root / "data" / "demo_initial_state.json",
        ]
        json_paths = [path for path in default_candidates if path.exists()]

    if not json_paths:
        print("No JSON file paths provided and default data/initial_state.json not found.")
        print("Usage: python scripts/find_obsolete_attributes.py data/initial_state.json")
        return 1

    expected = _extract_loader_keys(models_text)
    seen: dict[str, set[str]] = {
        "world": set(),
        "room": set(),
        "box": set(),
        "item": set(),
        "player": set(),
    }

    for path in json_paths:
        if not path.exists():
            print(f"WARN: Skipping missing JSON file: {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"WARN: Skipping unreadable JSON file {path}: {exc}")
            continue

        collected = _collect_json_keys(payload)
        for scope, keys in collected.items():
            seen[scope].update(keys)

    print("=== JSON Files Scanned ===")
    for path in json_paths:
        print(f"- {path}")

    print("\n=== Keys requested by loader code but not seen in scanned JSON ===")
    for scope in ["world", "player", "room", "box", "item"]:
        missing = sorted(expected[scope] - seen[scope])
        print(f"{scope}: {missing}")

    print("\n=== Keys present in scanned JSON but not requested in loader code ===")
    for scope in ["world", "player", "room", "box", "item"]:
        extra = sorted(seen[scope] - expected[scope])
        print(f"{scope}: {extra}")

    # Keep previous capability: attributes defined in models but not referenced outside models.
    outside_text = []
    for p in src.rglob("*.py"):
        if p.resolve() == models.resolve():
            continue
        outside_text.append(p.read_text(encoding="utf-8", errors="ignore"))
    outside = "\n".join(outside_text)

    attr_defs = _collect_attr_defs(models_text)
    never_outside: dict[str, list[str]] = defaultdict(list)
    for cls, attrs in attr_defs.items():
        for attr_name in sorted(attrs):
            if re.search(rf'\.{re.escape(attr_name)}\b', outside) is None:
                never_outside[cls].append(attr_name)

    print("\n=== Attributes defined in models.py but never referenced outside models.py ===")
    for cls in sorted({"Item", "Room", "Player", "Game"}):
        print(f"{cls}: {never_outside.get(cls, [])}")

    print("IMPORTANT NOTE: This script is currently giving false positives, so use this as a starting point only for manual review.")
    print("                In particular, it isn't aware of save/load game related attributes that are not in initial_state.json but are still relevant.")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
