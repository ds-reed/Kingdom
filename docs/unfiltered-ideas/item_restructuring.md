# World Architecture Summary: Items, Lexical Nouns, Portals, and Handles

## Overview
The world model distinguishes between **first‑class items**, **structural features**, and **lexical nouns**. This separation keeps the parser deterministic, reduces world‑authoring burden, and supports complex traversal mechanics such as ropes, ladders, and doors without cluttering the world JSON.

---

## Item Identity and Naming
Items now have three orthogonal identities:

- **Handle**: the unique, stable identifier used internally by the engine.  
- **Canonical name**: the linguistic identity used by the parser.  
- **Display name**: the player‑facing description.

Handles are human‑readable and author‑controlled when needed. A systematic prefix derived from the canonical name groups similar items, and the world builder ensures uniqueness by adding suffixes when necessary.

Only true items require handles. Lexical nouns do not.

---

## Lexical Nouns
Lexical nouns are built‑in vocabulary entries that represent structural features of rooms. They are always available to the parser and do not appear in the world JSON.

Examples include walls, doors, ladders, staircases, poles, hatches, and similar features tied to a direction or room geometry.

Lexical nouns:
- Require no handles  
- Carry no state  
- Provide parse targets for common environmental objects  
- Are automatically tied to room exits or directions  
- Are overridden when a real item with the same canonical name exists in the room  

This allows the world to have many doors, ladders, and staircases without requiring the author to create dozens of item entries.

---

## Real Items Override Lexical Nouns
When a real item with a matching canonical name exists in a room, it masks the corresponding lexical noun. This gives the item full behavioral control.

Examples:
- A talking door item overrides the lexical “east door.”  
- A broken ladder item overrides the lexical “up ladder.”  
- A rope tied to a hook overrides the lexical “down ravine.”

This keeps the parser’s resolution path consistent: real items first, lexical nouns second.

---

## Structural vs. Portable Traversal Mechanisms
Traversal mechanisms fall into two categories:

### Structural Traversal
These are built into the environment and are not portable. Examples include fixed ladders, staircases, fireman’s poles, and most doors.

Structural traversal is represented by:
- Room exits  
- Lexical nouns tied to those exits  
- Optional item overrides when special behavior is needed  

These features do not require handles unless they become real items.

### Portable Traversal
These are true items that can be carried, moved, tied, or otherwise manipulated. Examples include ropes, portable ladders, chains, and vines.

Portable traversal items:
- Have handles  
- Can span multiple rooms  
- Can dynamically create or remove traversal opportunities  
- Can override lexical nouns when active  

This supports complex interactions such as tying a rope to a hook to create a climbable path.

---

## Multi‑Room Items
Items can appear in multiple rooms simultaneously. This is essential for ropes, ladders, and other span objects.

A multi‑room item:
- Has a single handle  
- Appears in all rooms listed in its location set  
- Carries its own state  
- Provides traversal behavior when appropriate  

This ensures that climbing up or down a ladder or rope works symmetrically without duplicating objects.

---

## Portal Behavior
Traversal logic can originate from two places:

### Structural Portals
Defined by room exits. These represent built‑in traversal such as staircases or fixed ladders. Lexical nouns reference these exits when no item is present.

### Item‑Driven Portals
Defined by items that create traversal opportunities. Examples include ropes tied to hooks or portable ladders placed between rooms.

Item‑driven portals:
- Are activated by item state  
- Can appear or disappear dynamically  
- Override lexical nouns when active  
- Support multi‑room presence  

This allows portable items to modify the world’s traversal graph cleanly and predictably.

---

## World Builder Responsibilities
The world builder ensures:
- Handle uniqueness  
- Consistent prefixing based on canonical names  
- Automatic suffixing when duplicates occur  
- Clean grouping for disambiguation  

This reduces authoring burden while keeping handles readable and meaningful.

---

## Parser Resolution Path
When resolving a noun phrase:
1. Match canonical name.  
2. Look for real items in the room.  
3. If none exist, fall back to lexical nouns.  
4. Apply disambiguation using handle prefixes and context.  

This guarantees deterministic behavior and clean override semantics.

---

## Closing Thought
This architecture balances expressive power with authoring simplicity. The remaining design choice is how large the built‑in set of lexical nouns should be and whether any should be generated dynamically from room exits.
