Kingdom/
├── pyproject.toml              # Project metadata
├── main.py                     # Main game loop + CLI args (`--mode`)
├── demo.py                     # Demo runner / sample flow
├── run_kingdom.bat             # Windows launcher
├── data/
│   ├── initial_state.json      # Seed world state
│   ├── working_state.json      # Active save state
│   └── *.sav / *.bak.*         # Local saves and backups
├── docs/
│   ├── project_structure.md    # This file
│   └── todo.txt                # Outstanding task list
├── logs/                       # Session logs
├── scripts/                    # Backup and pre-edit utility scripts
└── src/
    └── kingdom/
        ├── __init__.py
        ├── actions.py          # Command handlers and game-loop actions
        ├── item_behaviors.py   # Item-specific behavior helpers
        ├── models.py           # Core world/domain models
        ├── parser.py           # Command parsing + noun/verb resolution
        ├── terminal_style.py   # TRS80/modern terminal presentation
        └── utilities.py        # Shared helpers (logging, utilities)

