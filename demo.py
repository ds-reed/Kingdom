"""
Demo and test script for the Kingdom game world simulator.
Shows gameplay examples, Verb usage, and Noun registry.
"""

from pathlib import Path
import sys
sys.path.append("./src")

from kingdom.models import Item, Box, Robber, Room, Player, Verb, Noun, Game


def demo():
    """Run a complete gameplay demonstration."""
    
    # Setup paths
    BASE_DIR = Path(__file__).parent
    DATA_PATH = BASE_DIR / "data" / "initial_state.json"
    SAVE_PATH = BASE_DIR / "data" / "working_state.json"
    
    # Create the Game (special noun representing the world)
    game = Game.get_instance()
    save_verb, load_verb = game.create_state_verbs()
    
    # Load initial kingdom
    print(f"--- Loading Kingdom from {DATA_PATH} ---")
    game.setup_world(DATA_PATH)

    # Print initial state
    print("\n--- Initial Boxes ---")
    for box in game.boxes:
        print(box)
    print("\n--- Initial Rooms ---")
    for room in game.rooms:
        print(room)

    # Save initial state using the save verb
    print(f"\n--- Saving current state using save_verb ---")
    print(save_verb.execute(SAVE_PATH))

    # Gameplay: Player takes items
    print("\n--- Gameplay: Player Takes Items ---")
    if game.boxes and game.rooms:
        player = Player("Hero")
        game.set_current_player(player)
        first_box = game.boxes[0]
        
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
        if game.rooms:
            library = game.rooms[1]  # Library room
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

    # Print state after player takes items
    print("\n--- State After Player Takes Items ---")
    for box in game.boxes:
        print(box)
    print("\n--- Rooms After Player Takes Items ---")
    for room in game.rooms:
        print(room)
    if game.current_player:
        print(f"\nPlayer's Sack: {game.current_player.sack}")

    # Test Verbs system
    print("\n--- Testing Verbs System ---")
    
    def examine_action(target):
        if isinstance(target, Room):
            exits = target.available_directions()
            visible_text = [obj.get_presence_text() for obj in [*target.items, *target.boxes]]
            if not exits:
                exits_text = "There are no visible exits."
            elif len(exits) == 1:
                exits_text = f"There is an exit to the {exits[0]}."
            else:
                exits_text = f"There are exits to the {', '.join(exits[:-1])} and {exits[-1]}."
            if visible_text:
                return f"You examine {target.name} carefully. {' '.join(visible_text)} {exits_text}"
            return f"You examine {target.name} carefully. {exits_text}"
        return f"You examine {target} carefully."
    
    def describe_action(location_name):
        return f"You stand in {location_name}, taking in the surroundings."
    
    examine_verb = Verb("examine", examine_action)
    describe_verb = Verb("describe", describe_action)
    
    print(f"Created verbs: {examine_verb}, {describe_verb}, {save_verb}, {load_verb}")
    print(f"Examine result: {examine_verb.execute('Golden Knight')}")
    print(f"Describe result: {describe_verb.execute('Library')}")

    # Hero walks through connected rooms and examines each one
    print("\n--- Hero Walkthrough ---")
    room_by_name = {room.name: room for room in game.rooms}
    current_room = room_by_name.get("Entrance Hall")
    walk_path = ["north", "east", "east", "south"]

    if current_room and game.current_player:
        print(f"{game.current_player.name} starts in {current_room.name}.")
        print(examine_verb.execute(current_room))
        print(current_room.get_description())

        for direction in walk_path:
            next_room = current_room.get_connection(direction)
            if next_room is None:
                print(f"No room to the {direction} from {current_room.name}. Walk ends.")
                break

            print(f"{game.current_player.name} goes {direction} to {next_room.name}.")
            current_room = next_room
            print(examine_verb.execute(current_room))
            print(current_room.get_description())

    # Demonstrate unified Noun registry (including Game)
    print("\n--- All Nouns in the Game World ---")
    print(f"Total nouns: {len(Noun.all_nouns)}")
    for noun in Noun.all_nouns:
        noun_type = type(noun).__name__
        print(f"  {noun_type}: {noun.get_name()}")

    # Load previously saved state using load verb
    print(f"\n--- Loading Boxes from {SAVE_PATH} using load_verb ---")
    print(load_verb.execute(SAVE_PATH))
    for box in game.boxes:
        print(box)
    
    print(f"\n--- Loaded Rooms---")
    for room in game.rooms:
        print(room)


if __name__ == "__main__":
    demo()
