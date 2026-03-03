# meta verbs include things like HELP and DEBUG that don't interact in any way with the world state. I may consolidate this later  

from unittest import result

from kingdom.model.models import Noun, QuitGame, SaveGame, LoadGame, GameOver
from kingdom.verbs.verb_handler import VerbHandler
from kingdom.model.verb_model import Verb

class MetaVerbHandler(VerbHandler):


    def load(self, target: Noun | None, words: tuple[str, ...] = ()):
        raise LoadGame() 

    def save(self, target: Noun | None, words: tuple[str, ...] = ()):
        raise SaveGame()

    def quit(self, target: Noun | None, words: tuple[str, ...] = ()):
        raise QuitGame()

    def die(self, target: Noun | None, words: tuple[str, ...] = ()):
        raise GameOver("You have met an untimely demise.")

    # ------------------------------------------------------------
    # DEBUG
    # ------------------------------------------------------------
    def DEBUG(self, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        # Resolve either a noun or keywords of interest
        parse = self.resolve_noun_or_word(
            words,
            interest=["room", "player", "Verbs", "commands", "all"]
        )
        noun = parse["noun"]
        keywords = parse["keywords"]
        
        def debug_noun(noun: Noun | None) -> str:
            lines = []
            lines.append(f"id: {id(noun)}\n")
            lines.append(f"class: {noun.__class__.__name__}\n")

            # Dump attributes
            for k, v in vars(noun).items():
                lines.append(f"{k}: {v!r}\n")

            return lines

        def debug_words(words: tuple[str, ...]) -> str:

            lines = ["debugging words..."]

            for word in words:
                matching_nouns = [noun for noun in Noun.all_nouns if noun.canonical_name()== word]

                for noun in matching_nouns:
                    lines.append(f"id: {id(noun)}\n")
                    lines.append(f"class: {noun.__class__.__name__}\n")
                    for k, v in vars(noun).items():
                        lines.append(f"{k}: {v!r}\n")

            return lines

        # Case 1: Keywords found in leftover words
        keywords = parse["keywords"]

        if keywords:
            if "room" in keywords or "all" in keywords:
                room = self.room()
                print("debugging current room...")
                return_msg = "No current room." if room is None else debug_noun(room)
                print(*return_msg)

            if "player" in keywords or "all" in keywords:
                player = self.player()
                print("debugging current player...")
                return_msg = "No current player." if player is None else debug_noun(player)
                print(*return_msg)
            
            if "verbs" in keywords or "commands" in keywords or "all" in keywords:
                print("debugging all verbs...")
                print(Verb.all_verbs)
            return 

        # Case 2: use target noun if present; try parser-resolved noun if not
        if target is None: target = noun
        
        if target is not None:
            return self.build_message(debug_noun(target))

        # Case 3: No noun, no keywords → debug raw words
        return self.build_message(debug_words(parse["raw"]))


    # ------------------------------------------------------------
    # HELP
    # ------------------------------------------------------------
    def help(self, target: Noun | None, words: tuple[str, ...] = ()) -> str:
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
        words: tuple[str, ...] = ()
    ) -> str:
        state = self.state()
        return self.build_message(f"Your current score is: {state.score}")


