# Kingdom

An object-oriented game-world simulation in Python. Kingdom is a structured game engine that allows you to model a fantasy world with items, containers, rooms, and player characters. This is just a framework for later implementation of Castle once we find the room data!

## Features

- **Item System**: Create items with properties like breakability and pickupability
- **Container System**: Boxes with customizable capacity limits for inventory management
- **Room System**: Interconnected rooms with items, boxes, and minigames
- **Character Classes**: Player (with 10-item sack capacity) and Robber characters
- **Action System**: Extensible Verb class with canonical names + synonym aliases
- **State Persistence**: Save and load game world state to/from JSON

## Project Structure

```
Kingdom/
├── main.py                 # Game orchestration and demo
├── pyproject.toml         # Project metadata
├── data/
│   ├── initial_state.json # Game world seed data
│   └── working_state.json # Current game state (generated)
├── src/
│   └── kingdom/
│       ├── __init__.py
│       ├── actions.py     # Command action handlers for main loop verbs
│       ├── parser.py      # Gentle command parsing helpers (case-insensitive noun/verb matching)
│       ├── utilities.py   # Shared utility helpers (session logging, tee output)
│       └── models.py      # Core game classes (Item, Box, Room, Player, Robber, Verb)
└── tests/                 # Test suite
```

## Core Classes

### Item
Represents an object in the game world.

```python
item = Item("Golden Knight", pickupable=True, refuse_string=None)
```

Properties:
- `name`: Item name
- `current_box`: Current container
- `is_broken`: Damage state
- `pickupable`: Whether the item can be picked up
- `refuse_string`: Custom message when refusing to pick up non-pickupable items

### Box
A container with optional capacity limits.

```python
treasure_chest = Box("Royal Vault", capacity=None)
treasure_chest.add_item(item)
```

### Room
A location with items, nested boxes, and optional minigames.

```python
hall = Room("Entrance Hall", desc="A grand hall...")
hall.add_item(item)
hall.add_box(treasure_chest)
```

### Player
A character with a 10-item sack capacity.

```python
hero = Player("Hero")
hero.take(box, item)  # Take from box or room
hero.drop(item)       # Drop item from sack
```

### Robber
A character with unlimited carrying capacity.

```python
thief = Robber("Shadow")
thief.steal(box, item)  # Steal from box or room
```

### Verb
Pairs action names with executable functions.

```python
examine = Verb("examine", lambda obj: f"You examine {obj} carefully.")
result = examine.execute("Golden Knight")  # "You examine Golden Knight carefully."
```

## Game State Format

Game worlds are stored in JSON with a nested structure:

```json
{
  "boxes": [
    {
      "box_name": "Royal Vault",
      "items": [
        "Golden Knight",
        {
          "name": "Crown of Kings",
          "pickupable": false,
          "refuse_string": "too sacred to steal"
        }
      ]
    }
  ],
  "rooms": [
    {
      "name": "Entrance Hall",
      "description": "A grand hall...",
      "connections": {
        "north": "Great Gallery",
        "down": "Secret Cellar"
      },
      "hidden_exits": ["down"],
      "items": ["Silver Goblet", "Ancient Tome"],
      "boxes": [
        {
          "box_name": "Throne Box",
          "items": ["Crown Jewels"]
        }
      ]
    }
  ]
}
```

`hidden_exits` is optional. Any direction listed there remains traversable by command but is omitted from visible exit listings (for example, `look` output).

## Usage

Run the demo:

```bash
python main.py
```

`python main.py` now defaults to modern terminal mode.

Run in modern terminal mode:

```bash
python main.py --mode modern
```

Run in TRS80 mode:

```bash
python main.py --mode trs80
```

Or on Windows with Python Launcher:

```bash
py main.py --mode modern
```

Or on Windows, double-click [run_kingdom.bat](run_kingdom.bat) to launch directly.

On Windows, Kingdom enforces a real terminal session. If it is launched without an attached console, it will automatically reopen itself in a PowerShell terminal window.

The demo will:
1. Load the initial kingdom state
2. Show a Player taking items from boxes and rooms
3. Demonstrate the Verb system with example actions
4. Save the state to `data/working_state.json`
5. Reload and display the updated state

Validate custom world JSON files before running:

```bash
python scripts/check_world_json.py data/initial_state.json
python scripts/check_world_json.py data/initial_state.json data/working_state.json
python scripts/check_world_json.py --strict data/my_world.json
```

On Windows, you can also run [run_state_check.bat](run_state_check.bat).
- Double-click with no arguments to validate the default state files.
- Or run from a terminal with custom paths, for example:

```bat
run_state_check.bat data\my_world.json
```

The checker verifies room-connection integrity, hidden-exit consistency, optional score sanity, and compatibility with the current loader.
Use `--strict` to make warnings fail with a non-zero exit code (useful for CI checks).

## Requirements

- Python 3.13+

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Kingdom

# Run the demo
python main.py
```

## License

MIT

## Author

Dave Reed
