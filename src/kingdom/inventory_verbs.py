# inventory Verbs

from kingdom.actions import Verb
from kingdom.models import DispatchContext, Item, Noun

class InventoryVerbHandler:
    def inventory(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        player = ctx.game.current_player
        if not player:
            return "No current player."

        sack = getattr(player, "sack", None)
        if sack is None:
            return "You have no inventory."

        contents = sack.contents
        if not contents:
            return "Your inventory is empty."

        lines = ["You are carrying:"]
        for item in contents:
            lines.append(f"- {item.get_noun_name()}")
        return "\n".join(lines)
    
    def take(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        room = ctx.state.current_room
        player = ctx.game.current_player

        # No target
        if target is None:
            return "Take what?"

        # Must be an item
        if not isinstance(target, Item):
            return f"You can't take the {target.get_noun_name()}."

        # Already in inventory
        if target in player.sack.contents:
            return f"You already have the {target.get_noun_name()}."

        # Item in room?
        if target in room.items:
            room.items.remove(target)
            player.sack.contents.append(target)
            return f"You take the {target.get_noun_name()}."

        # Item in an open box?
        for box in room.boxes:
            if box.is_openable and not box.is_open:
                continue
            if target in box.contents:
                box.contents.remove(target)
                player.sack.contents.append(target)
                return f"You take the {target.get_noun_name()} from the {box.get_noun_name()}."

        return "You don't see that here."


    def drop(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        room = ctx.state.current_room
        player = ctx.game.current_player

        # No target
        if target is None:
            return "Drop what?"

        # Must be an item
        if not isinstance(target, Item):
            return f"You can't drop the {target.get_noun_name()}."

        # Not in inventory
        if target not in player.sack.contents:
            return f"You aren't carrying the {target.get_noun_name()}."

        # Drop it
        player.sack.contents.remove(target)
        room.items.append(target)
        return f"You drop the {target.get_noun_name()}."

