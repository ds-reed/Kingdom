# Main → Parse → Interpret → Execute → Render  
_Architectural Overview of the Command Processing Pipeline_

This document defines the high‑level flow of player input through the engine. It establishes the responsibilities and boundaries of each layer: **Main**, **Parser**, **Interpreter**, **Executor**, and **Renderer**. The goal is a clean, rediscoverable architecture where each layer has a single, well‑defined purpose and no layer leaks responsibilities into another.

---

## 1. Overview

The engine processes a player command through five sequential layers:

1. **Main** — orchestration only  
2. **Parser** — syntax extraction  
3. **Interpreter** — semantic interpretation and disambiguation  
4. **Executor** — verb behavior and world mutation  
5. **Renderer** — narrative output

The parser may return **multiple ParsedActions** (e.g., “unlock and open trapdoor”).  
The Interpreter converts each ParsedAction into **zero, one, or many InterpretedCommands**.  
The Executor executes each InterpretedCommand **one at a time**.

---

## 2. Main (Orchestration Layer)

Main is responsible for:

- receiving raw input from the UI  
- invoking the parser  
- invoking the interpreter  
- invoking the executor  
- invoking the renderer  
- updating the world state  
- looping for the next command  

Main does **not** interpret syntax, resolve meaning, execute verbs, or render text.

### Main Loop (Conceptual)

```python
raw = ui.get_input()

parsed_actions = parser.parse(raw)

Interpreted_commands = interpreter.interpret(parsed_actions, world)

outcomes = []
for Interpreted in Interpreted_commands:
    outcomes.append(executor.execute(Interpreted, world))

renderer.render(outcomes, ui)
```

---

## 3. Parser (Syntactic Layer)

The parser converts raw text into one or more **ParsedActions**, each representing a syntactic command fragment.

### Responsibilities

- normalize text  
- tokenize  
- identify verbs  
- identify noun phrases  
- identify prepositional phrases  
- identify direction tokens  
- identify modifiers (including “all”)  
- preserve character spans  
- attach syntactic diagnostics  
- split multi‑verb commands (“unlock and open trapdoor”)  

### Output: `List[ParsedAction]`

Each `ParsedAction` contains:

- `primary_verb_token` + canonical verb  
- `object_phrases`  
- `prep_phrases`  
- `direction_tokens`  
- `modifiers`  
- `raw_text`  
- `diagnostics`  

---

## 4. Interpreter (Semantic Layer)

The Interpreter converts each `ParsedAction` into **zero, one, or many InterpretedCommands**.  
This step is **pure**, **deterministic**, and **side‑effect‑free**.

### Responsibilities

- confirm and interpret the verb  
- resolve noun phrases to world objects  
- detect and resolve ambiguity  
- interpret direction tokens  
- classify prepositional phrases  
- interpret modifiers and quantifiers  
- enforce verb argument rules  
- preserve surface forms  
- attach semantic diagnostics  
- expand “all” **only if** the verb’s signature allows it  
  (`verb.supports_all_expansion == True`)  

### Output: `List[InterpretedCommand]`

- **0** → invalid or unresolvable  
- **1** → normal case  
- **N** → ALL expansion or multi-target verbs  

---

## 5. Executor (Action Layer)

The Executor takes a single `InterpretedCommand` and applies the verb’s behavior to the world.

### Responsibilities

- invoke the correct verb handler  
- apply world changes  
- generate execution messages  
- generate execution diagnostics  
- determine whether the room should be re-rendered  

### Output: `CommandOutcome`

Contains:

- `Interpreted: InterpretedCommand`  
- `messages: List[str]`  
- `effects` (world state delta)  
- `diagnostics`  
- `should_render_room: bool`  

Renderer does **not** inspect world state or effects.

---

## 6. Renderer (Narrative Layer)

The renderer receives a list of **CommandOutcome** objects and produces narrative output.

It uses:

- the semantic interpretation (`InterpretedCommand`)  
- the execution results  
- the exact player‑typed phrases  

Renderer does **not** parse, resolve, or mutate world state.

---

## 7. Data Flow Summary

```
UI Input
   ↓
Main
   ↓
Parser → ParsedActions (syntax only)
   ↓
Interpreter → InterpretedCommands (meaning only)
   ↓
Executor → CommandOutcome (execution + messages)
   ↓
Renderer
   ↓
UI Output
```

---

## 8. Future Document: Verb Handling Pipeline

The Executor will delegate verb behavior to a dedicated **Verb Handling Pipeline**, which will define:

- required / optional arguments  
- whether “all” expansion is allowed  
- how prepositions and modifiers are interpreted  
- default success/failure messages  
- verb handler lookup  

