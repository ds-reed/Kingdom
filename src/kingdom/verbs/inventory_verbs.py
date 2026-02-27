# inventory Verbs

from kingdom.models import DispatchContext, Noun, Verb, Item, Box, Room, Game, Player, LocationType
from kingdom.verbs.verb_handler import VerbHandler

class InventoryVerbHandler(VerbHandler):
    def inventory(
        self,
        ctx: DispatchContext,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        player = self.player(ctx)
        if not player:
            return "DEBUG: No current player."

        contents = player.get_inventory_items()
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
        state = self.state(ctx)
        game = self.game(ctx)  
        room = self.room(ctx)
        player = self.player(ctx)

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
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return outcome.message or ""

        # ------------------------------------------------------------
        # 4. Determine where item is 
        # ------------------------------------------------------------
        loc = self.locate_item(ctx, target)
        # Not in room, not in inventory, not in any open box
        if loc is None:
            name = self.resolve_noun_or_word(target, words)
            if name:
                return f"I see no {name} here."
            return self.missing_target("take")


        if loc.type == LocationType.INVENTORY:
            return f"You already have {target.display_name()}."

        # ------------------------------------------------------------
        # 6. If it's here but not gettable
        # ------------------------------------------------------------
        if not getattr(target, "is_gettable", True) \
                    or isinstance(target, Box):  #can't take boxes for now
            refuse = getattr(target, "get_refuse_string", None)
            return refuse or f"You can't take {target.display_name()}."

        # ------------------------------------------------------------
        # 7. Take from room
        # ------------------------------------------------------------
        if loc.type is LocationType.ROOM_FLOOR:
            room.remove_item(target)
            player.add_to_sack(target)
            return f"You take {target.display_name()}."

        # ------------------------------------------------------------
        # 8. Take from open box
        # ------------------------------------------------------------
        if loc.type is LocationType.INSIDE_BOX:
            # Find the box again (loc.container should have it)
            found_box = loc.container
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
        state = self.state(ctx)
        game = self.game(ctx)
        room = self.room(ctx)
        player = self.player(ctx)

        # ------------------------------------------------------------
        # 1. DROP ALL
        # ------------------------------------------------------------
        if target is None and "all" in words:
            inventory_items = player.get_inventory_items()
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
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return outcome.message or ""

        # ------------------------------------------------------------
        # 4. Determine where the item is
        # ------------------------------------------------------------
        loc = self.locate_item(ctx, target)

        # Not in inventory
        if loc.type != LocationType.INVENTORY:
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
