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
        return list(self.data.keys())
    
    def sort_directions(self, directions: list[str]) -> list[str]:
        """Return the given directions in the registry's canonical display order."""
        # Normalize to canonical names
        canon = [self.get_canonical(d) for d in directions]

        # Filter out unknowns
        canon = [d for d in canon if d is not None]

        # Preserve registry order
        ordered = [d for d in self.data.keys() if d in canon]

        return ordered
    
    def _serialize_directions(self) -> dict[str, dict[str, object]]:
        payload: dict[str, dict[str, object]] = {}

        for canonical in sorted(self.get_all_directions()):
            synonyms = sorted(self.get_synonyms(canonical))

            entry: dict[str, object] = {}
            reverse = self.get_reverse(canonical)
            if reverse is not None:
                entry["reverse"] = reverse
            if synonyms:
                entry["synonyms"] = synonyms
            payload[canonical] = entry

        return payload


DIRECTIONS = DirectionRegistry()