# **Castle Warden System — Implementation Checklist (Modern Mode)**

## **1. Global Warden State**
- **TA** — warden presence/alive flag  
  - `1` = warden present this turn  
  - `0` = warden absent or dead  
- **T2** — darkness danger counter  
- **T4** — banana‑peel trap active flag  
- **Corpse state** stored in room data (equivalent to `A$(8)` and `A$(9)`)

## **2. Warden Spawn Conditions**
### **Patrol Spawn**
- Applies only in **patrolled rooms** (originally rooms 7–87).
- Triggered after movement or LOOK.
- Approx. **15% chance** per turn.
- If triggered:
  - Warden enters room.
  - Immediate attack.

### **Darkness Noise Spawn**
- Applies when:
  - Room is dark, **and**
  - Player has no light source.
- Each turn in darkness:
  - Increment `T2`.
  - First two turns: harmless warnings.
  - After that:
    - 60% chance: “danger” warning.
    - Otherwise: **noise event** → warden appears → immediate attack.

### **Collision Spawn**
- If player moves blindly in darkness and collides with warden:
  - “Crush his toes” event.
  - Immediate attack.

## **3. Warden Attack Behavior**
- Every warden encounter triggers an immediate shot.
- **30% chance** the shot hits and kills the player.
- If he misses:
  - TA remains `1`.
  - Player may act again.

## **4. Player Actions Against the Warden**
### **Clubbing**
- Requires **item #4** (club).
- If TA = 1 and target is “WARDEN”:
  - Warden dies instantly.
  - TA = 0.
  - Corpse state set in room.

### **Shooting**
- Requires gun + bullets (`BL > 0`).
- Shooting “WARDEN”:
  - Always kills him.
  - TA = 0.
  - Corpse state set.

### **Banana Peel Trap**
- Item #19 = banana peel.
- Dropping peel sets `T4 = 1`.
- If warden enters room while `T4 = 1`:
  - Instant death.
  - TA = 0.
  - T4 = 0.

## **5. Warden Death Handling**
- Set TA = 0.
- Update corpse state in room.
- Prevent repeated kills.
- Dragging corpse prints refusal message.
- Warden does **not** respawn.

## **6. Warden Escape Logic**
### **Rope Swing Escape**
- If player uses rope‑swing exit while TA = 1:
  - Print escape message.
  - **TA = 0** (warden loses track of player).
  - Warden does not follow.

## **7. Darkness System**
- Darkness applies only in dark rooms without light.
- `T2` increments each turn.
- Behavior:
  - Turns 1–2: “cannot see” warnings.
  - Turn ≥3:
    - 60% chance: “danger” warning.
    - Otherwise: noise → warden spawn.

## **8. Turn‑Based Limiter**
- TA prevents multiple warden events in a single turn.
- Reset TA at end of turn unless warden is actively present.

## **9. Persistence**
- Warden state persists across:
  - Save/load
  - Clone/continue
  - Room transitions
- Corpse state stored in room data.

## **10. Required Data Structures (Modern Engine)**
- `room.is_patrolled`
- `room.is_dark`
- `room.has_corpse`
- `player.has_light`
- `player.inventory`
- `warden.state` (alive, dead, present)
- `warden.in_room`
- `warden.spawn_reason` (patrol, noise, collision)
- `banana_peel.active`

## **11. Required Systems to Implement**
- Patrol system  
- Darkness escalation system  
- Noise generation system  
- Collision detection in darkness  
- Warden spawn manager  
- Warden attack resolver  
- Player combat actions (club, shoot)  
- Banana peel trap logic  
- Warden death handler  
- Rope‑swing escape handler  
- Persistence layer for warden/corpse state  
