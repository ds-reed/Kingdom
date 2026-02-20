from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from kingdom.models import Game, Room, Verb
from kingdom.parser import normalize_direction_token
from kingdom.terminal_style import trs80_clear_and_show_room


@dataclass
class GameActionState:
    current_room: Room | None = None
    hero_name: str | None = None


class QuitGame(Exception):
    pass


ConfirmAction = Callable[[str], bool]


def quit_action() -> None:
    raise QuitGame()


def save_action(game: Game, default_save_path: Path, path: str | None = None) -> str:
    target = Path(path) if path else default_save_path
    game.save_world(target)
    return f"Game saved to {target}"


def load_action(game: Game, default_save_path: Path, path: str | None = None) -> str:
    target = Path(path) if path else default_save_path
    game.load_world(target)
    return f"Game loaded from {target}"


def go_action(state: GameActionState, direction: str) -> str:
    if state.current_room is None:
        return "There is nowhere to go."

    canonical_direction = normalize_direction_token(direction)

    next_room = state.current_room.get_connection(canonical_direction)
    if next_room is None:
        return f"You can't go {canonical_direction} from here."

    state.current_room = next_room
    trs80_clear_and_show_room(state.current_room, hero_name=state.hero_name)
    print()
    return f"You go {canonical_direction}."


def _describe_room(room: Room) -> str:
    exits = room.available_directions()
    visible_text = [obj.get_presence_text() for obj in [*room.items, *room.boxes]]
    if not exits:
        exits_text = "There are no visible exits."
    elif len(exits) == 1:
        exits_text = f"There is an exit to the {exits[0]}."
    else:
        exits_text = f"There are exits to the {', '.join(exits[:-1])} and {exits[-1]}."
    if visible_text:
        return f"You examine {room.name} carefully. {' '.join(visible_text)} {exits_text}"
    return f"You examine {room.name} carefully. {exits_text}"


def examine_action(state: GameActionState, *target_words: str) -> str:
    if state.current_room is None:
        return "There is nothing to examine."

    if not target_words:
        return _describe_room(state.current_room)

    target_name = " ".join(target_words).strip().lower()
    if target_name in {"room", state.current_room.name.lower()}:
        return _describe_room(state.current_room)

    for obj in [*state.current_room.items, *state.current_room.boxes]:
        if obj.get_name().lower() == target_name:
            return f"You examine {obj.get_name()} carefully."

    return f"You don't see {target_name} here."


def verbs_action(verbs: Mapping[str, object]) -> str:
    canonical_verbs: dict[str, Verb] = {}
    for verb in verbs.values():
        if isinstance(verb, Verb):
            canonical_verbs.setdefault(verb.verb, verb)

    parts: list[str] = []
    for name in sorted(canonical_verbs.keys()):
        verb = canonical_verbs[name]
        if verb.synonyms:
            parts.append(f"{name} ({', '.join(verb.synonyms)})")
        else:
            parts.append(name)

    return f"Available verbs: {', '.join(parts)}"


def _register_aliases(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    for alias in verb.synonyms:
        verb_lookup[alias] = verb


def _confirm(prompt_text: str, confirm_action: ConfirmAction | None) -> bool:
    if confirm_action is None:
        return True
    return confirm_action(prompt_text)


def build_verbs(
    state: GameActionState,
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None = None,
) -> dict[str, Verb]:
    def confirmed_quit_action() -> str | None:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    def confirmed_save_action(path: str | None = None) -> str:
        target = Path(path) if path else default_save_path
        if not _confirm(f"Save game to {target}?", confirm_action):
            return "Save cancelled."
        return save_action(game, default_save_path, path)

    def confirmed_load_action(path: str | None = None) -> str:
        target = Path(path) if path else default_save_path
        if not _confirm(f"Load game from {target}?", confirm_action):
            return "Load cancelled."
        return load_action(game, default_save_path, path)

    quit_verb = Verb("quit", lambda: confirmed_quit_action(), synonyms=["exit", "q"])
    go_verb = Verb(
        "go",
        lambda direction: go_action(state, direction),
        synonyms=["move", "walk", "run", "skip", "head", "jog", "travel"],
    )
    save_verb = Verb("save", lambda path=None: confirmed_save_action(path), synonyms=["write"])
    load_verb = Verb("load", lambda path=None: confirmed_load_action(path), synonyms=["restore"])
    examine_verb = Verb("examine", lambda *words: examine_action(state, *words), synonyms=["inspect", "look"])

    verbs: dict[str, Verb] = {
        quit_verb.verb: quit_verb,
        go_verb.verb: go_verb,
        save_verb.verb: save_verb,
        load_verb.verb: load_verb,
        examine_verb.verb: examine_verb,
    }

    for verb in [quit_verb, go_verb, save_verb, load_verb, examine_verb]:
        _register_aliases(verbs, verb)

    verbs_verb = Verb("verbs", lambda: verbs_action(verbs), synonyms=["help", "commands"])
    verbs[verbs_verb.verb] = verbs_verb
    _register_aliases(verbs, verbs_verb)
    return verbs