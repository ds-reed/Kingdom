
### Summary of Naming Patterns Discussion (Final Leaning)

**Core Goal**  
Create readable, consistent, beautiful English-like state keys for `state_descriptions` while preserving uniformity in code (e.g. `can_open`, `is_open`) and avoiding invented words like "breaked".

**Final Preferred Direction**  
- Use **real English past participles / adjectives** in state keys (not base forms or computerish "not_open")
- Prefer natural-sounding words even when irregular ("lit" not "lighted", "broken" not "breaked", "worn" not "weared")
- Use **comma-separated** participles for combined states (e.g. open + lock)
- Order: usually most salient state first (open/closed before locked/unlocked)

**Leaning Toward These Key Styles**
- "opened,locked"
- "not_opened,locked"
- "not_opened,unlocked"
- "opened"                 (when lock state irrelevant or impossible)
- "lit"
- "not_lit"
- "broken"
- "not_broken"
- "worn"

**Why this won over alternatives**
- Avoids fake words ("breaked", "eated") → preserves English beauty
- More natural than base forms ("open,locked") or boolean-ish ("state:open=false,locked=true")
- Still machine-friendly and consistent (comma separator, predictable generation)
- Handles irregular verbs gracefully via small central lookup table

**Central Lookup Table (VERB_MUTATIONS)**
- Static dict loaded at init
- Maps base verb → positive/negative forms + already-message adjectives
- Example:
  - "open":   positive="opened", negative="closed", already_positive="open", already_negative="closed"
  - "light":  positive="lit",    negative="extinguished" / "not_lit"
  - "break":  positive="broken", negative="intact" / "not_broken"
- Regular verbs can fall back to auto-generated "verb + 'ed'" / "not_ + verb + 'ed'"
- Used for:
  - Generating state keys at runtime
  - Building natural "already" messages ("It's already lit.", "It's already broken.")

**Scope**
- Only applies to **persistent, reversible state verbs** (open/close, lock/unlock, light/extinguish, wear/remove, break/repair?, etc.)
- One-way destructive actions (eat, drink, destroy) stay outside this pattern — no persistent "eaten" or "drinked" states

**Overall Philosophy**
Prioritize readable, natural English in JSON keys and messages  
→ accept small, centralized exceptions for irregular verbs  
→ keep `can_verb` / `is_verb` uniformity in attributes  
→ generate keys/messages from lookup rather than hardcoding participles everywhere




{
  "name": "Heavy Stone Door",
  "noun_name": "door",

  "description": "A massive stone door carved with ancient runes blocks the way north.",

  "can_get": false,

  // Open / Close
  "can_open": true,
  "is_open": false,

  "open": {
    "msg": "With a low grinding sound, the heavy stone door swings open.",
    "already_msg": "The door is already open.",
    "rev_msg": "You push the massive door closed with effort.",
    "rev_already_msg": "The door is already closed."
  },

  // Lock / Unlock
  "can_lock": true,
  "is_locked": true,

  "lock": {
    "msg": "You turn the heavy iron key and hear a satisfying click as the door locks.",
    "already_msg": "The door is already locked.",
    "rev_msg": "The lock mechanism releases with a dull thunk.",
    "rev_already_msg": "The door is already unlocked."
  },

  // State-dependent descriptions
  "state_descriptions": {
    "opened": "The heavy stone door stands open, revealing a dark corridor beyond.",
    "not_opened,locked": "The heavy stone door is closed and firmly locked.",
    "not_opened,unlocked": "The heavy stone door is closed but appears unlocked.",
    "opened,locked": "The heavy stone door is open, though strangely still locked in place.",
    "default": "A massive stone door carved with ancient runes blocks the way north."
  },

  // Side effect when opened
  "open_exit": {
    "direction": "north",
    "destination": "Ancient Corridor",
    "rev_hides": true
  },

  // Optional: custom refusal or extra flavor
  "open_refuse_if_locked": "The door won't budge — it's locked tight.",
  "examine_locked": "The door is secured with a large iron lock that looks very old."
}
