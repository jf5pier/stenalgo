#!/usr/bin/python
# coding: utf-8
"""
Phase G — CP-SAT exact minimum-K search (see ATOMIC_KEYPRESS_REWIRE_PLAN.md's Phase G
section: "Phase G is only greedy-optimal, not proven-minimal... reusing
_colorFeatures/_minSpecialKeypressesNeeded's scaffolding... to search for something
smaller than K=6/7"). `src/phaseg.py`'s `greedyColorMarkers` finds *a* feasible K but
gives no guarantee it's the smallest possible; this module proves the minimum exactly
(or proves a candidate K infeasible), by direct search rather than by reusing
`_colorFeatures` itself -- that scaffolding's "conflict" semantics (at most one member
of a feature SET may share a key) is the wrong shape for Phase G's actual constraint,
which is per-cluster set-DISTINCTNESS over induced press-sets (see module docstring
below and `phaseg.verifyKeypressAssignment`, the ground truth this mirrors exactly --
not the pairwise `coOccurrencePairs`/`wouldCollideIfMergedPairs` pre-checks, which are
a greedy-only optimization, not part of the real constraint).

Scaling: the real lexicon has 47,799 homophone groups, but only their *signature* --
the set of distinct true press-sets held by their spellings -- matters to the coloring
problem (orthography and stroke identity don't). Deduplicating on signature collapses
this to ~200 distinct problems (see `groupSignatures`), making an exact CP-SAT
formulation tractable.
"""

from itertools import combinations

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from .phaseg import FrequencyByGroup, PressSetsByGroup, frequencyWeightedChordSizes, liveMarkers

# One homophone group's shape, stripped of orthography/stroke identity: the set of
# distinct true press-sets its spellings hold. Two groups with the same signature pose
# the identical coloring problem.
GroupSignature = frozenset[frozenset[str]]


def groupSignatures(pressSetsByGroup: PressSetsByGroup) -> list[GroupSignature]:
    """Deduplicate groups down to their distinct signatures (see module docstring)."""
    return sorted(
        {frozenset(pressSetByOrtho.values()) for pressSetByOrtho in pressSetsByGroup.values()},
        key=lambda sig: (len(sig), sorted(tuple(sorted(p)) for p in sig)),
    )


def _buildDistinctnessModel(
    markers: list[str], signatures: list[GroupSignature], numKeys: int
) -> tuple[cp_model.CpModel, dict[tuple[str, int], IntVar]]:
    """
    The shared core of every Phase G CP-SAT search: each marker gets exactly one of
    `numKeys` keypresses, and within every signature, every pair of its press-sets must
    induce a distinct touched-keypress set -- the exact ground truth
    `phaseg.verifyKeypressAssignment` checks, not a pairwise approximation of it.
    Callers (`_feasibleAssignment` for a hard mustShareKey search,
    `_bestAssignmentPreferring` for a soft preference search) add their own extra
    constraints/objective on top of this model and `x`.
    """
    model = cp_model.CpModel()
    x: dict[tuple[str, int], IntVar] = {
        (m, k): model.NewBoolVar(f"x_{i}_{k}") for i, m in enumerate(markers) for k in range(numKeys)
    }
    for m in markers:
        _ = model.AddExactlyOne(x[m, k] for k in range(numKeys))

    for sigIdx, signature in enumerate(signatures):
        presses = sorted(signature, key=sorted)
        touches: dict[tuple[int, int], IntVar] = {}
        for pressIdx, press in enumerate(presses):
            for k in range(numKeys):
                t = model.NewBoolVar(f"t_{sigIdx}_{pressIdx}_{k}")
                relevant = [x[m, k] for m in press]
                if relevant:
                    _ = model.AddMaxEquality(t, relevant)
                else:
                    _ = model.Add(t == 0)
                touches[(pressIdx, k)] = t
        for i in range(len(presses)):
            for j in range(i + 1, len(presses)):
                differsAt: list[IntVar] = []
                for k in range(numKeys):
                    a, b = touches[(i, k)], touches[(j, k)]
                    d = model.NewBoolVar(f"d_{sigIdx}_{i}_{j}_{k}")
                    # Exact XOR linearization -- d must be FORCED to 0 when touches agree,
                    # or the solver could satisfy "differs somewhere" without truly differing.
                    _ = model.Add(d <= a + b)
                    _ = model.Add(d <= 2 - a - b)
                    _ = model.Add(d >= a - b)
                    _ = model.Add(d >= b - a)
                    differsAt.append(d)
                _ = model.Add(sum(differsAt) >= 1)

    return model, x


def _addMustDifferPairs(
    model: cp_model.CpModel, x: dict[tuple[str, int], IntVar], numKeys: int, pairs: set[tuple[str, str]]
) -> None:
    """Force each (m1, m2) pair onto DIFFERENT keypresses: for every keypress, at most
    one of the two may sit there -- since each marker occupies exactly one keypress
    (`_buildDistinctnessModel`'s AddExactlyOne), this is enough to prevent them ever
    landing on the same one."""
    for m1, m2 in pairs:
        for k in range(numKeys):
            _ = model.Add(x[m1, k] + x[m2, k] <= 1)


def _aloneAndMustDifferPairs(
    markers: list[str], aloneKeys: frozenset[str], mustDifferGroups: frozenset[frozenset[str]]
) -> set[tuple[str, str]]:
    """Expand `aloneKeys` (each marker must share its keypress with no one) and
    `mustDifferGroups` (every pair WITHIN a group must land on different keypresses --
    not a hard requirement that they differ from markers outside the group) into the
    flat set of (m1, m2) pairs `_addMustDifferPairs` needs."""
    pairs: set[tuple[str, str]] = set()
    for m in aloneKeys:
        for other in markers:
            if other != m:
                pairs.add(tuple(sorted((m, other))))
    for group in mustDifferGroups:
        for m1, m2 in combinations(sorted(group), 2):
            pairs.add((m1, m2))
    return pairs


def _feasibleAssignment(
    markers: list[str],
    signatures: list[GroupSignature],
    numKeys: int,
    timeLimitS: float,
    mustShareKey: frozenset[frozenset[str]] = frozenset(),
    aloneKeys: frozenset[str] = frozenset(),
    mustDifferGroups: frozenset[frozenset[str]] = frozenset(),
) -> tuple[bool, dict[str, int] | None]:
    """
    Try to color `markers` onto `numKeys` abstract keypresses (see `_buildDistinctnessModel`).
    `mustShareKey` additionally pins each given marker pair onto the SAME keypress (e.g.
    for exploring a specific bundling decision, not merely letting the solver find one on
    its own); `aloneKeys` forces each given marker to share its keypress with nothing else;
    `mustDifferGroups` forces every pair within a group onto DIFFERENT keypresses. All
    three are HARD constraints: infeasible under them is reported as such, not silently
    dropped (see `_bestAssignmentPreferring` for a soft version of same-key preferences
    that never fails this way). Returns (provenFeasible, colorOf); when infeasible,
    colorOf is None; on a solver timeout without a proof either way, raises (a "no"
    answer must be a proof, not a guess -- see `minKeypressesSat`).
    """
    model, x = _buildDistinctnessModel(markers, signatures, numKeys)
    for pair in mustShareKey:
        m1, m2 = tuple(pair)
        for k in range(numKeys):
            _ = model.Add(x[m1, k] == x[m2, k])
    _addMustDifferPairs(model, x, numKeys, _aloneAndMustDifferPairs(markers, aloneKeys, mustDifferGroups))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeLimitS
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        colorOf = {m: next(k for k in range(numKeys) if solver.BooleanValue(x[m, k])) for m in markers}
        return True, colorOf
    if status == cp_model.INFEASIBLE:
        return False, None
    raise RuntimeError(
        f"CP-SAT could not prove numKeys={numKeys} feasible or infeasible within {timeLimitS}s "
        "(status UNKNOWN) -- raise timeLimitS rather than trusting a guess."
    )


def _bestAssignmentPreferring(
    markers: list[str],
    signatures: list[GroupSignature],
    numKeys: int,
    preferSameKey: frozenset[frozenset[str]],
    timeLimitS: float,
    aloneKeys: frozenset[str] = frozenset(),
    mustDifferGroups: frozenset[frozenset[str]] = frozenset(),
) -> tuple[dict[str, int], int]:
    """
    Among all valid colorings at this (already known feasible) `numKeys`, find one
    maximizing how many `preferSameKey` pairs land on the same keypress -- a SOFT
    tiebreaker, unlike `_feasibleAssignment`'s `mustShareKey`: a pair that genuinely
    can't share safely at this K is simply left apart rather than making the whole
    search infeasible. `aloneKeys`/`mustDifferGroups` (see `_feasibleAssignment`) are
    still HARD constraints even here -- only the same-key preference is soft. Returns
    (colorOf, howManyPreferencesSatisfied).
    """
    model, x = _buildDistinctnessModel(markers, signatures, numKeys)
    _addMustDifferPairs(model, x, numKeys, _aloneAndMustDifferPairs(markers, aloneKeys, mustDifferGroups))

    sameKeyVars: list[IntVar] = []
    for pair in preferSameKey:
        m1, m2 = tuple(pair)
        same = model.NewBoolVar(f"pref_{m1}_{m2}")
        perKeyAnd: list[IntVar] = []
        for k in range(numKeys):
            y = model.NewBoolVar(f"prefAt_{m1}_{m2}_{k}")
            _ = model.Add(y <= x[m1, k])
            _ = model.Add(y <= x[m2, k])
            _ = model.Add(y >= x[m1, k] + x[m2, k] - 1)
            perKeyAnd.append(y)
        _ = model.Add(same == sum(perKeyAnd))
        sameKeyVars.append(same)
    if sameKeyVars:
        model.Maximize(sum(sameKeyVars))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeLimitS
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"CP-SAT could not find/optimize a numKeys={numKeys} assignment within {timeLimitS}s "
            "-- this numKeys was already proven feasible elsewhere, so a timeout here means "
            "raise timeLimitS, not that no solution exists."
        )
    colorOf = {m: next(k for k in range(numKeys) if solver.BooleanValue(x[m, k])) for m in markers}
    satisfied = sum(1 for v in sameKeyVars if solver.BooleanValue(v))
    return colorOf, satisfied


def minKeypressesSat(
    pressSetsByGroup: PressSetsByGroup,
    maxK: int = 20,
    timeLimitS: float = 30.0,
    mustShareKey: frozenset[frozenset[str]] = frozenset(),
    aloneKeys: frozenset[str] = frozenset(),
    mustDifferGroups: frozenset[frozenset[str]] = frozenset(),
) -> tuple[int, dict[str, int]]:
    """
    The provably smallest number of keypresses onto which every live marker can be
    assigned without any homophone group's induced press-sets colliding -- scans
    numKeys = 1, 2, ... and returns the first CP-SAT proves feasible, so the result is
    a proof of minimality (every smaller numKeys was proven infeasible), not a greedy
    upper bound like `phaseg.runPhaseG`'s. `mustShareKey` (see `_feasibleAssignment`)
    pins specific marker pairs onto the same keypress throughout the scan; `aloneKeys`
    forces a marker to share its keypress with nothing else; `mustDifferGroups` forces
    every pair within a group onto different keypresses -- all HARD constraints applied
    throughout the scan (so they can inflate K, or make it infeasible outright, unlike a
    soft preference -- see `minKeypressesSatPreferring`).
    """
    markers = sorted(liveMarkers(pressSetsByGroup))
    signatures = groupSignatures(pressSetsByGroup)
    for numKeys in range(1, maxK + 1):
        feasible, colorOf = _feasibleAssignment(
            markers, signatures, numKeys, timeLimitS, mustShareKey, aloneKeys, mustDifferGroups
        )
        if feasible:
            assert colorOf is not None
            return numKeys, colorOf
    raise RuntimeError(f"no feasible assignment found up to maxK={maxK} under the given hard constraints")


def minKeypressesSatPreferring(
    pressSetsByGroup: PressSetsByGroup,
    preferSameKey: frozenset[frozenset[str]] = frozenset(),
    maxK: int = 20,
    timeLimitS: float = 30.0,
    aloneKeys: frozenset[str] = frozenset(),
    mustDifferGroups: frozenset[frozenset[str]] = frozenset(),
) -> tuple[int, dict[str, int], int]:
    """
    Two-phase search: first find the TRUE minimum K exactly as `minKeypressesSat` does
    -- unconstrained by the SOFT `preferSameKey` (so it can never inflate K), but still
    subject to any HARD `aloneKeys`/`mustDifferGroups` (those apply throughout, same as
    in `minKeypressesSat`, since they're requirements, not preferences). Then, AT that
    fixed minimum K, re-solve maximizing how many `preferSameKey` pairs end up sharing a
    keypress -- a tiebreaker among the (possibly many) equally-minimal colorings, not a
    requirement. Returns (numKeys, colorOf, preferencesSatisfied); `preferencesSatisfied`
    lets a caller tell "got it for free" (== len(preferSameKey)) apart from "couldn't fit
    it in at this K" (< len(preferSameKey)).
    """
    markers = sorted(liveMarkers(pressSetsByGroup))
    signatures = groupSignatures(pressSetsByGroup)
    numKeys, _ = minKeypressesSat(
        pressSetsByGroup, maxK=maxK, timeLimitS=timeLimitS, aloneKeys=aloneKeys, mustDifferGroups=mustDifferGroups
    )
    colorOf, satisfied = _bestAssignmentPreferring(
        markers, signatures, numKeys, preferSameKey, timeLimitS, aloneKeys, mustDifferGroups
    )
    return numKeys, colorOf, satisfied


def serializeAssignment(
    numKeys: int,
    colorOf: dict[str, int],
    mustShareKey: frozenset[frozenset[str]],
    unpressableMarkers: frozenset[str],
    weightByKeypress: dict[int, float],
    preferSameKey: frozenset[frozenset[str]] = frozenset(),
    preferencesSatisfied: int = 0,
    aloneKeys: frozenset[str] = frozenset(),
    mustDifferGroups: frozenset[frozenset[str]] = frozenset(),
) -> dict:
    """The persisted, adopted Phase G artifact -- a specific CP-SAT-proven assignment
    (not the search machinery itself), JSON-serializable for `util/build_phase_g_assignment.py`.
    `mustShareKey`/`aloneKeys`/`mustDifferGroups` record HARD-forced decisions
    (`minKeypressesSat`); `preferSameKey`/`preferencesSatisfied` record a SOFT tiebreaker
    (`minKeypressesSatPreferring`) -- distinct provenance, since the latter never risked
    inflating K to get its bundling, the former could have."""
    markersByKeypress: dict[int, list[str]] = {k: [] for k in range(numKeys)}
    for marker, k in colorOf.items():
        markersByKeypress[k].append(marker)
    return {
        "keypressCount": numKeys,
        "markersByKeypress": {str(k): sorted(ms) for k, ms in markersByKeypress.items()},
        "mustShareKey": [sorted(pair) for pair in sorted(mustShareKey, key=sorted)],
        "aloneKeys": sorted(aloneKeys),
        "mustDifferGroups": [sorted(group) for group in sorted(mustDifferGroups, key=sorted)],
        "preferSameKey": [sorted(pair) for pair in sorted(preferSameKey, key=sorted)],
        "preferencesSatisfied": f"{preferencesSatisfied}/{len(preferSameKey)}",
        "unpressableMarkers": sorted(unpressableMarkers),
        "frequencyWeightedChordSizes": {str(k): weightByKeypress.get(k, 0.0) for k in range(numKeys)},
    }


if __name__ == "__main__":
    import os
    import sys

    from .phaseg import loadResolvedPressSets

    if not os.path.exists("resolved_press_sets.json"):
        raise RuntimeError("Run `python -m src.elicitation` first to build resolved_press_sets.json.")

    # python -m src.phasegsat marker1:marker2 -- HARD: force this pair onto the same
    #   keypress throughout the K-scan (`mustShareKey`; can inflate K, or fail outright,
    #   if the pair can't safely share at the true minimum).
    # python -m src.phasegsat marker1~marker2 -- SOFT: find the TRUE minimum K first,
    #   then prefer this pair sharing a keypress only as a tiebreaker among equally-
    #   minimal colorings (`minKeypressesSatPreferring`; never inflates K).
    mustShareKey = frozenset(frozenset(arg.split(":")) for arg in sys.argv[1:] if ":" in arg)
    preferSameKey = frozenset(frozenset(arg.split("~")) for arg in sys.argv[1:] if "~" in arg)

    pressSetsByGroup = loadResolvedPressSets()
    signatures = groupSignatures(pressSetsByGroup)
    print("=== Phase G CP-SAT optimality search ===")
    print(f"Homophone groups considered:    {len(pressSetsByGroup)}")
    print(f"Distinct group signatures:      {len(signatures)}")
    if mustShareKey:
        print(f"Forced (hard) same-keypress pairs:   {[sorted(p) for p in mustShareKey]}")
    if preferSameKey:
        print(f"Preferred (soft) same-keypress pairs: {[sorted(p) for p in preferSameKey]}")

    if preferSameKey:
        numKeys, colorOf, satisfied = minKeypressesSatPreferring(pressSetsByGroup, preferSameKey=preferSameKey)
        print(f"Preferences satisfied:          {satisfied}/{len(preferSameKey)}")
    else:
        numKeys, colorOf = minKeypressesSat(pressSetsByGroup, mustShareKey=mustShareKey)
    print(f"\nProven minimum K:               {numKeys}")

    markersByKeypress: dict[int, list[str]] = {k: [] for k in range(numKeys)}
    for marker, k in colorOf.items():
        markersByKeypress[k].append(marker)
    print("\nKeypress -> markers:")
    for k in sorted(markersByKeypress):
        print(f"  {k}: {sorted(markersByKeypress[k])}")
