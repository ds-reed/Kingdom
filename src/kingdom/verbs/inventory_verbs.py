# inventory Verbs

from kingdom.model.noun_model import Noun, Item, Container, Room, World, Player
from kingdom.verbs.verb_handler import VerbHandler, VerbControl, ExecuteCommand

class InventoryVerbHandler(VerbHandler):
    def inventory(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
        **kwargs
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
        **kwargs
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


            for item in room.items:
                getable.append(item)

            # Items in open containers
            for container in room.containers:
                if container.is_openable and container.is_open:
                    for item in container.contents:
                        getable.append(item)
                else:
                    getable.append(container)  # if container isn't open, we still try to take it and let the refusal message come from the container's special handler

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
        if loc.type == self.LocationType.INVENTORY:
            return self.build_message(f"You already have {target.display_name()}.")

        # ------------------------------------------------------------
        # 5. If it's here but not gettable
        # ------------------------------------------------------------
        if not getattr(target, "is_gettable", True) \
                    or isinstance(target, Container):  #can't take containers for now
            refuse = getattr(target, "get_refuse_string", None)
            return self.build_message(refuse or f"You can't take {target.display_name()}.")

        # ------------------------------------------------------------
        # 7. Take from room
        # ------------------------------------------------------------
        if loc.type is self.LocationType.ROOM_FLOOR:
            room.remove_item(target)
            player.add_to_sack(target)
            return self.build_message(f"You take {target.display_name()}.")

        # ------------------------------------------------------------
        # 8. Take from open container
        # ------------------------------------------------------------
        if loc.type is self.LocationType.INSIDE_CONTAINER:
            # Find the container again (loc.container should have it)
            found_container = loc.container
            found_container.remove_item(target)
            player.add_to_sack(target)
            return self.build_message(
                f"You take {target.display_name()} "
                f"from {found_container.display_name()}."
            )

        # ------------------------------------------------------------
        # 9. Should never reach here
        # ------------------------------------------------------------
        return self.build_message("DEBUG: Take says I don't know how to do that.")


    def drop(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
        **kwargs
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
        if loc.type != self.LocationType.INVENTORY:
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


    def put(self, target, words, cmd: ExecuteCommand = None):
        player = self.player()
        room = self.room()

        # 1. Destination

        dest_target = next((pp["object"] for pp in cmd.prep_phrases if pp["prep"] == "into"), None)
        dest = dest_target.noun_object if dest_target else None

        if dest is None:
            return self.build_message("Put where?")

        if not isinstance(dest, Container):
            return self.build_message(f"You can't put things into {dest.display_name()}.")

        if dest.is_openable and not dest.is_open:
            return self.build_message(f"{dest.display_name().capitalize()} is closed.")

        # 2. Direct objects
        if not cmd.direct_objects:
            return self.build_message("Put what?")

        msgs = []

        for obj in [cmd.direct_objects]:                                            # furture preparation for multiple direct objects, currently cmd.direct_objects is a single noun_object due to stage 3 parser limitations
            if obj not in player.get_inventory_items():
                msgs.append(f"You're not carrying {obj.display_name()}.")
                continue

            if not getattr(obj, "is_gettable", True):
                msgs.append(f"You can't move {obj.display_name()}.")
                continue

            player.remove_from_sack(obj)
            dest.add_item(obj)
            msgs.append(f"You put {obj.display_name()} into {dest.display_name()}.")

        return self.build_message(" ".join(msgs))
