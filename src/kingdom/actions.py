from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Mapping, Sequence, TypeAlias

from kingdom.models import Game, Item, Room, Verb
from kingdom.parser import normalize_direction_token
from kingdom.terminal_style import trs80_clear_and_show_room


@dataclass
class GameActionState:
    current_room: Room | None = None
    hero_name: str | None = None


class QuitGame(Exception):
    pass


ConfirmAction = Callable[[str], bool]
PromptAction = Callable[[str], str]
LegacyVerbSpec: TypeAlias = tuple[str, tuple[str, ...]]

LEGACY_VERB_SPECS: tuple[LegacyVerbSpec, ...] = (
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

def quit_action() -> None:
    raise QuitGame()


def _derive_player_save_path(default_save_path: Path, hero_name: str | None) -> Path:
    if not hero_name:
        return default_save_path

    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in hero_name.strip())
    cleaned = cleaned.strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    if not cleaned:
        return default_save_path

    return default_save_path.with_name(f"{cleaned}.sav")


def _prompt_for_path(prompt_action: PromptAction | None, prompt_label: str, default_path: Path) -> Path:
    if prompt_action is None:
        return default_path

    raw_path = prompt_action(f"{prompt_label} file name [{default_path}]: ").strip()
    if not raw_path:
        return default_path
    return Path(raw_path)


def _is_game_command_target(target_words: tuple[str, ...], target: object | None) -> bool:
    normalized_words = [word.strip().lower() for word in target_words if word.strip()]
    if target is not None and not isinstance(target, Game):
        return False
    return isinstance(target, Game) or not normalized_words or normalized_words == ["game"]


def save_action(
    game: Game,
    default_save_path: Path,
    prompt_action: PromptAction | None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not _is_game_command_target(target_words, target):
        return "You can't save that."

    save_path = _prompt_for_path(prompt_action, "Save", default_save_path)

    game.save_world(save_path)
    return f"Game saved to {save_path}"


def load_action(
    game: Game,
    default_save_path: Path,
    prompt_action: PromptAction | None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not _is_game_command_target(target_words, target):
        return "You can't load that."

    load_path = _prompt_for_path(prompt_action, "Load", default_save_path)

    game.load_world(load_path)
    return f"Game loaded from {load_path}"


def go_action(state: GameActionState, direction: str) -> str:
    if state.current_room is None:
        return "There is nowhere to go."

    canonical_direction = normalize_direction_token(direction)

    next_room = state.current_room.get_connection(canonical_direction)
    if next_room is None:
        return f"You can't go {canonical_direction} from here."

    state.current_room = next_room
    trs80_clear_and_show_room(state.current_room, hero_name=state.hero_name, clear=False)
    print()
    return f"You go {canonical_direction}."


def climb_action(state: GameActionState, *target_words: str, target: object | None = None) -> str:
    if state.current_room is None:
        return "There is nowhere to climb."

    direction: str | None = None

    if target is not None:
        direction = getattr(target, "canonical_direction", None)
        if direction is None and hasattr(target, "get_noun_name"):
            direction = normalize_direction_token(target.get_noun_name())

    if direction is None and target_words:
        direction = normalize_direction_token(target_words[0])

    if direction is None:
        vertical_exits = [d for d in state.current_room.available_directions() if d in {"up", "down"}]
        if len(vertical_exits) == 1:
            return go_action(state, vertical_exits[0])
        if not vertical_exits:
            return "There is nothing here to climb."
        return "Climb where? Up or down?"

    if direction not in {"up", "down"}:
        return "You can only climb up or down."

    return go_action(state, direction)


def exit_action(
    state: GameActionState,
    confirm_action: ConfirmAction | None,
    prompt_action: PromptAction | None,
    *target_words: str,
    target: object | None = None,
) -> str:
    if not target_words and target is None:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    target_text = " ".join(target_words).strip().lower()

    if isinstance(target, Room) or target_text in {"room", "here"}:
        if state.current_room is None:
            return "There is nowhere to exit from."

        exits = state.current_room.available_directions()
        if not exits:
            return "There are no exits from here."
        if len(exits) == 1:
            return go_action(state, exits[0])

        if prompt_action is None:
            return f"Which direction do you want to exit? ({', '.join(exits)})"

        chosen_raw = prompt_action(f"Which direction? ({', '.join(exits)}): ").strip().lower()
        if not chosen_raw:
            return "Exit cancelled."
        return go_action(state, chosen_raw)

    if target_text in {"game", "program"}:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    if target_words:
        maybe_direction = normalize_direction_token(target_words[0])
        if maybe_direction in Room.DIRECTIONS:
            return go_action(state, maybe_direction)

    return "Exit where?"


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
        if obj.matches_reference(target_name):
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


def take_action(state: GameActionState, game: Game, *target_words: str, target: object | None = None) -> str:
    if state.current_room is None:
        return "There is nothing to take here."

    player = game.current_player
    if player is None:
        return "No hero is active yet."

    sources = [(state.current_room.name, state.current_room.items)]
    sources.extend((box.box_name, box.contents) for box in state.current_room.boxes)

    if target is not None:
        if not isinstance(target, Item):
            return "You can't take that."

        if player.sack.capacity is not None and len(player.sack.contents) >= player.sack.capacity:
            return f"{player.name}'s sack is full (max {player.sack.capacity} items)!"

        for container_name, contents in sources:
            if target in contents:
                contents.remove(target)
                player.sack.contents.append(target)
                target.current_box = player.sack
                return f"{player.name} takes {target.name} from {container_name}."

        return f"You don't see {target.get_noun_name()} here."

    if not target_words:
        return "Take what?"

    target_name = " ".join(target_words).strip().lower()
    if not target_name:
        return "Take what?"

    found_item = None
    found_contents = None
    found_container_name = ""

    for container_name, contents in sources:
        for item in contents:
            if item.matches_reference(target_name):
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


def drop_action(state: GameActionState, game: Game, *target_words: str, target: object | None = None) -> str:
    if state.current_room is None:
        return "There is nowhere to drop anything."

    player = game.current_player
    if player is None:
        return "No hero is active yet."

    if target is not None:
        if not isinstance(target, Item):
            return "You can't drop that."
        if target not in player.sack.contents:
            return f"{player.name} doesn't have {target.get_noun_name()}!"

        player.sack.contents.remove(target)
        state.current_room.items.append(target)
        target.current_box = None
        return f"{player.name} drops {target.name}."

    if not target_words:
        return "Drop what?"

    target_name = " ".join(target_words).strip().lower()
    if not target_name:
        return "Drop what?"

    for item in player.sack.contents:
        if item.matches_reference(target_name):
            player.sack.contents.remove(item)
            state.current_room.items.append(item)
            item.current_box = None
            return f"{player.name} drops {item.name}."

    return f"{player.name} doesn't have {target_name}!"


def is_present_in_known_containers(item: object, dispatch_context: dict | None) -> bool:
    current_box = getattr(item, "current_box", None)
    if current_box is not None and item in getattr(current_box, "contents", []):
        return True

    if not dispatch_context:
        return False

    state = dispatch_context.get("state")
    room = getattr(state, "current_room", None) if state is not None else None
    if room is not None:
        if item in getattr(room, "items", []):
            return True
        for box in getattr(room, "boxes", []):
            if item in getattr(box, "contents", []):
                return True

    game = dispatch_context.get("game")
    player = getattr(game, "current_player", None) if game is not None else None
    if player is not None and item in getattr(player.sack, "contents", []):
        return True

    return False


def consume_if_getable_and_present(item: object, dispatch_context: dict | None, missing_message: str) -> tuple[bool, str | None]:
    if not getattr(item, "pickupable", True):
        return False, "You can't eat that."

    if not is_present_in_known_containers(item, dispatch_context):
        return False, missing_message

    remove_method = getattr(item, "_remove_from_known_containers", None)
    if not callable(remove_method):
        return False, missing_message

    removed = remove_method(dispatch_context=dispatch_context)
    if not removed:
        return False, missing_message

    return True, None


def build_dispatch_context(state: GameActionState, game: Game) -> dict:
    return {
        "state": state,
        "game": game,
        "move_direction": lambda direction: go_action(state, direction),
        "consume_if_getable_and_present": consume_if_getable_and_present,
        "is_present_in_known_containers": is_present_in_known_containers,
    }


def eat_action(*target_words: str, target: object | None = None, dispatch_context: dict | None = None) -> str:
    default_refuse = "You can't eat that."
    default_success = "YUM! TASTES GOOD."

    if target is None:
        return "Eat what?"

    if not isinstance(target, Item):
        return default_refuse

    if not target.edible:
        return target.eat_refuse_string or default_refuse

    missing_message = target.eat_missing_string or default_refuse
    consumed, error_message = consume_if_getable_and_present(target, dispatch_context, missing_message)
    if not consumed:
        return error_message or target.eat_refuse_string or default_refuse

    return target.eat_success_string or default_success


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
    prompt_action: PromptAction | None,
) -> list[Verb]:
    player_default_save_path = _derive_player_save_path(default_save_path, state.hero_name)

    def confirmed_quit_action() -> str | None:
        if not _confirm("Are you sure you want to quit?", confirm_action):
            return "Quit cancelled."
        quit_action()

    def confirmed_save_action(*words: str, target: object | None = None) -> str:
        if not _is_game_command_target(words, target):
            return "You can't save that."
        if not _confirm("Save game?", confirm_action):
            return "Save cancelled."
        return save_action(game, player_default_save_path, prompt_action, *words, target=target)

    def confirmed_load_action(*words: str, target: object | None = None) -> str:
        if not _is_game_command_target(words, target):
            return "You can't load that."
        if not _confirm("Load game?", confirm_action):
            return "Load cancelled."
        return load_action(game, player_default_save_path, prompt_action, *words, target=target)

    quit_verb = Verb("quit", confirmed_quit_action, synonyms=["q"])
    exit_verb = Verb(
        "exit",
        lambda *words, target=None: exit_action(state, confirm_action, prompt_action, *words, target=target),
        synonyms=["leave"],
    )
    go_verb = Verb(
        "go",
        lambda direction: go_action(state, direction),
        synonyms=["move", "walk", "run", "skip", "slide", "head", "jog", "travel"],
    )
    climb_verb = Verb("climb", lambda *words, target=None: climb_action(state, *words, target=target))
    save_verb = Verb("save", confirmed_save_action, synonyms=["write"])
    load_verb = Verb("load", confirmed_load_action, synonyms=["restore"])
    examine_verb = Verb("examine", lambda *words: examine_action(state, *words), synonyms=["inspect", "look"])
    inventory_verb = Verb("inventory", lambda: inventory_action(game), synonyms=["inven"])
    take_verb = Verb("take", lambda *words, target=None: take_action(state, game, *words, target=target), synonyms=["get"])
    drop_verb = Verb("drop", lambda *words, target=None: drop_action(state, game, *words, target=target))
    eat_verb = Verb("eat", lambda *words, target=None: eat_action(*words, target=target))
    return [
        quit_verb,
        exit_verb,
        go_verb,
        climb_verb,
        save_verb,
        load_verb,
        examine_verb,
        inventory_verb,
        take_verb,
        drop_verb,
        eat_verb,
    ]


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
    prompt_action: PromptAction | None = None,
) -> dict[str, Verb]:
    verbs: dict[str, Verb] = {}

    for verb in _build_core_verbs(state, game, default_save_path, confirm_action, prompt_action):
        _register_verb(verbs, verb)

    verbs_verb = Verb("verbs", lambda: verbs_action(verbs), synonyms=["help", "commands"])
    _register_verb(verbs, verbs_verb)

    _register_legacy_stubs(verbs)

    return verbs