# inventory Verbs

from kingdom.model.noun_model import Noun, Item, Container
from kingdom.verbs.verb_handler import VerbHandler, VerbControl, ExecuteCommand, VerbOutcome
from kingdom.item_behaviors import try_item_special_handler

class InventoryVerbHandler(VerbHandler):
    def inventory(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
        cmd: ExecuteCommand = None
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
        cmd: ExecuteCommand = None
    ) -> str:
        
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers
        target = cmd.direct_object

        source, source_name, prep = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, preps=("in", "from"))

        if target:
            if target.get_class_name() == "Item":
                if player.has_item(target):
                    return(self.build_message(f"You already have {target.display_name()}."))
                inventory_items = [target]
                if getattr(target, "current_container", None):
                    source = target.current_container
            elif target.get_class_name() == "Container":
                return self.build_message(f"You can't take {target.display_name()} - taking containers not yet implemented.")    # todo some day..
        elif "all" in keywords or "everything" in keywords:
            if source:
                if isinstance(source, Container):
                    if getattr(source, "is_openable", False) and not getattr(source, "is_open", False):
                        return self.build_message(f"{source.display_name().capitalize()} is closed.")
                    inventory_items = [item for item in source.all_items() if getattr(item, "is_visible", True)]
                    if not inventory_items:
                        return self.build_message(f"The {source.display_name()} is empty.")
                else:
                    return self.build_message(f"You don't see any {source_name} here to take from.")
            else:
                inventory_items = [item for item in room.all_items() if getattr(item, "is_visible", True)]
        else:
            if not cmd.direct_object_token:
                return self.build_message(self.missing_target(cmd.verb_token))
            return self.build_message(f"You see no {cmd.direct_object_token} here.")

        msgs = []
        for item in inventory_items:
            outcome = try_item_special_handler(item, "take", words)
            if outcome:
                msgs.append(outcome.message or "")
                if outcome.control == VerbControl.STOP: 
                    return self.build_message(msgs)
                if outcome.control == VerbControl.SKIP:
                    continue
            if not getattr(item, "is_takeable", True):  # if the item is not takeable, either by default or explicitly, refuse the take action. 
                refuse = item.take_refuse_string or f"You can't {cmd.verb_token} {item.display_name()}."
                msgs.append(refuse)
                continue

            if source:
                sack_full_msg=player.take_item_from_container(item, source)
            else:
                sack_full_msg=player.take_item_from_room(item, room)
            if not sack_full_msg:
                msgs.append(f"You {cmd.verb_token} {item.display_name()}.")
            else:
                msgs.append(sack_full_msg)

        return self.build_message(msgs)


    def drop(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
        cmd: ExecuteCommand = None
    ) -> str:
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers
        target = cmd.direct_object
        target_token = cmd.direct_object_token
        words = []
        dest_handle = None

        dest, dest_name, prep = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, preps=("into", "in"))

        if target and target.get_class_name() == "Item" and player.has_item(target):
            inventory_items = [target] 
        elif "all" in keywords or "everything" in keywords:
            inventory_items = player.get_inventory_items()
            if not inventory_items:
                return self.build_message("You don't have anything!")
        else:
            if not cmd.direct_object_token:
                return self.build_message(self.missing_target(cmd.verb_token))
            return self.build_message(f"You have no {cmd.direct_object_token}.")
        

        if dest is None and dest_name != "room":
            if dest_name:
                return self.build_message(f"You don't see any {dest_name} here.")
            else:
                return self.build_message(self.missing_target(f"{cmd.verb_token} {target_token} {prep}"))
        
        if dest:
            if dest.get_class_name() != "Container":
                return self.build_message(f"You can't put things into {dest.display_name()}.")

            if getattr(dest, "is_openable", False) and not getattr(dest, "is_open", False):
                return self.build_message(f"{dest.display_name().capitalize()} is closed.")
            dest_handle = [dest.handle]


        msgs = []
        for item in inventory_items:
            outcome = try_item_special_handler(item, "drop", dest_handle)   # for drop with a destination, we pass the destination handle as context to the special handler
            if outcome:
                msgs.append(outcome.message or "")
                if outcome.control == VerbControl.STOP: 
                    return self.build_message(msgs)
                if outcome.control == VerbControl.SKIP:
                    continue

            if dest:
                container_full_msg = player.put_item_into_container(item, dest)
                if container_full_msg:
                    msgs.append(container_full_msg)
                else:
                    msgs.append(f"You put {item.display_name()} into {dest.display_name()}.")
            else:
                player.drop_item_to_room(item, room)
                msgs.append(f"You {cmd.verb_token} {item.display_name()} into the room.")

        return self.build_message(msgs)
