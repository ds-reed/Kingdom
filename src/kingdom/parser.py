"""Command parsing and tokenization.

Handles user input parsing, direction alias normalization, and command resolution.
Defines ParseMatch, ParseResult, and ResolvedCommand dataclasses.
"""
from dataclasses import dataclass
import re
from typing import Iterable

from kingdom.model.models import Noun 
from kingdom.model.models import DIRECTIONS, DirectionNoun
from kingdom.model.verb_model import Verb



WORD_PATTERN = re.compile(r"[a-zA-Z0-9']+")

@dataclass(frozen=True)
class ParseMatch:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class ParseResult:
    raw_text: str
    normalized_text: str
    tokens: list[str]
    primary_verb: ParseMatch | None
    verbs: list[ParseMatch]
    nouns: list[ParseMatch]
    unknown_tokens: list[str]


@dataclass(frozen=True)
class ResolvedCommand:
    verb: str
    args: list[str]
    parse: ParseResult


def normalize_text(text: str) -> str:
    return text.lower().strip()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return WORD_PATTERN.findall(normalized)


def parse_command(
    text: str,
    known_verbs: Iterable[str] | None = None,
    known_nouns: Iterable[str] | None = None,
) -> ParseResult:
    tokens = tokenize(text)
    normalized_text = " ".join(tokens)

    verb_names = _default_verb_names() if known_verbs is None else _sanitize_names(known_verbs)
    noun_names = _default_noun_names() if known_nouns is None else _sanitize_names(known_nouns)

    verbs = _find_matches(tokens, verb_names)
    occupied_by_verbs = _occupied_indexes(verbs)
    nouns = _find_matches(tokens, noun_names, blocked_indexes=occupied_by_verbs)

    occupied = occupied_by_verbs | _occupied_indexes(nouns)
    unknown_tokens = [token for index, token in enumerate(tokens) if index not in occupied]

    return ParseResult(
        raw_text=text,
        normalized_text=normalized_text,
        tokens=tokens,
        primary_verb=verbs[0] if verbs else None,
        verbs=verbs,
        nouns=nouns,
        unknown_tokens=unknown_tokens,
    )


def resolve_command(
    text: str,
    known_verbs: Iterable[str],
    known_nouns: Iterable[str] | None = None,
) -> ResolvedCommand | None:
    parse_result = parse_command(text, known_verbs=known_verbs, known_nouns=known_nouns)
    primary_verb = parse_result.primary_verb

    # Implicit GO: single direction token
    tokens = parse_result.tokens
    if len(tokens) == 1 and DIRECTIONS.is_direction(tokens[0]):
        dn = DirectionNoun.get_direction_noun(tokens[0])
        return ResolvedCommand(
            verb="go",
            args=[dn.canonical_direction],
            parse=parse_result,
        )


    if primary_verb is None:
        return None

    return ResolvedCommand(
        verb=primary_verb.text,
        args=parse_result.tokens[primary_verb.end:],
        parse=parse_result,
    )


def _sanitize_names(names: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for name in names:
        normalized = " ".join(tokenize(name))
        if normalized:
            cleaned.append(normalized)
    return sorted(set(cleaned), key=lambda value: (-len(value.split()), value))


def _default_verb_names() -> list[str]:
    return _sanitize_names(name for verb in Verb.all_verbs for name in verb.all_names())


def _default_noun_names() -> list[str]:
    return _sanitize_names(noun.get_name() for noun in Noun.all_nouns if not isinstance(noun, Verb))


def _build_phrase_parts(names: list[str]) -> list[tuple[str, list[str]]]:
    return [(name, name.split()) for name in names]


def _find_matches(
    tokens: list[str],
    names: list[str],
    blocked_indexes: set[int] | None = None,
) -> list[ParseMatch]:
    blocked = blocked_indexes or set()
    phrase_parts = _build_phrase_parts(names)
    matches: list[ParseMatch] = []
    occupied = set(blocked)
    index = 0

    while index < len(tokens):
        if index in occupied:
            index += 1
            continue

        best_name = None
        best_end = index

        for name, parts in phrase_parts:
            phrase_len = len(parts)
            end = index + phrase_len
            if end > len(tokens):
                continue
            if any(position in occupied for position in range(index, end)):
                continue
            if tokens[index:end] == parts:
                best_name = name
                best_end = end
                break

        if best_name is not None:
            matches.append(ParseMatch(text=best_name, start=index, end=best_end))
            occupied.update(range(index, best_end))
            index = best_end
        else:
            index += 1

    return matches


def _occupied_indexes(matches: list[ParseMatch]) -> set[int]:
    return {index for match in matches for index in range(match.start, match.end)}