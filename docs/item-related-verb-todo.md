# Kingdom Text Adventure — Updated TODO (Refactor-Safe Ordering)

This list reflects the corrected sequencing: stabilize world verbs → inventory verbs → unify signatures → remove legacy → structural cleanup → puzzle verbs later.

## Phase 0 — Immediate Cleanup (Safe, Low-Risk)
- [ ] Remove unused `words` param or convert to `words: tuple[str, ...] = ()`
- [ ] Switch all messages to `target.get_noun_name()`
- [ ] Remove `Game.boxes` and all references
- [ ] Verify `player.sack` initialization and save/load persistence
- [ ] Add `Room.get_accessible_contents()` helper

## Phase 1 — World-State Verbs (Minimum Playable Set)
- [ ] Add `WorldStateVerbHandler` if not already present
- [ ] Port `look` verb (room look, look at X, look inside X)
- [ ] Confirm world-state verbs share consistent signatures

## Phase 2 — Inventory Verbs (Incremental, Testable)
- [ ] Add `InventoryVerbHandler` skeleton
- [ ] Port `inventory`
- [ ] Port `drop`
- [ ] Port `take` (single item → no-target lookup → take all)

## Phase 3 — Verb Signature Unification (Critical Stabilization)
- [ ] Standardize all verb handlers to:
      `def handle(self, ctx, target=None, words: tuple[str, ...] = ())`
- [ ] Remove or simplify adapters now that signatures match

## Phase 4 — Remove Legacy Verb Layer (Isolated Step)
- [ ] Delete old `*_action` functions
- [ ] Remove legacy verb dispatch wrappers
- [ ] Confirm all verbs route through new handlers

## Phase 5 — Structural Engine Cleanup
- [ ] Break `Verb` out of `Noun` inheritance
- [ ] Update registration and parser to use standalone verbs
- [ ] Add `game.get_all_nouns()` and `game.find_noun_by_name()`
- [ ] Remove reliance on `Noun.all_nouns`

## Phase 6 — Optional Helpers (After Engine Stabilizes)
- [ ] Add `Room.find_item_by_reference(ref)` helper
- [ ] Integrate into `take`, `examine`, and `look inside`

## Phase 7 — Puzzle Verbs (Rebuild Cleanly Later)
- [ ] Design new `PuzzleVerbHandler`
- [ ] Rebuild puzzle verbs from scratch using clean engine patterns
- [ ] Add puzzle-specific behaviors to items/rooms instead of verbs

