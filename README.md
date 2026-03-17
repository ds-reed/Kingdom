# Kingdom

run_castle_modern.bat runs the castle demo in modern mode
run_castle_old_school.bat runs the castle demo in a more authentic TRS-80 style
run_kingdom.bat runs the kingdom framework with the default initial_state.json instead of the castle demo

Kingdom is a command-driven text adventure engine in Python. It loads world state from JSON, builds a runtime lexicon from the current world and verb registry, parses free-text commands, interprets them in context, and dispatches execution through modular verb handlers.

The current codebase is organized around four main areas:

- world and persistence models in `src/kingdom/model/`
- parser / interpreter / executor flow in `src/kingdom/language/`
- verb logic in `src/kingdom/verbs/`
- rendering and terminal UI in `src/kingdom/renderer.py` and `src/kingdom/UI.py`

## Current Highlights

- JSON-backed world bootstrapping and save/load
- Parser -> interpreter -> executor pipeline
- Lexicon generated from current nouns, verbs, directions, and prepositions
- Context-sensitive noun resolution against room, inventory, and open containers
- Prepositional phrase parsing for commands such as `put all into bag` and `tie rope to hook`
- Implicit direction handling for single-token movement such as `west`
- Support for modifiers such as `all`
- Item-specific special behaviors in `src/kingdom/item_behaviors.py`
- Modern and OLD_SCHOOL-style terminal presentation modes

## Repository Layout

```text
Kingdom/
├── main.py
├── pyproject.toml
├── README.md
├── run_kingdom.bat
├── run_castle_modern.bat
├── run_castle_old_school.bat
├── run_state_check.bat
├── data/
│   ├── initial_state.json
│   ├── working_state.json
│   └── other save / scratch JSON files
├── docs/
│   ├── project_structure.md
│   ├── main_parse_through_render_flow.md
│   ├── Parser Design Note (Updated).md
│   ├── Parser Refactor TODO.md
│   └── trs80_legacy_spirit_guide.md
├── logs/
├── saves/
├── scripts/
│   ├── check_world_json.py
│   └── find_obsolete_attributes.py
├── tests/
│   ├── regression.py
│   ├── test_inventory_get_behavior.py
│   ├── test_save_load_roundtrip.py
│   └── test_world_container_persistence.py
└── src/kingdom/
    ├── __init__.py
    ├── item_behaviors.py
    ├── renderer.py
    ├── terminal_style.py
    ├── UI.py
    ├── utilities.py
    ├── rendering/
    │   ├── command_results.py
    │   ├── descriptions.py
    │   └── textutils.py
    ├── language/
    │   ├── executor.py
    │   ├── interpreter.py
    │   ├── lexicon.py
    │   ├── parser.py
    │   └── tests/
    ├── model/
    │   ├── direction_model.py
    │   ├── game_model.py
    │   ├── noun_model.py
    │   └── verb_model.py
    └── verbs/
        ├── inventory_verbs.py
        ├── meta_verbs.py
        ├── movement_verbs.py
        ├── state_changing_verbs.py
        ├── state_dependent_verbs.py
        ├── verb_handler.py
        └── verb_registration.py
```

## Runtime Flow

### 1. Bootstrapping

`main.py` initializes the terminal mode, loads `data/initial_state.json`, creates the player and session state, registers verbs, builds the lexicon, and renders the starting room.

Primary setup code lives in:

- `src/kingdom/model/game_init.py`
- `src/kingdom/model/game_persistence.py`
- `src/kingdom/verbs/verb_registration.py`

### 2. Parsing

`src/kingdom/language/parser.py` converts raw input into one or more `ParsedAction` objects.

Current parser responsibilities include:

- normalization and tokenization
- explicit verb detection
- implicit verb handling for direction-only input
- noun phrase grouping
- conjunction grouping
- prepositional phrase capture
- modifier capture, including `all`
- unknown token tracking

### 3. Interpretation

`src/kingdom/language/interpreter.py` converts parsed syntax into `InterpretedCommand` objects.

This layer resolves:

- the executable verb object
- direct objects
- prepositional targets
- direction arguments
- modifiers

### 4. Execution

`src/kingdom/language/executor.py` bridges interpreted commands into the current verb handler contract.

Verb behavior is organized by concern in `src/kingdom/verbs/`:

- `movement_verbs.py`
- `inventory_verbs.py`
- `state_changing_verbs.py`
- `state_dependent_verbs.py`
- `meta_verbs.py`

Item-specific overrides and puzzle logic live in `src/kingdom/item_behaviors.py`.

### 5. Rendering

`src/kingdom/renderer.py` and `src/kingdom/UI.py` handle presentation and terminal-specific output.

## Parser and Command Enhancements

The current language stack supports more than simple `verb noun` commands.

Examples of supported command shapes include:

- `west`
- `open lunch bag`
- `look in lunch bag`
- `get fish from lunch bag`
- `put all into bag`
- `tie rope to hook`
- `unlock and open trapdoor`

Important parser/runtime behaviors:

- direction synonyms are recognized through the direction registry
- noun resolution uses the active lexicon built from live game objects
- open-container items can be individually targeted by commands such as `get fish`
- bulk `get all` behavior is intentionally narrower and does not automatically drain open containers
- prepositions are normalized through the lexicon, so synonyms such as `inside` can map to canonical forms such as `into`

## Running the Game

### Python

```bash
python main.py
python main.py --mode modern
python main.py --mode OLD_SCHOOL
```

### Windows launchers

- `run_kingdom.bat`
- `run_kingdom_modern.bat`
- `run_kingdom_OLD_SCHOOL.bat`

## World Data and Persistence

- Seed world: `data/initial_state.json`
- Save files: `saves/*.json`
- World/entity models: `src/kingdom/model/noun_model.py`
- Session/bootstrap state: `src/kingdom/model/game_init.py`
- Save/load I/O: `src/kingdom/model/game_persistence.py`

The world JSON defines:

- rooms and go_exits
- swim and climb exits
- items, containers, and features
- item attributes such as openable, lockable, lightable, edible, climbable, and custom special handlers

## Validation and Tests

### World JSON validation

```bash
python scripts/check_world_json.py data/initial_state.json
python scripts/check_world_json.py data/initial_state.json data/working_state.json
```

Windows helper:

- `run_state_check.bat`

### Pytest

Default pytest discovery is configured in `pyproject.toml` for `tests/` and `src/kingdom/tests` with `test_*.py` naming plus the smoke-test file `tests/regression.py`.

Run the current non-language suite:

```bash
pytest --ignore=src/kingdom/language/tests
```

Run the smoke test directly:

```bash
pytest tests/regression.py
```

Run the parser/language tests separately when needed:

```bash
pytest src/kingdom/language/tests
```

Run the smoke flow directly:

```bash
pytest tests/regression.py -q
```

Current top-level regression coverage includes:

- save/load roundtrip persistence
- room/container/feature persistence behavior
- inventory regression checks such as `get all` vs. implicit single-item pickup from open containers
- end-to-end smoke flow through the main command pipeline

## Requirements

- Python 3.13+
- `pytest` for test runs

## Notes

- `docs/main_parse_through_render_flow.md` is the best high-level architecture note for the current command pipeline.
- `src/kingdom/language/tests/` contains parser/interpreter-focused tests and harnesses that are intentionally separate from the broader gameplay regression suite.
- The TRS80 BASIC source under `docs/TRS80-basic source/` preserves the original inspiration and reference material for the project.
