"""Phase 3A baseline tests — document current behavior before any Phase 3 changes.

These tests establish what already works and flag the spawn-lexicon gap that Phase 3C will fix.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from kingdom.engine.item_behaviors import _spawn_room_item
from kingdom.engine.verbs.verb_registration import register_verbs
from kingdom.language.interpreter import _resolve_target_noun
from kingdom.language.lexicon import add_noun_to_lexicon, lex
from kingdom.language.parser import parse
from kingdom.model.game_model import get_game
from kingdom.model.noun_model import Container, Item, Player, Room, World


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def game_session(tmp_path: Path):
    game = get_game()
    game.reset_all_state()

    data_path = PROJECT_ROOT / "data" / "initial_state.json"
    world = World.get_instance()
    game.world = world
    game.setup_world(data_path)

    from kingdom.model.noun_model import Player
    player = Player("Phase3ATester")
    game.init_session(
        world=world,
        current_player=player,
        player_name="Phase3ATester",
        save_path=tmp_path / "phase3a.tmp.json",
    )

    register_verbs()
    lexicon = lex()
    game.lexicon = lexicon

    return {"game": game, "lexicon": lexicon}


# ---------------------------------------------------------------------------
# Test 1: Same handle in two rooms → each resolves its own room-local item
# ---------------------------------------------------------------------------

def test_same_handle_two_rooms_resolves_room_local():
    """Resolver uses room-local item iteration; same handle in two rooms → each room resolves its own item.

    This is already correct after Phase 2 (interpreter iterates current room candidates).
    The test locks that behavior as a regression guard before Phase 3D changes the global registry.
    """
    room_a = Room("East Hall", "The east hall.")
    room_b = Room("West Hall", "The west hall.")

    # Two items sharing the same handle — will overwrite each other in Noun._by_name,
    # but _resolve_target_noun uses room.items iteration, not the global registry.
    item_a = Item("Silver Florins", handle="florins")
    item_b = Item("Gold Florins", handle="florins")

    room_a.items.append(item_a)
    room_b.items.append(item_b)

    assert _resolve_target_noun(room_a, "florins") is item_a
    assert _resolve_target_noun(room_b, "florins") is item_b


# ---------------------------------------------------------------------------
# Test 2: Spawn gap — spawned item's handle absent from lexicon
# ---------------------------------------------------------------------------

def test_spawn_gap_handle_not_registered_in_lexicon(game_session):
    """After spawning an item, its handle and synonyms are absent from lexicon.noun_tokens.

    The lexicon is built once at setup_world(). Runtime-spawned items register in Noun._by_name
    via __post_init__ but never update lexicon.noun_tokens, so is_noun() returns False for
    their tokens. This means the parser classifies them as unknown rather than known nouns,
    and synonyms are completely invisible to the parser's noun-classification path.

    The interpreter's resolver (room.items iteration) works independently of the lexicon,
    so handle-based resolution still works. Synonym-based resolution does not currently
    resolve for Item objects in this path.

    Phase 3C will fix this by wiring add_noun_to_lexicon() into _spawn_room_item().
    """
    game = game_session["game"]
    lexicon = game_session["lexicon"]

    spawned = Item("Phantom Blade", handle="phantomblade", synonyms=["phantomsword"])
    game.current_room.items.append(spawned)

    # Handle and synonyms are NOT registered in the lexicon
    assert "phantomblade" not in lexicon.noun_tokens
    assert "phantomsword" not in lexicon.noun_tokens

    # The interpreter's resolver DOES find the item (it iterates room.items, not lexicon)
    assert _resolve_target_noun(game.current_room, "phantomblade") is spawned
    assert _resolve_target_noun(game.current_room, "phantomsword") is None


# ---------------------------------------------------------------------------
# Test 3: has_item() object-reference behavior (regression guard for Phase 3B)
# ---------------------------------------------------------------------------

def test_room_has_item_uses_object_reference():
    """Room.has_item() returns the item when present, None when not.

    Guards against changes in Phase 3B breaking the existing object-reference API.
    """
    room = Room("Guard Post", "A small guard post.")
    present = Item("Iron Key", handle="ironkey3a")
    absent = Item("Bronze Key", handle="bronzekey3a")

    room.items.append(present)

    assert room.has_item(present) is present
    assert room.has_item(absent) is None


def test_container_has_item_uses_object_reference():
    """Container.has_item() returns True when present, False when not.

    Guards against changes in Phase 3B breaking the existing object-reference API.
    """
    crate = Container("Wooden Crate", "A sturdy crate.")
    present = Item("Nail", handle="nail3a")
    absent = Item("Bolt", handle="bolt3a")

    crate.contents.append(present)

    assert crate.has_item(present) is True
    assert crate.has_item(absent) is False


# ---------------------------------------------------------------------------
# Phase 3B: has_item_by_alias() on Room, Container, Player
# ---------------------------------------------------------------------------

def test_room_has_item_by_alias_resolves_name_synonym_and_miss():
    room = Room("Alias Hall", "Room for alias matching.")
    item = Item("Velvet Cloak", handle="cloak", synonyms=["mantle"])
    room.items.append(item)

    assert room.has_item_by_alias("cloak") is item
    assert room.has_item_by_alias("mantle") is item
    assert room.has_item_by_alias("missing-item") is None


def test_container_has_item_by_alias_resolves_name_synonym_and_miss():
    container = Container("Travel Trunk", "A heavy trunk.")
    item = Item("Crystal Vial", handle="vial", synonyms=["flask"])
    container.contents.append(item)

    assert container.has_item_by_alias("vial") is item
    assert container.has_item_by_alias("flask") is item
    assert container.has_item_by_alias("missing-item") is None


def test_player_has_item_by_alias_resolves_name_synonym_and_miss():
    player = Player("AliasTester")
    item = Item("Field Rations", handle="rations", synonyms=["provisions"])
    player.sack.contents.append(item)

    assert player.has_item_by_alias("rations") is item
    assert player.has_item_by_alias("provisions") is item
    assert player.has_item_by_alias("missing-item") is None


# ---------------------------------------------------------------------------
# Phase 3C: runtime lexicon patch on spawn
# ---------------------------------------------------------------------------

def test_add_noun_to_lexicon_registers_handle_and_synonym(game_session):
    game = game_session["game"]
    lexicon = game_session["lexicon"]

    spawned = Item("Phantom Blade", handle="phantomblade", synonyms=["phantomsword"])
    game.current_room.items.append(spawned)

    assert "phantomblade" not in lexicon.noun_tokens
    assert "phantomsword" not in lexicon.noun_tokens

    add_noun_to_lexicon(spawned, lexicon)

    assert "phantomblade" in lexicon.noun_tokens
    assert "phantomsword" in lexicon.noun_tokens

    parsed = parse("get phantomsword", lexicon)[0]
    assert any(np["head"] == "phantomsword" for np in parsed.object_phrases)


def test_spawn_room_item_updates_lexicon_and_is_idempotent(game_session):
    game = game_session["game"]
    lexicon = game_session["lexicon"]

    _spawn_room_item(
        game,
        name="Ghost Blade",
        handle="ghostblade",
        synonyms=["ghostsword"],
    )

    assert "ghostblade" in lexicon.noun_tokens
    assert "ghostsword" in lexicon.noun_tokens
    parsed = parse("get ghostblade", lexicon)[0]
    assert any(np["head"] == "ghostblade" for np in parsed.object_phrases)

    # Duplicate handle spawn should no-op safely.
    count_before = sum(1 for item in game.current_room.items if item.obj_handle() == "ghostblade")
    _spawn_room_item(
        game,
        name="Ghost Blade",
        handle="ghostblade",
        synonyms=["ghostsword"],
    )
    count_after = sum(1 for item in game.current_room.items if item.obj_handle() == "ghostblade")

    assert count_after == count_before == 1


# ---------------------------------------------------------------------------
# Phase 3D: multi-candidate Noun name registry internals
# ---------------------------------------------------------------------------

def test_noun_registry_get_all_by_name_returns_all_duplicates():
    first = Item("registrycoin3d", description="Registry Coin One", handle="registrycoin3d_one")
    second = Item("registrycoin3d", description="Registry Coin Two", handle="registrycoin3d_two")

    matches = Item.get_all_by_name("registrycoin3d")

    assert first in matches
    assert second in matches
    assert len(matches) >= 2


def test_noun_registry_get_by_name_remains_singular_wrapper():
    first = Item("wrappergem3d", description="Wrapper Gem One", handle="wrappergem3d_one")
    second = Item("wrappergem3d", description="Wrapper Gem Two", handle="wrappergem3d_two")

    resolved = Item.get_by_name("wrappergem3d")
    all_matches = Item.get_all_by_name("wrappergem3d")

    assert resolved in all_matches
    assert len(all_matches) >= 2
