from __future__ import annotations

from kingdom.rendering import descriptions


class _DummyGame:
    def __init__(self, room):
        self.current_room = room


class _DummyThing:
    def __init__(self, name: str, *, render_priority: int = 0, is_visible: bool = True):
        self._name = name
        self.render_priority = render_priority
        self.is_visible = is_visible

    def stateful_name(self) -> str:
        return self._name


class _DummyContainer(_DummyThing):
    def __init__(
        self,
        name: str,
        *,
        render_priority: int = 0,
        is_visible: bool = True,
        is_transparent: bool = False,
        contents=None,
    ):
        super().__init__(name, render_priority=render_priority, is_visible=is_visible)
        self.is_transparent = is_transparent
        self.contents = list(contents or [])


class _DummyRoom:
    def __init__(self, *, name: str, items=None, containers=None, exits=None):
        self.name = name
        self.items = list(items or [])
        self.containers = list(containers or [])
        self._exits = list(exits or [])

    def get_all_exits(self, movement_type="all", visible_only=True):
        return list(self._exits)


def test_describe_room_concise_applies_article_and_capitalization_to_item_bullets(monkeypatch):
    room = _DummyRoom(
        name="Cellar",
        items=[_DummyThing("small brass key")],
        containers=[
            _DummyContainer(
                "glass case",
                is_transparent=True,
                contents=[_DummyThing("fish")],
            )
        ],
    )
    monkeypatch.setattr(descriptions, "get_game", lambda: _DummyGame(room))

    lines = descriptions.RoomRenderer().describe_room_concise(room)

    assert "You see:" in lines
    assert "- A small brass key" in lines
    assert "- A glass case" in lines
    assert "- A fish in the glass case" in lines
    assert "- A fish" not in lines


def test_describe_room_concise_capitalizes_exit_bullets_without_article(monkeypatch):
    room = _DummyRoom(
        name="Cellar",
        exits=[("go", "north", object()), ("go", "down", object())],
    )
    monkeypatch.setattr(descriptions, "get_game", lambda: _DummyGame(room))

    lines = descriptions.RoomRenderer().describe_room_concise(room)

    assert "Available exits:" in lines
    assert "- North" in lines
    assert "- Down" in lines
    assert "- A north" not in lines
    assert "- A down" not in lines