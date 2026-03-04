from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import fields
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kingdom.model.noun_model import Container


class SerializableStubItem:
    def __init__(self, name: str, is_gettable: bool = True):
        self.name = name
        self.is_gettable = is_gettable

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "is_gettable": self.is_gettable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SerializableStubItem":
        return cls(
            name=data.get("name", "unnamed"),
            is_gettable=bool(data.get("is_gettable", True)),
        )


def _reset_container_registry() -> None:
    Container.all_containers.clear()
    Container._by_name.clear()


def _build_container_samples() -> list[Container]:
    _reset_container_registry()

    plain = Container(name="Plain Pot")

    openable_closed = Container(
        name="Wooden Chest",
        is_openable=True,
        is_open=False,
        closed_state_description="The chest is shut tight.",
    )

    openable_open = Container(
        name="Glass Case",
        handle="display_case",
        description="A display case with brass trim.",
        capacity=12,
        is_openable=True,
        is_open=True,
        opened_state_description="The display case stands open.",
        open_action_description="You swing the glass door open.",
        close_action_description="You carefully close the glass door.",
    )

    lockable_unlocked = Container(
        name="Iron Safe",
        is_lockable=True,
        is_locked=False,
        unlock_key="safe_key",
    )

    lockable_locked = Container(
        name="Ancient Locker",
        is_lockable=True,
        is_locked=True,
        unlock_key="rusty_key",
        locked_description="The locker is rusted shut.",
        open_exit_direction="down",
        open_exit_destination="catacombs",
    )

    with_contents = Container(
        name="Canvas Bag",
        is_openable=True,
        is_open=True,
    )
    with_contents.contents.append(SerializableStubItem("coin"))
    with_contents.contents.append(SerializableStubItem("wax apple", is_gettable=False))

    return [
        plain,
        openable_closed,
        openable_open,
        lockable_unlocked,
        lockable_locked,
        with_contents,
    ]


def _container_from_payload(payload: dict[str, Any]) -> Container:
    constructor_fields = {f.name for f in fields(Container) if f.init}
    init_kwargs = {k: v for k, v in payload.items() if k in constructor_fields}

    container = Container(**init_kwargs)

    for item_payload in payload.get("items", []):
        container.contents.append(SerializableStubItem.from_dict(item_payload))

    return container


def run_container_roundtrip(output_file: Path | None = None) -> Path:
    original_containers = _build_container_samples()
    serialized = [container.to_dict() for container in original_containers]

    if output_file is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="kingdom_container_test_"))
        output_file = temp_dir / "container_roundtrip.json"
    else:
        output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(serialized, file, indent=2)

    with output_file.open("r", encoding="utf-8") as file:
        loaded_payload = json.load(file)

    _reset_container_registry()
    rebuilt_containers = [_container_from_payload(entry) for entry in loaded_payload]

    original_as_dict = serialized
    rebuilt_as_dict = [container.to_dict() for container in rebuilt_containers]

    assert original_as_dict == rebuilt_as_dict, "Container round-trip mismatch after save/load"

    for data in rebuilt_as_dict:
        assert "name" in data

    return output_file


def test_container_roundtrip_standalone() -> None:
    path = run_container_roundtrip()
    assert path.exists()


def main() -> None:
    output_file = run_container_roundtrip()
    print(f"Container round-trip test passed. Output: {output_file}")


if __name__ == "__main__":
    main()
