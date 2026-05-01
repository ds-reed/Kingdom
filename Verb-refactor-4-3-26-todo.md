# Kingdom Engine Verb System Refactor — Phased TODO Plan

This document outlines the recommended phased approach for modernizing the verb system, interpreter, and executor.  
The goal is to reduce complexity, eliminate duplication, and support multi‑turn continuations while preserving stability.

---

# Phase 0 — Baseline Stabilization (Optional)
**Goal:** Ensure the current system is stable before structural changes.

- [ ] Add lightweight logging around parser → interpreter → executor transitions  
- [ ] Add debug flag to print `InterpretedCommand` and `ExecuteCommand` objects  
- [ ] Add unit tests for TAKE, DROP, GIVE, LOOK, OPEN, CLIMB, SAY, EAT  
- [ ] Add tests for ambiguous noun resolution (“fish”, “key”, “door”)  

---

# Phase 1 — Interpreter Upgrade (Verb Slot System)
**Goal:** Move syntactic complexity out of verb handlers and into the interpreter.

### 1.1 Introduce Verb Slot Declarations
- [ ] Extend `Verb` to carry role-slot metadata (role → accepted prepositions)  
- [ ] Define slot metadata in `verb_registration.py` as part of each verb surface declaration  
- [ ] Add support for multiple roles per verb (e.g., GIVE: recipient + trade_item)  
- [ ] Add support for verbs with no roles (movement, meta, stateful)  

### 1.2 Interpreter Role Assignment
- [ ] Map prepositional phrases → semantic roles using the current verb's registered slot metadata  
- [ ] Validate missing/extra roles  
- [ ] Normalize synonyms (“loot” → take‑all‑from)  
- [ ] Normalize “all/everything” into a modifier  
- [ ] Apply fallback container logic (“take coin” from only open transparent container)  
- [ ] Resolve directions for movement verbs  

### 1.3 Interpreter Output Contract
- [ ] Add `cmd.roles: dict[str, Noun]`  
- [ ] Add `cmd.modifiers: list[str]`  
- [ ] Ensure verb handlers no longer inspect raw preposition lists  

---

# Phase 2 — Executor Upgrade (Conversation State)
**Goal:** Add multi‑turn continuation and ambiguity resolution.

### 2.1 Track Last Attempted Command
- [ ] Store last verb, last roles, last missing role, last candidates  
- [ ] Store original `InterpretedCommand`  

### 2.2 Detect Continuation Input
- [ ] If previous command was incomplete → treat next input as continuation  
- [ ] Resolve ambiguous nouns (“blue one”)  
- [ ] Resolve missing roles (“to the mermaid”)  
- [ ] Resolve implicit verbs (“north”, “down”, “inside”)  

### 2.3 Re‑issue Completed Commands
- [ ] Merge continuation input into previous command  
- [ ] Reconstruct a new `InterpretedCommand`  
- [ ] Re‑run interpreter → executor → verb handler  

### 2.4 Executor Error Handling
- [ ] Standardize error codes for missing roles  
- [ ] Standardize error codes for ambiguity  
- [ ] Ensure verb handlers return structured errors the executor can use  

---

# Phase 3 — State‑Changing Verb Framework
**Goal:** Consolidate duplicated logic across OPEN/CLOSE/UNLOCK/LIGHT/etc.

### 3.1 Create Declarative Table
- [ ] Define `STATE_VERBS = { verb: {capability, state_attr, desired_state, already_msg, requires_item, side_effect} }`  
- [ ] Mark special verbs (tie, hit, turn) as `custom=True`  

### 3.2 Implement `_run_state_change()`
- [ ] Handle modifier checks  
- [ ] Handle missing target  
- [ ] Run special handler pipeline  
- [ ] Run capability/state checks  
- [ ] Run required‑item checks  
- [ ] Apply state mutation  
- [ ] Apply side effects  
- [ ] Build final message list  

### 3.3 Migrate Verbs
- [ ] open  
- [ ] close  
- [ ] unlock  
- [ ] light  
- [ ] extinguish  
- [ ] rub  
- [ ] tie (custom)  
- [ ] hit (custom)  
- [ ] turn (custom)  

---

# Phase 4 — Inventory Verb Simplification
**Goal:** Rewrite TAKE, DROP, GIVE, TRADE, PUT using interpreter roles + noun model.

### 4.1 Rewrite TAKE
- [ ] Use `cmd.roles.get("source")`  
- [ ] Use modifiers for “all”  
- [ ] Remove preposition parsing logic  
- [ ] Remove fallback container logic (interpreter now handles it)  

### 4.2 Rewrite DROP
- [ ] Use `cmd.roles.get("destination")`  
- [ ] Remove preposition parsing logic  

### 4.3 Rewrite GIVE / TRADE
- [ ] Use `cmd.roles.get("recipient")`  
- [ ] Use `cmd.roles.get("trade_item")`  
- [ ] Remove all preposition parsing logic  
- [ ] Remove trade‑specific parsing logic  

### 4.4 Rewrite PUT / INSERT
- [ ] Use `destination` and `surface` roles  
- [ ] Remove preposition parsing logic  

---

# Phase 5 — Stateful Verb Cleanup
**Goal:** Clean up verbs like LOOK, SAY, EAT, LISTEN.

### 5.1 LOOK
- [ ] Use interpreter roles for “look in”  
- [ ] Remove ad‑hoc preposition parsing  
- [ ] Simplify container logic  

### 5.2 SAY
- [ ] Use capability flags only  
- [ ] Remove ad‑hoc “wish” logic (move to special handler)  

### 5.3 EAT
- [ ] Use capability flags  
- [ ] Remove inventory checks duplicated across verbs  

### 5.4 LISTEN
- [ ] Use capability flags  
- [ ] Simplify room vs item logic  

---

# Phase 6 — Movement Verb Review (Optional)
**Goal:** Keep movement verbs clean and consistent.

- [ ] Ensure interpreter handles direction resolution  
- [ ] Ensure verb handlers handle movement semantics  
- [ ] Ensure noun model handles exit passability  

---

# Phase 7 — Final Cleanup and Documentation
**Goal:** Consolidate and document the new architecture.

- [ ] Update architecture document (done!)  
- [ ] Add developer guide for writing new verbs  
- [ ] Add examples of verb slot declarations  
- [ ] Add examples of continuation flows  
- [ ] Add unit tests for continuation logic  
- [ ] Add unit tests for state‑changing verbs  
- [ ] Add unit tests for inventory verbs  

---

# Phase 8 — Stretch Goals (Future)
**Optional enhancements:**

- [ ] Multi‑verb commands (“take lamp and coin”)  
- [ ] Pronoun resolution (“take it”, “open them”)  
- [ ] Contextual implicit verbs (“climb rope” → climb up)  
- [ ] NPC interaction verbs (“ask”, “tell”, “talk to”)  
- [ ] Scriptable verb behaviors in JSON  

---

# Summary

This phased plan ensures:

- minimal breakage  
- maximum clarity  
- incremental improvements  
- clean separation of concerns  
- a modern, maintainable verb system  
- support for multi‑turn conversations and ambiguity resolution  

It’s the roadmap to the engine you’ve been evolving toward — now formalized and ready to implement.

