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

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from .phaseg import PressSetsByGroup, liveMarkers

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


def _feasibleAssignment(
    markers: list[str], signatures: list[GroupSignature], numKeys: int, timeLimitS: float
) -> tuple[bool, dict[str, int] | None]:
    """
    Try to color `markers` onto `numKeys` abstract keypresses such that, within every
    signature, every pair of its press-sets induces a distinct touched-keypress set --
    the exact ground truth `phaseg.verifyKeypressAssignment` checks, not a pairwise
    approximation of it. Returns (provenFeasible, colorOf); when infeasible, colorOf is
    None; on a solver timeout without a proof either way, raises (a "no" answer must be
    a proof, not a guess -- see `minKeypressesSat`).
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


def minKeypressesSat(
    pressSetsByGroup: PressSetsByGroup, maxK: int = 20, timeLimitS: float = 30.0
) -> tuple[int, dict[str, int]]:
    """
    The provably smallest number of keypresses onto which every live marker can be
    assigned without any homophone group's induced press-sets colliding -- scans
    numKeys = 1, 2, ... and returns the first CP-SAT proves feasible, so the result is
    a proof of minimality (every smaller numKeys was proven infeasible), not a greedy
    upper bound like `phaseg.runPhaseG`'s.
    """
    markers = sorted(liveMarkers(pressSetsByGroup))
    signatures = groupSignatures(pressSetsByGroup)
    for numKeys in range(1, maxK + 1):
        feasible, colorOf = _feasibleAssignment(markers, signatures, numKeys, timeLimitS)
        if feasible:
            assert colorOf is not None
            return numKeys, colorOf
    raise RuntimeError(f"no feasible assignment found up to maxK={maxK}")


if __name__ == "__main__":
    import os

    from .phaseg import loadResolvedPressSets

    if not os.path.exists("resolved_press_sets.json"):
        raise RuntimeError("Run `python -m src.elicitation` first to build resolved_press_sets.json.")

    pressSetsByGroup = loadResolvedPressSets()
    signatures = groupSignatures(pressSetsByGroup)
    print("=== Phase G CP-SAT optimality search ===")
    print(f"Homophone groups considered:    {len(pressSetsByGroup)}")
    print(f"Distinct group signatures:      {len(signatures)}")

    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    print(f"\nProven minimum K:               {numKeys}")

    markersByKeypress: dict[int, list[str]] = {k: [] for k in range(numKeys)}
    for marker, k in colorOf.items():
        markersByKeypress[k].append(marker)
    print("\nKeypress -> markers:")
    for k in sorted(markersByKeypress):
        print(f"  {k}: {sorted(markersByKeypress[k])}")
