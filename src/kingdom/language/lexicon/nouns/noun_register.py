

def populate_noun_registry(game, noun_registry):
    # Items
    for item in Item.all_items:
        noun_registry.register(
            canonical=item.noun_name,
            synonyms={item.noun_name},
            adjectives=set(),
            category="item",
            world_object=item
        )

    # Boxes
    for box in Box.all_boxes:
        noun_registry.register(
            canonical=box.noun_name,
            synonyms={box.noun_name},
            adjectives=set(),
            category="box",
            world_object=box
        )

    # Features
    for room in game.rooms:
        for feature in room.features:
            noun_registry.register(
                canonical=feature.noun_name,
                synonyms={feature.noun_name},
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
            synonyms={dn._noun_name},
            adjectives=set(),
            category="direction",
            world_object=dn
        )

    # Player
    player = game.state.current_player
    noun_registry.register(
        canonical="me",
        synonyms={"self", "myself"},
        adjectives=set(),
        category="player",
        world_object=player
    )
