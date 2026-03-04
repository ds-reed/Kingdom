from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Optional, List, Dict, ClassVar

from kingdom.model.noun_model import Noun, Item, _derive_noun_name


def serialize_non_default(obj: Any) -> dict:
    """
    Serialize dataclass fields according to persistence rules.
    - Skips runtime fields (init=False)
    - Uses metadata: "always", "if_set", "persist_if_parent", default=non_default
    """
    payload = {}
    for f in fields(obj):
        if f.init is False:
            continue

        value = getattr(obj, f.name)
        persist_rule = f.metadata.get("persist", "non_default")
        parent_field = f.metadata.get("persist_if_parent")

        # Save if parent is True (even if value == default)
        if parent_field:
            parent_value = getattr(obj, parent_field, False)
            if parent_value is True:
                payload[f.name] = value
                continue

        if persist_rule == "always":
            payload[f.name] = value
            continue

        if persist_rule == "if_set":
            if value is not None:
                payload[f.name] = value
            continue

        # Default: omit None / False / default value
        if value is None:
            continue
        if isinstance(value, bool) and not value:
            continue
        if value == f.default:
            continue

        payload[f.name] = value

    return payload


@dataclass
class Container(Noun):
    """
    A container that can hold items, be opened/closed, locked, etc.
    """
    all_containers: ClassVar[List["Container"]] = field(default_factory=list)
    _by_name: ClassVar[Dict[str, "Container"]] = field(default_factory=dict)

    # Required: what the player sees / reads in text
    name: str = field(metadata={"persist": "always"})

    # Optional override: parser/search key (stable, lowercase)
    # Auto-derived from name if missing
    handle: Optional[str] = field(default=None, metadata={"persist": "if_set"})

    # Legacy field (preserved but unused; will be removed later)
    noun_name: str = field(init=False)

    # Optional long text for examine/look
    description: Optional[str] = field(default=None, metadata={"persist": "if_set"})

    # Normal optional fields
    capacity: Optional[int] = None
    is_openable: bool = False
    is_open: bool = field(default=False, metadata={"persist_if_parent": "is_openable"})
    opened_state_description: Optional[str] = None
    closed_state_description: Optional[str] = None
    open_action_description: Optional[str] = None
    close_action_description: Optional[str] = None
    is_lockable: bool = False
    is_locked: bool = field(default=False, metadata={"persist_if_parent": "is_lockable"})
    unlock_key: Optional[str] = None
    locked_description: Optional[str] = None
    open_exit_direction: Optional[str] = None
    open_exit_destination: Optional[str] = None

    # Runtime state – never saved
    contents: List["Item"] = field(default_factory=list, init=False)

    def __post_init__(self):
        super().__init__()

        # Legacy support (remove later)
        self.noun_name = self.name

        # Set parser handle: explicit → derived → fallback
        self.handle = (
            self.handle
            or _derive_noun_name(self.name)
            or self.name.lower()
        )

        # Register using parser-friendly handle (lowercased)
        searchkey = self.handle.lower()
        if searchkey in Container._by_name:
            print(f"Warning: duplicate handle '{searchkey}' — overwriting previous")
        Container._by_name[searchkey] = self
        Container.all_containers.append(self)

    # ───────────────────────────────────────────────
    # Noun interface methods
    # ───────────────────────────────────────────────

    def get_name(self) -> str:
        """Legacy - will be removed in favor of canonical_name"""
        return self.name

    def display_name(self) -> str:
        """What the player sees in text / inventory"""
        return self.description or self.name

    def canonical_name(self) -> str:
        """Stable parser / lookup key"""
        return self.handle

    # ───────────────────────────────────────────────
    # Serialization
    # ───────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Convert to dict for saving.
        Fully automatic + one special case for contents → items.
        """
        payload = serialize_non_default(self)

        if self.contents:
            payload["items"] = [item.to_dict() for item in self.contents]

        return payload


def _serialize_container(container: Container) -> dict:
    return container.to_dict()


# Temporary alias – remove when no more Box references exist
Box = Container