from kingdom.model.models import Game, DirectionNoun, GameActionState


def iter_known_noun_names(game: Game):
    for noun in game.get_all_nouns():
        yield noun.get_name()
        yield noun.get_descriptive_phrase()
        yield noun.get_noun_name()


def _iter_local_target_candidates(game: Game, state: GameActionState):
    yield game

    if state.current_room is not None:
        for direction_noun in DirectionNoun.get_direction_nouns_for_available_exits(state.current_room):
            yield direction_noun

        yield state.current_room
        for item in state.current_room.items:
            yield item
        for box in state.current_room.boxes:
            yield box
            if not box.is_openable or box.is_open:
                for item in box.contents:
                    yield item

    player = getattr(state, "current_player", None)
    if player is None:
        player = game.current_player
    if player is not None:
        for item in player.sack.contents:
            yield item


def _resolve_target_noun(game: Game, state: GameActionState, resolved_command) -> object | None:
    noun_matches = resolved_command.parse.nouns
    if not noun_matches:
        return None

    local_candidates = list(_iter_local_target_candidates(game, state))
    for noun_match in noun_matches:
        for candidate in local_candidates:
            if candidate.matches_reference(noun_match.text):
                return candidate

    return None