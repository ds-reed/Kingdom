# textutils.py

import re
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


_ARTICLE_TOKENS = {"a", "an", "the"}
_PRONOUNS = {
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
}
# Locative / indefinite adverbs that never take an article.
# "from somewhere", "from nowhere", "from here", etc. must not be rewritten.
_NO_ARTICLE_ADVERBS = {
    "somewhere", "nowhere", "everywhere", "anywhere",
    "here", "there", "elsewhere",
    "ahead", "behind", "above", "below", "nearby",
    "inside", "outside", "beyond", "upstairs", "downstairs",
}

_NON_NOUN_HEADS = {
    "get", "take", "drop", "put", "open", "close", "unlock", "lock",
    "light", "extinguish", "rub", "turn", "hit", "eat", "give", "loot",
    "go", "swim", "climb", "look", "move", "push", "pull", "throw",
    "getting", "taking", "dropping", "putting", "opening", "closing",
    "unlocking", "locking", "lighting", "extinguishing", "rubbing",
    "turning", "hitting", "eating", "giving", "looting", "going",
    "swimming", "climbing", "looking", "moving", "pushing", "pulling",
    "throwing", "sliding",
}

_DIRECTION_WORDS = {
    "north", "south", "east", "west", "up", "down", "inside", "outside",
}

_INFINITIVE_CUE_WORDS = {
    "begin", "begins", "began", "begun",
    "start", "starts", "started",
    "seem", "seems", "seemed",
    "try", "tries", "tried",
    "attempt", "attempts", "attempted",
    "want", "wants", "wanted",
    "need", "needs", "needed",
    "continue", "continues", "continued",
}


def strip_duplicate_leading_articles(text: str) -> str:
    """Collapse repeated article prefixes to a single article token."""
    if not text:
        return text

    raw = text.lstrip()
    leading_space = text[: len(text) - len(raw)]
    parts = raw.split()
    if not parts:
        return text

    lowered = [part.lower() for part in parts]
    if lowered[0] not in _ARTICLE_TOKENS:
        return text

    i = 1
    while i < len(lowered) and lowered[i] in _ARTICLE_TOKENS:
        i += 1

    if i == 1:
        return text

    collapsed = [parts[0]] + parts[i:]
    return leading_space + " ".join(collapsed)


def _needs_article_insertion(phrase: str) -> bool:
    parts = [p for p in phrase.split() if p]
    if not parts:
        return False

    first = parts[0]
    lfirst = first.lower()
    if lfirst in _ARTICLE_TOKENS or lfirst in _PRONOUNS or lfirst in _NO_ARTICLE_ADVERBS:
        return False
    if lfirst in _NON_NOUN_HEADS:
        return False
    if first[:1].isdigit():
        return False
    if lfirst.endswith("s") and lfirst not in {"glass", "boss", "chess"}:
        return False
    if len(parts) >= 2 and parts[0].istitle() and parts[1].istitle():
        return False
    return True


def _insert_article(phrase: str, *, prefer_definite: bool) -> str:
    normalized = strip_duplicate_leading_articles(phrase.strip())
    if not _needs_article_insertion(normalized):
        return normalized
    if prefer_definite:
        return add_definite_article(normalized)
    return add_indefinite_article(normalized)


def _definitize_phrase(phrase: str) -> str:
    """Convert article-like noun phrases to a definite form when safe."""
    normalized = strip_duplicate_leading_articles(phrase.strip())
    if not normalized:
        return normalized

    core = strip_leading_article(normalized)
    if not core:
        return normalized

    # Only force to definite when the core appears noun-phrase-like.
    if _needs_article_insertion(core):
        return add_definite_article(core)

    return normalized


def normalize_articles_in_sentence(text: str) -> str:
    """
    Conservative phrase-level article normalization.
    We only target frequent game feedback templates and keep everything else unchanged.
    """
    if not text:
        return text

    out = text

    # 1) Clean repeated article prefixes in-place.
    out = re.sub(
        r"\b(?P<a1>a|an|the)\s+(?P<a2>a|an|the)\s+(?P<body>[A-Za-z][^\n]*)",
        lambda m: f"{m.group('a1')} {m.group('body')}",
        out,
        flags=re.IGNORECASE,
    )

    # 2) Insert article after common action verbs when noun phrase is bare.
    #    Example: "You get fish" -> "You get a fish".
    out = re.sub(
        r"(?:(?<=^)|(?<=[.!?]\s))You\s+(?P<verb>get|take|drop|open|close|unlock|lock|light|extinguish|rub|turn|hit|eat|give|loot)\s+(?P<phrase>[A-Za-z][A-Za-z'\- ]{0,60})(?P<tail>[.!?]|$)",
        lambda m: f"You {m.group('verb')} {_insert_article(m.group('phrase'), prefer_definite=False)}{m.group('tail')}",
        out,
        flags=re.IGNORECASE,
    )

    # 2b) For direct-refusal phrasing, prefer a definite referent.
    #     Example: "You can't get a greasy brown lunch bag." -> "You can't get the greasy brown lunch bag."
    out = re.sub(
        r"(?:(?<=^)|(?<=[.!?]\s))You\s+can't\s+(?P<verb>get|take|drop|open|close|unlock|lock|light|extinguish|rub|turn|hit|eat|give|loot)\s+(?P<phrase>[A-Za-z][A-Za-z'\- ]{0,60})(?P<tail>[.!?]|$)",
        lambda m: f"You can't {m.group('verb')} {_definitize_phrase(m.group('phrase'))}{m.group('tail')}",
        out,
        flags=re.IGNORECASE,
    )

    # 3) Insert article for frequent indirect-object segments: into/on/to/from/with.
    def _normalize_prep_phrase(m: re.Match) -> str:
        prep = m.group("prep")
        phrase = m.group("phrase")
        tail = m.group("tail")

        # Do not rewrite infinitive action phrases like "begins to play" / "seems to fill".
        if prep.lower() == "to":
            before = m.string[: m.start()]
            prev_match = re.search(r"([A-Za-z']+)\s*$", before)
            prev_word = prev_match.group(1).lower() if prev_match else ""
            first_word = phrase.split()[0].lower() if phrase.split() else ""

            if prev_word in _INFINITIVE_CUE_WORDS:
                return f"{prep} {phrase}{tail}"
            if first_word in _NON_NOUN_HEADS or first_word.endswith("ing"):
                return f"{prep} {phrase}{tail}"

        return f"{prep} {_insert_article(phrase, prefer_definite=True)}{tail}"

    out = re.sub(
        r"\b(?P<prep>into|in|on|onto|to|from|with)\s+(?P<phrase>[A-Za-z][A-Za-z'\- ]{0,60})(?P<tail>[.!?,]|$)",
        _normalize_prep_phrase,
        out,
        flags=re.IGNORECASE,
    )

    return out


def normalize_terminal_dot_run(line: str) -> str:
    """
    Terminal dot policy:
    - allow only trailing '.' or '...'
    - '..' -> '.'
    - '....' (or more) -> '...'
    - '?.', '!.', or ':.' (period after terminal punctuation) -> strips the spurious period(s)
    """
    if not line:
        return line

    # Strip periods that appear after ?, !, or : — they're spurious
    m = re.search(r"([?!:])\.+$", line)
    if m:
        return line[: m.start()] + m.group(1)

    match = re.search(r"\.+$", line)
    if not match:
        return line

    dots = match.group(0)
    if len(dots) == 1 or len(dots) == 3:
        return line
    replacement = "." if len(dots) == 2 else "..."
    return line[: match.start()] + replacement


def sentence_case_line(line: str) -> str:
    for i, ch in enumerate(line):
        if ch.isalpha():
            return line[:i] + ch.upper() + line[i + 1 :]
    return line


def capitalize_bullet_line(line: str) -> str:
    stripped = line.lstrip()
    leading = line[: len(line) - len(stripped)]
    if not stripped.startswith("-"):
        return line

    bullet_body = stripped[1:].lstrip()
    if not bullet_body:
        return line

    capped = sentence_case_line(bullet_body)
    return f"{leading}- {capped}"


def normalize_bullet_line(line: str) -> str:
    stripped = line.lstrip()
    leading = line[: len(line) - len(stripped)]
    if not stripped.startswith("-"):
        return line

    bullet_body = stripped[1:].lstrip()
    if not bullet_body:
        return line

    first_word = bullet_body.split()[0].lower() if bullet_body.split() else ""
    if first_word in _DIRECTION_WORDS:
        return f"{leading}- {sentence_case_line(bullet_body)}"

    normalized = _insert_article(bullet_body, prefer_definite=False)
    normalized = sentence_case_line(normalized)
    return f"{leading}- {normalized}"


def ensure_trailing_punctuation(line: str) -> str:
    if not line:
        return line
    trimmed = line.rstrip()
    if not trimmed:
        return ""
    if trimmed.endswith((".", "!", "?", ":", "...")):
        return trimmed
    return trimmed + "."


def normalize_outcome_text(text: str | None) -> str:
    if not text:
        return ""

    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]

    # preserve intentional paragraph structure, but strip outer empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    out_lines: list[str] = []
    for line in lines:
        if not line.strip():
            out_lines.append("")
            continue

        cleaned = strip_duplicate_leading_articles(line)
        if cleaned.lstrip().startswith("-"):
            cleaned = normalize_bullet_line(cleaned)
            cleaned = normalize_terminal_dot_run(cleaned)
            out_lines.append(cleaned)
            continue

        cleaned = normalize_articles_in_sentence(cleaned)
        cleaned = sentence_case_line(cleaned)
        cleaned = normalize_terminal_dot_run(cleaned)
        cleaned = ensure_trailing_punctuation(cleaned)
        out_lines.append(cleaned)

    return "\n".join(out_lines)


