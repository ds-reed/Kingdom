# meta verbs for help and the like

from kingdom.models import DispatchContext, Noun, Verb, DispatchContext

class MetaVerbHandler:
    
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

