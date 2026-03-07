# parser/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

TokenSpan = Tuple[int, int]  # (start_index_in_text, end_index_exclusive)


@dataclass
class Diagnostic:
    code: str
    message: str
    span: Optional[TokenSpan] = None
    severity: str = "info"  # "info" | "warning" | "error"


@dataclass
class ParsedAction:
    # Core text + tokens
    raw_text: str = ""
    normalized_text: str = ""
    tokens: List[str] = field(default_factory=list)
    token_spans: List[TokenSpan] = field(default_factory=list)

    # Verb fields
    verb_candidates: List[Any] = field(default_factory=list)  # verb objects or IDs from lexicon
    primary_verb: Optional[Any] = None
    primary_verb_token: Optional[str] = None
    primary_verb_canonical: Optional[str] = None

    # Noun + phrase fields
    noun_candidates: List[Any] = field(default_factory=list)  # noun objects or IDs
    object_phrases: List[Any] = field(default_factory=list)   # Stage 2+
    prep_phrases: List[Any] = field(default_factory=list)     # Stage 3+
    conjunction_groups: List[Any] = field(default_factory=list)

    # Direction + modifier fields
    direction_tokens: List[str] = field(default_factory=list)
    modifier_tokens: List[str] = field(default_factory=list)

    # Other fields
    unknown_tokens: List[str] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)
