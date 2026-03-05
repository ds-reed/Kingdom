# not functioning - ignore this file
from kingdom.model.noun_model import Item, Container, DirectionNoun



def populate_noun_registry(game, noun_registry):
    from kingdom.model.game_init import get_action_state

    # Items
    for item in Item.all_items:
        noun_registry.register(
            canonical=item.name,
            synonyms={item.name},
            adjectives=set(),
            category="item",
            world_object=item
        )

    # Containers
    for container in Container.all_:
        noun_registry.register(
            canonical=container.name,
            synonyms={container.name},
            adjectives=set(),
            category="container",
            world_object=container
        )

    # Features
    for room in game.rooms:
        for feature in room.features:
            noun_registry.register(
                canonical=feature.name,
                synonyms={feature.name},
                adjectives=set(),
                category="feature",
                world_object=feature
            )

    # Rooms
    for room in game.rooms:
        noun_registry.register(
            canonical=room.name.lower(),
            synonyms=set(),
            adjectives=set(),
            category="room",
            world_object=room
        )

    # Directions
    for dn in DirectionNoun._direction_nouns_by_reference.values():
        noun_registry.register(
            canonical=dn.canonical_direction,
            synonyms={dn.canonical_direction},
            adjectives=set(),
            category="direction",
            world_object=dn
        )

    # Player
    player = get_action_state().current_player
    noun_registry.register(
        canonical="me",
        synonyms={"self", "myself"},
        adjectives=set(),
        category="player",
        world_object=player
    )
