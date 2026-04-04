# Kingdom Engine — Verb Slot System Specification  
### **Semantic Role Mapping for Prepositional Phrases**

This document defines the **Verb Slot System**, a declarative mechanism used by the Semantic Interpretation Layer to map prepositional phrases into **semantic roles** for verb handlers.

The authoritative source of slot metadata is the verb surface definition in `verb_registration.py`, carried at runtime by `Verb` instances in the verb model. The interpreter consumes this metadata; it does not define per-verb slot tables itself.

The goal is to:

- remove preposition‑parsing logic from verb handlers  
- unify TAKE / DROP / GIVE / TRADE / PUT / LOOK semantics  
- support multi‑role verbs cleanly  
- support continuation and ambiguity resolution  
- keep the parser responsible for *syntax*, the interpreter responsible for *semantic resolution*, and verb handlers responsible for *meaning*  

This system is central to the modernized command pipeline.

---

# 1. Overview

Many verbs accept **prepositional phrases** that modify their meaning:

- “take coin **from** chest”  
- “give coin **to** mermaid **for** clam”  
- “put cat **into** bag **on** table”  
- “look **in** chest”  

The Verb Slot System allows each verb to declare:

- which prepositions it accepts  
- which **semantic role** each preposition fills  
- whether multiple roles are allowed  
- whether roles are required or optional  

The interpreter uses these declarations to produce:

```python
cmd.roles = {
    "source": <container>,
    "recipient": <npc>,
    "trade_item": <item>,
    "destination": <container>,
    "surface": <item>,
}
```

Verb handlers then read `cmd.roles` instead of parsing raw prepositions.

---

# 2. Data Structure

The system is defined on each registered verb:

```python
Verb(
    "<verb>",
    handler,
    synonyms=[...],
    modifiers=[...],
    uses_directions=False,
    role_slots={
        "<role_name>": ["prep1", "prep2", ...],
    },
)
```

### Example:

```python
Verb("take", inventory.take, role_slots={"source": ["from", "in"]})
Verb("drop", inventory.drop, role_slots={"destination": ["into", "in", "onto", "on"]})
Verb("give", inventory.give, role_slots={"recipient": ["to", "with"], "trade_item": ["for"]})
Verb("put", inventory.drop, role_slots={"destination": ["into", "in"], "surface": ["on", "onto"]})
Verb("look", stateful.look, role_slots={"container": ["in", "inside"]})
```

`verb_registration.py` is the single source of truth for verb surface metadata:

- canonical verb names
- synonyms
- allowed modifiers
- direction usage
- semantic roles and accepted prepositions

The `Verb` model stores and exposes that metadata to the interpreter.

---

# 2.1 Interpreter Output Contract

The interpreter emits an `InterpretedCommand` that includes role-aware fields.

Required for slot-based verbs:

```python
cmd.roles: dict[str, object]  # resolved world objects keyed by semantic role
cmd.modifiers: list[str]      # normalized modifiers (including "all")
```

Transitional compatibility (allowed during migration only):

```python
cmd.prep_phrases: list[dict]  # legacy shape retained temporarily for older handlers
```

Migration rule:

- New or refactored handlers read only `cmd.roles` and `cmd.modifiers`.
- `cmd.prep_phrases` remains read-only legacy data until all target handlers are migrated, then it can be removed from handler usage.

---

# 3. Interpreter Responsibilities

When the interpreter receives a `ParsedAction`, it:

### 3.1 Matches prepositions to roles  
For each `(prep, noun)` pair:

- inspect the current verb's registered `role_slots`
- find which role the preposition belongs to
- resolve the noun to a world object
- assign it to `cmd.roles[role]`

### 3.2 Validates role usage  
- unknown prepositions → error  
- duplicate roles → error  

Role requiredness is verb-semantic and is enforced by verb handlers (not interpreter).

### 3.3 Normalizes synonyms  
Examples:

- “loot chest” → `verb="take"`, `modifiers=["all"]`, `roles={"source": chest}`  
- “search chest” → `verb="look"`, `roles={"container": chest}`  

### 3.4 Handles fallback container logic  
If TAKE has no explicit `source` role but **exactly one open *transparent* container** in the room contains the target item, the interpreter automatically fills:

```python
cmd.roles["source"] = that_container
```

Notes:

- This fallback **only applies to transparent containers**, because their contents are visible without opening them.
- Opaque containers require explicit player intent (“take coin from chest”).
- If multiple transparent containers contain matching items, the interpreter reports ambiguity instead of guessing.
- Verb handlers no longer implement this logic; they simply read `cmd.roles["source"]`.


### 3.5 Handles “all/everything”  
Interpreter normalizes these into:

```python
cmd.modifiers.append("all")
```

### 3.6 Handles direction resolution  
Movement verbs do not use slots, but interpreter still resolves directions.

---

# 4. Verb Handler Responsibilities

Verb handlers **do not** parse prepositions.

They simply read:

```python
source = cmd.roles.get("source")
recipient = cmd.roles.get("recipient")
destination = cmd.roles.get("destination")
surface = cmd.roles.get("surface")
trade_item = cmd.roles.get("trade_item")
```

Verb handlers decide:

- what the verb *means*  
- what world mutations to perform  
- what messages to return  

They do **not**:

- resolve nouns  
- interpret prepositions  
- track conversation state  
- mutate world state directly (they call noun methods)  

---

# 5. Executor Responsibilities (Continuation)

The executor uses the slot system to support multi‑turn commands:

### Example: Ambiguity  
```
> take fish
Which fish?
> the blue one
```

Executor:

- sees TAKE was missing a resolved direct object  
- sees “blue one” matches one candidate  
- reconstructs: `take blue fish`  
- re‑issues the command  

### Example: Missing role  
```
> give coin
Give coin to whom?
> mermaid
```

Executor:

- sees GIVE was missing role “recipient”  
- fills `cmd.roles["recipient"] = mermaid`  
- re‑issues the command  

The slot system makes this trivial because roles are explicit.

---

# 5.1 Minimal Ambiguity Contract (Interpreter → Executor)

The interpreter does not choose among equally valid noun matches. It returns structured ambiguity context for the executor.

Minimum contract for ambiguous references:

- `code="ambiguous_target"` (or role-specific variant such as `ambiguous_recipient`)
- `details["role"]` with the affected role name (`direct`, `source`, `recipient`, etc.)
- `details["token"]` with the player token that was ambiguous
- `details["candidates"]` as an ordered list of candidate handles/descriptors

Executor behavior:

- ask a clarification question
- preserve the pending command state
- merge follow-up input into the missing/ambiguous role and re-issue

Interpreter behavior:

- deterministic candidate ordering
- no hidden auto-pick when multiple candidates remain

---

# 6. Required vs Optional Roles

By default, roles are **optional**.

Verb handlers decide whether a role is required.

Example:

- TAKE: `source` optional  
- DROP: `destination` optional  
- GIVE: `recipient` required  
- PUT: `destination` required, `surface` optional  

Verb handlers return structured errors:

```python
return self.outcome_missing_prep_target("Give coin to whom?", code="missing_recipient")
```

The executor uses these to trigger continuation mode.

---

# 7. Multi‑Role Example: PUT

Command:

```
put cat into bag on table
```

Interpreter produces:

```python
cmd.roles = {
    "destination": <bag>,
    "surface": <table>
}
```

Verb handler:

```python
dest = cmd.roles.get("destination")
surf = cmd.roles.get("surface")
```

No preposition parsing required.

---

# 8. Multi‑Verb Example: GIVE / TRADE

Command:

```
give coin to mermaid for clam
```

Interpreter:

```python
cmd.roles = {
    "recipient": <mermaid>,
    "trade_item": <clam>
}
```

Verb handler:

```python
recipient = cmd.roles["recipient"]
trade_item = cmd.roles.get("trade_item")
```

---

# 9. Movement and Meta Verbs

Movement verbs (go, climb, swim, teleport)  
and meta verbs (help, debug, score, save, load)  
**do not use verb slots**.

Interpreter handles:

- direction resolution  
- noun resolution (debug/help)  

Verb handlers handle semantics.

---

# 10. Adding a New Verb

To add a new verb with prepositional roles:

1. Register the verb in `verb_registration.py` with `role_slots` metadata  
2. Implement verb handler using `cmd.roles`  
3. Do **not** parse prepositions in the verb  
4. Let interpreter handle synonyms and fallback logic  
5. Let executor handle continuation  

Example:

```python
Verb(
    "attach",
    attach_handler,
    role_slots={
        "target": ["to", "onto"],
        "tool": ["with"],
    },
)
```

---

# 11. Summary

The Verb Slot System:

- centralizes preposition logic  
- simplifies verb handlers  
- supports multi‑turn commands  
- supports ambiguity resolution  
- keeps parser focused on syntax and interpreter focused on semantic resolution  
- keeps verb handlers focused on semantics  
- keeps noun model focused on world mutation  

It is the backbone of the modernized verb architecture.

---

# 12. Definition of Done (Interpreter Contract Gate)

Before starting large verb-handler rewrites, all of the following should be true:

- `InterpretedCommand` exposes `roles` and normalized `modifiers` for slot-based verbs.
- Slot-mapped commands no longer require handler-side preposition parsing.
- Unknown prepositions and duplicate role assignments produce structured errors.
- Ambiguous noun resolution produces structured ambiguity context (no silent global fallback).
- Transparent-container fallback behavior is preserved exactly as specified in section 3.4.
- Regression tests cover TAKE/DROP/GIVE role mapping plus at least one ambiguity case.