# game_state_verbs.py

from tkinter.font import names

from kingdom.models import Game, Noun, QuitGame, Verb, DispatchContext
from kingdom.UI import render_current_room, UI

class GameStateVerbHandler:

    def load(self, dispatch_context: DispatchContext, target: Noun | None, words: list[str]):
        return dispatch_context.ui.request_load()

    def save(self, dispatch_context: DispatchContext, target: Noun | None, words: list[str]):
        return dispatch_context.ui.request_save()

    def score(self, dispatch_context: DispatchContext, target: Noun | None, words: list[str]):
        game = dispatch_context.game
        if game is None:
            return "Score is unavailable."
        return f"Your current score is: {game.score}"   

    
    def help(self, dispatch_context: DispatchContext, target: Noun | None, words: list[str]):
        if words == None or len(words) == 0: 
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

    def quit(self, dispatch_context: DispatchContext, target: Noun | None, words: list[str]):
        if dispatch_context.ui.request_quit():
            raise QuitGame()
        else:
            return "Quit cancelled."   


# future commands history, help, etc. could be added here
