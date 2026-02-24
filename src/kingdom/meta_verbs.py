# meta verbs for help and the like

from kingdom.models import DispatchContext, Noun, Verb, DispatchContext

class MetaVerbHandler:
    
    def DEBUG(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()) -> str:
        print(f"DEBUG: DispatchContext: {ctx}, \n\ntarget: {target}, \n\nwords: {words}")
        if target is None and words and words[0] == "room":
            if(ctx.state.current_room is None):
                return "No current room."
            print(f"DEBUG: Current room: {ctx.state.current_room.get_noun_name() }")
            return self.debug_noun(ctx.state.current_room)
        elif target is None and words and words[0] == "player":
            if getattr(ctx.game, "current_player", None) is None:
                return "No current player."
            print("DEBUG: Current player:", getattr(ctx.game, "current_player", None))
            return self.debug_noun(getattr(ctx.game, "current_player", None))
        else:
            return self.debug_noun(target)
    
    def debug_noun(self, noun: Noun):
        if noun is None:
            return "No target noun was passed."

        lines = []
        lines.append(f"id: {id(noun)}")  # ⭐ Add instance identity

        for k, v in vars(noun).items():
            lines.append(f"{k}: {v!r}")

        return "\n".join(lines)



    def help(self, ctx: DispatchContext, target: Noun | None, words:tuple[str, ...] = () ):
        if not words:
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
                "  - help"
            )
        elif words[0] in ("commands", "verbs"): 
            names = {
                    verb.verb
                    for verb in Verb.all_verbs
                    if not verb.hidden
                }
            parts = sorted(names)
            return "Available commands: " + ", ".join(parts)
        else:
            return "Help is not available for that topic."

