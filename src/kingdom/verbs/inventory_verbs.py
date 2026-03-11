# inventory Verbs

from kingdom.model.noun_model import Noun, Item, Container
from kingdom.verbs.verb_handler import VerbHandler, VerbControl, ExecuteCommand, VerbOutcome
from kingdom.item_behaviors import try_item_special_handler

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
        cmd: ExecuteCommand = None
    ) -> str:
        
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers
        target = cmd.direct_object

        source, source_name = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, prep=("from", "in"))
        

        if target:
            if target.get_class_name() == "Item":
                inventory_items = [target]
            elif target.get_class_name() == "Container":
                return self.build_message(f"You can't take {target.display_name()} - taking containers not yet implemented.")
        elif "all" in keywords or "everything" in keywords:
            if source:
                if isinstance(source, Container):
                    inventory_items = source.all_items()
                else:
                    return self.build_message(f"You don't see any {source_name} here to take from.")
            else:
                inventory_items = room.all_items()
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
            if hasattr(item, "is_takeable") and not item.is_takeable:
                msgs.append(item.get_refuse_string or f"You can't take {item.display_name()}.")
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

        if target and target.get_class_name() == "Item":
            inventory_items = [target] 
        elif "all" in keywords or "everything" in keywords:
            inventory_items = player.get_inventory_items()
        else:
            if not cmd.direct_object_token:
                return self.build_message(self.missing_target(cmd.verb_token))
            return self.build_message(f"You have no {cmd.direct_object_token}.")

        msgs = []
        for item in inventory_items:
            outcome = try_item_special_handler(item, "drop", words)
            if outcome:
                msgs.append(outcome.message or "")
                if outcome.control == VerbControl.STOP: 
                    return self.build_message(msgs)
                if outcome.control == VerbControl.SKIP:
                    continue

            player.drop_item_to_room(item, room)
            msgs.append(f"You {cmd.verb_token} {item.display_name()}.")

        return self.build_message(msgs)


    def put(self, target, words, cmd: ExecuteCommand = None):
        player = self.player()

        # 1. Destination
        print("put cmd.prep_phrases:", cmd.prep_phrases)
        dest, dest_name = self.extract_indirect_from_prep_phrases(cmd.prep_phrases, prep=("into"))

        if dest is None:
            if dest_name:
                return self.build_message(f"You don't see any {dest_name} here.")
            return self.build_message("Put where?")

        if not isinstance(dest, Container):
            return self.build_message(f"You can't put things into {dest.display_name()}.")

        if dest.is_openable and not dest.is_open:
            return self.build_message(f"{dest.display_name().capitalize()} is closed.")

        # 2. Direct objects
        if not cmd.direct_object:
            return self.build_message("Put what?")

        msgs = []

        target = cmd.direct_object if cmd.direct_object else None                                        
        if target not in player.get_inventory_items():
            return(f"You're not carrying {target.display_name()}.")  

        outcome = try_item_special_handler(target, "put", [dest.handle])        # special handers expecting list of words, so pass the handle of the destination as a single word in a list

        if outcome: 
                msgs.append( outcome.message or "")
                if outcome.control == VerbControl.STOP:
                    return self.build_message(msgs)
        if not outcome or outcome.control != VerbControl.SKIP:
            container_full_msg = player.put_item_into_container(target, dest)
            if container_full_msg:
                msgs.append(container_full_msg)
            else:
                msgs.append(f"You put {target.display_name()} into {dest.display_name()}.")

        return self.build_message(msgs)
