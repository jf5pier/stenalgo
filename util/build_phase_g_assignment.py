"""
Persist Phase G's adopted keypress assignment (2026-09-19 session): the CP-SAT-proven
minimum K over `resolved_press_sets.json`, with `nbr_p` sharing a keypress with `p` per
the user's explicit preference.

Uses `minKeypressesSatPreferring` (SOFT preference), not `minKeypressesSat` with
`mustShareKey` (HARD constraint): the soft search finds the true minimum K first,
unconstrained, then only prefers the p/nbr_p bundling as a tiebreaker among equally-
minimal colorings -- so it can never inflate K to honor the preference, unlike the hard
version (which happened to also find K=5 here, confirmed by an earlier exploration, but
that was a fact about this specific pair, not a property of the mechanism used to get
it). `preferencesSatisfied` in the persisted artifact records whether it was actually
honored (it is, here: still K=5, 0 conflicts against the real 47,799-group lexicon).

This is the canonical, checked-in artifact other work (Phase P, or future re-runs)
should read -- not something to regenerate by ad hoc inline scripts each time, per the
plan's own note that this was previously missing (see RESUME_2026-09-19-phaseG.md's
"Still open" item 2, now addressed for the CP-SAT path the same way it was for the
elicitation-model regeneration path).

Run: python -m util.build_phase_g_assignment
Requires resolved_press_sets.json (`python -m src.elicitation` first) and
questionnaire.json (same command) for the full atom inventory (unpressable markers).
"""
import json
import os

from src.phaseg import frequencyWeightedChordSizes, liveMarkers, loadGroupOrthoFrequencies, \
    loadResolvedPressSets, verifyKeypressAssignment
from src.phasegsat import minKeypressesSatPreferring, serializeAssignment

PREFER_SAME_KEY = frozenset({frozenset({"p", "nbr_p"})})
OUTPUT_PATH = "phase_g_keypress_assignment.json"


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

    numKeys, colorOf, satisfied = minKeypressesSatPreferring(pressSetsByGroup, preferSameKey=PREFER_SAME_KEY)

    # The whole point of persisting rather than trusting the search blindly: re-verify
    # against the real ground truth before writing anything out.
    conflicts = verifyKeypressAssignment(pressSetsByGroup, colorOf)
    if conflicts:
        raise RuntimeError(f"refusing to persist: {len(conflicts)} conflicts found under this assignment")

    unpressableMarkers = frozenset(allAtoms - liveMarkers(pressSetsByGroup))
    weightByKeypress = frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf)

    artifact = serializeAssignment(
        numKeys, colorOf, mustShareKey=frozenset(), unpressableMarkers=unpressableMarkers,
        weightByKeypress=weightByKeypress, preferSameKey=PREFER_SAME_KEY, preferencesSatisfied=satisfied,
    )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: K={numKeys}, 0 conflicts (verified against "
          f"{len(pressSetsByGroup)} groups), preferences satisfied {satisfied}/{len(PREFER_SAME_KEY)}, "
          f"{len(unpressableMarkers)} unpressable markers")
    for k in sorted(int(k) for k in artifact["markersByKeypress"]):
        print(f"  {k}: {artifact['markersByKeypress'][str(k)]}")


if __name__ == "__main__":
    main()
