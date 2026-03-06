# ======================================================================
# PARSER TEST HARNESS DATASET
# ======================================================================
# This file contains:
#   - Test phrases grouped by parser stage
#   - Expected minimal ParsedSyntax fields for each stage
#   - Designed to evolve as the parser grows
#
# NOTE:
#   Expected results are *minimal* and reflect ONLY what each stage
#   of the parser is responsible for. Later stages expand expectations.
# ======================================================================

TESTS = {

    # ------------------------------------------------------------------
    # STAGE 1 — Minimal Syntax Extraction
    # ------------------------------------------------------------------
    "stage_1": [
        {
            "input": "go north",
            "expected": {
                "primary_verb_token": "go",
                "primary_verb_canonical": "go",
                "verb_candidates": ["go"],
                "tokens": ["go", "north"],
                "unknown_tokens": [],
            }
        },
        {
            "input": "look",
            "expected": {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "verb_candidates": ["look"],
                "tokens": ["look"],
                "unknown_tokens": [],
            }
        },
        {
            "input": "take lamp",
            "expected": {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "verb_candidates": ["take"],
                "tokens": ["take", "lamp"],
                "unknown_tokens": [],
            }
        },
        {
            "input": "drop all",
            "expected": {
                "primary_verb_token": "drop",
                "primary_verb_canonical": "drop",
                "verb_candidates": ["drop"],
                "tokens": ["drop", "all"],
                "unknown_tokens": [],
            }
        },
        {
            "input": "inventory",
            "expected": {
                "primary_verb_token": "inventory",
                "primary_verb_canonical": "inventory",
                "verb_candidates": ["inventory"],
                "tokens": ["inventory"],
                "unknown_tokens": [],
            }
        },
    ],

    # ------------------------------------------------------------------
    # STAGE 2 — Phrase Grouping + Conjunctions
    # ------------------------------------------------------------------
    "stage_2": [
        {
            "input": "grab the sword and shield",
            "expected": {
                "primary_verb_token": "grab",
                "primary_verb_canonical": "take",
                "object_phrases": [
                    {"head": "sword", "adjectives": [], "span": (1, 2)},
                    {"head": "shield", "adjectives": [], "span": (3, 4)},
                ],
                "conjunction_groups": [
                    ["sword", "shield"]
                ]
            }
        },
        {
            "input": "take all from the table",
            "expected": {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "object_phrases": [
                    {"head": "all", "adjectives": [], "span": (1, 2)}
                ],
                "prep_phrases": [
                    {"prep": "from", "object": "table"}
                ]
            }
        },
        {
            "input": "look at the strange statue",
            "expected": {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "object_phrases": [
                    {"head": "statue", "adjectives": ["strange"], "span": (3, 5)}
                ]
            }
        },
    ],

    # ------------------------------------------------------------------
    # STAGE 3 — Prepositions + Modifiers
    # ------------------------------------------------------------------
    "stage_3": [
        {
            "input": "look in the drawer",
            "expected": {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "modifier_tokens": ["in"],
                "prep_phrases": [
                    {"prep": "in", "object": "drawer"}
                ]
            }
        },
        {
            "input": "go through the door",
            "expected": {
                "primary_verb_token": "go",
                "primary_verb_canonical": "go",
                "direction_tokens": ["through"],  # ambiguous
                "prep_phrases": [
                    {"prep": "through", "object": "door"}
                ]
            }
        },
        {
            "input": "take all in the bag",
            "expected": {
                "primary_verb_token": "take",
                "primary_verb_canonical": "take",
                "modifier_tokens": ["all"],
                "prep_phrases": [
                    {"prep": "in", "object": "bag"}
                ]
            }
        },
    ],

    # ------------------------------------------------------------------
    # STAGE 4 — Multiword Lexemes + synonym Support
    # ------------------------------------------------------------------
    "stage_4": [
        {
            "input": "pick up everything",
            "expected": {
                "primary_verb_token": "pick up",
                "primary_verb_canonical": "take",
                "object_phrases": [
                    {"head": "everything", "adjectives": [], "span": (2, 3)}
                ]
            }
        },
        {
            "input": "look inside the chest",
            "expected": {
                "primary_verb_token": "look",
                "primary_verb_canonical": "look",
                "modifier_tokens": ["inside"],
                "prep_phrases": [
                    {"prep": "inside", "object": "chest"}
                ]
            }
        },
        {
            "input": "put the apple in the basket",
            "expected": {
                "primary_verb_token": "put",
                "primary_verb_canonical": "put",
                "object_phrases": [
                    {"head": "apple", "adjectives": [], "span": (1, 3)}
                ],
                "prep_phrases": [
                    {"prep": "in", "object": "basket"}
                ]
            }
        },
    ],

    # ------------------------------------------------------------------
    # RESOLVER-ONLY TESTS (parser should NOT interpret semantics)
    # ------------------------------------------------------------------
    "resolver_only": [
        {
            "input": "talk to the guard",
            "expected": {
                "primary_verb_token": "talk",
                "primary_verb_canonical": "talk",
                "prep_phrases": [
                    {"prep": "to", "object": "guard"}
                ]
            }
        },
        {
            "input": "ask the wizard about the amulet",
            "expected": {
                "primary_verb_token": "ask",
                "primary_verb_canonical": "ask",
                "prep_phrases": [
                    {"prep": "about", "object": "amulet"}
                ]
            }
        },
        {
            "input": "say hello",
            "expected": {
                "primary_verb_token": "say",
                "primary_verb_canonical": "say",
                "object_phrases": [
                    {"head": "hello", "adjectives": [], "span": (1, 2)}
                ]
            }
        },
    ],

    # ------------------------------------------------------------------
    # OUT OF SCOPE (parser should tokenize but not interpret)
    # ------------------------------------------------------------------
    "out_of_scope": [
        {
            "input": "attack the troll",
            "expected": {
                "primary_verb_token": "attack",
                "primary_verb_canonical": "attack",
                "object_phrases": [
                    {"head": "troll", "adjectives": [], "span": (1, 3)}
                ]
            }
        },
        {
            "input": "sharpen the knife",
            "expected": {
                "primary_verb_token": "sharpen",
                "primary_verb_canonical": "sharpen",
                "object_phrases": [
                    {"head": "knife", "adjectives": [], "span": (1, 3)}
                ]
            }
        },
    ],
    # Add at the end of OUT_OF_SCOPE or create a new group

    "intentional_failures": [
        {
            "input": "intentional failure 1",
            "expected": {
                "primary_verb_token": "XYZZY",
                "diagnostics": ["This is an intentional failure case."]
            }
        },
        {
            "input": "intentional failure 2",
            "expected": {
                "primary_verb_token": "PLUGH",
                "diagnostics": ["This is an intentional failure case."]
            }
        }
    ]

    
}


