# TRS-80 Castle Legacy Spirit Guide (Modern Port Notes)

This is a modern design companion mined from the original TRS-80 BASIC source.

Goal: preserve the spirit of early home computing adventure design (puzzle flavor, terse feedback, quirky world reactions) without recreating the brittle, hardcoded control flow.

## Source Mined

- `docs/TRS80-basic source/Castle-main/Castle_1.BAS` through `Castle_7.BAS`
- `docs/TRS80-basic source/Castle-main/decoder_ring`

## Legacy Verb Corpus (as declared in source)


From `Castle_1.BAS` DATA tables:

 movement/core: GO, WALK, LOOK, SLIDE, GET, TAKE, DROP, THROW, INVENTORY, INVEN
 interaction: READ, OPEN, KICK, KNOCK, INSERT, SHOOT, CLIMB, QUIT, UNLOCK, CLOSE
 puzzle/system: TURN, RUN, LIGHT, SCORE, WASH, SWIM, PUSH, DIAL, EAT
 action/edge: SMASH, BREAK, DRINK, RUB, DRAG, SAVE, SKIP, KILL, PRESS
 traversal rope: SWING, UNTIE, TIE
## What the Old Game Did Well (Worth Keeping)

- Strong command personality (specific prompts like “READ WHAT?”, “INSERT IT INTO WHAT?”)
- Puzzle verbs linked tightly to room/object state (rope, crank, hidden openings, trapdoor)
- Memorable consequences and humor (danger, odd responses, dramatic flavor)
- Verb flexibility via synonyms (GET/TAKE, PUSH/PRESS, etc.)
- “Special verbs as traversal” pattern (SWIM, SWING) for non-obvious movement routes

## Legacy Behaviors with High Reuse Value

- **Read as clue delivery**
  - Book-specific messages and context-sensitive text
- **Shoot with explicit fallback**
  - “Shoot in the air” allowed; target-specific branch for warden
- **Insert as context-sensitive puzzle action**
  - Requires object context and often “into what” prompting
- **Rope state machine (tie/untie/swing)**
  - Tie state and prior room influence what traversal is possible
- **Drink/Eat as world-state changers**
  - Not only inventory consumption; can alter player state (size)
- **Drag as heavy-object interaction**
  - Distinct from pickup; dead-warden/body constraints

## Variable Concepts to Preserve (Rename, Don’t Copy)

Old variables like `N1`, `N2`, `A$(8)`, `TA`, `IS`, `BL` are useful conceptually, but should be represented as named fields:

- `current_room_id`, `previous_room_id`
- object/room state enums (instead of magic values in one slot)
- `warden_alert_state`
- `hero_size_state`
- `ammo_count`
- `rope_state` (tied, carried, spanning, detached)

## Modern Translation Rules (Guardrails)

1. **Data-driven first**
   - Add JSON fields and object behavior hooks before writing verb-specific branch ladders.
2. **Object handles behavior**
   - Keep verb handlers thin; route special behavior to item/room/actor logic.
3. **Prompt quality matters**
   - Preserve concise “WHAT?” feedback style where it improves command UX.
4. **Separate traversal from visibility**
   - Keep hidden exits traversable when discovered or invoked by special verbs.
5. **Prefer state names over flag bytes**
   - No encoded multi-meaning status bytes in modern code.

## Suggested Implementation Order (Low Risk)

1. Read (data-driven readable text)
2. Push/Press (button/switch hooks)
3. Turn (crank/key generalized turnables)
4. Break/Smash (breakable object state)
5. Shoot (ammo + air shot + target hook)
6. Rope package: tie/untie/swing
7. Drink/Eat size system + size-gated room behavior
8. Drag/Kill + warden encounter integration

## Tone & Spirit Checklist

When implementing a verb, keep at least one of these:

- a short, distinctive response line
- a surprising world reaction
- a room/object-specific branch
- a consequence that feels physical (noise, weight, visibility, movement)

That preserves the “home-computing adventure” feel while still using maintainable modern architecture.
