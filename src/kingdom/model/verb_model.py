from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, ClassVar
from kingdom.utilities import normalize_key   


@dataclass(repr=False)
class Verb:
    """A verb paired with a handler method.

    Verbs know:
      - their name
      - their synonyms
      - their handler function
      - how to perform noun-side overrides (double dispatch)
    """

    all_verbs: ClassVar[list["Verb"]] = []
    _by_name: ClassVar[dict[str, "Verb"]] = {}

    name: str
    action: Callable
    synonyms: list[str] | None = field(default_factory=list)
    hidden: bool = False
    modifiers: list[str] | None = field(default_factory=list)
    uses_directions: bool = False

    def __post_init__(self):
        self.name = str(self.name).strip().lower()
        self.hidden = bool(self.hidden)
        self.uses_directions = bool(self.uses_directions)

        # Better to keep modifiers & synonyms as sets for fast lookup
        self.modifiers = {
            normalize_key(modifier)
            for modifier in (self.modifiers or [])
            if str(modifier).strip()
        }

        raw_synonyms = {
            str(s).strip().lower()
            for s in (self.synonyms or [])
            if str(s).strip() and str(s).strip().lower() != self.name
        }
        self.synonyms = sorted(raw_synonyms)   # keep nice list for display/help

        Verb.all_verbs.append(self)

        # ─── Register all lookup keys ──────────────────────────────
        self.searchkey = normalize_key(self.name)

        # Register search key, avoiding duplicates but allowing overwrites with a warning
        if self.searchkey in Verb._by_name:
            other = Verb._by_name[self.searchkey]
            if other is not self:
                print(f"Warning: verb key '{self.searchkey}' already registered to '{other.name}', "
                      f"overwriting with '{self.name}'")
        Verb._by_name[self.searchkey] = self

    def __repr__(self):
        if self.synonyms:
            return f"\nVerb({self.name}, synonyms={list(self.synonyms)})"
        return f"\nVerb({self.name})"

    def all_names(self):
        return (self.name, *self.synonyms)

    def execute(self, target, words):
        """Execute this verb with noun override + handler fallback."""

        # 1. Noun override: on_<verb>
        if target is not None:
            override = getattr(target, f"on_{self.name}", None)
            if callable(override):
                result = override(words)
                if result is not None:
                    return result

        # 2. Handler fallback
        return self.action(target, words)
    
    def canonical_name(self) -> str:
        return self.name
    
    def display_name(self) -> str:
        return self.name
    
    def handle(self) -> str:
        return self.searchkey
    
    def synonym_names(self) -> list[str]:
        return self.synonyms

    @classmethod
    def get_by_name(cls, name: str) -> "Verb | None":
        if not name:
            return None
        key = str(name).strip().lower()
        return cls._by_name.get(key)
    



