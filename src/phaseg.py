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
# only needs the press-sets themselves, not the stroke/lemma identity behind them. Each
# spelling maps to a LIST of alternate press-sets (almost always length 1) -- more than
# one only when the spelling is itself a homograph reading of itself (see
# `src.elicitation.resolveGroupPressSets`); alternates of the SAME spelling are allowed
# to collide with each other (same output text), only alternates belonging to
# *different* spellings must never induce the same keypress set.
PressSetsByGroup = dict[str, dict[str, list[frozenset[str]]]]

# Same group id, each spelling's corpus frequency (see `elicitation.buildFrequencyByGroupOrtho`).
FrequencyByGroup = dict[str, dict[str, float]]


def loadResolvedPressSets(path: str = "resolved_press_sets.json") -> PressSetsByGroup:
    """Reload E6's persisted artifact (see `src.elicitation.serializeResolvedPressSets`)."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    pressSetsByGroup: PressSetsByGroup = {}
    for entry in entries:
        strokesKey = "|".join(",".join(map(str, stroke)) for stroke in entry["strokes"])
        groupId = f"{entry['lemmeGramCat']}@{strokesKey}"
        pressSetsByGroup[groupId] = {
            ortho: [frozenset(alt) for alt in alternates]
            for ortho, alternates in entry["pressSets"].items()
        }
    return pressSetsByGroup


def loadGroupOrthoFrequencies(path: str = "resolved_press_sets.json") -> FrequencyByGroup:
    """Reload each spelling's corpus frequency from the same E6 artifact, keyed the same
    way as `loadResolvedPressSets`. Older artifacts written before frequency-weighted
    chord-size reporting existed simply have no "frequencies" field -- absent entries
    read back as 0.0 (see `frequencyWeightedChordSizes`)."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    frequencyByGroup: FrequencyByGroup = {}
    for entry in entries:
        strokesKey = "|".join(",".join(map(str, stroke)) for stroke in entry["strokes"])
        groupId = f"{entry['lemmeGramCat']}@{strokesKey}"
        frequencyByGroup[groupId] = dict(entry.get("frequencies", {}))
    return frequencyByGroup


def liveMarkers(pressSetsByGroup: PressSetsByGroup) -> set[str]:
    """Every marker that appears in at least one elicited press. A marker no press ever
    contains is unpressable by construction -- excluded here, not assigned a keypress."""
    return {
        atom
        for pressSetByOrtho in pressSetsByGroup.values()
        for alternates in pressSetByOrtho.values()
        for pressSet in alternates
        for atom in pressSet
    }


def coOccurrencePairs(pressSetsByGroup: PressSetsByGroup) -> set[frozenset[str]]:
    """Pairs of markers ever pressed together in the same reading's resolved press-set.
    These can never share a keypress: a keypress can't be pressed "halfway", so merging
    two markers that are sometimes needed together would make it impossible to ever
    press one without the other -- destroying the very distinction they exist to make."""
    pairs: set[frozenset[str]] = set()
    for pressSetByOrtho in pressSetsByGroup.values():
        for alternates in pressSetByOrtho.values():
            for pressSet in alternates:
                for a, b in combinations(sorted(pressSet), 2):
                    pairs.add(frozenset({a, b}))
    return pairs


def wouldCollideIfMergedPairs(pressSetsByGroup: PressSetsByGroup) -> set[frozenset[str]]:
    """
    Pairs of markers that never co-occur but would still be unsafe to bundle onto one
    keypress. Merging m1 and m2 means pressing either one asserts BOTH (a keypress
    can't be pressed "halfway"): if some spelling's press-set is exactly T union {m1}
    and ANOTHER SPELLING's *in the same group* is exactly T union {m2} (identical except
    one has m1 where the other has m2), merging makes both induce T union {m1, m2} --
    indistinguishable. This is the plan's own worked example: pers_2 and nbr_p may
    share a keypress "iff parlent is never pressed with nbr_p alone" -- i.e. iff no
    such T-matching pair exists.

    Only compares press-sets belonging to DIFFERENT spellings: two alternates of the
    SAME spelling (a self-homograph reading, e.g. "calmez"'s impératif/indicatif
    readings) are allowed to look mergeable -- they already produce the same output
    text, so there is nothing to keep distinguishable between them.
    """
    unsafe: set[frozenset[str]] = set()
    for pressSetByOrtho in pressSetsByGroup.values():
        orthos = sorted(pressSetByOrtho)
        for orthoA, orthoB in combinations(orthos, 2):
            for setA, setB in ((a, b) for a in pressSetByOrtho[orthoA] for b in pressSetByOrtho[orthoB]):
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
    DIFFERENT spellings whose INDUCED press-sets (after keypress bundling) are
    identical. Two alternates of the same spelling inducing the same value is not a
    conflict (see `wouldCollideIfMergedPairs`)."""
    groupId: str
    inducedPressSet: frozenset[str]
    orthos: tuple[str, ...]


def verifyKeypressAssignment(
    pressSetsByGroup: PressSetsByGroup, colorOf: dict[str, int]
) -> list[KeypressConflict]:
    """
    Full (not merely pairwise) safety check: for every group, recompute every spelling's
    (every alternate's) induced press-set under this keypress assignment and confirm no
    two DIFFERENT spellings collide. `coOccurrencePairs`/`wouldCollideIfMergedPairs` are a
    pairwise characterization of what makes a coloring safe; this is the ground-truth
    simulation that would also catch any residual multi-marker-bundle interaction a
    pairwise analysis alone might miss.
    """
    markersByKeypress: dict[int, set[str]] = defaultdict(set)
    for marker, keypress in colorOf.items():
        markersByKeypress[keypress].add(marker)
    frozenMarkersByKeypress = {k: frozenset(ms) for k, ms in markersByKeypress.items()}

    conflicts: list[KeypressConflict] = []
    for groupId, pressSetByOrtho in pressSetsByGroup.items():
        orthosByInduced: dict[frozenset[str], set[str]] = defaultdict(set)
        for ortho, alternates in pressSetByOrtho.items():
            for trueMarkers in alternates:
                induced = inducedPressSet(trueMarkers, colorOf, frozenMarkersByKeypress)
                orthosByInduced[induced].add(ortho)
        for induced, orthos in orthosByInduced.items():
            if len(orthos) > 1:
                conflicts.append(KeypressConflict(groupId, induced, tuple(sorted(orthos))))
    return conflicts


def frequencyWeightedChordSizes(
    pressSetsByGroup: PressSetsByGroup, frequencyByGroup: FrequencyByGroup, colorOf: dict[str, int]
) -> dict[int, float]:
    """
    Per the plan's Phase G objective ("minimize K; report frequency-weighted chord
    sizes -- full cost optimization is Phase P"): for each keypress, the total corpus
    frequency of every spelling whose TRUE (elicited, not induced) press-set touches it
    -- i.e. how often that keypress actually gets struck in real writing. This is a
    Phase P input (a busy keypress should land on an easy physical key/finger), not
    something Phase G optimizes against; Phase G only reports it. A group missing from
    `frequencyByGroup` (e.g. an older artifact written before frequencies were tracked)
    contributes 0.0, not an error.
    """
    weightByKeypress: dict[int, float] = defaultdict(float)
    for groupId, pressSetByOrtho in pressSetsByGroup.items():
        frequencyByOrtho = frequencyByGroup.get(groupId, {})
        for ortho, alternates in pressSetByOrtho.items():
            frequency = frequencyByOrtho.get(ortho, 0.0)
            touchedKeypresses = {colorOf[marker] for trueMarkers in alternates for marker in trueMarkers}
            for keypress in touchedKeypresses:
                weightByKeypress[keypress] += frequency
    return dict(weightByKeypress)


@dataclass
class PhaseGResult:
    keypressCount: int
    markersByKeypress: dict[int, frozenset[str]]
    unpressableMarkers: frozenset[str]
    conflicts: list[KeypressConflict]
    frequencyWeightedChordSizes: dict[int, float]


def _findSharedKeypressPair(
    conflict: KeypressConflict, pressSetsByGroup: PressSetsByGroup, colorOf: dict[str, int]
) -> frozenset[str] | None:
    """For a verified conflict, find one pair of markers -- one from each of two
    colliding spellings' TRUE (not induced) press-sets -- that currently share a
    keypress. Forcing them apart is guaranteed to change at least one of the colliding
    spellings' induced set, since inducing pulls in whatever keypress each true marker
    sits on: two spellings can induce the identical union even with completely disjoint
    true press-sets, if each one's markers happen to land on the same PAIR of keypresses
    as the other's (see e.g. {pers_3, nbr_p} vs {pers_2, pers_1} both touching the same
    two keypresses) -- a failure mode no pairwise pre-check catches. Each colliding
    spelling may have several alternates (self-homograph readings); any alternate of one
    colliding spelling paired with any alternate of the other is a valid pair to search."""
    alternatesByOrtho = [pressSetsByGroup[conflict.groupId][ortho] for ortho in conflict.orthos]
    for i in range(len(alternatesByOrtho)):
        for j in range(i + 1, len(alternatesByOrtho)):
            for trueSetA in alternatesByOrtho[i]:
                for trueSetB in alternatesByOrtho[j]:
                    for markerA in trueSetA:
                        for markerB in trueSetB:
                            if markerA != markerB and colorOf[markerA] == colorOf[markerB]:
                                return frozenset({markerA, markerB})
    return None


def runPhaseG(
    pressSetsByGroup: PressSetsByGroup,
    allAtoms: set[str] = frozenset(),
    maxRepairPasses: int = 50,
    frequencyByGroup: FrequencyByGroup | None = None,
) -> PhaseGResult:
    """
    Build the must-differ graph (hard co-occurrence + would-collide-if-merged), greedily
    color it, and verify the result against every group's actual press-sets. Pairwise
    pre-checks alone are not sufficient (two spellings can induce the same union via two
    *different* marker pairs landing on the same two keypresses without either pair ever
    being individually unsafe -- see `_findSharedKeypressPair`), so any conflict found by
    verification triggers forcing one implicated marker pair apart and re-coloring,
    repeating until clean or no further progress is possible (residual conflicts are
    returned rather than hidden).
    """
    markers = liveMarkers(pressSetsByGroup)
    mustDifferEdges = set(coOccurrencePairs(pressSetsByGroup) | wouldCollideIfMergedPairs(pressSetsByGroup))

    colorOf = greedyColorMarkers(markers, mustDifferEdges)
    conflicts = verifyKeypressAssignment(pressSetsByGroup, colorOf)
    for _ in range(maxRepairPasses):
        if not conflicts:
            break
        newEdges = {
            edge for conflict in conflicts
            if (edge := _findSharedKeypressPair(conflict, pressSetsByGroup, colorOf)) is not None
        }
        if not newEdges - mustDifferEdges:
            break  # no progress possible; report the residual conflicts honestly
        mustDifferEdges |= newEdges
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
        frequencyWeightedChordSizes=frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup or {}, colorOf),
    )


if __name__ == "__main__":
    import os

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

    result = runPhaseG(pressSetsByGroup, allAtoms, frequencyByGroup=frequencyByGroup)

    print("=== Phase G grouping report ===")
    print(f"Homophone groups considered:  {len(pressSetsByGroup)}")
    print(f"Live markers (ever pressed):  {len(liveMarkers(pressSetsByGroup))}")
    print(f"Unpressable markers:          {len(result.unpressableMarkers)} {sorted(result.unpressableMarkers)}")
    print(f"Keypresses (K), greedy:       {result.keypressCount}")
    print(f"Verification conflicts:       {len(result.conflicts)}")

    totalWeight = sum(result.frequencyWeightedChordSizes.values()) or 1.0
    print("\nKeypress -> markers (frequency-weighted usage; Phase P input, not optimized here):")
    for keypress in sorted(result.markersByKeypress):
        weight = result.frequencyWeightedChordSizes.get(keypress, 0.0)
        share = 100.0 * weight / totalWeight
        print(f"  {keypress}: {sorted(result.markersByKeypress[keypress])}  "
              f"(usage weight {weight:.1f}, {share:.1f}%)")

    if result.conflicts:
        print("\nConflicts found (greedy coloring was unsafe -- needs investigation):")
        for conflict in result.conflicts[:10]:
            print(f"   {conflict.groupId}: {sorted(conflict.inducedPressSet)} -> {conflict.orthos}")
