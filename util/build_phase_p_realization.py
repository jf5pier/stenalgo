"""
Persist Phase P's milestone-1 output (see RESUME_2026-09-19-phaseP-plan.md): for each of
Phase G's abstract keypress groups (`phase_g_keypress_assignment.json`), search for a
physical right-hand coda key-combo (`starboard3h.json`'s keys `[16..25]`) that realizes it
as a brand-new trailing stroke appended after a word's own strokes (an extra "syllable"),
without colliding with any word's existing stroke in the live `theory`, or with any other
affected word's own newly-composed stroke -- composing ALL of a word's needed groups
into that one shared extra stroke, not just the group currently being decided.

This is milestone 1's concrete deliverable -- it does NOT yet rewrite `theory`/persist a
final stroke-per-word table (that's the deferred `theory.tsv`-replacement work described in
the plan). It writes `phase_p_keypress_realization.json`: per keypress group, the chosen
coda key-combo (or null if left unassigned), its cost, the alternate candidates considered,
and any residual collisions the greedy group-by-group search still missed (see
`realizeKeypressGroupsAsExtraStroke`'s own docstring for why those can happen and why a
final full-assignment verification pass is needed to catch them).

Run: python -m util.build_phase_p_realization
Requires Dictionary.pickle/FirstTheory.pickle (`python dictionary.py` first),
phase_g_keypress_assignment.json (`python -m util.build_phase_g_assignment`) and
resolved_press_sets.json (`python -m src.elicitation`).
"""
import json
import os

from src.ambiguitychecker import (
    buildKeypressGroupExtraAlternates, buildKeypressGroupToWords, buildWordsByOrthoLemme, buildWordToStrokes,
    realizeKeypressGroupsAsExtraStroke,
)
from src.keyboard import Starboard
from util._theoryio import loadFirstTheory

PHASE_G_PATH = "phase_g_keypress_assignment.json"
RESOLVED_PRESS_SETS_PATH = "resolved_press_sets.json"
OUTPUT_PATH = "phase_p_keypress_realization.json"

# Human preference (2026-09-22 session), keyed by MARKER rather than Phase G's own group
# id, since which markers Phase G bundles together (and under what id) can shift between
# reruns -- whichever group ends up holding this marker gets steered toward this physical
# key. `pers_3` on -t: mnemonic, many pers_3 verb forms end in a written "t". `impératif`
# on -k and `pers_2` on -d: kept in that physical order, both ahead of pers_3's -t.
PREFERRED_KEYS_BY_MARKER: dict[str, tuple[int, ...]] = {
    "impératif": (18,),  # -k
    "pers_2": (19,),     # -d
    "pers_3": (20,),     # -t
}


def main() -> None:
    if not os.path.exists(PHASE_G_PATH):
        raise RuntimeError(f"Run `python -m util.build_phase_g_assignment` first to generate {PHASE_G_PATH}.")
    if not os.path.exists(RESOLVED_PRESS_SETS_PATH):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {RESOLVED_PRESS_SETS_PATH}.")

    theory = loadFirstTheory()
    starboard = Starboard.fromJSONFile("starboard3h.json")
    if starboard is None:
        raise RuntimeError("starboard3h.json not found; run dictionary.py once first to generate it.")

    with open(PHASE_G_PATH, encoding="utf-8") as f:
        phaseG = json.load(f)
    markersByKeypress = {
        int(groupId): frozenset(markers) for groupId, markers in phaseG["markersByKeypress"].items()
    }

    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        resolvedGroups = json.load(f)

    wordToStrokes = buildWordToStrokes(theory)
    wordsByOrthoLemme = buildWordsByOrthoLemme(theory)
    groupToWords = buildKeypressGroupToWords(resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme)
    # A self-homograph spelling's OTHER readings (e.g. "calmez" = impératif or pers_2 --
    # see src.elicitation.resolveGroupPressSets) beyond the primary one groupToWords
    # already carries -- realized as their own additional strokes, never forced together
    # with the primary reading (the "-kt" over-marking bug this whole design fixes).
    extraGroupSetsByWord = buildKeypressGroupExtraAlternates(
        resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme
    )
    preferredKeysByGroup: dict[int, tuple[int, ...]] = {}
    for marker, keys in PREFERRED_KEYS_BY_MARKER.items():
        groupId = next((gid for gid, markers in markersByKeypress.items() if marker in markers), None)
        if groupId is not None:
            preferredKeysByGroup[groupId] = keys
    assignment = realizeKeypressGroupsAsExtraStroke(
        groupToWords, theory, starboard,
        extraGroupSetsByWord=extraGroupSetsByWord, preferredKeysByGroup=preferredKeysByGroup,
    )

    artifact = {}
    for groupId in sorted(markersByKeypress):
        chosenKeys = assignment.chosenKeysByGroup.get(groupId)
        artifact[str(groupId)] = {
            "markers": sorted(markersByKeypress[groupId]),
            "affectedWords": len(groupToWords.get(groupId, [])),
            "chosenKeys": list(chosenKeys) if chosenKeys is not None else None,
            "cost": assignment.costByGroup.get(groupId),
            "alternates": [
                {"keys": list(keys), "cost": cost} for keys, cost in assignment.alternatesByGroup.get(groupId, [])
            ],
        }

    theoryCollisionOrthos: list[str] = [w.ortho for w in assignment.residualTheoryCollisions]
    # In-scope (same-lemmeGramCat) collisions Phase P itself failed to prevent -- the real bar.
    sameLemmeGramCatCollisionOrthos: list[tuple[str, str]] = [
        (w1.ortho, w2.ortho) for w1, w2 in assignment.residualCollisions
    ]
    # Same bare lemma, different gramCat -- the already-documented "aller"-style
    # cross-category clash (detectCrossCategoryClash), a separate issue, not Phase P's job.
    crossCategoryClashOrthos: list[tuple[str, str]] = [
        (w1.ortho, w2.ortho) for w1, w2 in assignment.crossCategoryClashCollisions
    ]
    # Different lemma entirely -- the reserved */# keys' job, not yet applied to this
    # `theory`; reported for visibility only, not a Phase P defect.
    crossLemmaCollisionOrthos: list[tuple[str, str]] = [
        (w1.ortho, w2.ortho) for w1, w2 in assignment.crossLemmaCollisions
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "keypressGroups": artifact,
            "residualCollisions": {
                "theoryCollisions": theoryCollisionOrthos,
                "sameLemmeGramCatCollisions (Phase P's own job)": sameLemmeGramCatCollisionOrthos,
                "crossCategoryClashCollisions (out of scope -- aller-style, separate issue)": crossCategoryClashOrthos,
                "crossLemmaCollisions (out of scope -- */# track's job)": crossLemmaCollisionOrthos,
            },
        }, f, ensure_ascii=False, indent=1)

    feasibleCount = len(assignment.chosenKeysByGroup)
    extraAlternateStrokeCount = sum(len(alts) for alts in extraGroupSetsByWord.values())
    print(f"Self-homograph spellings with extra reading(s) beyond their primary "
          f"(e.g. \"calmez\"): {len(extraGroupSetsByWord)} words, "
          f"{extraAlternateStrokeCount} extra strokes realized.")
    for marker, keys in PREFERRED_KEYS_BY_MARKER.items():
        groupId = preferredKeysByGroup and next(
            (gid for gid, k in preferredKeysByGroup.items() if k == keys), None
        )
        honored = assignment.preferredKeyHonoredByGroup.get(groupId) if groupId is not None else None
        status = "honored" if honored else ("NOT honored -- fell back to normal search" if honored is not None
                                             else "marker not live, no group to steer")
        print(f"Preferred key {list(keys)} for marker {marker!r}: {status}")
    print(f"Wrote {OUTPUT_PATH}: {feasibleCount}/{len(markersByKeypress)} keypress groups realized"
          f" ({len(theoryCollisionOrthos)} residual theory collisions,"
          f" {len(sameLemmeGramCatCollisionOrthos)} residual same-lemmeGramCat collisions [Phase P's own job],"
          f" {len(crossCategoryClashOrthos)} cross-category clashes [out of scope, aller-style],"
          f" {len(crossLemmaCollisionOrthos)} cross-lemma collisions [out of scope, */# track's job]).")
    for groupId in sorted(markersByKeypress):
        entry = artifact[str(groupId)]
        status = f"keys {entry['chosenKeys']} (cost {entry['cost']})" if entry["chosenKeys"] else "UNASSIGNED"
        print(f"  group {groupId} {entry['markers']}: {entry['affectedWords']} words -> {status}")


if __name__ == "__main__":
    main()
