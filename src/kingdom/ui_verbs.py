# ui_verbs.py — handlers for verbs related to UI actions (SAVE, LOAD, QUIT)

from kingdom.models import DispatchContext, Noun, QuitGame
from kingdom.UI import UI


class UIVerbHandler:

    def load(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        return ctx.ui.request_load()

    def save(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        return ctx.ui.request_save()

    def quit(self, ctx: DispatchContext, target: Noun | None, words: tuple[str, ...] = ()):
        if ctx.ui.request_quit():
            raise QuitGame()
        else:
            return "Quit cancelled."
