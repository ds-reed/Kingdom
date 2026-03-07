# ======================================================================
# PARSER TEST HARNESS DATASET (UPDATED FOR MULTI-ACTION PARSER)
# ======================================================================

TESTS = {

    # ------------------------------------------------------------------
    # STAGE 1 — Minimal Syntax Extraction
    # ------------------------------------------------------------------

    "stage_1": [

        # --------------------------------------------------------------
        # Core Stage 1 (10)
        # --------------------------------------------------------------

        {
            "input": "take the shimmering translucent blue crystal",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "verb_candidates": ["take"],
                    "tokens": ["take", "the", "shimmering", "translucent", "blue", "crystal"],
                    "unknown_tokens": ["the", "shimmering", "translucent", "blue"]
                }
            ]
        },

        {
            "input": "examine the badly charred and half-burnt parchment",
            "expected": [
                {
                    "primary_verb_token": "examine",
                    "primary_verb_canonical": "look",
                    "verb_candidates": ["look"],
                    "tokens": ["examine", "the", "badly", "charred", "and", "half-burnt", "parchment"],
                    "unknown_tokens": ["the", "badly", "charred", "and", "half-burnt"]
                }
            ]
        },

        {
            "input": "open the massive ancient double-reinforced doors",
            "expected": [
                {
                    "primary_verb_token": "open",
                    "primary_verb_canonical": "open",
                    "verb_candidates": ["open"],
                    "tokens": ["open", "the", "massive", "ancient", "double-reinforced", "doors"],
                    "unknown_tokens": ["the", "massive", "ancient", "double-reinforced", "doors"]
                }
            ]
        },

        {
            "input": "drop the extremely heavy rusted iron anvil",
            "expected": [
                {
                    "primary_verb_token": "drop",
                    "primary_verb_canonical": "drop",
                    "verb_candidates": ["drop"],
                    "tokens": ["drop", "the", "extremely", "heavy", "rusted", "iron", "anvil"],
                    "unknown_tokens": ["the", "extremely", "heavy", "rusted", "iron"]
                }
            ]
        },

        {
            "input": "inspect the small intricately carved ivory figurine",
            "expected": [
                {
                    "primary_verb_token": "inspect",
                    "primary_verb_canonical": "look",
                    "verb_candidates": ["look"],
                    "tokens": ["inspect", "the", "small", "intricately", "carved", "ivory", "figurine"],
                    "unknown_tokens": ["the", "small", "intricately", "carved", "ivory"]
                }
            ]
        },

        {
            "input": "pick up the long sharp jagged glass shard",
            "expected": [
                {
                    "primary_verb_token": "pick",
                    "primary_verb_canonical": "take",
                    "verb_candidates": ["take"],
                    "tokens": ["pick", "up", "the", "long", "sharp", "jagged", "glass", "shard"],
                    "unknown_tokens": ["the", "long", "sharp", "jagged", "glass"]
                }
            ]
        },

        {
            "input": "wear the smelly old tattered leather boots",
            "expected": [
                {
                    "primary_verb_token": None,
                    "primary_verb_canonical": None,
                    "verb_candidates": [ ],
                    "tokens": ["wear", "the", "smelly", "old", "tattered", "leather", "boots"],
                    "unknown_tokens": ["wear", "the", "smelly", "old", "tattered", "leather"]
                }
            ]
        },

        {
            "input": "read the barely legible faded crimson ink",
            "expected": [
                {
                    "primary_verb_token": None,
                    "primary_verb_canonical": None,
                    "verb_candidates": [ ],
                    "tokens": ["read", "the", "barely", "legible", "faded", "crimson", "ink"],
                    "unknown_tokens": ["read", "the", "barely", "legible", "faded", "crimson", "ink"]
                }
            ]
        },

        {
            "input": "break the thick solid granite pillar",
            "expected": [
                {
                    "primary_verb_token": "break",
                    "primary_verb_canonical": "break",
                    "verb_candidates": ["break"],
                    "tokens": ["break", "the", "thick", "solid", "granite", "pillar"],
                    "unknown_tokens": ["the", "thick", "solid", "granite", "pillar"]
                }
            ]
        },

        {
            "input": "push the huge dusty mahogany wardrobe",
            "expected": [
                {
                    "primary_verb_token": "push",
                    "primary_verb_canonical": "push",
                    "verb_candidates": ["push"],
                    "tokens": ["push", "the", "huge", "dusty", "mahogany", "wardrobe"],
                    "unknown_tokens": ["the", "huge", "dusty", "mahogany"]
                }
            ]
        },

        # --------------------------------------------------------------
        # Stage 1 Sentinel Subset (6)
        # --------------------------------------------------------------

        {
            "input": "take the blue pill and the red pill",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "verb_candidates": ["take"],
                    "tokens": ["take", "the", "blue", "pill", "and", "the", "red", "pill"],
                    "unknown_tokens": ["the", "blue", "and", "the", "red"]
                }
            ]
        },

        {
            "input": "mix the red and yellow powders",
            "expected": [
                {
                    "primary_verb_token": "mix",
                    "primary_verb_canonical": "mix",
                    "verb_candidates": ["mix"],
                    "tokens": ["mix", "the", "red", "and", "yellow", "powders"],
                    "unknown_tokens": ["the", "red", "and", "yellow"]
                }
            ]
        },

        {
            "input": "collect the bones and the skulls",
            "expected": [
                {
                    "primary_verb_token": None,
                    "primary_verb_canonical": None,
                    "verb_candidates": [],
                    "tokens": ["collect", "the", "bones", "and", "the", "skulls"],
                    "unknown_tokens": ["collect", "the", "bones", "and", "the", "skulls"]
                }
            ]
        },

        {
            "input": "get the key from the box",
            "expected": [
                {
                    "primary_verb_token": None,
                    "primary_verb_canonical": None,
                    "verb_candidates": [],
                    "tokens": ["get", "the", "key", "from", "the", "box"],
                    "unknown_tokens": ["get", "the", "from", "the"]
                }
            ]
        },

        {
            "input": "put the gold in the bag",
            "expected": [
                {
                    "primary_verb_token": "put",
                    "primary_verb_canonical": "put",
                    "verb_candidates": ["put"],
                    "tokens": ["put", "the", "gold", "in", "the", "bag"],
                    "unknown_tokens": ["the", "gold", "in", "the"]
                }
            ]
        },

        {
            "input": "cut the steak with the knife",
            "expected": [
                {
                    "primary_verb_token": "cut",
                    "primary_verb_canonical": "cut",
                    "verb_candidates": ["cut"],
                    "tokens": ["cut", "the", "steak", "with", "the", "knife"],
                    "unknown_tokens": ["the", "steak", "with", "the"]
                }
            ]
        },

        {
            "input": "open, feed and fight the basket",
            "expected": [
                {
                    "primary_verb_token": "open",
                    "primary_verb_canonical": "open",
                    "verb_candidates": ["open", "feed", "attack"],
                    "tokens": ["open", "feed", "and", "fight", "the", "basket"],
                    "unknown_tokens": ["and", "the"]
                }
            ]
        },


    ],

     # ------------------------------------------------------------------
    # STAGE 2 — Phrase Grouping + Conjunctions
    # ------------------------------------------------------------------
    "stage_2": [

        {
            "input": "grab the sword and shield",
            "expected": [
                {
                    "primary_verb_token": "grab",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "sword", "adjectives": [], "span": (2, 3)},
                        {"head": "shield", "adjectives": [], "span": (4, 5)}
                    ],
                    "conjunction_groups": [["sword", "shield"]]
                }
            ]
        },

        {
            "input": "take all from the table",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "table", "adjectives": [], "span": (4, 5)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": {"head": "table", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

        {
            "input": "look at the strange statue",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "object_phrases": [
                        {"head": "statue", "adjectives": ["strange"], "span": (3, 5)}
                    ]
                }
            ]
        },

        {
            "input": "take the shimmering crystal",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "crystal", "adjectives": ["shimmering"], "span": (2, 4)}
                    ]
                }
            ]
        },

        {
            "input": "grab the carved ivory figurine",
            "expected": [
                {
                    "primary_verb_token": "grab",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "figurine", "adjectives": ["carved", "ivory"], "span": (2, 5)}
                    ]
                }
            ]
        },

        {
            "input": "take the boots and cloak",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "boots", "adjectives": [], "span": (2, 3)},
                        {"head": "cloak", "adjectives": [], "span": (4, 5)}
                    ],
                    "conjunction_groups": [["boots", "cloak"]]
                }
            ]
        },

        {
            "input": "open the chest and drawer",
            "expected": [
                {
                    "primary_verb_token": "open",
                    "primary_verb_canonical": "open",
                    "object_phrases": [
                        {"head": "chest", "adjectives": [], "span": (2, 3)},
                        {"head": "drawer", "adjectives": [], "span": (4, 5)}
                    ],
                    "conjunction_groups": [["chest", "drawer"]]
                }
            ]
        },

        {
            "input": "take the rope from the wall",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "rope", "adjectives": [], "span": (2, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": {"head": "wall", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

        {
            "input": "inspect the dusty mahogany desk",
            "expected": [
                {
                    "primary_verb_token": "inspect",
                    "primary_verb_canonical": "look",
                    "object_phrases": [
                        {"head": "desk", "adjectives": ["dusty", "mahogany"], "span": (2, 5)}
                    ]
                }
            ]
        },

        {
            "input": "take the bread and water",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "bread", "adjectives": [], "span": (2, 3)},
                        {"head": "water", "adjectives": [], "span": (4, 5)}
                    ],
                    "conjunction_groups": [["bread", "water"]]
                }
            ]
        },

        {
            "input": "grab the stone from the river",
            "expected": [
                {
                    "primary_verb_token": "grab",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "stone", "adjectives": [], "span": (2, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": {"head": "river", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

        {
            "input": "take the powder and gear",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "powder", "adjectives": [], "span": (2, 3)},
                        {"head": "gear", "adjectives": [], "span": (4, 5)}
                    ],
                    "conjunction_groups": [["powder", "gear"]]
                }
            ]
        },

        {
            "input": "open the gate with the key",
            "expected": [
                {
                    "primary_verb_token": "open",
                    "primary_verb_canonical": "open",
                    "object_phrases": [
                        {"head": "gate", "adjectives": [], "span": (2, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "with", "object": {"head": "key", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

        {
            "input": "take the journal from the drawer",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "journal", "adjectives": [], "span": (2, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": {"head": "drawer", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

        {
            "input": "inspect the mirror on the wall",
            "expected": [
                {
                    "primary_verb_token": "inspect",
                    "primary_verb_canonical": "look",
                    "object_phrases": [
                        {"head": "mirror", "adjectives": [], "span": (2, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "on", "object": {"head": "wall", "adjectives": [], "span": (4, 5)}}
                    ]
                }
            ]
        },

    ],

    # ------------------------------------------------------------------
    # STAGE 3 — Phrase Grouping + Conjunctions
    # ------------------------------------------------------------------

    "stage_3": [

        {
            "input": "look in the drawer",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "modifier_tokens": ["in"],
                    "prep_phrases": [
                        {"prep": "in", "object": "drawer"}
                    ]
                }
            ]
        },

        {
            "input": "go through the door",
            "expected": [
                {
                    "primary_verb_token": "go",
                    "primary_verb_canonical": "go",
                    "direction_tokens": ["through"],
                    "prep_phrases": [
                        {"prep": "through", "object": "door"}
                    ]
                }
            ]
        },

        {
            "input": "take all in the bag",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "modifier_tokens": ["all", "in"],
                    "prep_phrases": [
                        {"prep": "in", "object": "bag"}
                    ]
                }
            ]
        },

        {
            "input": "look inside the chest",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "modifier_tokens": ["inside"],
                    "prep_phrases": [
                        {"prep": "inside", "object": "chest"}
                    ]
                }
            ]
        },

        {
            "input": "go past the guard",
            "expected": [
                {
                    "primary_verb_token": "go",
                    "primary_verb_canonical": "go",
                    "direction_tokens": ["past"],
                    "prep_phrases": [
                        {"prep": "past", "object": "guard"}
                    ]
                }
            ]
        },

        {
            "input": "look toward the river",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "direction_tokens": ["toward"],
                    "prep_phrases": [
                        {"prep": "toward", "object": "river"}
                    ]
                }
            ]
        },

        {
            "input": "inspect the mirror on the wall",
            "expected": [
                {
                    "primary_verb_token": "inspect",
                    "primary_verb_canonical": "look",
                    "object_phrases": [
                        {"head": "mirror", "adjectives": [], "span": (1, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "on", "object": "wall"}
                    ]
                }
            ]
        },

        {
            "input": "take the rope from the wall",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "rope", "adjectives": [], "span": (1, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": "wall"}
                    ]
                }
            ]
        },

        {
            "input": "look under the table",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "under", "object": "table"}
                    ]
                }
            ]
        },

        {
            "input": "look behind the curtain",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "behind", "object": "curtain"}
                    ]
                }
            ]
        },

        {
            "input": "look beneath the pedestal",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "beneath", "object": "pedestal"}
                    ]
                }
            ]
        },

        {
            "input": "look between the doors",     #doors not a noun - door is. Shouldn't find any phrase
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": []
                }
            ]
        },

        {
            "input": "look beyond the gate",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "beyond", "object": "gate"}
                    ]
                }
            ]
        },

        {
            "input": "look across the river",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "across", "object": "river"}
                    ]
                }
            ]
        },

        {
            "input": "look above the ceiling",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "above", "object": "ceiling"}
                    ]
                }
            ]
        },

        {
            "input": "look below the floor",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "prep_phrases": [
                        {"prep": "below", "object": "floor"}
                    ]
                }
            ]
        },

        {
            "input": "take everything inside the chest",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "modifier_tokens": ["everything", "inside"],
                    "prep_phrases": [
                        {"prep": "inside", "object": "chest"}
                    ]
                }
            ]
        },

        {
            "input": "take the boots from the wardrobe",
            "expected": [
                {
                    "primary_verb_token": "take",
                    "primary_verb_canonical": "take",
                    "object_phrases": [
                        {"head": "boots", "adjectives": [], "span": (1, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "from", "object": "wardrobe"}
                    ]
                }
            ]
        },

        {
            "input": "inspect the cloak on the hook",
            "expected": [
                {
                    "primary_verb_token": "inspect",
                    "primary_verb_canonical": "look",
                    "object_phrases": [
                        {"head": "cloak", "adjectives": [], "span": (1, 3)}
                    ],
                    "prep_phrases": [
                        {"prep": "on", "object": "hook"}
                    ]
                }
            ]
        },

        {
            "input": "look outside the cellar",
            "expected": [
                {
                    "primary_verb_token": "look",
                    "primary_verb_canonical": "look",
                    "direction_tokens": ["outside"],
                    "prep_phrases": [
                        {"prep": "outside", "object": "cellar"}
                    ]
                }
            ]
        },
    {
        "input": "Get the key from the box on the table",
        "expected": [
            {
                "primary_verb_token": "get",
                "primary_verb_canonical": "take",
                "object_phrases": [
                    {"head": "key", "adjectives": [], "span": (1, 2)}
                ],
                "prep_phrases": [
                    {"prep": "from", "object": "box"},
                    {"prep": "on", "object": "table"}
                ]
            }
        ]
    },

    {
        "input": "Put the gold in the bag under the bed",
        "expected": [
            {
                "primary_verb_token": "put",
                "primary_verb_canonical": "put",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "in", "object": "bag"},
                    {"prep": "under", "object": "bed"}
                ]
            }
        ]
    },

    {
        "input": "Take the letter out of the envelope in the desk",
        "expected": [
            {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "object_phrases": [
                    {"head": "letter", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "of", "object": "envelope"},
                    {"prep": "in", "object": "desk"}
                ]
            }
        ]
    },

    {
        "input": "Look at the map on the wall by the door",
        "expected": [
            {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "object_phrases": [
                    {"head": "map", "adjectives": [], "span": (2, 4)}
                ],
                "prep_phrases": [
                    {"prep": "on", "object": "wall"},
                    {"prep": "by", "object": "door"}
                ]
            }
        ]
    },

    {
        "input": "Give the ring from the drawer to the elf",
        "expected": [
            {
                "primary_verb_token": "give",
                "primary_verb_canonical": "give",
                "object_phrases": [
                    {"head": "ring", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "from", "object": "drawer"},
                    {"prep": "to", "object": "elf"}
                ]
            }
        ]
    },

    {
        "input": "Move the statue from the pedestal to the floor",
        "expected": [
            {
                "primary_verb_token": "move",
                "primary_verb_canonical": "move",
                "object_phrases": [
                    {"head": "statue", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "from", "object": "pedestal"},
                    {"prep": "to", "object": "floor"}
                ]
            }
        ]
    },

    {
        "input": "Pour water from the jug into the basin",
        "expected": [
            {
                "primary_verb_token": "pour",
                "primary_verb_canonical": "pour",
                "object_phrases": [
                    {"head": "water", "adjectives": [], "span": (0, 1)}
                ],
                "prep_phrases": [
                    {"prep": "from", "object": "jug"},
                    {"prep": "into", "object": "basin"}
                ]
            }
        ]
    },

    {
        "input": "Pull the lever on the panel behind the curtain",
        "expected": [
            {
                "primary_verb_token": "pull",
                "primary_verb_canonical": "pull",
                "object_phrases": [
                    {"head": "lever", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "on", "object": "panel"},
                    {"prep": "behind", "object": "curtain"}
                ]
            }
        ]
    },

    {
        "input": "Slide the bolt on the gate with the hook",
        "expected": [
            {
                "primary_verb_token": "slide",
                "primary_verb_canonical": "slide",
                "object_phrases": [
                    {"head": "bolt", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "on", "object": "gate"},
                    {"prep": "with", "object": "hook"}
                ]
            }
        ]
    },

    {
        "input": "Reach for the handle on the ceiling above the hatch",
        "expected": [
            {
                "primary_verb_token": "reach",
                "primary_verb_canonical": "reach",
                "prep_phrases": [
                    {"prep": "on", "object": "ceiling"},
                    {"prep": "above", "object": "hatch"}
                ]
            }
        ]
    },

    {
        "input": "Take a sip of the wine",
        "expected": [
            {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "wine"}
                ]
            }
        ]
    },

    {
        "input": "Get a handful of dirt",
        "expected": [
            {
                "primary_verb_token": "get",
                "primary_verb_canonical": "take",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "dirt"}
                ]
            }
        ]
    },

    {
        "input": "Pick up a piece of the mirror",
        "expected": [
            {
                "primary_verb_token": "pick",
                "primary_verb_canonical": "take",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "mirror"}
                ]
            }
        ]
    },

    {
        "input": "Read a page of the journal",
        "expected": [
            {
                "primary_verb_token": "read",
                "primary_verb_canonical": "read",
                "object_phrases": [
                    {"head": "page", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "of", "object": "journal"}
                ]
            }
        ]
    },

    {
        "input": "Drop a stack of coins",
        "expected": [
            {
                "primary_verb_token": "drop",
                "primary_verb_canonical": "drop",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "coins"}
                ]
            }
        ]
    },

        {
        "input": "Grab a clump of moss",
        "expected": [
            {
                "primary_verb_token": "grab",
                "primary_verb_canonical": "take",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "moss"}
                ]
            }
        ]
    },

    {
        "input": "Use a drop of the elixir",
        "expected": [
            {
                "primary_verb_token": "use",
                "primary_verb_canonical": "use",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Throw a stone from the pile",
        "expected": [
            {
                "primary_verb_token": "throw",
                "primary_verb_canonical": "throw",
                "object_phrases": [
                    {"head": "stone", "adjectives": [], "span": (2, 3)}
                ],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Cut a length of rope",
        "expected": [
            {
                "primary_verb_token": "cut",
                "primary_verb_canonical": "cut",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "of", "object": "rope"}
                ]
            }
        ]
    },

    {
        "input": "Take a look at the statue",
        "expected": [
            {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "at", "object": "statue"}
                ]
            }
        ]
    },

    {
        "input": "Put the donkey in front of the cart",
        "expected": [
            {
                "primary_verb_token": "put",
                "primary_verb_canonical": "put",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Stand the torch inside the bracket",
        "expected": [
            {
                "primary_verb_token": "stand",
                "primary_verb_canonical": "stand",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Lay the sword across the altar",
        "expected": [
            {
                "primary_verb_token": "lay",
                "primary_verb_canonical": "lay",
                "object_phrases": [
                    {"head": "sword", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Sit the idol atop the pedestal",
        "expected": [
            {
                "primary_verb_token": "sit",
                "primary_verb_canonical": "sit",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "atop", "object": "pedestal"}
                ]
            }
        ]
    },

    {
        "input": "Hang the cloak over the hook",
        "expected": [
            {
                "primary_verb_token": "hang",
                "primary_verb_canonical": "hang",
                "object_phrases": [
                    {"head": "cloak", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "over", "object": "hook"}
                ]
            }
        ]
    },

    {
        "input": "Wedge the coin between the stones",
        "expected": [
            {
                "primary_verb_token": "wedge",
                "primary_verb_canonical": "wedge",
                "object_phrases": [
                    {"head": "coin", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                     {'prep': 'between', 'object': 'stones'}
                ]
            }
        ]
    },

    {
        "input": "Press the button beneath the ledge",
        "expected": [
            {
                "primary_verb_token": "press",
                "primary_verb_canonical": "press",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Throw the meat beyond the fence",
        "expected": [
            {
                "primary_verb_token": "throw",
                "primary_verb_canonical": "throw",
                "object_phrases": [
                    {"head": "meat", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "beyond", "object": "fence"}
                ]
            }
        ]
    },

    {
        "input": "Roll the barrel toward the cellar",
        "expected": [
            {
                "primary_verb_token": "roll",
                "primary_verb_canonical": "roll",
                "object_phrases": [
                    {"head": "barrel", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "toward", "object": "cellar"}
                ]
            }
        ]
    },

    {
        "input": "Climb up the beanstalk",
        "expected": [
            {
                "primary_verb_token": "climb",
                "primary_verb_canonical": "climb",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },
    {
        "input": "Unlock the gate with the skeleton key",
        "expected": [
            {
                "primary_verb_token": "unlock",
                "primary_verb_canonical": "unlock",
                "object_phrases": [
                    {"head": "gate", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "with", "object": "key"}
                ]
            }
        ]
    },

    {
        "input": "Hit the post with the sledgehammer",
        "expected": [
            {
                "primary_verb_token": "hit",
                "primary_verb_canonical": "hit",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Cut the steak with the knife",
        "expected": [
            {
                "primary_verb_token": "cut",
                "primary_verb_canonical": "cut",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "with", "object": "knife"}
                ]
            }
        ]
    },

    {
        "input": "Dig the grave with the shovel",
        "expected": [
            {
                "primary_verb_token": "dig",
                "primary_verb_canonical": "dig",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Light the candle with the flint",
        "expected": [
            {
                "primary_verb_token": "light",
                "primary_verb_canonical": "light",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Pry the crate with the crowbar",
        "expected": [
            {
                "primary_verb_token": "pry",
                "primary_verb_canonical": "pry",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Stir the pot with the ladle",
        "expected": [
            {
                "primary_verb_token": "stir",
                "primary_verb_canonical": "stir",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Fix the link with the pliers",
        "expected": [
            {
                "primary_verb_token": "fix",
                "primary_verb_canonical": "fix",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Clean the shield with the polish",
        "expected": [
            {
                "primary_verb_token": "clean",
                "primary_verb_canonical": "clean",
                "object_phrases": [
                    {"head": "shield", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Mend the shirt with the needle",
        "expected": [
            {
                "primary_verb_token": "mend",
                "primary_verb_canonical": "mend",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Use the iron key on the wooden door",
        "expected": [
            {
                "primary_verb_token": "use",
                "primary_verb_canonical": "use",
                "object_phrases": [
                    {"head": "key", "adjectives": ["iron"], "span": (1, 4)}
                ],
                "prep_phrases": [
                    {"prep": "on", "object": "door"}
                ]
            }
        ]
    },

    {
        "input": "Attack the goblin using the mace",
        "expected": [
            {
                "primary_verb_token": "attack",
                "primary_verb_canonical": "attack",
                "object_phrases": [
                    {"head": "goblin", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Open the box using the small key",
        "expected": [
            {
                "primary_verb_token": "open",
                "primary_verb_canonical": "open",
                "object_phrases": [
                    {"head": "box", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Look inside the hollow tree",
        "expected": [
            {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },

    {
        "input": "Peer through the stained glass",
        "expected": [
            {
                "primary_verb_token": "peer",
                "primary_verb_canonical": "peer",
                "object_phrases": [],
                "prep_phrases": []
            }
        ]
    },
    {
        "input": "Look under the bed",
        "expected": [
            {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "under", "object": "bed"}
                ]
            }
        ]
    },

    {
        "input": "Walk past the guard",
        "expected": [
            {
                "primary_verb_token": "walk",
                "primary_verb_canonical": "walk",
                "object_phrases": [],
                "prep_phrases": [
                    {"prep": "past", "object": "guard"}
                ]
            }
        ]
    },


    ]
}