# meta verbs include things like HELP and DEBUG that don't interact in any way with the world state. I may consolidate this later  

from kingdom.model.noun_model import Noun, Item, Room, Container, Feature, Player
from kingdom.model.game_init import QuitGame, SaveGame, LoadGame, GameOver
from kingdom.verbs.verb_handler import VerbHandler, ExecuteCommand, VerbOutcome
from kingdom.model.verb_model import Verb

class MetaVerbHandler(VerbHandler):



    def load(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs):
        raise LoadGame() 

    def save(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs):
        raise SaveGame()

    def quit(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs):
        raise QuitGame()

    def die(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs):
        raise GameOver("You have met an untimely demise.")

    # ------------------------------------------------------------
    # DEBUG
    # ------------------------------------------------------------
    def DEBUG(self, target: Noun | None, words: tuple[str, ...] = (), cmd: "ExecuteCommand" = None) -> str:


        def debug_set(noun, field):
            if noun is None:
                return f"No noun found to set {field}."

            if not hasattr(noun, field):
                return f"Noun '{noun.display_name()}' does not have a field named '{field}'."

            current_value = getattr(noun, field)
            new_value = not current_value

            setattr(noun, field, new_value)

            return f"Set {field} of '{noun.display_name()}' to {new_value}."
        
        def debug_noun(noun: Noun | None) -> list[str]:
            if noun is None:
                return ["No target noun was passed."]

            lines = []
            lines.append(f"id: {id(noun)}")
            lines.append(f"class: {noun.get_class_name()}")

            # Special handling for Room objects
            if noun.get_class_name() == "Room":
                for field, value in vars(noun).items():

                    # Summaries for collections of nouns
                    if field in ("items", "containers", "features"):
                        names = [obj.display_name() for obj in value]
                        if names:
                            lines.append(f"{field}:")
                            for name in names:
                                lines.append(f"  - {name}")
                        else:
                            lines.append(f"{field}: []")
                        continue

                    # Summaries for exit dictionaries
                    if field in ("connections", "swim_exits", "climb_exits"):
                        exits = {d: r.name for d, r in value.items()}
                        if exits:
                            lines.append(f"{field}:")
                            for direction, room_name in exits.items():
                                lines.append(f"  {direction}: {room_name}\n")
                        else:
                            lines.append(f"{field}: {{}}\n")
                        continue

                    # Everything else: print raw, one per line
                    lines.append(f"{field}: {value!r}")

                return lines


            # Default behavior for non-Room nouns
            for k, v in vars(noun).items():
                lines.append(f"{k}: {v!r}")

            return lines
        
        def debug_player(player: Player | None) -> list[str]:
            if player is None:
                return ["No current player."]

            lines = []
            lines.append(f"id: {id(player)}")
            lines.append(f"name: {player.name}")
            inventory = player.get_inventory_items()
            if inventory:
                lines.append("Inventory:")
                for item in inventory:
                    lines.append(f"  - {item.display_name()}")
            else:
                lines.append("Inventory: []\n")
            return lines
        

        # Resolve either a noun or keywords of interest

        room = self.room()
        player = self.player()
        noun = None
        keywords = []
        lexicon = self.lexicon()

        if cmd.direct_object:
            noun = cmd.direct_object
        elif cmd.direct_object_token:
            noun = Item.get_by_name(cmd.direct_object_token) or Feature.get_by_name(cmd.direct_object_token) or Container.get_by_name(cmd.direct_object_token)  
            if noun is None:
                keywords = [cmd.direct_object_token]    # if no noun found, treat the noun-like token as a keyword for debugging purposes
        
        if cmd.modifiers is not None:
            keywords.extend(cmd.modifiers)

        # Case 1: Noun

        if noun:
            debug_noun(noun)
            return self.build_message(debug_noun(noun))
        

        # Case 1: Keywords  

        if keywords:
            if "room" in keywords or "all" in keywords:
                lines = ["debugging current room..."]
                return_msg = "No current room." if room is None else debug_noun(room)
                lines.append(return_msg)
                return(self.build_message(lines))

            if "player" in keywords or "all" in keywords:
                lines = ["debugging current player..."]
                return_msg = ["No current player."] if player is None else debug_player(player)
                lines.extend(return_msg)
                return(self.build_message(lines))
            
            if "verbs" in keywords or "commands" in keywords or "all" in keywords:
                lines = ["debugging all verbs..."]
                lines.extend(str(verb) for verb in Verb.all_verbs)
                return(self.build_message(lines))

            if "set" in keywords:
                target_noun = noun if noun is not None else self.room()  # default to current room if no noun specified
                bool_attrs = [
                    name for name, value in vars(target_noun).items()
                    if isinstance(value, bool)
                    ]
                print(f"Boolean fields available to toggle on {target_noun.display_name()}")
                for field in bool_attrs:
                    print(f" - {field} - {getattr(target_noun, field)}")

                field_name: str = input("Enter field to toggle (e.g. 'is_dark'): ").strip()
                debug_set(target_noun, field_name)
                return self.build_message(f"Toggled {field_name} on {target_noun.display_name()}.")

            if "lexicon" in keywords:
                lines = ["debugging lexicon..."]
                lines.append(str(lexicon))
                return self.build_message(lines)

        # Nothing to debug - print message
        lines = ["DEBUG: No keywords found to debug. Try 'debug room', 'debug player', 'debug verbs', or 'debug set'."]
        return self.build_message(lines)


    # ------------------------------------------------------------
    # HELP
    # ------------------------------------------------------------
    def help(self, target: Noun | None, words: tuple[str, ...] = (), **kwargs) -> str:
        # Resolve either a noun or keywords of interest
        result = self.resolve_noun_or_word(
            words,
            interest=["commands", "verbs", "all"]
        )

        keywords = result["keywords"]
        raw = result["raw"]

        def default_help_text() -> str:
            return(
                "You can try commands like:\n"
                "  - look\n"
                "  - go <direction>\n"
                "  - take <item>\n"
                "  - drop <item>\n"
                "  - inventory\n"
                "  - save\n"
                "  - load\n"
                "  - score\n"
                "  - help\n"
                "\n"
                "Type 'help commands' to see all available verbs."
            )

        def help_all_verbs() -> list[str]:
            lines = ["Available commands:"]
            names = {
                verb.name
                for verb in Verb.all_verbs
                if not verb.hidden
            }
            lines.extend(f"  - {name}" for name in sorted(names))
            return lines
        
        # If keywords used: "help commands" or "help verbs"
        if keywords:
            if "commands" in keywords or "verbs" in keywords or "all" in keywords:
                return self.build_message(help_all_verbs())
            else:
                return self.build_message(f"Help is not available for '{' '.join(keywords)}'.")
  
        # Only show for valid target, Don't show for other nouns to avoid spoilers. Can refine with a 'found' flag in the future.
        if target is not None:
            return self.build_message(f"There is no more information available for '{target.display_name()}'.")
     
        # If raw words with no matches are present
        if raw:
            return self.build_message(f"Help is not available for '{' '.join(raw)}'.")
        
        # No noun, no keywords, no raw words → default help text
        return self.build_message(default_help_text())


    # ------------------------------------------------------------
    # SCORE
    # ------------------------------------------------------------
    def score(
        self,
        target: Noun | None,
        words: tuple[str, ...] = (),
        **kwargs    
    ) -> str:
        state = self.state()
        return self.build_message(f"Your current score is: {state.score}")


