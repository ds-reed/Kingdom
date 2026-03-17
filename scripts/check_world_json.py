#!/usr/bin/env python3
"""Validate Kingdom world-state JSON files for consistency.

Usage:
    python scripts/check_world_json.py data/initial_state.json
    python scripts/check_world_json.py data/initial_state.json data/working_state.json
    python scripts/check_world_json.py --strict data/my_world.json

Checks performed:
- Valid JSON and expected top-level structure
- Room naming quality (missing/duplicate names)
- Connection integrity (destination rooms exist)
- hidden_exits integrity (directions reference declared room go_exits)
- Optional score field sanity (integer-compatible, non-negative)
- Loadability with current Game model implementation
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.append(str(ROOT / "src"))

from kingdom.model.noun_model import World  # noqa: E402
from kingdom.model.game_model import setup_world  # noqa: E402


@dataclass
class ValidationResult:
    file_path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_nonempty_description(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _load_json(path: Path, result: ValidationResult) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.errors.append("File does not exist.")
        return None
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return None

    if not isinstance(payload, dict):
        result.errors.append("Top-level JSON must be an object with keys like 'boxes' and 'rooms'.")
        return None

    return payload


def _extract_destination(entry: Any) -> tuple[str | None, str | None]:
    if isinstance(entry, str):
        return None, entry

    if isinstance(entry, dict):
        direction = entry.get("direction")
        destination = entry.get("room")
        if isinstance(direction, str):
            direction = direction.strip() or None
        else:
            direction = None
        if isinstance(destination, str):
            destination = destination.strip() or None
        else:
            destination = None
        return direction, destination

    return None, None


def _validate_rooms(payload: dict[str, Any], result: ValidationResult) -> None:
    rooms = payload.get("rooms", [])

    if not isinstance(rooms, list):
        result.errors.append("'rooms' must be a list.")
        return

    room_names: list[str] = []
    room_name_set: set[str] = set()

    for index, room in enumerate(rooms):
        room_label = f"rooms[{index}]"

        if not isinstance(room, dict):
            result.errors.append(f"{room_label} must be an object.")
            continue

        name = room.get("name")
        if not _is_nonempty_description(name):
            result.errors.append(f"{room_label}.name must be a non-empty string.")
            continue

        normalized_name = str(name).strip()
        room_names.append(normalized_name)

        if normalized_name in room_name_set:
            result.errors.append(f"Duplicate room name: '{normalized_name}'.")
        room_name_set.add(normalized_name)

    for index, room in enumerate(rooms):
        room_label = f"rooms[{index}]"
        if not isinstance(room, dict):
            continue

        room_name = room.get("name") if _is_nonempty_description(room.get("name")) else room_label

        go_exits = room.get("go_exits", {})
        connection_dirs: set[str] = set()

        if isinstance(go_exits, dict):
            for direction, destination in go_exits.items():
                if not _is_nonempty_description(direction):
                    result.errors.append(f"{room_name}: connection direction keys must be non-empty strings.")
                    continue

                direction_name = str(direction).strip()
                connection_dirs.add(direction_name)

                if isinstance(destination, dict):
                    _, destination_name = _extract_destination(destination)
                else:
                    destination_name = destination.strip() if isinstance(destination, str) else None

                if not destination_name:
                    result.errors.append(
                        f"{room_name}: connection '{direction_name}' must target a non-empty room name."
                    )
                elif destination_name not in room_name_set:
                    result.errors.append(
                        f"{room_name}: connection '{direction_name}' points to missing room '{destination_name}'."
                    )

        elif isinstance(go_exits, list):
            for item_index, entry in enumerate(go_exits):
                direction_name, destination_name = _extract_destination(entry)

                if isinstance(entry, dict):
                    if not direction_name:
                        result.errors.append(
                            f"{room_name}: go_exits[{item_index}].direction must be a non-empty string."
                        )
                    else:
                        connection_dirs.add(direction_name)

                    if not destination_name:
                        result.errors.append(
                            f"{room_name}: go_exits[{item_index}].room must be a non-empty string."
                        )
                    elif destination_name not in room_name_set:
                        result.errors.append(
                            f"{room_name}: go_exits[{item_index}] points to missing room '{destination_name}'."
                        )

                elif isinstance(entry, str):
                    if entry not in room_name_set:
                        result.errors.append(
                            f"{room_name}: go_exits[{item_index}] points to missing room '{entry}'."
                        )
                else:
                    result.errors.append(
                        f"{room_name}: go_exits[{item_index}] must be an object or room-name string."
                    )
        else:
            result.errors.append(f"{room_name}: 'go_exits' must be an object or list.")

        hidden_exits = room.get("hidden_exits", [])
        if hidden_exits is None:
            hidden_exits = []

        if not isinstance(hidden_exits, list):
            result.errors.append(f"{room_name}: 'hidden_exits' must be a list when present.")
            continue

        for item_index, direction in enumerate(hidden_exits):
            if not _is_nonempty_description(direction):
                result.errors.append(
                    f"{room_name}: hidden_exits[{item_index}] must be a non-empty direction string."
                )
                continue

            direction_name = str(direction).strip()
            if connection_dirs and direction_name not in connection_dirs:
                result.errors.append(
                    f"{room_name}: hidden_exits includes '{direction_name}' but no such connection exists."
                )


def _validate_top_level(payload: dict[str, Any], result: ValidationResult) -> None:
    boxes = payload.get("boxes", [])
    if not isinstance(boxes, list):
        result.errors.append("'boxes' must be a list.")

    if "score" not in payload:
        result.warnings.append("Top-level 'score' is missing (recommended: include score: 0).")
    else:
        score = payload.get("score")
        try:
            normalized = int(score)
            if normalized < 0:
                result.warnings.append("Top-level 'score' is negative; score is typically non-negative.")
        except (TypeError, ValueError):
            result.errors.append("Top-level 'score' must be integer-compatible when present.")


def _validate_loadability(path: Path, result: ValidationResult) -> None:
    game = World.get_instance()
    try:
        setup_world(game, path)
    except Exception as exc:
        result.errors.append(f"Current model loader rejected this file: {type(exc).__name__}: {exc}")


def validate_world_file(path: Path) -> ValidationResult:
    result = ValidationResult(file_path=path)
    payload = _load_json(path, result)
    if payload is None:
        return result

    _validate_top_level(payload, result)
    _validate_rooms(payload, result)
    _validate_loadability(path, result)
    return result


def _print_result(result: ValidationResult) -> None:
    print(f"\n== {result.file_path} ==")

    if result.ok and not result.warnings:
        print("OK: No issues found.")
        return

    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for message in result.errors:
            print(f"  - {message}")

    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for message in result.warnings:
            print(f"  - {message}")

    if result.ok:
        print("PASS WITH WARNINGS")
    else:
        print("FAILED")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Kingdom world JSON files.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (non-zero exit code).",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more world JSON file paths to validate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    any_errors = False
    any_warnings = False
    for raw_path in args.files:
        path = Path(raw_path)
        if not path.is_absolute():
            path = (ROOT / path).resolve()

        result = validate_world_file(path)
        _print_result(result)
        if not result.ok:
            any_errors = True
        if result.warnings:
            any_warnings = True

    if any_errors:
        return 1

    if args.strict and any_warnings:
        print("\nStrict mode enabled: warnings are treated as failures.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
