# inventory Verbs

from kingdom.models import Noun, Item, Box, Room, Game, Player, LocationType
from kingdom.verbs.verb_handler import VerbHandler, VerbControl

class InventoryVerbHandler(VerbHandler):
    def inventory(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        player = self.player()
        inventory = player.get_inventory_items()

        if not inventory:
            return self.build_message("You don't have anything.")

        names = [item.display_name() for item in inventory]

        count = len(names)
        label = "item" if count == 1 else "items"

        return self.build_message(
            f"You have ({count} {label}): "
            f"{', '.join(names)}"
        )


    def take(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        

        state = self.state()
        game = self.game()  
        room = self.room()
        player = self.player()

        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]

        # ------------------------------------------------------------
        # 1. TAKE ALL 
        # ------------------------------------------------------------
        if target is None and ("all" in keywords or "everything" in keywords):     #target is none check to prevent recursive calls in all loop
            getable: list[Item] = []

            # Items on floor - need a function in the room class to get all gettable items to handle boxes and other containers in the future
            for item in room.items:
                getable.append(item)

            # Items in open boxes - need a function in the room class to get all gettable items to handle nested boxes and other containers in the future
            for box in room.boxes:
                if box.is_openable and box.is_open:
                    for item in box.contents:
                        getable.append(item)
                else:
                    getable.append(box)  # if box isn't open, we still try to take it and let the refusal message come from the box's special handler

            return self.handle_all(getable, self.take, "take")
        
        # ------------------------------------------------------------
        # 2. Missing target
        # ------------------------------------------------------------
        if target is None:
                return self.build_message(self.missing_target("take"))
   
        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------

        outcome = self.run_special_handler(target, "take", words)
        if outcome and outcome.control in (VerbControl.STOP, VerbControl.SKIP):
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Determine if item is already in inventory
        # ------------------------------------------------------------
        loc = self.locate_item(target)
        if loc.type == LocationType.INVENTORY:
            return self.build_message(f"You already have {target.display_name()}.")

        # ------------------------------------------------------------
        # 5. If it's here but not gettable
        # ------------------------------------------------------------
        if not getattr(target, "is_gettable", True) \
                    or isinstance(target, Box):  #can't take boxes for now
            refuse = getattr(target, "get_refuse_string", None)
            return self.build_message(refuse or f"You can't take {target.display_name()}.")

        # ------------------------------------------------------------
        # 7. Take from room
        # ------------------------------------------------------------
        if loc.type is LocationType.ROOM_FLOOR:
            room.remove_item(target)
            player.add_to_sack(target)
            return self.build_message(f"You take {target.display_name()}.")

        # ------------------------------------------------------------
        # 8. Take from open box
        # ------------------------------------------------------------
        if loc.type is LocationType.INSIDE_BOX:
            # Find the box again (loc.container should have it)
            found_box = loc.container
            found_box.remove_item(target)
            player.add_to_sack(target)
            return self.build_message(
                f"You take {target.display_name()} "
                f"from {found_box.display_name()}."
            )

        # ------------------------------------------------------------
        # 9. Should never reach here
        # ------------------------------------------------------------
        return self.build_message("DEBUG: Take says I don't know how to do that.")


    def drop(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
    ) -> str:
        state = self.state()
        game = self.game()
        room = self.room()
        player = self.player()

        parse = self.resolve_noun_or_word(words, interest=['all', 'everything'])
        keywords = parse["keywords"]

        # ------------------------------------------------------------
        # 1. DROP ALL
        # ------------------------------------------------------------
        if target is None and ("all" in keywords or "everything" in keywords):     #target is none check to prevent recursive calls in all loop
            inventory_items = player.get_inventory_items()
            return self.handle_all(inventory_items, self.drop, "drop")

        # ------------------------------------------------------------
        # 2. Missing target
        # ------------------------------------------------------------
        if target is None:
            if not words:
                return self.build_message(self.missing_target("drop"))
            return self.build_message(f"You have no {' '.join(words)}.")

        # ------------------------------------------------------------
        # 3. Special handler pipeline
        # ------------------------------------------------------------
        outcome = self.run_special_handler(target, "drop", words)
        if outcome: 
            return self.build_message(outcome.message or "")

        # ------------------------------------------------------------
        # 4. Determine where the item is
        # ------------------------------------------------------------
        loc = self.locate_item(target)

        # Not in inventory
        if loc.type != LocationType.INVENTORY:
            name = target.display_name()
            if name:
                return self.build_message(f"You aren't carrying {name}.")
            return self.build_message(self.missing_target("drop"))

        # ------------------------------------------------------------
        # 5. Perform the drop
        # ------------------------------------------------------------
        player.remove_from_sack(target)
        room.add_item(target)
        return self.build_message(f"You drop {target.display_name()}.")
