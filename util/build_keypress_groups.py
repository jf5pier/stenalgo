"""
Persist the adopted keypress assignment of Discriminating-Feature Grouping (Grouping
Phase) (2026-09-19 session): the CP-SAT-proven
minimum K over `resolved_press_sets.json`, under the user's explicit constraints:

HARD (real requirements -- CAN inflate K, or fail outright, if unsafe):
- `f` shares its keypress with nothing else (`ALONE_KEYS`).
- `infinitif`, `pers_1`, `pers_2`, `pers_3` are pairwise forced onto different
  keypresses (`MUST_DIFFER_GROUPS`).

SOFT, in descending priority order (`PREFERENCE_TIERS`, via
`minKeypressesSatWithPriorities` -- lexicographic: tier 0 is honored as well as
possible first, tier 1 only as a tiebreaker among colorings that already achieve tier
0's best, and so on; none of them can ever inflate K):
1. `nbr_p` shares a keypress with `p`.
2. `future` shares a keypress with `passé`.
3. `nbr_p`/`p`'s keypress has no OTHER marker on it (stays exclusive to the two of them).

Confirmed against the real lexicon: still K=6 (the hard constraints didn't cost
anything extra here), all three soft tiers fully achieved, 0 conflicts.

This is the canonical, checked-in artifact other work (Discriminating-Feature Stroke
Realization (Realization Phase), or future re-runs)
should read -- not something to regenerate by ad hoc inline scripts each time, per the
plan's own note that this was previously missing (see RESUME_2026-09-19-phaseG.md's
"Still open" item 2, now addressed for the CP-SAT path the same way it was for the
elicitation-model regeneration path).

Run: python -m util.build_keypress_groups
Requires resolved_press_sets.json (`python -m src.elicitation` first) and
questionnaire.json (same command) for the full atom inventory (unpressable markers).
"""
import json
import os

from src.featuregrouping import frequencyWeightedChordSizes, liveMarkers, loadGroupOrthoFrequencies, \
    loadResolvedPressSets, verifyKeypressAssignment
from src.featuregroupingsat import ExclusiveGroupPreference, SameKeyPreference, minKeypressesSatWithPriorities, \
    serializeAssignment

ALONE_KEYS = frozenset({"f"})
MUST_DIFFER_GROUPS = frozenset({frozenset({"infinitif", "pers_1", "pers_2", "pers_3"})})
PREFERENCE_TIERS: list[SameKeyPreference | ExclusiveGroupPreference] = [
    SameKeyPreference(frozenset({frozenset({"p", "nbr_p"})})),
    SameKeyPreference(frozenset({frozenset({"future", "passé"})})),
    ExclusiveGroupPreference(frozenset({"nbr_p", "p"})),
]
OUTPUT_PATH = "keypress_groups.json"


def main() -> None:
    if not os.path.exists("resolved_press_sets.json"):
        raise RuntimeError("Run `python -m src.elicitation` first to build resolved_press_sets.json.")

    pressSetsByGroup = loadResolvedPressSets()
    frequencyByGroup = loadGroupOrthoFrequencies()

    allAtoms: set[str] = set()
    if os.path.exists("questionnaire.json"):
        with open("questionnaire.json", encoding="utf-8") as qf:
            for item in json.load(qf):
                allAtoms.update(item["atomsA"])
                allAtoms.update(item["atomsB"])

    numKeys, colorOf, achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup, PREFERENCE_TIERS, aloneKeys=ALONE_KEYS, mustDifferGroups=MUST_DIFFER_GROUPS,
    )

    # The whole point of persisting rather than trusting the search blindly: re-verify
    # against the real ground truth before writing anything out.
    conflicts = verifyKeypressAssignment(pressSetsByGroup, colorOf)
    if conflicts:
        raise RuntimeError(f"refusing to persist: {len(conflicts)} conflicts found under this assignment")

    unpressableMarkers = frozenset(allAtoms - liveMarkers(pressSetsByGroup))
    weightByKeypress = frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf)

    artifact = serializeAssignment(
        numKeys, colorOf, mustShareKey=frozenset(), unpressableMarkers=unpressableMarkers,
        weightByKeypress=weightByKeypress, aloneKeys=ALONE_KEYS, mustDifferGroups=MUST_DIFFER_GROUPS,
        preferenceTiers=PREFERENCE_TIERS, achievedPerTier=achieved,
    )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: K={numKeys}, 0 conflicts (verified against "
          f"{len(pressSetsByGroup)} groups), tier scores {achieved}, "
          f"{len(unpressableMarkers)} unpressable markers")
    for k in sorted(int(k) for k in artifact["markersByKeypress"]):
        print(f"  {k}: {artifact['markersByKeypress'][str(k)]}")


if __name__ == "__main__":
    main()
