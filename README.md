# Kingdom

Kingdom is a command-driven text adventure engine in Python. It loads world state from JSON, builds a runtime lexicon from the active world and verb registry, parses free-text commands, interprets them in context, and dispatches execution through modular verb handlers.

## limitations
- no world builder yet
- no world sanity checker yet
- no resolution of name collisions in created objects; world designer responsible for unique names (including synonyms)
- no handling of multi-objects commands (ie. take banana and egg)

## Launchers

- run_castle_modern.bat: castle demo in modern mode
- run_castle_old_school.bat: castle demo in TRS-80 style presentation
- run_kingdom.bat: framework entry with default world data
- run_regression.bat: quick regression run helper

## Current Highlights

- JSON-backed world bootstrapping and save/load
- Parser -> interpreter -> executor pipeline
- Lexicon generated from current nouns, verbs, directions, and prepositions
- Context-sensitive noun resolution against room, inventory, and open containers
- Prepositional phrase parsing for commands such as put all into bag and tie rope to hook
- Implicit direction handling for single-token movement such as west
- Support for modifiers such as all
- Item-specific special behaviors in src/kingdom/engine/item_behaviors.py
- Modern and OLD_SCHOOL terminal presentation modes

## Repository Layout

```text
Kingdom/
|-- main.py
|-- pyproject.toml
|-- README.md
|-- run_castle_modern.bat
|-- run_castle_old_school.bat
|-- run_kingdom.bat
|-- run_regression.bat
|-- run_save_load.bat
|-- run_state_check.bat
|-- data/
|   |-- demo_castle.json
|   |-- initial_state.json
|   |-- working_state.demo.json
|   |-- working_state.json
|   `-- temporary roundtrip/scratch JSON files
|-- docs/
|   |-- 100 challenging phrases for parser testing.md
|   |-- Interpretter TODO.md
|   |-- main_parse_through_render_flow.md
|   |-- Parser Design Note (Updated).md
|   |-- Parser Refactor TODO.md
|   |-- trs80_legacy_spirit_guide.md
|   |-- TRS80-basic source/
|   `-- unfiltered-ideas/
|-- logs/
|-- saves/
|-- scripts/
|   |-- check_world_json.py
|   `-- find_obsolete_attributes.py
|-- tests/
|   |-- regression.py
|   |-- test_inventory_get_behavior.py
|   |-- test_save_load_roundtrip.py
|   `-- test_world_container_persistence.py
`-- src/kingdom/
    |-- __init__.py
    |-- utilities.py
    |-- GUI/
    |   |-- terminal_style.py
    |   `-- UI.py
    |-- engine/
    |   |-- __init__.py
    |   |-- exception_handling.py
    |   |-- item_behaviors.py
    |   `-- verbs/
    |       |-- __init__.py
    |       |-- inventory_verbs.py
    |       |-- meta_verbs.py
    |       |-- movement_verbs.py
    |       |-- state_changing_verbs.py
    |       |-- state_dependent_verbs.py
    |       |-- verb_handler.py
    |       `-- verb_registration.py
    |-- language/
    |   |-- __init__.py
    |   |-- executor.py
    |   |-- interpreter.py
    |   |-- lexicon.py
    |   |-- parser.py
    |   `-- tests/
    |-- model/
    |   |-- __init__.py
    |   |-- direction_model.py
    |   |-- game_model.py
    |   |-- noun_model.py
    |   `-- verb_model.py
    `-- rendering/
        |-- command_results.py
        |-- descriptions.py
        `-- textutils.py
```

## Runtime Flow

1. Bootstrapping

- main.py parses args, sets terminal mode, starts session logging, and initializes game state.
- Boot/init path is driven through src/kingdom/engine/exception_handling.py.

2. Parsing

- src/kingdom/language/parser.py converts raw input into parsed actions.
- Supports normalization, explicit/implicit verbs, noun phrase grouping, conjunctions, prepositions, modifiers, and unknown token tracking.

3. Interpretation

- src/kingdom/language/interpreter.py resolves parsed actions into executable command objects.
- Resolves verbs, direct objects, prepositional targets, direction arguments, and modifiers.

4. Execution

- src/kingdom/language/executor.py bridges interpreted commands into verb handlers.
- Verb behavior modules live in src/kingdom/engine/verbs/.
- Item-specific overrides and puzzle behavior live in src/kingdom/engine/item_behaviors.py.

5. Rendering and UI

- Terminal/UI behavior lives in src/kingdom/GUI/.
- Output formatting and narrative text composition live in src/kingdom/rendering/.

## Running the Game

### Python

```bash
python main.py
python main.py --mode modern
python main.py --mode OLD_SCHOOL
```

### Windows launchers

- run_kingdom.bat
- run_castle_modern.bat
- run_castle_old_school.bat

## World Data and Persistence

- Seed world: data/initial_state.json
- Demo world: data/demo_castle.json
- Save files: saves/*.json
- World/entity models: src/kingdom/model/noun_model.py
- Save/load I/O: Game.save_game() and Game.load_game() in src/kingdom/model/game_model.py

The world JSON defines rooms, exits (go/swim/climb), items, containers, features, and behavior attributes.

## Validation and Tests

### World JSON validation

```bash
python scripts/check_world_json.py data/initial_state.json
python scripts/check_world_json.py data/initial_state.json data/working_state.json
```

Windows helper:

- run_state_check.bat

### Pytest

Pytest discovery in pyproject.toml includes tests/ and src/kingdom/tests, with test_*.py naming plus tests/regression.py.

Run full suite:

```bash
pytest -q
```

Run smoke/regression flow directly:

```bash
pytest tests/regression.py -q
```

Run parser/language tests separately when needed:

```bash
pytest src/kingdom/language/tests
```

## Requirements

- Python 3.13+
- pytest

## Notes

- docs/main_parse_through_render_flow.md is the best high-level architecture note for command flow.
- src/kingdom/language/tests/ contains parser/interpreter-focused tests and harnesses that are intentionally separate from broader gameplay regression checks.
- docs/TRS80-basic source/ preserves the original inspiration and reference material.
