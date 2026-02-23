# game_state_verbs.py


from kingdom.models import Game, Noun, Room, Box, Item, Verb, DispatchContext

class WorldVerbHandler:

    def score(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        game = ctx.game
        if game is None:
            return "Score is unavailable."
        return f"Your current score is: {game.score}"   
    

    def look(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
    
        room = ctx.state.current_room

        # 1. Plain LOOK
        if target is None and not words:
            return self._describe_room(room)

        # 2. LOOK INSIDE X
        if "inside" in words:
            if isinstance(target, Box):
                return describe_box_contents(target)
            return "You can't look inside that."

        # 3. LOOK AT ROOM
        if isinstance(target, Room):
            return describe_room(room)


        # 5. LOOK AT ITEM
        if isinstance(target, Item):
            return describe_item_look(target)

        # 6. LOOK AT BOX
        if isinstance(target, Box):
            return describe_box_contents(target)

        return "You don't see that here."


    def _describe_room(self, room: Room) -> str:

        if room is None:
            return "You are nowhere."

        if _is_dark_room(room):
            return _dark_room_message(room)
        
        exits = room.available_directions(visible_only=True)
        visible_text = [obj.get_presence_text() for obj in [*room.items, *room.boxes]]
        exits_text = _build_visible_exits_text(exits)
        long_description = room.description.strip() if room.description else room.name
        
        return f"{long_description} {exits_text}"


    def _is_dark_room(room: Room) -> bool:
        return getattr(room, "is_dark", False)  






# future commands history, help, etc. could be added here
