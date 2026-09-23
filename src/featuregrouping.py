#!/usr/bin/python
# coding: utf-8
"""
Discriminating-Feature Grouping (Grouping Phase) loaders and verifiers (the spec is
docs/specs/discriminating-features.md; the exact CP-SAT solver is
src/featuregroupingsat.py): assign every live atomic feature to an abstract keypress group,
minimizing K, without breaking any homophone group's no-conflict property. Input is
`resolved_press_sets.json`
(the persisted artifact of the Elicitation Phase's Press-Set Resolution) --
NOT `src/featureextractor.py`'s discriminator-selection output.

Vocabulary (GLOSSARY.md / the plan's own fixed vocabulary): Marker (atomic feature),
Press (the marker-set a writer presses for one word), Keypress (the abstract unit a
group of markers maps to -- physical key assignment is Discriminating-Feature Stroke
Realization (Realization Phase)).
"""

import json
from collections import defaultdict
from dataclasses import dataclass

# One homophone group's per-spelling press-sets, keyed by an opaque group id (see
# `loadResolvedPressSets`) rather than elicitation.py's LemmaHomophoneGroupKey -- the Grouping Phase
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
    conflict (they already produce the same output text)."""
    groupId: str
    inducedPressSet: frozenset[str]
    orthos: tuple[str, ...]


def verifyKeypressAssignment(
    pressSetsByGroup: PressSetsByGroup, colorOf: dict[str, int]
) -> list[KeypressConflict]:
    """
    Full (not merely pairwise) safety check: for every group, recompute every spelling's
    (every alternate's) induced press-set under this keypress assignment and confirm no
    two DIFFERENT spellings collide. This is the ground-truth simulation, which also
    catches multi-marker-bundle interactions a pairwise analysis alone would miss.
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
    Per the plan's Phase G objective for Discriminating-Feature Grouping (Grouping Phase)
    ("minimize K; report frequency-weighted chord sizes -- full cost optimization is
    Phase P", i.e. Discriminating-Feature Stroke Realization (Realization Phase)): for
    each keypress, the total corpus
    frequency of every spelling whose TRUE (elicited, not induced) press-set touches it
    -- i.e. how often that keypress actually gets struck in real writing. This is a
    Realization Phase input (a busy keypress should land on an easy physical key/finger),
    not something the Grouping Phase optimizes against; the Grouping Phase only reports it. A
    group missing from `frequencyByGroup` (e.g. an older artifact written before frequencies
    were tracked) contributes 0.0, not an error.
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
