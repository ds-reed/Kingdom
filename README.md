# Kingdom

A command-driven text adventure engine in Python.

Kingdom loads world state from JSON, parses free-text commands, resolves nouns in context, and dispatches verbs through modular handlers. The codebase is organized around a split model layer, parser/resolver flow, renderer/UI, and verb handler modules.

## Current Highlights

- Refactored **verb handler architecture** (`src/kingdom/verbs/*`)
- Registry-based **direction system** with synonyms and implicit movement
- Context-aware command resolution (`parse_command` + `resolve_command`)
- Room rendering split into semantic presentation logic (`renderer.py`)
- Save/load support backed by JSON world state (`game_persistence.py`)
- Two terminal presentation modes: **modern** and **trs80**

## Project Layout

```text
Kingdom/
├── main.py
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
│   ├── find_obsolete_attributes.py
│   └── validate_save_load_roundtrip.py
├── tests/
│   ├── test_parser.py
│   ├── test_world_container_persistence.py
│   └── ...
└── src/kingdom/
    ├── __init__.py
    ├── dispatch_context.py
    ├── item_behaviors.py
    ├── parser.py
    ├── resolver.py
    ├── renderer.py
    ├── terminal_style.py
    ├── UI.py
    ├── utilities.py
    ├── language/
    │   ├── lexicon/
    │   │   ├── noun_registry.py
    │   │   └── verb_registry.py
    │   └── parser/
    ├── model/
    │   ├── noun_model.py
    │   ├── verb_model.py
    │   ├── game_init.py
    │   └── game_persistence.py
    └── verbs/
        ├── verb_handler.py
        ├── movement_verbs.py
        ├── state_changing_verbs.py
        ├── inventory_verbs.py
        └── meta_verbs.py
```

## Runtime Architecture

### 1) Bootstrapping (`main.py`)

- Parses CLI args (`--mode modern|trs80`)
- Loads world data from `data/initial_state.json`
- Creates player and game state (`GameActionState`)
- Builds UI and initializes session state
- Registers verbs through `build_verb_registry(...)`

### 2) Parsing (`parser.py`)

- Tokenizes and normalizes player input
- Identifies primary verb and noun phrases
- Resolves implicit movement (single direction token => `go`)

### 3) Dispatch (`model.Verb` + handlers)

- Verb executes noun-side override if present (`on_<verb>`)
- Falls back to handler method
- Verb model lives in `src/kingdom/model/verb_model.py`
- Handler modules are grouped by concern:
  - movement
  - inventory
  - state changing
  - meta/help/debug

### 4) Presentation (`renderer.py` + `UI.py`)

- Builds room/item/exit text in renderer
- UI layer handles terminal-specific display behavior

## Commands (Current Core Set)

The current core verbs are registered in `src/kingdom/language/lexicon/verb_registry.py`.

Examples include:

- `go`, `swim`, `teleport` (hidden)
- `take`, `drop`, `inventory`
- `open`, `close`, `unlock`, `light`, `extinguish`, `eat`, `rub`, `say`, `make` (hidden)
- `look`, `save`, `load`, `quit`
- `help`, `score`, `debug` (hidden)

Direction synonyms are supported through the direction registry and world data.

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
- World/entity models live in `src/kingdom/model/noun_model.py`
- Session/bootstrap state lives in `src/kingdom/model/game_init.py`
- Save/load I/O lives in `src/kingdom/model/game_persistence.py`

## Validate World JSON

```bash
python scripts/check_world_json.py data/initial_state.json
python scripts/check_world_json.py data/initial_state.json data/working_state.json
```

Windows helper:

- `run_state_check.bat`

By default, `run_state_check.bat` validates `data/initial_state.json` and then
runs the save/load roundtrip validator.

## Validate Save/Load Roundtrip

```bash
python scripts/validate_save_load_roundtrip.py
```

This script performs a full save→load roundtrip and verifies constructor-backed
fields on rooms, containers, and items are preserved.

`run_state_check.bat` now runs both:
- world JSON checks (`scripts/check_world_json.py`)
- save/load roundtrip validation (`scripts/validate_save_load_roundtrip.py`)

## Requirements

- Python 3.13+

## Notes

- `tests/demo.py` is present as a smoke-test style script, while `main.py` is the primary runtime entrypoint.
- TRS80-basic source is the orignial 1978 era BASIC version of Castle, which the Kingdom framework is intended to support
