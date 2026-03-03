class Verb:
    """A verb paired with a handler method.

    Verbs know:
      - their name
      - their synonyms
      - their handler function
      - how to perform noun-side overrides (double dispatch)
    """

    all_verbs = []

    def __init__(self, name, action, synonyms=None, hidden=False):
        self.name = str(name).strip().lower()
        self.action = action
        self.hidden = bool(hidden)

        # Normalize synonyms
        self.synonyms = tuple(
            sorted(
                {
                    s.strip().lower()
                    for s in (synonyms or [])
                    if s.strip().lower() != self.name
                }
            )
        )

        Verb.all_verbs.append(self)

    def all_names(self):
        return (self.name, *self.synonyms)

    def execute(self, target, words):
        """Execute this verb with noun override + handler fallback."""

        # 1. Noun override: on_<verb>
        if target is not None:
            override = getattr(target, f"on_{self.name}", None)
            if callable(override):
                result = override(words)
                if result is not None:
                    return result

        # 2. Handler fallback
        return self.action(target, words)

    def __repr__(self):
        if self.synonyms:
            return f"Verb({self.name}, synonyms={list(self.synonyms)})"
        return f"Verb({self.name})"
