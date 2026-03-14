class DirectionRegistry:
    def __init__(self):
        # The nested data (Canonical -> Details)
        self.data = {}
        # The shortcut map (synonym -> Canonical)
        self.synonym_to_canonical = {}

    def register(self, canonical: str, *, synonyms=None, reverse=None):
        canonical = canonical.lower().strip()
        synonyms = [s.lower().strip() for s in synonyms] if synonyms else []
        
        # 1. Build the nested "JSON-style" structure
        self.data[canonical] = {
            "reverse": reverse.lower().strip() if reverse else None,
            "synonyms": synonyms
        }

        # 2. Build the shortcut map for quick lookups
        for s in synonyms:
            self.synonym_to_canonical[s] = canonical
        if reverse:
            self.synonym_to_canonical[reverse.lower().strip()] = canonical

    def get_canonical(self, name):
        """Turns 'n' or 'North' into 'north'"""
        name = name.lower().strip()
        # If it's already a canonical name, return it
        if name in self.data:
            return name
        # Otherwise, look it up in our synonym shortcut map
        return self.synonym_to_canonical.get(name)

    def get_reverse(self, name):
        """Finds the opposite of any input (synonym or canonical)"""
        canonical = self.get_canonical(name)
        if canonical:
            return self.data[canonical]["reverse"]
        return None
    
    def get_synonyms(self, canonical):
        return list(self.data.get(canonical, {}).get("synonyms", []))
    
    def is_direction(self, name) -> bool:
        """Checks if the input is a valid direction (synonym or canonical)"""
        return self.get_canonical(name) is not None

    def get_all_directions(self):
        """Returns a list of all canonical directions"""
        return sorted(self.data.keys())

DIRECTIONS = DirectionRegistry()