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

        room = self.room(ctx)

        parse= self.resolve_noun_or_word(words, interest=["inside", "in"])
        noun = parse["noun"]
        keywords = parse["keywords"]
        raw = parse["raw"]

        renderer = RoomRenderer()

        if "inside" in keywords or "in" in keywords:
            if target is None:
                return self.build_message("Look inside what?")
            if isinstance(target, Box):
                return self.build_message(renderer.describe_box_contents(target))
            return self.build_message(f"You can't look inside the {target.get_noun_name()}.")
        
        if not target: target = noun

        if target is not None:
            if getattr(target, "examine_string", None) is not None:
                return self.build_message(target.examine_string)
            elif isinstance(target, Box):
                return self.build_message(f"You see {target.display_name()}. There might be something interesting inside.")
            elif room.has_item(target):
                return self.build_message(f"You see {target.display_name()} here.")
            else:
                return self.build_message(f"You see no {target.canonical_name()} here.")
            
        if raw: return self.build_message("I don't understand what you want to look at.")

        ctx.ui.render_room(render_current_room(ctx.game.state, display=False), clear=False)

        return  
