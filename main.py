"""
Kingdom Game World Simulator - Core API
Uses Game model methods for setup, save, and load functionality.
See demo.py for gameplay examples.
"""

from pathlib import Path
import sys
sys.path.append("./src")

from kingdom.models import Game


def main():
    """Run a minimal verb-based load/save flow."""
    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "initial_state.json"
    save_path = base_dir / "data" / "working_state.json"

    game = Game.get_instance()

    game.setup_world(data_path)

    save_verb, load_verb = game.create_state_verbs()
    print(save_verb.execute(save_path))
    print(load_verb.execute(save_path))


if __name__ == "__main__":
    main()
