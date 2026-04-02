# inventory Verbs

from kingdom.model.noun_model import Noun, Item, Container
from kingdom.engine.verbs.verb_handler import VerbHandler, VerbControl, ExecuteCommand, VerbOutcome
from kingdom.engine.item_behaviors import try_item_special_handler
from kingdom.language.outcomes import CommandOutcome

class InventoryVerbHandler(VerbHandler):
    def inventory(self, cmd: ExecuteCommand = None) -> CommandOutcome:
        player = self.player()
        inventory = player.get_inventory_items()

        if not inventory:
            return self.outcome_not_available(self.build_message("You don't have anything."), code="empty_inventory")

        names = [item.canonical_name() for item in inventory]

        count = len(names)
        label = "item" if count == 1 else "items"

        bullet_list = "\n".join(f"- {name}" for name in names)

        return self.outcome_success(
            self.build_message(
                f"You have ({count} {label}):\n{bullet_list}"
            )
        )

    

    def take(self, cmd: ExecuteCommand = None) -> CommandOutcome:
        
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object if cmd.direct_object else None
        prep_phrases = cmd.prep_phrases if cmd.prep_phrases else []
        direct_object_token = cmd.direct_object_token if cmd.direct_object_token else None
        verb_token = cmd.verb_token if cmd.verb_token else None


        source, source_name, prep = self.extract_indirect_from_prep_phrases(prep_phrases, preps=("in", "from"))

        # TODO: more parsing to do. Need to update interpreter so this can all be simplified
        # this has gotten horifyingly complex and needs to be cleaned up
        # indirect object resolution belongs to the interpreter, not the verbs.
        #
        if source: 
            if not (room.has_container(source) or room.has_item(source)):
                return self.outcome_not_available(f"You don't see any {source_name} here to take from.", code="source_not_here")
            if source.get_class_name() != "Container":
                return self.outcome_invalid_target(f"You can take things from a {source_name}!", code="invalid_source_type")
     
        if not target and direct_object_token and source:             #if we have a noun that wasn't resolved to an object in the room, check if it is in the referenced container.  
            candidate_item = Item.get_by_name(direct_object_token)    #this is the item's object
            if getattr(candidate_item, "is_visible", False):          #if not visible, don't allow taking.
                if getattr(source, "is_open", False):                 # is source container open
                    if candidate_item in source.contents:            # is it in the source container?
                        target = candidate_item

        # Backward-compatible convenience: if source was omitted, allow pulling
        # a single item from the first open room container that contains it.
        if not target and direct_object_token and not source:
            for container in room.containers:
                if getattr(container, "is_openable", False) and not getattr(container, "is_open", False):
                    continue
                candidate_item = container.has_item_by_alias(direct_object_token)
                if candidate_item is not None and getattr(candidate_item, "is_visible", True):
                    source = container
                    source_name = container.obj_handle()
                    target = candidate_item
                    break

        if prep and not source_name:
            return self.outcome_missing_prep_target(
                self.missing_target(f"{verb_token} {direct_object_token} {prep}"),
                code="missing_indirect_target",
            )
        
        if verb_token == "loot":            # loot implies taking everyting from a container, so add "all" modifier if loot is used
            keywords.append("all")
            if not source:                  # looting direct object same as looting from indirect object, e.g. "loot chest" implies "loot all from chest"
                source = target
                target = None
                   
        if target:
            if target.get_class_name() == "Item":
                if player.has_item(target):
                    return self.outcome_no_op(self.build_message(f"You already have {target.display_name()}."), code="already_in_inventory")
                inventory_items = [target]
            elif target.get_class_name() == "Container":
                inventory_items = [target]
            else:
                refuse = getattr(target, "take_refuse_description", None) or f"You can't {verb_token} {target.display_name()}."
                return self.outcome_blocked(self.build_message(refuse), code="target_not_takeable")
        elif "all" in keywords or "everything" in keywords:
            if source:
                if getattr(source, "is_openable", False) and not getattr(source, "is_open", False):
                    return self.outcome_precondition_failed(
                        self.build_message(f"{source.display_name().capitalize()} is closed."),
                        code="source_container_closed",
                    )
                inventory_items = [item for item in source.contents if getattr(item, "is_visible", True)]
                if not inventory_items:
                    return self.outcome_no_op(self.build_message(f"The {source.display_name()} is empty."), code="source_empty")
            else:
                inventory_items = [item for item in room.all_items() if getattr(item, "is_visible", True)]
        else:
            if not direct_object_token:
                return self.outcome_missing_target(self.missing_target(verb_token), code="missing_direct_target")
            return self.outcome_not_available(f"You see no {direct_object_token} here.", code="direct_target_not_here")

        msgs = []
        for item in inventory_items:
            outcome = try_item_special_handler(item, "take", indirect_obj=source if source else None)  # Pass the source handle as context for the special handler
            if outcome:
                msgs.append(outcome.message or "")
                if outcome.control == VerbControl.STOP: 
                    return self.outcome_success(self.build_message(msgs), code="item_handler_stop")
                if outcome.control == VerbControl.SKIP:
                    continue
            if not getattr(item, "is_takeable", True):  # if the item is not takeable, either by default or explicitly, refuse the take action. 
                refuse = item.take_refuse_description or f"You can't {verb_token} {item.display_name()}."
                msgs.append(refuse)
                continue

            if source:
                sack_full_msg=player.take_item_from_container(item, source)
            else:
                sack_full_msg=player.take_item_from_room(item, room)
            if not sack_full_msg:
                msgs.append(f"You {verb_token} {item.display_name()}.")
            else:
                msgs.append(sack_full_msg)

        return self.outcome_success(self.build_message(msgs))


    def drop(self, cmd: ExecuteCommand = None) -> CommandOutcome:
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object = cmd.direct_object if cmd.direct_object else None
        prep_phrases = cmd.prep_phrases = cmd.prep_phrases if cmd.prep_phrases else []

        dest_handle = None
        dest, dest_name, prep = self.extract_indirect_from_prep_phrases(prep_phrases, preps=("into", "in", "onto", "on"))   # for drop, only accept prepositions that imply a destination container or surface. fix this logic when we have lexical nouns like "room" for now, use keywords to allow dropping into room as well.

        if dest: 
            if not room.has_container(dest):
                return self.outcome_not_available(f"You don't see any {dest_name} here to drop into.", code="dest_not_here")
            if dest.get_class_name() != "Container":
                return self.outcome_invalid_target(f"You can't put things into {dest_name}!", code="invalid_dest_type")

        # check constraints for drop with a preposition, e.g. "drop lamp into chest"
        # will return if destination is invalid in any way
        if prep_phrases:
            if not prep:    # preposition found that has unrecognized applicability to "drop" (eg. "drop lamp beneath fish")
                return self.outcome_invalid_target(
                    f"I don't understand how to {cmd.verb_token} {next(iter(prep_phrases))['prep']} things.",
                    code="unsupported_preposition",
                )
            if "room" not in keywords and "down" not in keywords:   # accept room or down (implies room) as a destination and treat like no preposition phrase was given
                if not dest:    # no resolved desination noun object
                    if not dest_name:
                        return self.outcome_missing_prep_target(
                            self.missing_target(f"{cmd.verb_token} {cmd.direct_object_token} {prep}"),
                            code="missing_drop_destination",
                        )
                    else:
                        return self.outcome_not_available(
                            f"You don't see any {dest_name} here to {cmd.verb_token} {prep} things into.",
                            code="drop_destination_not_here",
                        )
                
                if dest.get_class_name() != "Container":    #can't drop torch into fish
                    return self.outcome_invalid_target(
                        f"You can't put things into {dest.display_name()}.",
                        code="drop_destination_invalid",
                    )

                if getattr(dest, "is_openable", False) and not getattr(dest, "is_open", False):
                    return self.outcome_precondition_failed(
                        f"{dest.display_name().capitalize()} is closed.",
                        code="drop_destination_closed",
                    )
                dest_handle = [dest.handle]
                
        # check constraints for drop without a preposition, e.g. "drop lamp"
        if target and target.get_class_name() == "Item" and player.has_item(target):
            inventory_items = [target] 
        elif "all" in keywords or "everything" in keywords:
            inventory_items = player.get_inventory_items()
            if not inventory_items:
                return self.outcome_not_available(self.build_message("You don't have anything!"), code="empty_inventory")
        else:
            if not cmd.direct_object_token:
                return self.outcome_missing_target(self.missing_target(cmd.verb_token), code="missing_direct_target")
            return self.outcome_not_available(f"You have no {cmd.direct_object_token}.", code="not_in_inventory")
        
        # loop on all resolved inventory items to drop
        msgs = []
        for item in inventory_items:
            # check special handlers for each item being dropped. This allows items to have custom drop behavior
            outcome = try_item_special_handler(item, "drop", indirect_obj=dest_handle)  # Pass the destination handle as context for the special handler
            if outcome:
                msgs.append(outcome.message or "")
                if outcome.control == VerbControl.STOP: 
                    return self.outcome_success(self.build_message(msgs), code="item_handler_stop")
                if outcome.control == VerbControl.SKIP:
                    continue
        
            # perform the drop action into destination (room or into container)
            if dest:
                container_full_msg = player.put_item_into_container(item, dest)
                if container_full_msg:
                    msgs.append(container_full_msg)
                else:
                    msgs.append(f"You put {item.display_name()} into {dest.display_name()}.")
            else:
                player.drop_item_to_room(item, room)
                msgs.append(f"You {cmd.verb_token} {item.display_name()} into the room.")

        return self.outcome_success(self.build_message(msgs))
    

    def give(self, cmd: ExecuteCommand = None) -> CommandOutcome:                  #give and trade the same for now. Give implies trade if container accepts trades
        room = self.room()
        player = self.player()

        keywords = cmd.modifiers = cmd.modifiers if cmd.modifiers else []
        target = cmd.direct_object = cmd.direct_object if cmd.direct_object else None
        target_name = cmd.direct_object_token if cmd.direct_object_token else None
        prep_phrases = cmd.prep_phrases = cmd.prep_phrases if cmd.prep_phrases else []
        verb_token = cmd.verb_token if cmd.verb_token else None

        source, source_name, prep = self.extract_indirect_from_prep_phrases(prep_phrases, preps=("to", "with"))
        trade_item, trade_item_name, prep2 = self.extract_indirect_from_prep_phrases(prep_phrases, preps=("for",))   # allow "give fish to mermaid for clam" as well as "trade fish to mermaid for clam"

        msgs = []

        # check various constraints

        if target_name:
            target = Item.get_by_name(target_name)
            if not player.has_item(target):
                return self.outcome_not_available(f"You don't have {target_name} to {verb_token}.", code="give_item_not_owned")
        else:
            return self.outcome_missing_target(self.missing_target(verb_token), code="missing_direct_target")
    
        if not prep:
            if not prep2:
                return self.outcome_missing_target(f"{verb_token} what/to whom?", code="missing_give_targets")    # if just give/trade with no what or to whom
            else:
                for container in room.containers: 
                    tradeable = getattr(container, "is_tradeable", False)                                # is_tradeable here means a container that will trade items with you
                    if tradeable and container.has_item(trade_item):                         # we have a traget and a proposed trade good, so see if there is a container that will trade with has and has it
                        source = container
                        source_name = container.canonical_name()
                        break   

        if not source_name:
            return self.outcome_missing_prep_target(
                self.missing_target(f"{verb_token} {cmd.direct_object_token} {prep}"),
                code="missing_recipient",
            )
        
        if not source:    # if source_name and no source, it means source_name was not found in the room``
            return self.outcome_not_available(
                f"You don't see any {source_name} here to {verb_token} {prep}.",
                code="recipient_not_here",
            )
        
        can_trade = getattr(source, "is_tradeable", False)
        if not can_trade:
            if verb_token == "trade":      # if you say trade specifically, then the target must be tradeable. 
                return self.outcome_blocked(
                    f"{source.canonical_name().capitalize()} doesn't seem interested in trading.",
                    code="recipient_not_tradeable",
                )
            if target and player.has_item(target):        #othewise, it is just a give action
                player.remove_from_sack(target)
                msgs.append(f"You give {target.canonical_name()} to {source.canonical_name()}.")   #later check max items


        # finally, the main trade logic - need to work in the special behaviors still, but lets test and see where we are
        # trade_item_name is set if "for" phrase is used
        # source is set if to/with phrase is used and resolved to a noun object in the room
        # target is set if direct object is resolved to an item in room
        # target_name is availble if a noun was used but wasn't in room
        # later update for dispatch to special handler on all three items involved (source, target, trade_item) 

        if trade_item_name:
            trade_item = Item.get_by_name(trade_item_name)
            if not source.has_item(trade_item):
                msgs.append(f"{source.canonical_name().capitalize()} doesn't have {trade_item_name} to trade with you.")
            elif not player.has_item(target):
                msgs.append(f"You don't have {target.canonical_name()} to trade with {source.canonical_name()}.")
            else:
                # make the trade
                source.remove_item(trade_item)
                player.add_to_sack(trade_item)
                player.remove_from_sack(target)
                source.add_item(target) 
                msgs.append(f"You receive {trade_item.display_name()} from {source.canonical_name()} in exchange for {target.canonical_name()}.")        
        else:
            trade_item = source.contents[0] if getattr(source, "contents", None) else None
            if not trade_item:
                msgs.append(f"{source.canonical_name().capitalize()} doesn't have anything to trade with you.")
            elif not player.has_item(target):
                msgs.append(f"You don't have {target.canonical_name()} to trade with {source.canonical_name()}.")
            else:
                #make the trade
                source.remove_item(trade_item)
                player.add_to_sack(trade_item)
                player.remove_from_sack(target)
                source.add_item(target) 
                msgs.append(f"You receive {trade_item.display_name()} from {source.canonical_name()} in exchange for {target.canonical_name()}.")

        return self.outcome_success(self.build_message(msgs))


    
            

                
        
    
        





