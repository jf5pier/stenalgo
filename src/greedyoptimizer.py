#!/usr/bin/python
# coding: utf-8
#

# Grammatical-category priority for the `*`/`#` cross-lemma/cross-category marking
# rule (see RESUME_2026-09-20-starhash-priority.md's regret-minimization design).
# Higher value = more canonical/unmarked.
# Fitted on the residual population left after that design's ratio-10x exemption and
# homograph exclusion are applied -- a single consistent linear order (`ADV > PRO:pos
# > NOM > VER > ADJ > ADJ:pos`) that reproduces every observed category-pair-type's
# regret-optimal marking direction. Categories absent here weren't observed in that
# residual; src/ambiguitychecker.py's decideStarHashMark falls back to per-pair
# frequency when either side is missing from this table.
GRAMCAT_PRIORITY: dict[str, int] = {
    "ADV":     50,
    "PRO:pos": 40,
    "NOM":     30,
    "VER":     20,
    "ADJ":     10,
    "ADJ:pos":  0,
}
