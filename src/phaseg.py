#!/usr/bin/python
# coding: utf-8
"""
Phase G — grouping (see ATOMIC_KEYPRESS_REWIRE_PLAN.md's Phase G section): assign every
live marker to an abstract keypress, minimizing K, without breaking any homophone
group's no-conflict property. Input is `resolved_press_sets.json` (Phase E6's persisted
artifact) -- NOT `src/featureextractor.py`'s `buildDiscriminatorSelection` output.

Vocabulary (GLOSSARY.md / the plan's own fixed vocabulary): Marker (atomic feature),
Press (the marker-set a writer presses for one word), Keypress (the abstract unit a
group of markers maps to -- physical key assignment is Phase P).
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

# One homophone group's per-spelling press-sets, keyed by an opaque group id (see
# `loadResolvedPressSets`) rather than elicitation.py's LemmaHomophoneGroupKey -- Phase G
# only needs the press-sets themselves, not the stroke/lemma identity behind them.
PressSetsByGroup = dict[str, dict[str, frozenset[str]]]


def loadResolvedPressSets(path: str = "resolved_press_sets.json") -> PressSetsByGroup:
    """Reload E6's persisted artifact (see `src.elicitation.serializeResolvedPressSets`)."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    pressSetsByGroup: PressSetsByGroup = {}
    for entry in entries:
        strokesKey = "|".join(",".join(map(str, stroke)) for stroke in entry["strokes"])
        groupId = f"{entry['lemmeGramCat']}@{strokesKey}"
        pressSetsByGroup[groupId] = {ortho: frozenset(atoms) for ortho, atoms in entry["pressSets"].items()}
    return pressSetsByGroup


def liveMarkers(pressSetsByGroup: PressSetsByGroup) -> set[str]:
    """Every marker that appears in at least one elicited press. A marker no press ever
    contains is unpressable by construction -- excluded here, not assigned a keypress."""
    return {
        atom
        for pressSetByOrtho in pressSetsByGroup.values()
        for pressSet in pressSetByOrtho.values()
        for atom in pressSet
    }


def coOccurrencePairs(pressSetsByGroup: PressSetsByGroup) -> set[frozenset[str]]:
    """Pairs of markers ever pressed together in the same spelling's resolved press-set.
    These can never share a keypress: a keypress can't be pressed "halfway", so merging
    two markers that are sometimes needed together would make it impossible to ever
    press one without the other -- destroying the very distinction they exist to make."""
    pairs: set[frozenset[str]] = set()
    for pressSetByOrtho in pressSetsByGroup.values():
        for pressSet in pressSetByOrtho.values():
            for a, b in combinations(sorted(pressSet), 2):
                pairs.add(frozenset({a, b}))
    return pairs


def wouldCollideIfMergedPairs(pressSetsByGroup: PressSetsByGroup) -> set[frozenset[str]]:
    """
    Pairs of markers that never co-occur but would still be unsafe to bundle onto one
    keypress. Merging m1 and m2 means pressing either one asserts BOTH (a keypress
    can't be pressed "halfway"): if some spelling's press-set is exactly T union {m1}
    and another spelling *in the same group* is exactly T union {m2} (identical except
    one has m1 where the other has m2), merging makes both induce T union {m1, m2} --
    indistinguishable. This is the plan's own worked example: pers_2 and nbr_p may
    share a keypress "iff parlent is never pressed with nbr_p alone" -- i.e. iff no
    such T-matching pair exists.
    """
    unsafe: set[frozenset[str]] = set()
    for pressSetByOrtho in pressSetsByGroup.values():
        pressSets = list(pressSetByOrtho.values())
        for setA, setB in combinations(pressSets, 2):
            onlyInA, onlyInB = setA - setB, setB - setA
            if len(onlyInA) == 1 and len(onlyInB) == 1:
                (markerA,), (markerB,) = onlyInA, onlyInB
                unsafe.add(frozenset({markerA, markerB}))
    return unsafe


def greedyColorMarkers(markers: set[str], mustDifferEdges: set[frozenset[str]]) -> dict[str, int]:
    """Welsh-Powell greedy coloring (largest-degree-first): assigns each marker a
    keypress id such that no `mustDifferEdges` pair shares one. Not necessarily the
    minimum K -- a cheap, honest first feasible assignment; CP-SAT optimality (per the
    plan's `_colorFeatures`/`_minSpecialKeypressesNeeded` seed) is a later refinement."""
    adjacency: dict[str, set[str]] = {m: set() for m in markers}
    for edge in mustDifferEdges:
        a, b = tuple(edge)
        adjacency[a].add(b)
        adjacency[b].add(a)
    order = sorted(markers, key=lambda m: -len(adjacency[m]))
    colorOf: dict[str, int] = {}
    for marker in order:
        usedColors = {colorOf[neighbor] for neighbor in adjacency[marker] if neighbor in colorOf}
        colorOf[marker] = next(c for c in range(len(markers) + 1) if c not in usedColors)
    return colorOf


def inducedPressSet(
    trueMarkers: frozenset[str], colorOf: dict[str, int], markersByKeypress: dict[int, frozenset[str]]
) -> frozenset[str]:
    """What actually gets asserted when writing a word whose true required markers are
    `trueMarkers`, under a keypress assignment: press every keypress covering at least
    one needed marker -- doing so also asserts every OTHER marker bundled onto that same
    keypress, since a keypress can't be pressed "halfway"."""
    touchedKeypresses = {colorOf[marker] for marker in trueMarkers}
    result: set[str] = set()
    for keypress in touchedKeypresses:
        result |= markersByKeypress[keypress]
    return frozenset(result)


@dataclass
class KeypressConflict:
    """A keypress assignment's own E5-style finding: within one group, two or more
    spellings whose INDUCED press-sets (after keypress bundling) are identical."""
    groupId: str
    inducedPressSet: frozenset[str]
    orthos: tuple[str, ...]


def verifyKeypressAssignment(
    pressSetsByGroup: PressSetsByGroup, colorOf: dict[str, int]
) -> list[KeypressConflict]:
    """
    Full (not merely pairwise) safety check: for every group, recompute each spelling's
    induced press-set under this keypress assignment and confirm no two spellings
    collide. `coOccurrencePairs`/`wouldCollideIfMergedPairs` are a pairwise
    characterization of what makes a coloring safe; this is the ground-truth simulation
    that would also catch any residual multi-marker-bundle interaction a pairwise
    analysis alone might miss.
    """
    markersByKeypress: dict[int, set[str]] = defaultdict(set)
    for marker, keypress in colorOf.items():
        markersByKeypress[keypress].add(marker)
    frozenMarkersByKeypress = {k: frozenset(ms) for k, ms in markersByKeypress.items()}

    conflicts: list[KeypressConflict] = []
    for groupId, pressSetByOrtho in pressSetsByGroup.items():
        orthosByInduced: dict[frozenset[str], list[str]] = defaultdict(list)
        for ortho, trueMarkers in pressSetByOrtho.items():
            induced = inducedPressSet(trueMarkers, colorOf, frozenMarkersByKeypress)
            orthosByInduced[induced].append(ortho)
        for induced, orthos in orthosByInduced.items():
            if len(orthos) > 1:
                conflicts.append(KeypressConflict(groupId, induced, tuple(sorted(orthos))))
    return conflicts


@dataclass
class PhaseGResult:
    keypressCount: int
    markersByKeypress: dict[int, frozenset[str]]
    unpressableMarkers: frozenset[str]
    conflicts: list[KeypressConflict]


def runPhaseG(pressSetsByGroup: PressSetsByGroup, allAtoms: set[str] = frozenset()) -> PhaseGResult:
    """Build the must-differ graph (hard co-occurrence + would-collide-if-merged),
    greedily color it, and verify the result against every group's actual press-sets."""
    markers = liveMarkers(pressSetsByGroup)
    mustDifferEdges = coOccurrencePairs(pressSetsByGroup) | wouldCollideIfMergedPairs(pressSetsByGroup)
    colorOf = greedyColorMarkers(markers, mustDifferEdges)
    conflicts = verifyKeypressAssignment(pressSetsByGroup, colorOf)

    markersByKeypress: dict[int, set[str]] = defaultdict(set)
    for marker, keypress in colorOf.items():
        markersByKeypress[keypress].add(marker)

    return PhaseGResult(
        keypressCount=len(markersByKeypress),
        markersByKeypress={k: frozenset(ms) for k, ms in markersByKeypress.items()},
        unpressableMarkers=frozenset(allAtoms - markers),
        conflicts=conflicts,
    )


if __name__ == "__main__":
    import os

    if not os.path.exists("resolved_press_sets.json"):
        raise RuntimeError("Run `python -m src.elicitation` first to build resolved_press_sets.json.")

    pressSetsByGroup = loadResolvedPressSets()

    allAtoms: set[str] = set()
    if os.path.exists("questionnaire.json"):
        with open("questionnaire.json", encoding="utf-8") as qf:
            for item in json.load(qf):
                allAtoms.update(item["atomsA"])
                allAtoms.update(item["atomsB"])

    result = runPhaseG(pressSetsByGroup, allAtoms)

    print("=== Phase G grouping report ===")
    print(f"Homophone groups considered:  {len(pressSetsByGroup)}")
    print(f"Live markers (ever pressed):  {len(liveMarkers(pressSetsByGroup))}")
    print(f"Unpressable markers:          {len(result.unpressableMarkers)} {sorted(result.unpressableMarkers)}")
    print(f"Keypresses (K), greedy:       {result.keypressCount}")
    print(f"Verification conflicts:       {len(result.conflicts)}")

    print("\nKeypress -> markers:")
    for keypress in sorted(result.markersByKeypress):
        print(f"  {keypress}: {sorted(result.markersByKeypress[keypress])}")

    if result.conflicts:
        print("\nConflicts found (greedy coloring was unsafe -- needs investigation):")
        for conflict in result.conflicts[:10]:
            print(f"   {conflict.groupId}: {sorted(conflict.inducedPressSet)} -> {conflict.orthos}")
