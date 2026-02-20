import json
from pathlib import Path
import sys
sys.path.append("./src")
from kingdom.models import Item, Box, Robber, Room, Player, Verbs, _construct_boxes, _construct_rooms


def setup_kingdom(filepath):
    # Read file and construct boxes and rooms
    with open(filepath, 'r') as file:
        data = json.load(file)

    # Support new format: { boxes: [...], rooms: [...] }
    if isinstance(data, dict):
        boxes = _construct_boxes(data.get('boxes', []))
        rooms = _construct_rooms(data.get('rooms', []))
    else:
        boxes = _construct_boxes(data)
        rooms = []

    return boxes, rooms

def save_kingdom_state(boxes, filepath, rooms=None):
    # This writes the current state back to a file
    payload = {}
    payload['boxes'] = []
    for box in boxes:
        box_data = {
            "box_name": box.box_name,
            "items": [item.name for item in box.contents]
        }
        payload['boxes'].append(box_data)

    if rooms is not None:
        payload['rooms'] = []
        for room in rooms:
            room_data = {
                'name': room.name,
                'description': room.description,
                'items': [it.name for it in room.items],
                'boxes': [
                    {
                        'box_name': box.box_name,
                        'items': [item.name for item in box.contents]
                    }
                    for box in room.boxes
                ]
            }
            payload['rooms'].append(room_data)

    # Prevent accidentally overwriting the canonical initial state
    target = Path(filepath)
    if target.name == "initial_state.json":
        raise RuntimeError("Refusing to overwrite initial_state.json")

    with open(filepath, 'w') as file:
        json.dump(payload, file, indent=4)

def load_kingdom_state(filepath):
    # Read file and construct boxes and rooms
    with open(filepath, 'r') as file:
        data = json.load(file)

    if isinstance(data, dict):
        boxes = _construct_boxes(data.get('boxes', []))
        rooms = _construct_rooms(data.get('rooms', []))
    else:
        boxes = _construct_boxes(data)
        rooms = []

    return boxes, rooms


def main():
    # 1. Define the path to the data folder
    # __file__ is a special variable that points to this specific script
    BASE_DIR = Path(__file__).parent
    DATA_PATH = BASE_DIR / "data" / "initial_state.json"

    # 2. Run the setup
    print(f"--- Loading Kingdom from {DATA_PATH} ---")
    boxes, rooms = setup_kingdom(DATA_PATH)

    # 3. Print initial state
    print("--- Initial Boxes ---")
    for box in boxes:
        print(box)
    print("--- Initial Rooms ---")
    for room in rooms:
        print(room)

    # 4. Save current state to a working file (never overwrite initial_state.json)
    SAVE_PATH = BASE_DIR / "data" / "working_state.json"
    save_kingdom_state(boxes, SAVE_PATH, rooms=rooms)
    print(f"--- Saved current state to {SAVE_PATH} ---")

    # 5. Example: Make a Player and try to take items from boxes and rooms
    if boxes and rooms:
        player = Player("Hero")
        first_box = boxes[0]
        if len(first_box.contents) >= 2:
            # Try taking the Crown of Kings (non-pickupable)
            crown_item = None
            for item in first_box.contents:
                if item.name == "Crown of Kings":
                    crown_item = item
                    break
            if crown_item:
                player.take(first_box, crown_item)
            # Try taking Golden Knight (pickupable)
            gold_item = first_box.contents[0] if first_box.contents and first_box.contents[0].pickupable else None
            if gold_item:
                player.take(first_box, gold_item)
        
        # Try taking an item from a room
        if rooms:
            library = rooms[1]  # Library room
            if library.items:
                # Try to take Ancient Tome (non-pickupable)
                for item in library.items:
                    if item.name == "Ancient Tome":
                        player.take(library, item)
                        break
                # Try to take Leather Book
                for item in library.items:
                    if item.name == "Leather Book":
                        player.take(library, item)
                        break

    # 6. Print state after player takes items
    print("--- State after player takes items ---")
    for box in boxes:
        print(box)
    print("--- Rooms after player takes items ---")
    for room in rooms:
        print(room)
    if 'player' in locals():
        print(f"Player's Sack: {player.sack}")

    # Example: Create and use some Verbs
    print("\n--- Testing Verbs ---")
    
    def examine_action(item_name):
        return f"You examine {item_name} carefully."
    
    def describe_action(location_name):
        return f"You stand in {location_name}, taking in the surroundings."
    
    examine_verb = Verbs("examine", examine_action)
    describe_verb = Verbs("describe", describe_action)
    
    print(f"Created verbs: {examine_verb}, {describe_verb}")
    print(f"Examine result: {examine_verb.execute('Golden Knight')}")
    print(f"Describe result: {describe_verb.execute('Library')}")

    # 7. Load previously saved state and print (should reflect pre-take)
    loaded_boxes, loaded_rooms = load_kingdom_state(SAVE_PATH)
    print(f"--- Loaded Boxes from {SAVE_PATH} ---")
    for box in loaded_boxes:
        print(box)
    print(f"--- Loaded Rooms from {SAVE_PATH} ---")
    for room in loaded_rooms:
        print(room)

if __name__ == "__main__":
    main()
