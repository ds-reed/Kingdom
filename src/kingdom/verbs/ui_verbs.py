# ui_verbs.py — handlers for verbs related to UI actions (SAVE, LOAD, QUIT)

from kingdom.models import DispatchContext, Noun, QuitGame, Box
from kingdom.UI import UI
from kingdom.renderer import RoomRenderer, render_current_room
from kingdom.verbs.verb_handler import VerbHandler


class UIVerbHandler(VerbHandler):

    def load(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        return ctx.ui.request_load()

    def save(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        return ctx.ui.request_save()

    def quit(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        if ctx.ui.request_quit():
            raise QuitGame()
        else:
            return "Quit cancelled."

    def look(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        if words and words[0] in ("inside", "in"):
            if target is None:
                return "Look inside what?"
            renderer = RoomRenderer()
            if isinstance(target, Box):
                return renderer.describe_box_contents(target)
            return f"You can't look inside the {target.get_noun_name()}."

        ctx.ui.render_room(render_current_room(ctx.game.state, display=False), clear=False)

        return  
