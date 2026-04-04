# Kingdom Engine Architecture  
### **Layer Responsibilities, Data Flow, and Updated Continuation Model**

This document describes the conceptual layers of the Kingdom text‑adventure engine and the responsibilities of each layer.  
It incorporates the updated architecture we refined through discussion — especially the clarified roles of the **interpreter**, **executor**, **verb handlers**, and the **noun model**.

The goals remain:

- maintain separation of concerns  
- reduce architectural leaks  
- support both OLD_SCHOOL and modern presentation modes  
- support multi‑turn commands, ambiguity resolution, and continuation input  
- keep world mutation centralized in the model layer  

The engine is organized into **eight cooperating layers**, plus two important cross‑cutting subsystems:

1. Terminal Layer  
2. Input Layer  
3. Renderer Layer  
4. Main Loop Layer  
5. Parser Layer  
6. Semantic Interpretation Layer  
7. Verb Execution Layer  
8. Game Model Layer  

**Cross‑cutting subsystems:**

- **State‑Changing Verb Framework** (within Verb Execution Layer)  
- **Conversation‑State Executor** (continuation + ambiguity resolution)  

Each layer communicates through structured data contracts, not ad‑hoc strings.

---

# 🧭 Turn Flow Overview

**Input path:**

```
UI → main loop → parser → interpreter → executor → verb handlers → model
```

**Output path:**

```
model/query results → rendering helpers → UI → terminal
```

---

# 1. Terminal Layer (Device / Presentation)

**Responsibilities:**

- manage OLD_SCHOOL vs modern terminal modes  
- low‑level printing, wrapping, clearing  
- optional session logging  

**Non‑responsibilities:**

- no parsing  
- no semantic logic  
- no world mutation  

---

# 2. Input Layer (UI / Interaction)

**Responsibilities:**

- collect raw player input  
- provide confirm/save/load/quit prompts  
- forward output to terminal layer  
- enforce safe filename prompts  

**Non‑responsibilities:**

- no parsing or interpretation  
- no world mutation  

---

# 3. Renderer Layer (Formatting and Text Composition)

**Responsibilities:**

- convert model facts into player‑facing lines  
- build room descriptions  
- build exit summaries  
- shape text for UI  

**Non‑responsibilities:**

- no parser/interpreter logic  
- no verb execution  
- no world mutation  

---

# 4. Main Layer (Entry Point and Orchestrator)

### 4a. Entry Point

**Responsibilities:**

- parse startup args  
- set terminal mode  
- initialize session logging  
- initialize game state  
- run the command loop  

### 4b. Turn Orchestrator

**Responsibilities:**

- receive raw input  
- dispatch through parse → interpret → execute  
- handle SaveGame, LoadGame, QuitGame, GameOver  
- trigger room rendering on startup/load/recovery  

**Notes:**

- runtime state lives in `Game` via `get_game()`  

---

# 5. Parser Layer (Syntax)

**Contract:**  
`parse(text, lexicon) → list[ParsedAction]`

**Responsibilities:**

- tokenize and normalize input  
- identify verb token and verb source  
- capture noun phrases and prepositional phrases  
- capture directions, modifiers, unknown tokens  
- split conjunctions  

**Non‑responsibilities:**

- no world mutation  
- no semantic role assignment  
- no verb execution  

---

# 6. Semantic Interpretation Layer (Resolution)

**Contract:**  
`interpret(parsed_actions, world, lexicon) → list[InterpretedCommand]`

**Responsibilities:**

- resolve parsed fields into executable command shape  
- resolve nouns to world objects when possible  
- **map prepositions → semantic roles using verb‑declared slot tables**  
- normalize synonyms (e.g., “loot” → take‑all‑from)  
- normalize “all/everything”  
- apply fallback container logic  
- resolve directions for movement verbs  
- preserve token context for error messaging  

**Non‑responsibilities:**

- no world mutation  
- no conversation‑state tracking  
- no capability checks  
- no verb semantics  

---

# 7. Verb Execution Layer (Action Behavior + Conversation State)

This layer contains two cooperating subsystems:

1. **Conversation‑State Executor**  
2. **Verb Handlers**  

Together they turn an `InterpretedCommand` into a `CommandOutcome`.

---

## 7a. Conversation‑State Executor (Continuation + Ambiguity Resolution)

**Responsibilities:**

- track incomplete or ambiguous commands  
  - “take fish” → “Which fish?”  
  - “give coin” → “Give coin to whom?”  
- track missing semantic roles  
- track ambiguous candidates  
- detect continuation input  
  - “the blue one”  
  - “to the mermaid”  
  - “in the bag”  
- synthesize a completed command and re‑issue it  
- handle implicit verbs  
  - “north” → go north  
  - noun‑only follow‑ups (“the rope”)  

**Non‑responsibilities:**

- no world mutation  
- no capability checks  
- no semantic interpretation  
- no rendering  

The executor is a **conversation manager**, not a world‑mutation engine.

---

## 7b. Verb Handlers (Verb Semantics)

**Responsibilities:**

- implement verb semantics  
- perform capability/state checks  
- run special handler pipeline  
- call noun‑model methods for world mutation  
- apply side effects (e.g., opening exits)  
- construct narrative messages  
- return `CommandOutcome`  

**Non‑responsibilities:**

- no parsing  
- no preposition → role mapping  
- no conversation‑state tracking  
- no low‑level world mutation logic  

Verb handlers decide *what the verb means*, not *how the world is mutated*.

---

## 7c. State‑Changing Verb Framework (Shared Logic)

Many verbs share a common pattern:

- capability check (`is_openable`, `is_lightable`, etc.)  
- state check (`is_open`, `is_lit`, etc.)  
- special handler pipeline  
- state mutation  
- optional side effects  
- message construction  

These verbs (open, close, unlock, light, extinguish, rub, etc.) are unified under a shared helper framework inside the verb layer.

This keeps verb semantics clean and avoids duplication.

---

## 7d. Verb Slot Declarations (Interpreter → Verb Contract)

Each verb may declare the prepositions it accepts and the semantic roles they map to.

These declarations belong to the verb surface in `verb_registration.py` and are stored on `Verb` instances in the verb model. The interpreter reads that metadata when assigning semantic roles.

Example:

```python
Verb("give", inventory.give, role_slots={
  "recipient": ["to", "with"],
  "trade_item": ["for"],
})

Verb("take", inventory.take, role_slots={
  "source": ["from", "in"],
})

Verb("put", inventory.drop, role_slots={
  "destination": ["into", "in"],
  "surface": ["on", "onto"],
})
```

The interpreter uses this registered verb metadata to assign roles automatically.

This removes preposition‑parsing logic from verb handlers.

---

# 8. Game Model Layer (World State and Mutation)

**Responsibilities:**

- represent rooms, exits, items, containers, features, player  
- maintain session state in `Game`  
- support save/load and world reconstruction  
- maintain score and discovery metrics  
- **provide all primitive world‑mutation operations**, including:  
  - moving items between room/inventory/containers  
  - opening/closing/locking/unlocking  
  - updating state attributes  
  - managing container contents  
  - managing exits and passability  
  - updating discovery score  
  - dispatching special handlers  

**Non‑responsibilities:**

- no parsing  
- no semantic interpretation  
- no conversation‑state tracking  
- no rendering  

The noun model *is* the world‑mutation API.

---

# Data Contracts Between Layers

- **Parser output:** `ParsedAction`  
- **Interpreter output:** `InterpretedCommand`  
- **Executor output:** `CommandOutcome`  
- **Verb handler input:** `ExecuteCommand`  
- **Persistent runtime state:** `Game`, `SessionPrefs`  

These contracts are explicit and stable.

---

# Practical Refactor Guidance

- keep orchestration in `engine/exception_handling`  
- keep syntax in parser  
- keep semantic role mapping in interpreter  
- keep verb semantics in verb handlers  
- keep world mutation in noun model  
- keep text shaping in renderer  
- keep continuation logic in executor  

This separation keeps the command pipeline testable, predictable, and maintainable.

