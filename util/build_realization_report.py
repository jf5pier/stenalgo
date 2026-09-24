"""
Persist the report-build output of Discriminating-Feature Stroke Realization (Realization
Phase) (see docs/specs/discriminating-features.md §4): for each of the abstract keypress groups of
Discriminating-Feature Grouping (Grouping Phase) (`keypress_groups.json`), search for a
physical right-hand coda key-combo (`starboard3h.json`'s keys `[16..25]`) that realizes it
as a brand-new trailing stroke appended after a word's own strokes (an extra "syllable"),
without colliding with any word's existing stroke in the live `theory`, or with any other
affected word's own newly-composed stroke -- composing ALL of a word's needed groups
into that one shared extra stroke, not just the group currently being decided.

This is the report-build call site -- it does NOT rewrite `theory` or persist a
final stroke-per-word table; the disambiguated theory is computed inline by `Dictionary.buildDisambiguatedTheory`
(the inline path) on every exporter run. It writes `realization_report.json`: per keypress group, the chosen
coda key-combo (or null if left unassigned), its cost, the alternate candidates considered,
and any residual collisions the greedy group-by-group search still missed (see
`realizeKeypressGroupsAsExtraStroke`'s own docstring for why those can happen and why a
final full-assignment verification pass is needed to catch them).

Run: python -m util.build_realization_report
Requires Dictionary.pickle/PhoneticTheory.pickle (`python -m util.build_phonetic_theory` first),
keypress_groups.json (`python -m util.build_keypress_groups`) and
resolved_press_sets.json (`python -m src.elicitation`).
"""
import json
import os

from src.ambiguitychecker import (
    PREFERRED_KEYS_BY_MARKER, buildKeypressGroupExtraAlternates, buildKeypressGroupToWords, buildWordsByOrthoLemme,
    buildWordToStrokes, realizeKeypressGroupsAsExtraStroke, resolvePreferredKeysByGroup,
)
from src.keyboard import Starboard
from util._theoryio import loadPhoneticTheory

PHASE_G_PATH = "keypress_groups.json"
RESOLVED_PRESS_SETS_PATH = "resolved_press_sets.json"
OUTPUT_PATH = "realization_report.json"


def main() -> None:
    if not os.path.exists(PHASE_G_PATH):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {PHASE_G_PATH}.")
    if not os.path.exists(RESOLVED_PRESS_SETS_PATH):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {RESOLVED_PRESS_SETS_PATH}.")

    theory = loadPhoneticTheory()
    starboard = Starboard.fromJSONFile("starboard3h.json")
    if starboard is None:
        raise RuntimeError("starboard3h.json not found; it is a committed input -- run from the repo root.")

    with open(PHASE_G_PATH, encoding="utf-8") as f:
        keypressGroups = json.load(f)
    markersByKeypress = {
        int(groupId): frozenset(markers) for groupId, markers in keypressGroups["markersByKeypress"].items()
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
    preferredKeysByGroup = resolvePreferredKeysByGroup(markersByKeypress)
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
    # In-scope (same-lemmeGramCat) collisions the Realization Phase itself failed to prevent
    # -- the real bar.
    sameLemmeGramCatCollisionOrthos: list[tuple[str, str]] = [
        (w1.ortho, w2.ortho) for w1, w2 in assignment.residualCollisions
    ]
    # Same bare lemma, different gramCat -- the already-documented "aller"-style
    # cross-category clash (detectCrossCategoryClash), a separate issue, not the
    # Realization Phase's job.
    crossCategoryClashOrthos: list[tuple[str, str]] = [
        (w1.ortho, w2.ortho) for w1, w2 in assignment.crossCategoryClashCollisions
    ]
    # Different lemma entirely -- the star/hash mark track's job, not yet applied to this
    # `theory`; reported for visibility only, not a Realization Phase defect.
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
