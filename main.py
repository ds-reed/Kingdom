"""
Kingdom Text-based Game Framework 

See castle_demo.json for sample world
"""

import sys
from pathlib import Path
sys.path.append("./src")

from kingdom.utilities import SessionLogger, ensure_terminal_session, parse_args

from kingdom.GUI.terminal_style import tty_set_terminal_mode, set_session_logger
from kingdom.GUI.UI import ui

from kingdom.engine.exception_handling import init_game_state, process_command


def main() -> None:
    args = parse_args()
    if not ensure_terminal_session():
        return

    tty_set_terminal_mode(args.mode)

    world_file = args.file

    base_dir = Path(__file__).parent
    logger = SessionLogger(base_dir)
    logger.start()
    set_session_logger(logger)   


    try:
        
        game = init_game_state(world_file)
        
        recovery_mode = False

        while True:

            command = ui.prompt("\n> ")
            ui.print()

            should_quit, recovery_mode, output = process_command(
                raw_command=command,
                world=game.world,
                lexicon=game.lexicon,
                recovery_mode=recovery_mode,
            )
            
            ui.print(output) if output else None
            if should_quit:
                break

    finally:
        logger.stop()


if __name__ == "__main__":
    main()
