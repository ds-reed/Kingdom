# game_state_verbs.py

from kingdom.dispatch_context import DispatchContext
from kingdom.models import Game

class GameStateVerbHandler:
    def save(self, dispatch_context, words):
        game = dispatch_context.game
        default_path = dispatch_context.save_path
        confirm = dispatch_context.confirm_callback
        prompt = dispatch_context.prompt_callback

        if game is None:
            return "No game is active yet."
        if default_path is None:
            return "No save path is configured."

        # Game-state verbs should not target nouns
        if words and words[0] not in ("", None):
            return "You can't save that."

        if not _confirm("Save game?", confirm):
            return "Save cancelled."

        save_path = _prompt_for_path(prompt, "Save", default_path)
        game.save_world(save_path)

        return f"Game saved to {save_path}."


    def load(self, dispatch_context: DispatchContext, words):
        path = dispatch_context.save_path
        dispatch_context.game.load_from_file(path)
        return f"Game restored from {path}."

    def score(self, dispatch_context: DispatchContext, words):
        hero = dispatch_context.state.hero
        return f"Your score is {hero.score}."



