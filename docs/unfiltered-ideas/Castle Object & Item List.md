# 🧱 Castle Object & Item List (Reconstructed from Source)

This list merges items explicitly referenced in verb handlers, items referenced in inventory logic (`NP()`), items referenced in room state (`A$()`), items referenced in the object‑index printout, and items referenced in puzzles (rope, plum, plum pit, etc.). Where behavior is known, it’s included. Where behavior is only implied, it’s marked.

## **1. Core Items (Confirmed by Code)**

| ID | Name | Behavior / Notes |
|----|------|------------------|
| **1** | (Swimming flag) | Not a real item; used to track underwater state. |
| **2** | **Key** | Unlocks trapdoor in Rooms 1–2. Likely dropped by guard. |
| **3** | **Torch** | Light source; interacts with darkness system. |
| **4** | **Club** | Kills warden instantly; used in some KICK/SMASH actions. |
| **5** | **Dime** | Used in phone; phone is broken. |
| **6** | **Lighter** | Lights torch. |
| **7** | **Fish** | Eating causes vomiting; may increase score. |
| **8** | **Newspaper** | READ prints boring tax news. |
| **9** | **Carrot** | Screams when eaten; sets I9=9. |
| **10** | **Book** | Pig Latin; unreadable. |
| **11** | **Liquid / Bottle** | DRINK triggers growth/shrink logic. |
| **12** | **Cake** | Shrinks player; may cause falling death. |
| **13** | **Mushroom** | Growth/shrink logic. |
| **14** | **Lamp** | RUB summons genie in Room 73. |
| **15** | **Purse** | Magic purse; infinite coins. |
| **16** | **Plum** | Eating reveals ruby (item 17). |
| **17** | **Ruby (Plum Pit)** | Appears after eating plum. |
| **18** | **Potion** | From object list; behavior not implemented. |
| **19** | **Banana Peel** | Dropping activates T4=1; kills warden if he enters. |
| **20** | **Gem** | Decorative; cannot be taken. |

## **2. Environmental / Room Objects (From Object Index)**

These are not inventory items but appear in rooms:

| ID | Object | Notes |
|----|---------|-------|
| **1** | Guard | Blocks Room 2; killable; likely drops key. |
| **2** | Princess | Not referenced in verb logic; likely rescue objective. |
| **3** | Dragon | Not referenced; likely hazard or puzzle. |
| **4** | Treasure | Scoring object. |
| **5** | Wall | For LOOK/KICK messages. |
| **6** | Door | Many rooms have doors; OPEN/CLOSE logic. |
| **7** | Window | Room 18 has special ASCII art view. |
| **8** | Ladder | Climbable? Verb CLIMB exists. |
| **9** | Rope | Used in rope swing puzzle. |
| **10** | Key | Environmental version of item #2. |
| **11** | Sword | Not referenced in verbs; may be cut content. |
| **12** | Shield | Same as above. |
| **13** | Map | READ? Not implemented. |
| **14** | Compass | Possibly decorative. |
| **15** | Torch | Environmental version of item #3. |
| **16** | Book | Environmental version of item #10. |
| **17** | Scroll | READ? Not implemented. |
| **18** | Potion | DRINK? Not implemented. |
| **19** | Ring | Decorative. |
| **20** | Gem | Decorative. |

---

# 🧱 Castle Verb List (Reconstructed from Source)

This list merges the verb DATA tables (lines 700–1100), the ON‑GOTO verb dispatch tables (lines 2600–3000), special-case verbs (QUIT, SCORE, SAVE, etc.), and hidden verbs (LD → LOOK).

## **1. Movement Verbs**
- GO  
- WALK  
- RUN  
- SLIDE  
- CLIMB  
- SWIM  
- IN / OUT  
- UP / DOWN  
- LEFT / RIGHT  
- NORTH / SOUTH / EAST / WEST  
- EXIT  

## **2. Interaction Verbs**
- LOOK  
- READ  
- OPEN  
- CLOSE  
- UNLOCK  
- INSERT  
- PUSH  
- TURN  
- PRESS  
- KNOCK  
- KICK  
- SMASH  
- BREAK  
- TIE  
- UNTIE  
- DIAL  
- LIGHT  
- TORCH (alias)  
- RUB  
- DRAG  
- SWING  

## **3. Inventory Verbs**
- GET  
- TAKE  
- DROP  
- THROW  
- INVENTORY / INVEN  
- SAVE  
- SKIP  

## **4. Combat Verbs**
- KILL  
- SHOOT  
- (CLUB via KICK/SMASH logic)  

## **5. Consumption Verbs**
- EAT  
- DRINK  

## **6. Meta Verbs**
- QUIT  
- SCORE  
- PRINT (debug?)  
- PLEASE (easter egg)  
- NO (easter egg)  
- PLUGH / MUZZY (easter eggs)  
