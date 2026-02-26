# meta verbs include things like HELP and DEBUG that don't interact in any way with the world state. I may consolidate this later  

from kingdom.models import DispatchContext, Noun, Verb
from kingdom.verbs.verb_handler import VerbHandler

class MetaVerbHandler(VerbHandler):

    # ------------------------------------------------------------
    # DEBUG
    # ------------------------------------------------------------
    def DEBUG(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
       


        # Special cases: room / player
        if target is None and words:
            if words[0] == "room":
                room = ctx.state.current_room
                if room is None:
                    return "No current room."
                return self.debug_noun(room)

            if words[0] == "player":
                player = getattr(ctx.game, "current_player", None)
                if player is None:
                    return "No current player."
                return self.debug_noun(player)
            
            else:
                return self.debug_words(words)

        # Default: debug the noun passed
        return self.debug_noun(target)

    def debug_noun(self, noun: Noun | None) -> str:
        if noun is None:
            return "No target noun was passed."

        lines = []
        lines.append(f"id: {id(noun)}")
        lines.append(f"class: {noun.__class__.__name__}")

        # Dump attributes
        for k, v in vars(noun).items():
            lines.append(f"{k}: {v!r}")

        return "\n".join(lines)

    def debug_words(self, words: tuple[str, ...]) -> str:
        print(f"DEBUGGING WORDS: {words}")

        lines = []

        for word in words:
            matching_nouns = [noun for noun in Noun.all_nouns if noun.get_noun_name() == word]

            for noun in matching_nouns:
                lines.append(f"id: {id(noun)}")
                lines.append(f"class: {noun.__class__.__name__}")
                for k, v in vars(noun).items():
                    lines.append(f"{k}: {v!r}")

        return "\n".join(lines)

    # ------------------------------------------------------------
    # HELP
    # ------------------------------------------------------------
    def help(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        # No topic: show general help
        if not words:
            return self.default_help_text()

        topic = words[0]

        # "help commands" or "help verbs"
        if topic in ("commands", "verbs", "all"):
            return self.list_all_verbs()

        return f"Help is not available for '{topic}'."

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def default_help_text(self) -> str:
        return (
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
            "Type 'help commands' to see all available verbs."
        )

    def list_all_verbs(self) -> str:
        names = {
            verb.name
            for verb in Verb.all_verbs
            if not verb.hidden
        }
        parts = sorted(names)
        return "Available commands: " + ", ".join(parts)


    # ------------------------------------------------------------
    # SCORE
    # ------------------------------------------------------------
    def score(
        self,
        ctx: DispatchContext,
        target: Noun | None,
        words: tuple[str, ...] = ()
    ) -> str:
        game = ctx.game
        if game is None:
            return "Score is unavailable."
        return f"Your current score is: {game.score}"


