from kingdom.model.noun_model import World, DirectionNoun
from kingdom.model.game_init import GameActionState


def iter_known_noun_names(game: World):
    for noun in game.get_all_nouns():
        yield noun.canonical_name()
        yield noun.display_name()



def _iter_local_target_candidates(game: World, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for container in state.current_room.containers:
            yield container
            if not container.is_openable or container.is_open:
                for item in container.contents:
                    yield item

    player = getattr(state, "current_player", None)
    if player is not None:
        for item in player.sack.contents:
            yield item


def _resolve_target_noun(game: World, state: GameActionState, resolved_command) -> object | None:
    noun_matches = resolved_command.parse.nouns
    if not noun_matches:
        return None

    local_candidates = list(_iter_local_target_candidates(game, state))
    if state.current_room is not None and resolved_command.verb in {"look", "examine", "inspect", "x"}:
        for feature in getattr(state.current_room, "features", []):
            local_candidates.append(feature)
    for noun_match in noun_matches:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                return candidate

    return None