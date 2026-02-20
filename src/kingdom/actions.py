from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, Sequence, TypeAlias

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
LegacyVerbSpec: TypeAlias = tuple[str, tuple[str, ...]]

LEGACY_VERB_SPECS: tuple[LegacyVerbSpec, ...] = (
    ("drop", ()),
    ("throw", ()),
    ("read", ()),
    ("open", ()),
    ("kick", ()),
    ("knock", ()),
    ("insert", ()),
    ("shoot", ()),
    ("climb", ()),
    ("unlock", ()),
    ("close", ()),
    ("turn", ()),
    ("light", ("torch",)),
    ("score", ()),
    ("wash", ()),
    ("swim", ()),
    ("push", ("press",)),
    ("dial", ()),
    ("break", ("smash",)),
    ("drink", ()),
    ("rub", ()),
    ("drag", ()),
    ("kill", ()),
    ("swing", ()),
    ("untie", ()),
    ("tie", ()),
)

NO_CARROT_MESSAGE = "YOU HAVE NO CARROT! ARE YOU TRYING TO CONFUSE ME?"
EAT_CARROT_MESSAGE = (
    "THE CHEERY ORANGE CARROT SCREAMS AS YOU FORCE IT DOWN YOUR HIDEOUS THROAT. "
    "HIS SCREAMS DIE OUT TO A GURGLE AS HE IS DRIVEN INTO THE PIT OF YOUR GREEDY STOMACH."
)


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


def legacy_stub_action(verb_name: str, *args: str) -> str:
    if args:
        return f"'{verb_name}' is recognized but not implemented yet. ({' '.join(args)})"
    return f"'{verb_name}' is recognized but not implemented yet."


def inventory_action(game: Game) -> str:
    player = game.current_player
    if player is None:
        return "No hero is active yet."

    sack_items = [item.name for item in player.sack.contents]
    if not sack_items:
        return f"{player.name}'s sack is empty."

    item_label = "item" if len(sack_items) == 1 else "items"
    return f"{player.name}'s sack contains ({len(sack_items)} {item_label}): {', '.join(sack_items)}"


def take_action(state: GameActionState, game: Game, *target_words: str) -> str:
    if state.current_room is None:
        return "There is nothing to take here."

    player = game.current_player
    if player is None:
        return "No hero is active yet."

    if not target_words:
        return "Take what?"

    target_name = " ".join(target_words).strip().lower()
    if not target_name:
        return "Take what?"

    sources = [(state.current_room.name, state.current_room.items)]
    sources.extend((box.box_name, box.contents) for box in state.current_room.boxes)

    found_item = None
    found_contents = None
    found_container_name = ""

    for container_name, contents in sources:
        for item in contents:
            if item.name.lower() == target_name:
                found_item = item
                found_contents = contents
                found_container_name = container_name
                break
        if found_item is not None:
            break

    if found_item is None or found_contents is None:
        return f"You don't see {target_name} here."

    if not found_item.pickupable:
        return found_item.refuse_string

    if player.sack.capacity is not None and len(player.sack.contents) >= player.sack.capacity:
        return f"{player.name}'s sack is full (max {player.sack.capacity} items)!"

    found_contents.remove(found_item)
    player.sack.contents.append(found_item)
    found_item.current_box = player.sack
    return f"{player.name} takes {found_item.name} from {found_container_name}."


def _find_carrot_containers(state: GameActionState, game: Game) -> tuple[object | None, object | None]:
    player = game.current_player
    if player is None:
        return None, None

    for item in player.sack.contents:
        if "carrot" in item.name.lower():
            return player.sack.contents, item

    if state.current_room is None:
        return None, None

    for item in state.current_room.items:
        if "carrot" in item.name.lower():
            return state.current_room.items, item

    for box in state.current_room.boxes:
        for item in box.contents:
            if "carrot" in item.name.lower():
                return box.contents, item

    return None, None


def eat_action(state: GameActionState, game: Game, *target_words: str) -> str:
    if game.current_player is None:
        return "No hero is active yet."

    if target_words:
        requested_target = " ".join(target_words).strip().lower()
        if requested_target and "carrot" not in requested_target:
            return "You can't eat that."

    container, carrot_item = _find_carrot_containers(state, game)
    if carrot_item is None or container is None:
        return NO_CARROT_MESSAGE

    container.remove(carrot_item)
    carrot_item.current_box = None
    return EAT_CARROT_MESSAGE


def _register_aliases(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    for alias in verb.synonyms:
        verb_lookup[alias] = verb


def _register_verb(verb_lookup: dict[str, Verb], verb: Verb) -> None:
    verb_lookup[verb.verb] = verb
    _register_aliases(verb_lookup, verb)


def _merge_aliases(verb_lookup: dict[str, Verb], verb: Verb, aliases: Sequence[str]) -> None:
    merged_synonyms = list(verb.synonyms)
    for alias in aliases:
        if alias not in merged_synonyms:
            merged_synonyms.append(alias)
        verb_lookup[alias] = verb
    verb.synonyms = tuple(sorted(set(merged_synonyms)))


def _confirm(prompt_text: str, confirm_action: ConfirmAction | None) -> bool:
    if confirm_action is None:
        return True
    return confirm_action(prompt_text)


def _build_core_verbs(
    state: GameActionState,
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None,
) -> list[Verb]:
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

    quit_verb = Verb("quit", confirmed_quit_action, synonyms=["exit", "q"])
    go_verb = Verb(
        "go",
        lambda direction: go_action(state, direction),
        synonyms=["move", "walk", "run", "skip", "slide", "head", "jog", "travel"],
    )
    save_verb = Verb("save", confirmed_save_action, synonyms=["write"])
    load_verb = Verb("load", confirmed_load_action, synonyms=["restore"])
    examine_verb = Verb("examine", lambda *words: examine_action(state, *words), synonyms=["inspect", "look"])
    inventory_verb = Verb("inventory", lambda: inventory_action(game), synonyms=["inven"])
    take_verb = Verb("take", lambda *words: take_action(state, game, *words), synonyms=["get"])
    eat_verb = Verb("eat", lambda *words: eat_action(state, game, *words))
    return [quit_verb, go_verb, save_verb, load_verb, examine_verb, inventory_verb, take_verb, eat_verb]


def _build_legacy_stub_verbs(specs: Sequence[LegacyVerbSpec] = LEGACY_VERB_SPECS) -> list[Verb]:
    return [
        Verb(canonical_name, partial(legacy_stub_action, canonical_name), synonyms=list(aliases))
        for canonical_name, aliases in specs
    ]


def _register_legacy_stubs(verb_lookup: dict[str, Verb]) -> None:
    for legacy_verb in _build_legacy_stub_verbs():
        existing = verb_lookup.get(legacy_verb.verb)
        if existing is None:
            _register_verb(verb_lookup, legacy_verb)
            continue
        _merge_aliases(verb_lookup, existing, legacy_verb.synonyms)


def build_verbs(
    state: GameActionState,
    game: Game,
    default_save_path: Path,
    confirm_action: ConfirmAction | None = None,
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}

    for verb in _build_core_verbs(state, game, default_save_path, confirm_action):
        _register_verb(verbs, verb)

    verbs_verb = Verb("verbs", lambda: verbs_action(verbs), synonyms=["help", "commands"])
    _register_verb(verbs, verbs_verb)

    _register_legacy_stubs(verbs)

    return verbs