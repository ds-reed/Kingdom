# inventory Verbs

from kingdom.actions import Verb
from kingdom.models import DispatchContext, Noun, Item, Box

class InventoryVerbHandler:
    def inventory(
        self,
        ctx: DispatchContext,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        player = ctx.game.current_player
        if not player:
            return "No current player."

        sack = getattr(player, "sack", None)
        if sack is None:
            return "You have no inventory."

        contents = sack.contents
        if not contents:
            return f"{player.name}'s sack is empty."

        # Use full descriptive names
        names = [item.name for item in contents]

        count = len(names)
        label = "item" if count == 1 else "items"

        return (
            f"{player.name}'s sack contains ({count} {label}): "
            f"{', '.join(names)}"
        )

    def take(
        self,
        ctx: DispatchContext,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        state = ctx.state
        game = ctx.game
        room = state.current_room
        player = game.current_player

        # ------------------------------------------------------------
        # 1. Take ALL
        # ------------------------------------------------------------
        if target is None and "all" in words:
            # Collect all pickupable items in room or open boxes
            pickupable: list[Item] = []

            # Items on floor
            for item in room.items:
                if getattr(item, "is_gettable", True):
                    pickupable.append(item)

            # Items in open boxes
            for box in room.boxes:
                if box.is_openable and box.is_open:
                    for item in box.contents:
                        if getattr(item, "is_gettable", True):
                            pickupable.append(item)

            if not pickupable:
                return "There is nothing here you can take."

            taken_names: list[str] = []
            messages: list[str] = []

            # Take each item using the single-item path
            for item in list(pickupable):
                result = self.take(ctx, target=item, words=("all",))
                if result:
                    messages.append(result)
                taken_names.append(item.get_noun_name())

            # Summary line
            summary = (
                f"{player.name} takes {len(taken_names)} "
                f"item{'s' if len(taken_names) != 1 else ''}: "
                f"{', '.join(taken_names)}."
            )

            return "\n".join(messages + [summary])

        # ------------------------------------------------------------
        # 2. Normal Take (single item)
        # ------------------------------------------------------------
        if target is None:
            return "What do you want to take?"

        # Already in inventory
        if target in player.sack.contents:
            return f"You already have the {target.get_noun_name()}."

        # Is it in the room?
        in_room = target in room.items

        # Is it in an open box?
        found_box = next(
            (
                box
                for box in room.boxes
                if box.is_openable and box.is_open and target in box.contents
            ),
            None,
        )

        # If it's here but not gettable
        if in_room or found_box:
            if not getattr(target, "is_gettable", True):
                refuse = getattr(target, "get_refuse_string", None)
                return refuse or f"You can't take the {target.get_noun_name()}."

        # Take from room
        if in_room:
            room.items.remove(target)
            player.sack.contents.append(target)
            return f"You take the {target.get_noun_name()}."

        # Take from open box
        if found_box:
            found_box.contents.remove(target)
            player.sack.contents.append(target)
            return (
                f"You take the {target.get_noun_name()} "
                f"from the {found_box.get_noun_name()}."
            )

        return "You don't see that here."



    def drop(
        self,
        ctx: DispatchContext,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        state = ctx.state
        game = ctx.game
        room = state.current_room
        player = game.current_player

        # ------------------------------------------------------------
        # 1. DROP ALL
        # ------------------------------------------------------------
        if target is None and "all" in words:
            inventory_items = list(player.sack.contents)

            if not inventory_items:
                return "You aren't carrying anything."

            dropped_names: list[str] = []
            messages: list[str] = []

            # Drop each item using the single-item path
            for item in inventory_items:
                result = self.drop(ctx, target=item, words=("all",))
                if result:
                    messages.append(result)
                dropped_names.append(item.get_noun_name())

            # Summary line
            summary = (
                f"{player.name} drops {len(dropped_names)} "
                f"item{'s' if len(dropped_names) != 1 else ''}: "
                f"{', '.join(dropped_names)}."
            )

            return "\n".join(messages + [summary])

        # ------------------------------------------------------------
        # 2. Normal DROP (single item)
        # ------------------------------------------------------------
        if target is None:
            return "What do you want to drop?"

        # Must be an item
        if not isinstance(target, Item):
            return f"You can't drop the {target.get_noun_name()}."

        # Not in inventory
        if target not in player.sack.contents:
            return f"You aren't carrying the {target.get_noun_name()}."

        # Perform the drop
        player.sack.contents.remove(target)
        room.items.append(target)

        return f"You drop the {target.get_noun_name()}."

