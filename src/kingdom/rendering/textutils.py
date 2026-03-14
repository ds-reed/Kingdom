# textutils.py

from typing import Sequence

def strip_leading_article(text: str) -> str:
    t = text.strip()
    lowered = t.lower()
    for art in ("a ", "an ", "the "):
        if lowered.startswith(art):
            return t[len(art):].strip()
    return t

def add_indefinite_article(noun: str) -> str:
    core = strip_leading_article(noun)
    if not core:
        return noun
    if core[0].lower() in "aeiou":
        return f"an {core}"
    return f"a {core}"

def add_definite_article(noun: str) -> str:
    return f"the {strip_leading_article(noun)}"

def pluralize(noun: str) -> str:
    core = strip_leading_article(noun)
    if core.endswith("y") and core[-2].lower() not in "aeiou":
        return core[:-1] + "ies"
    if core.endswith(("s", "x", "z", "ch", "sh")):
        return core + "es"
    return core + "s"

def terminate(sentence: str) -> str:
    s = sentence.rstrip()
    while s and s[-1] in ".!?":
        s = s[:-1]
    return s + "."

def capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]

def join_with_and(parts: Sequence[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"

def normalize_description(text: str) -> str:
    text = text.strip()

    # Remove trailing period
    if text.endswith("."):
        text = text[:-1]

    # Lowercase everything
    text = text.lower()

    return text


