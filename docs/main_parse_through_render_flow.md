# Main -> Parse -> Interpret -> Execute -> Render
_Current Architectural Overview of the Command Processing Pipeline_

This document reflects the current implementation of the command pipeline.

It describes responsibilities and boundaries of Main, Parser, Interpreter, Executor, and Renderer as they exist today.

---

## 1. Overview

The engine processes a player command through five sequential layers:

1. Main (orchestration)
2. Parser (syntax extraction)
3. Interpreter (semantic mapping)
4. Executor (verb execution and world mutation)
5. Renderer (room/summary text formatting)

Important current-state notes:

- parse returns a list of ParsedAction, but current parser implementation produces one ParsedAction per raw command
- interpret currently produces one InterpretedCommand per ParsedAction
- execute runs one InterpretedCommand at a time and returns CommandOutcome
- per-command output is currently printed directly from outcome.message in the orchestration layer

---

## 2. Main (Orchestration Layer)

Main and orchestration live in:

- main.py
- src/kingdom/engine/exception_handling.py

Responsibilities:

- receive raw input from UI
- invoke parse -> interpret -> execute
- print command outcomes
- handle lifecycle exceptions (SaveGame, LoadGame, QuitGame, GameOver)
- manage recovery mode behavior
- loop for next command

Main does not implement parser logic, semantic resolution, or verb rule logic.

### Main Loop (Current Conceptual Shape)

```python
raw = ui.prompt("\n> ")
parsed_actions = parse(raw, lexicon)
interpreted_commands = interpret(parsed_actions, world, lexicon)

for cmd in interpreted_commands:
    outcome = execute(cmd, world, raw)
    ui.print(outcome.message if outcome else "Command executed.")
```

---

## 3. Parser (Syntactic Layer)

Parser module: src/kingdom/language/parser.py

The parser converts raw input text into ParsedAction structures.

### Responsibilities

- normalize and tokenize text
- identify verb candidates and verb source
- collect object phrases
- collect and canonicalize prepositional phrase shape
- capture direction and modifier tokens
- track unknown tokens

### Output: list[ParsedAction]

Current ParsedAction fields include:

- raw_text
- tokens
- primary_verb
- primary_verb_token
- verb_source
- object_phrases
- prep_phrases
- conjunction_groups
- direction_tokens
- modifier_tokens
- unknown_tokens

---

## 4. Interpreter (Semantic Layer)

Interpreter module: src/kingdom/language/interpreter.py

The interpreter maps ParsedAction into InterpretedCommand for execution.

### Responsibilities

- resolve verb object from parsed verb data
- map direct object token data into interpreted target shape
- map prepositional targets
- map direction and modifiers for execution
- provide implicit movement behavior when no explicit verb is present

### Output: list[InterpretedCommand]

Current behavior:

- one InterpretedCommand per ParsedAction in normal flow
- no active ALL expansion in interpreter at this time
- ambiguity handlers are present as placeholders and currently return no expansion

---

## 5. Executor (Action Layer)

Executor module: src/kingdom/language/executor.py

The executor adapts interpreted commands to the verb-handler contract and executes verb logic.

### Responsibilities

- build ExecuteCommand payload for verb handlers
- resolve target objects against current room and inventory context
- invoke verb.execute and require CommandOutcome
- return CommandOutcome

### Output: CommandOutcome

Current CommandOutcome fields:

- verb: str
- command: InterpretedCommand
- message: str
- effects: list[str]

Notes:

- diagnostics and should_render_room flags are not currently part of CommandOutcome
- orchestration formats CommandOutcome via rendering.command_results before UI print

---

## 6. Renderer (Narrative Layer)

Renderer modules:

- src/kingdom/rendering/descriptions.py
- src/kingdom/rendering/command_results.py
- src/kingdom/rendering/textutils.py

Current renderer role:

- render room descriptions (for startup, load, and recovery transitions)
- render summary/exit text helpers
- provide shared text formatting utilities

Current architecture note:

- there is not yet a dedicated render(outcomes) pass for each command turn
- most per-turn verb output still originates in verb handlers, but now crosses a render boundary through CommandOutcome formatting

---

## 7. Data Flow Summary (Current)

```text
UI input
  -> Main/process_command
  -> Parser (ParsedAction list)
  -> Interpreter (InterpretedCommand list)
  -> Executor (CommandOutcome)
  -> Renderer format_command_outcome(outcome)
  -> UI print formatted text

Room transitions and lifecycle events:
  model state -> rendering helpers -> UI.render_room
```

---

## 8. Near-Term Evolution

The current pipeline is functional, with the command outcome contract now enforced end to end.

Likely next cleanup targets:

- move more per-turn text assembly into rendering modules
- formalize multi-action parsing and semantic expansion behavior
- add richer outcome metadata when renderer-driven turn output is introduced

