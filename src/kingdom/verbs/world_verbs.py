# world verbs: look, score, etc. - things that primarily interact with the world state rather than player inventory or UI


from typing import Sequence

from kingdom.models import Game, Noun, Room, Box, Item, Verb, DispatchContext
from kingdom.renderer import RoomRenderer, render_current_room

class WorldVerbHandler:
 
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



    def score(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        game = ctx.game
        if game is None:
            return "Score is unavailable."
        return f"Your current score is: {game.score}"   
    

    def look(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        if words and words[0] in ("inside", "in"):
            if target is None:
                return "Look inside what?"
            renderer = RoomRenderer()
            if isinstance(target, Box):
                return renderer.describe_box_contents(target)
            return f"You can't look inside the {target.get_noun_name()}."

        # Render the room description and contents
        render_current_room(ctx.game.state)
        return  


    # future commands history, help, etc. could be added here
