# Kingdom Engine Architecture: Layer Responsibilities and Data Flow

This document describes the current conceptual layers of the Kingdom text-adventure engine and the responsibilities of each layer.

The primary goals are:

- maintain separation of concerns
- reduce architectural leaks
- support both OLD_SCHOOL and modern presentation modes

The engine is organized into eight cooperating layers:

1. Terminal Layer (device I/O primitives)
2. Input Layer (UI interaction)
3. Renderer Layer (text composition)
4. Main Loop Layer (orchestration)
5. Parser Layer (syntax)
6. Semantic Interpretation Layer (resolution)
7. Verb Execution Layer (action behavior)
8. Game Model Layer (world state and persistence)

Each layer should communicate through structured data contracts, not ad hoc raw strings.

---

## Current Module Map

```text
main.py
|-- kingdom.utilities (args/session helpers)
|-- kingdom.GUI.terminal_style (terminal mode + low-level tty I/O)
|-- kingdom.GUI.UI (user interaction facade)
`-- kingdom.engine.exception_handling
	|-- init_game_state (startup/init)
	`-- process_command (single-turn orchestration)
		|-- kingdom.language.parse
		|-- kingdom.language.interpret
		|-- kingdom.language.execute
		`-- kingdom.engine.verbs.*
			`-- kingdom.model.*

rendering branch:
kingdom.rendering.descriptions
kingdom.rendering.command_results
kingdom.rendering.textutils
```

### Turn Flow

Input path:

```text
UI -> main loop -> parser -> interpreter -> executor -> verb handlers -> model
```

Output path:

```text
model/query results -> rendering helpers -> UI -> terminal
```

---

## 1. Terminal Layer (Device / Presentation)

Current implementation: src/kingdom/GUI/terminal_style.py

Responsibilities:

- mode switching between OLD_SCHOOL and modern output
- low-level print/prompt and wrapping behavior
- screen clearing and terminal presentation details
- optional session logging integration

Non-responsibilities:

- no command parsing or semantic resolution
- no game rule evaluation
- no world mutation

---

## 2. Input Layer (UI / Interaction)

Current implementation: src/kingdom/GUI/UI.py

Responsibilities:

- collect raw player input
- provide confirm/save/load/quit prompts
- forward printable output and room lines to terminal layer
- enforce safe save/load filename prompts

Non-responsibilities:

- no parsing, interpretation, or execution
- no direct mutation of world entities

---

## 3. Renderer Layer (Formatting and Text Composition)

Current implementation:

- src/kingdom/rendering/descriptions.py
- src/kingdom/rendering/command_results.py
- src/kingdom/rendering/textutils.py

Responsibilities:

- convert model facts into player-facing lines
- build room description output
- build summary text such as exit messages

Non-responsibilities:

- no parser/interpreter logic
- no action rule execution
- no direct input handling

---

## 4. Main Layer (Entry Point and Orchestrator)

Current implementation:

- entry point in main.py
- orchestration in src/kingdom/engine/exception_handling.py

### 4a. Entry Point

Responsibilities:

- parse startup args
- set terminal mode
- initialize session logging
- initialize game state
- run the command loop

### 4b. Turn Orchestrator

Responsibilities:

- receive raw command input
- parse -> interpret -> execute pipeline dispatch
- handle SaveGame, LoadGame, QuitGame, and GameOver control flow
- handle recovery mode constraints
- trigger room rendering on startup/load/game-over recovery

Important note:

- runtime state is held in Game via get_game(), along with SessionPrefs and current world/player references

---

## 5. Parser Layer (Syntax)

Current implementation: src/kingdom/language/parser.py

Primary contract:

- parse(text, lexicon) -> list[ParsedAction]

Responsibilities:

- normalize and tokenize input
- identify primary verb and verb source
- capture object phrases and prepositional phrases
- capture direction/modifier/unknown tokens
- split and group conjunction patterns

Non-responsibilities:

- no world mutation
- no verb execution

---

## 6. Semantic Interpretation Layer (Resolution)

Current implementation: src/kingdom/language/interpreter.py

Primary contract:

- interpret(parsed_actions, world, lexicon) -> list[InterpretedCommand]

Responsibilities:

- resolve parsed fields into executable command shape
- attach resolved direct/prepositional targets when available
- canonicalize direction handling for verb usage
- preserve token context for error handling and downstream messaging

Non-responsibilities:

- no world mutation
- no direct terminal output

---

## 7. Verb Execution Layer (Action Behavior)

Current implementation:

- bridge: src/kingdom/language/executor.py
- command contract: src/kingdom/engine/verbs/verb_handler.py (ExecuteCommand)
- handlers: src/kingdom/engine/verbs/*.py
- special behavior hooks: src/kingdom/engine/item_behaviors.py

Primary contract:

- execute(interpreted_command, world, original_command) -> CommandOutcome

Responsibilities:

- map interpreted command into handler command contract
- execute verb-specific rules and mutations
- return outcome messages for display
- enforce gameplay constraints via handler logic

Non-responsibilities:

- no raw input handling
- no terminal rendering concerns

---

## 8. Game Model Layer (World State and Persistence)

Current implementation:

- src/kingdom/model/noun_model.py
- src/kingdom/model/game_model.py
- src/kingdom/model/direction_model.py
- src/kingdom/model/verb_model.py

Responsibilities:

- represent rooms, exits, items, containers, features, player
- maintain session state in Game
- support save/load and world reconstruction
- maintain gameplay metrics such as score and discovery counters

Non-responsibilities:

- no parser logic
- no UI/terminal I/O

---

## Data Contracts Between Layers

Current contracts in code:

- Parser output: ParsedAction
- Interpreter output: InterpretedCommand
- Executor output: CommandOutcome
- Verb handler input: ExecuteCommand
- Persistent runtime/session state: Game and SessionPrefs

These contracts are explicit and module-scoped. Verb execution now requires CommandOutcome rather than ad hoc string returns.

---

## Practical Refactor Guidance

When refactoring, prefer these boundaries:

- keep orchestration and exception-routing in engine/exception_handling
- keep syntax concerns in parser
- keep semantic mapping in interpreter
- keep behavior rules in engine/verbs and item_behaviors
- keep text shaping in rendering
- keep storage/state invariants in model

This keeps the command pipeline easier to test and reduces cross-layer coupling.