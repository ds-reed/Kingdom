# ======================================================================
# PARSER TEST HARNESS DATASET (UPDATED FOR MULTI-ACTION PARSER)
# ======================================================================

TESTS = {

    # ------------------------------------------------------------------
    # STAGE 3 — Minimal Syntax Extraction
    # ------------------------------------------------------------------

    "stage_3": [


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

  

    ]
}