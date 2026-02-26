# inventory Verbs

from kingdom.models import DispatchContext, Noun, Verb, Item, Box
from kingdom.verbs.verb_handler import VerbHandler

class InventoryVerbHandler(VerbHandler):
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
            return "DEBUG: player missing sack."

        contents = sack.contents
        if not contents:
            return f"You don't have anything."

        names = [item.display_name() for item in contents]

        count = len(names)
        label = "item" if count == 1 else "items"

        return (
            f"You have ({count} {label}): "
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
        # 1. TAKE ALL (use the base-class ALL handler)
        # ------------------------------------------------------------
        if target is None and "all" in words:
            getable: list[Item] = []

            # Items on floor
            for item in room.items:
                if getattr(item, "is_gettable", True):
                    getable.append(item)

            # Items in open boxes
            for box in room.boxes:
                if box.is_openable and box.is_open:
                    for item in box.contents:
                        if getattr(item, "is_gettable", True):
                            getable.append(item)

            return self.handle_all(ctx, getable, self.take, "take")

        # ------------------------------------------------------------
        # 2. Missing target
        # ------------------------------------------------------------
        if target is None and not words:
            return self.missing_target("take")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome = self.run_special_handler(target, "take", words, ctx)
        if outcome is not None:
            return outcome

        # ------------------------------------------------------------
        # 4. Already in inventory
        # ------------------------------------------------------------
        if player.has_item(target):
            return f"You already have {target.display_name()}."

        # ------------------------------------------------------------
        # 5. Determine where the item is
        # ------------------------------------------------------------
        location = self.find_item_location(ctx, target)

        # Not in room, not in inventory, not in any open box
        if location is None:
            name = self.resolve_noun_or_word(target, words)
            if name:
                return f"I see no {name} here."
            return self.missing_target("take")

        # ------------------------------------------------------------
        # 6. If it's here but not gettable
        # ------------------------------------------------------------
        if not getattr(target, "is_gettable", True) or isinstance(target, Box):
            refuse = getattr(target, "get_refuse_string", None)
            return refuse or f"You can't take {target.display_name()}."

        # ------------------------------------------------------------
        # 7. Take from room
        # ------------------------------------------------------------
        if location == "room":
            room.remove_item(target)
            player.add_to_sack(target)
            return f"You take {target.display_name()}."

        # ------------------------------------------------------------
        # 8. Take from open box
        # ------------------------------------------------------------
        if location == "box":
            # Find the box again (find_item_location doesn't return it)
            found_box = next(
                box for box in room.boxes
                if box.is_openable and box.is_open and target in box.contents
            )
            found_box.remove_item(target)
            player.add_to_sack(target)
            return (
                f"You take {target.display_name()} "
                f"from {found_box.display_name()}."
            )

        # ------------------------------------------------------------
        # 9. Should never reach here
        # ------------------------------------------------------------
        return "DEBUG: Take says I don't know how to do that."


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
            return self.handle_all(ctx, inventory_items, self.drop, "drop")

        # ------------------------------------------------------------
        # 2. Missing target
        # ------------------------------------------------------------
        if target is None and not words:
            return self.missing_target("drop")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome = self.run_special_handler(target, "drop", words, ctx)
        if outcome is not None:
            return outcome

        # ------------------------------------------------------------
        # 4. Determine where the item is
        # ------------------------------------------------------------
        location = self.find_item_location(ctx, target)

        # Not in inventory
        if location != "inventory":
            name = self.resolve_noun_or_word(target, words)
            if name:
                return f"You aren't carrying {name}."
            return self.missing_target("drop")

        # ------------------------------------------------------------
        # 5. Perform the drop
        # ------------------------------------------------------------
        player.remove_from_sack(target)
        room.add_item(target)
        return f"You drop {target.display_name()}."
