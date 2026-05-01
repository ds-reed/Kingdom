from __future__ import annotations

from kingdom.rendering import descriptions


class _DummyGame:
    def __init__(self, room):
        self.current_room = room


class _DummyThing:
    def __init__(
        self,
        name: str,
        *,
        render_priority: int = 0,
        is_visible: bool = True,
        location_description: str | None = None,
    ):
        self._name = name
        self.render_priority = render_priority
        self.is_visible = is_visible
        self.location_description = location_description

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
        location_description: str | None = None,
    ):
        super().__init__(
            name,
            render_priority=render_priority,
            is_visible=is_visible,
            location_description=location_description,
        )
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
    assert "- A fish held by the glass case" in lines
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


def test_describe_presence_transparent_container_uses_authored_possession_tail(monkeypatch):
    renderer = descriptions.RoomRenderer()
    monkeypatch.setattr(descriptions, "Container", _DummyContainer)
    mermaid = _DummyContainer(
        "beautiful mermaid",
        is_transparent=True,
        contents=[_DummyThing("magnificent vase")],
        location_description="lounges gracefully on the narrow ledge, tightly clutching ",
    )

    text = renderer.describe_presence(mermaid)

    assert "tightly clutching a magnificent vase" in text
    assert "clutching has" not in text


def test_describe_presence_transparent_container_inserts_has_when_needed(monkeypatch):
    renderer = descriptions.RoomRenderer()
    monkeypatch.setattr(descriptions, "Container", _DummyContainer)
    case = _DummyContainer(
        "glass case",
        is_transparent=True,
        contents=[_DummyThing("ruby")],
        location_description="rests on the altar",
    )

    text = renderer.describe_presence(case)

    assert "rests on the altar has a ruby" in text