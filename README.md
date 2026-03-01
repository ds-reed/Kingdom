# Kingdom

A command-driven text adventure engine in Python.

Kingdom loads world state from JSON, parses free-text commands, resolves nouns in context, and dispatches verbs through modular handlers. The codebase now uses a refactored structure centered on `models`, `actions`, `parser`, `renderer`, and verb handler modules.

## Current Highlights

- Refactored **verb handler architecture** (`src/kingdom/verbs/*`)
- Registry-based **direction system** with aliases and implicit movement
- Context-aware command resolution (`parse_command` + `resolve_command`)
- Room rendering split into semantic presentation logic (`renderer.py`)
- Save/load support backed by JSON world state
- Two terminal presentation modes: **modern** and **trs80**

## Project Layout

```text
Kingdom/
├── main.py
├── demo.py
├── pyproject.toml
├── run_kingdom.bat
├── run_kingdom_modern.bat
├── run_kingdom_TRS80.bat
├── run_state_check.bat
├── data/
│   ├── initial_state.json
│   ├── demo_initial_state.json
│   ├── working_state.json
│   └── *.sav / *.bak.*
├── docs/
│   ├── project_structure.md
│   ├── trs80_legacy_spirit_guide.md
│   └── ...
├── logs/
├── scripts/
│   ├── check_world_json.py
│   ├── backup_incremental.py
│   └── pre_edit.py
└── src/kingdom/
    ├── __init__.py
    ├── actions.py
    ├── dispatch_context.py
    ├── item_behaviors.py
    ├── models.py
    ├── parser.py
    ├── renderer.py
    ├── terminal_style.py
    ├── UI.py
    ├── utilities.py
    └── verbs/
        ├── verb_handler.py
        ├── movement_verbs.py
        ├── state_changing_verbs.py
        ├── inventory_verbs.py
        ├── ui_verbs.py
        └── meta_verbs.py
```

## Runtime Architecture

### 1) Bootstrapping (`main.py`)

- Parses CLI args (`--mode modern|trs80`)
- Loads world data from `data/initial_state.json`
- Creates player and game state (`GameActionState`)
- Builds UI and dispatch context
- Registers verbs through `build_verbs(...)`

### 2) Parsing (`parser.py`)

- Tokenizes and normalizes player input
- Identifies primary verb and noun phrases
- Resolves implicit movement (single direction token => `go`)

### 3) Dispatch (`models.Verb` + handlers)

- Verb executes noun-side override if present (`on_<verb>`)
- Falls back to handler method
- Handler modules are grouped by concern:
  - movement
  - inventory
  - state changing
  - UI/system
  - meta/help/debug

### 4) Presentation (`renderer.py` + `UI.py`)

- Builds room/item/exit text in renderer
- UI layer handles terminal-specific display behavior

## Commands (Current Core Set)

The current core verbs are registered in `src/kingdom/actions.py`.

Examples include:

- `go`, `swim`, `teleport` (hidden)
- `take`, `drop`, `inventory`
- `open`, `close`, `unlock`, `light`, `extinguish`, `eat`, `rub`, `say`, `make` (hidden)
- `look`, `save`, `load`, `quit`
- `help`, `score`, `debug` (hidden)

Direction aliases are supported through the direction registry and world data.

## Running the Game

### Python

```bash
python main.py
```

Default mode is `modern`.

```bash
python main.py --mode modern
python main.py --mode trs80
```

### Windows launchers

- `run_kingdom.bat`
- `run_kingdom_modern.bat`
- `run_kingdom_TRS80.bat`

## Data and State

- Seed world: `data/initial_state.json`
- Working save examples: `data/working_state.json`, `data/*-save.json`
- Runtime world loading/serialization lives in `src/kingdom/models.py`

## Validate World JSON

```bash
python scripts/check_world_json.py data/initial_state.json
python scripts/check_world_json.py data/initial_state.json data/working_state.json
```

Windows helper:

- `run_state_check.bat`

## Requirements

- Python 3.13+

## Notes

- `demo.py` is present as a smoke-test style script, while `main.py` is the primary runtime entrypoint.
- Several backup/reference files are intentionally kept in the repo (`*.bak.*`, `old.py`, legacy docs).
