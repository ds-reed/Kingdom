class Item:
    all_items = []  # Class variable to track every item created

    def __init__(self, name, pickupable=True, refuse_string=None):
        self.name = name
        self.current_box = None
        self.is_broken = False
        self.pickupable = pickupable
        self.refuse_string = refuse_string or f"You can't pick up {name}"
        Item.all_items.append(self)

    def __repr__(self):
        """Controls how the item looks when printed in a list."""
        status = " [BROKEN]" if self.is_broken else ""
        return f"'{self.name}{status}'"

class Box:
    def __init__(self, box_name, capacity=None):
        self.box_name = box_name
        self.contents = []
        self.capacity = capacity  # None = unlimited

    def add_item(self, item):
        """The King claims an item. If it's in another box, he seizes it."""
        if self.capacity is not None and len(self.contents) >= self.capacity:
            print(f"KING {self.box_name}: The box is full!")
            return

        if item.current_box == self:
            print(f"KING {self.box_name}: I already own {item.name}!")
            return

        # Handle the move logic (Seizing from another box)
        if item.current_box is not None:
            print(f"KING {self.box_name}: Seizing {item.name} from {item.current_box.box_name}!")
            item.current_box.contents.remove(item)

        # Update states
        self.contents.append(item)
        item.current_box = self
        print(f"KING {self.box_name}: {item.name} has been added to the treasury.")

    def __repr__(self):
        return f"Box({self.box_name}, contents={self.contents})"

class Robber:
    def __init__(self, name):
        self.name = name
        # Composition: The Robber HAS a Box (his sack)
        self.sack = Box(f"{name}'s Sack")

    def steal(self, from_container, item):
        """The robber takes a specific item object from a box or room."""
        # Determine which type of container we're dealing with
        if isinstance(from_container, Box):
            contents = from_container.contents
            container_name = from_container.box_name
        elif isinstance(from_container, Room):
            contents = from_container.items
            container_name = from_container.name
        else:
            raise TypeError("from_container must be a Box or Room")

        assert item in contents, f"{item.name} isn't even in {container_name}!"

        # Check if item is pickupable
        if not item.pickupable:
            print(f"!!! {self.name} tries to steal from {container_name}...")
            print(f"{item.refuse_string}")
            return

        print(f"!!! {self.name} sneaks into {container_name}...")
        contents.remove(item)
        self.sack.add_item(item)

        # The 'Careless' part: 50% chance to break it during the theft
        import random
        if random.random() > 0.5:
            self.break_item(item)

    def break_item(self, item):
        item.is_broken = True
        print(f"CRACK! {self.name} was careless and broke {item.name}!")


class Player:
    """A player character who can collect items in their sack (max 10 items)."""
    def __init__(self, name):
        self.name = name
        self.sack = Box(f"{name}'s Sack", capacity=10)

    def take(self, from_container, item):
        """The player takes an item from a box or room."""
        # Determine which type of container we're dealing with
        if isinstance(from_container, Box):
            contents = from_container.contents
            container_name = from_container.box_name
        elif isinstance(from_container, Room):
            contents = from_container.items
            container_name = from_container.name
        else:
            raise TypeError("from_container must be a Box or Room")

        assert item in contents, f"{item.name} isn't even in {container_name}!"

        # Check if item is pickupable
        if not item.pickupable:
            print(f"{self.name} tries to pick up {item.name}...")
            print(f"{item.refuse_string}")
            return

        # Check sack capacity
        if len(self.sack.contents) >= self.sack.capacity:
            print(f"{self.name}'s sack is full (max {self.sack.capacity} items)!")
            return

        print(f"{self.name} takes {item.name} from {container_name}.")
        contents.remove(item)
        self.sack.contents.append(item)
        item.current_box = self.sack

    def drop(self, item):
        """The player drops an item from their sack."""
        if item not in self.sack.contents:
            print(f"{self.name} doesn't have {item.name}!")
            return
        print(f"{self.name} drops {item.name}.")
        self.sack.contents.remove(item)
        item.current_box = None


class Room:
    """A simple Room that can hold `Item` objects and connect to other rooms.

    Adapted from the Castle example; uses the project's `Item` class.
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.items = []  # list[Item]
        self.boxes = []  # list[Box]
        self.connections = {}
        self.minigame = None

    def add_item(self, item):
        """Add an Item instance or create one from a string name."""
        if isinstance(item, Item):
            self.items.append(item)
        elif isinstance(item, str):
            self.items.append(Item(item))
        else:
            raise TypeError("Room.add_item expects an Item or str")

    def add_box(self, box):
        """Add a Box instance to this room."""
        if not isinstance(box, Box):
            raise TypeError("Room.add_box expects a Box instance")
        self.boxes.append(box)

    def connect_room(self, direction, room):
        self.connections[direction] = room

    def get_description(self):
        return self.description

    def set_minigame(self, func):
        self.minigame = func

    def play_minigame(self, *args, **kwargs):
        if callable(self.minigame):
            return self.minigame(*args, **kwargs)
        return None

    def __repr__(self):
        items_str = [it.name for it in self.items]
        boxes_str = [b.box_name for b in self.boxes]
        return f"Room({self.name}, desc='{self.description}', items={items_str}, boxes={boxes_str})"





def _construct_boxes(data):
    """Construct Box and Item objects from loaded JSON data list.

    Expects `data` to be a list of dicts with keys 'box_name' and 'items'.
    Each item can be a string or a dict with 'name', 'pickupable', 'refuse_string'.
    """
    all_boxes = []
    for entry in data:
        new_box = Box(entry["box_name"])
        for item_spec in entry.get("items", []):
            if isinstance(item_spec, str):
                new_item = Item(item_spec)
            else:
                new_item = Item(
                    item_spec.get("name"),
                    pickupable=item_spec.get("pickupable", True),
                    refuse_string=item_spec.get("refuse_string")
                )
            new_box.add_item(new_item)
        all_boxes.append(new_box)
    return all_boxes


def _construct_rooms(data):
    """Construct Room objects from loaded JSON data list.

    Each room dict should have 'name', 'description', optional 'items', and optional 'boxes'.
    Items can be strings or dicts with 'name', 'pickupable', 'refuse_string'.
    """
    all_rooms = []
    for entry in data:
        room = Room(entry.get("name"), entry.get("description", ""))
        # Add items to the room
        for item_spec in entry.get("items", []):
            if isinstance(item_spec, str):
                room.add_item(item_spec)
            else:
                item_obj = Item(
                    item_spec.get("name"),
                    pickupable=item_spec.get("pickupable", True),
                    refuse_string=item_spec.get("refuse_string")
                )
                room.items.append(item_obj)
        # Add boxes to the room
        for box_data in entry.get("boxes", []):
            box = Box(box_data.get("box_name"))
            for item_spec in box_data.get("items", []):
                if isinstance(item_spec, str):
                    item_obj = Item(item_spec)
                else:
                    item_obj = Item(
                        item_spec.get("name"),
                        pickupable=item_spec.get("pickupable", True),
                        refuse_string=item_spec.get("refuse_string")
                    )
                box.add_item(item_obj)
            room.add_box(box)
        all_rooms.append(room)
    return all_rooms


class Verbs:
    """A verb paired with an action function.
    
    Verbs are used to define actions that can be performed in the game.
    Each verb has a name and an associated callable that implements the action.
    """
    def __init__(self, verb, action):
        """Initialize a Verb.
        
        Args:
            verb: The verb name (e.g., 'take', 'drop', 'examine')
            action: A callable that performs the action
        """
        self.verb = verb
        self.action = action
    
    def execute(self, *args, **kwargs):
        """Execute the action associated with this verb."""
        if not callable(self.action):
            raise TypeError(f"Action for verb '{self.verb}' is not callable")
        return self.action(*args, **kwargs)
    
    def __repr__(self):
        return f"Verb({self.verb})"
