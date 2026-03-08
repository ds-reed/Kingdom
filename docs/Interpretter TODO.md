# Interpreter and Executor TODO  
_Semantic Interpretation and Execution Pipeline_

This document defines the responsibilities, structure, and implementation plan for the **Interpreter** and **Executor** layers. These layers convert syntactic `ParsedActions` into semantic `InterpretedCommands`, apply verb behavior to the world, and produce `CommandOutcome` objects for the renderer.

---

# 1. Goals of the Interpreter + Executor

- interpret the player’s intent  
- resolve references to world objects  
- detect and resolve ambiguity  
- classify directions and prepositional phrases  
- enforce verb argument rules  
- preserve the exact words the player typed  
- expand “all” when appropriate  
- prepare clean semantic structures for execution  
- apply verb behavior to the world  
- produce narrative messages and world effects  

---

# 2. Interpreter (Semantic Layer)

The Interpreter converts each `ParsedAction` into **zero, one, or many InterpretedCommands**.  
This step is **pure**, **deterministic**, and **side‑effect‑free**.

---

## 2.1 Responsibilities

- Confirm and interpret the verb  
- Resolve noun phrases to world objects  
- Detect ambiguity (multiple matching objects)  
  - resolve via heuristics, or  
  - mark command as ambiguous  
- Interpret direction tokens  
- Classify prepositional phrases  
- Interpret modifiers and quantifiers  
- Enforce verb argument rules  
- Preserve surface forms  
- Attach semantic diagnostics  
- Expand “all” only if `verb.supports_all_expansion == True`  
- Otherwise pass “all” to the verb handler for special behavior  

---

## 2.2 Verb Flag: `supports_all_expansion`

Each verb defines:

```
supports_all_expansion: bool
```

Meaning:

- **True** → Interpreter expands ALL into multiple InterpretedCommands  
- **False** → Interpreter leaves ALL as a modifier; verb handler decides behavior  

Examples:

- take → True  
- drop → True  
- put → True  
- light → False  
- attack → False  
- eat → False  

---

## 2.3 Output: `InterpretedCommand`

### Verb
- `verb`: `VerbEntry`  
- `verb_token`: player‑typed verb  

### Direction
- `direction`: canonical  
- `direction_token`: player‑typed  

### Targets (Direct, Indirect, Location)
Each target is a `InterpretedTarget`:

```
InterpretedTarget:
    object: WorldObject
    surface_phrase: str
    surface_head: str
    surface_adjectives: List[str]
    canonical_head: str
```

Fields:
- `direct: Optional[InterpretedTarget]`
- `indirect: Optional[InterpretedTarget]`
- `location: Optional[InterpretedTarget]`

### Modifiers
- `modifiers: List[str]`  
- `modifier_tokens: List[str]`  

### Diagnostics
- `diagnostics: List[str]`

### Raw Input
- `raw_text: str`

`InterpretedCommand` is **immutable**.

---

# 3. Executor (Action Layer)

The Executor takes a single `InterpretedCommand` and applies the verb’s behavior to the world.

---

## 3.1 Responsibilities

- Invoke the correct verb handler  
- Apply world changes  
- Generate execution messages  
- Generate execution diagnostics  
- Determine whether the room should be re-rendered  

---

## 3.2 Output: `CommandOutcome`

```
CommandOutcome:
    Interpreted: InterpretedCommand
    messages: List[str]
    effects: WorldDelta
    diagnostics: List[str]
    should_render_room: bool
```

Renderer consumes only this object.

---

# 4. Interpreter TODO (Implementation Plan)

- Implement `InterpretedCommand` and `InterpretedTarget` dataclasses  
- Add `supports_all_expansion` to Verb class  
- Implement verb resolution  
- Implement direction resolution  
- Implement noun phrase resolution  
- Implement ambiguity detection  
- Implement prepositional phrase classification  
- Implement modifier handling  
- Implement ALL expansion logic  
- Enforce verb argument rules  
- Produce final `InterpretedCommand` objects  

---

# 5. Executor TODO (Implementation Plan)

- Implement `CommandOutcome` dataclass  
- Implement verb dispatch  
- Implement verb handlers  
- Implement world mutation logic  
- Implement room re-render logic  

---

# 6. Testing Strategy

- Unit tests for Interpreter (pure)  
- Unit tests for Executor (world mutation)  
- Integration tests for multi‑action sequences  
- Tests for ALL expansion vs. ALL override  
- Tests for ambiguous nouns, invalid directions, missing objects  

---

# 7. Milestone: One Verb End-to-End

Implement full pipeline for one verb (recommended: **take** or **go**):

- ParsedAction → InterpretedCommand → CommandOutcome → rendered output  

This stabilizes the architecture before Stage 4 parser work.
