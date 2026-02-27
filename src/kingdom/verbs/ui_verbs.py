# ui_verbs.py — handlers for verbs related to UI actions (SAVE, LOAD, QUIT)

from ast import parse

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

        parse= self.resolve_noun_or_word(target, words, interest=["inside", "in"])

        target = parse["noun"]
        if target is not None:
            if not isinstance(target, Box):
                if getattr(target, "examine_string", None) is not None:
                    return self.build_message(target.examine_string)
                else:
                    return self.build_message(f"You see {target.get_name()}.")

        if parse["keywords"] is not None:
            if target is None:
                return self.build_message("Look inside what?")
            renderer = RoomRenderer()
            if isinstance(target, Box):
                return self.build_message(renderer.describe_box_contents(target))
            return self.build_message(f"You can't look inside the {target.get_noun_name()}.")

        ctx.ui.render_room(render_current_room(ctx.game.state, display=False), clear=False)

        return  
