from ..phaseg import (
    coOccurrencePairs,
    greedyColorMarkers,
    inducedPressSet,
    liveMarkers,
    runPhaseG,
    verifyKeypressAssignment,
    wouldCollideIfMergedPairs,
)


def _parler_press_sets() -> dict[str, dict[str, frozenset[str]]]:
    """The parler cluster's resolved press-sets (see elicitation_test.py's
    `_opposition_answers`): parle needs pers_1, parles needs pers_2, parlent needs
    nbr_p -- all three singleton and mutually distinct, so all three markers must end
    up on separate keypresses (any pairwise merge collapses two of them together)."""
    return {
        "parler_VER": {
            "parle": frozenset({"pers_1"}),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"nbr_p"}),
        }
    }


# ── liveMarkers / coOccurrencePairs / wouldCollideIfMergedPairs ──────────────

def test_liveMarkers_is_the_union_of_every_press():
    pressSetsByGroup = _parler_press_sets()
    assert liveMarkers(pressSetsByGroup) == {"pers_1", "pers_2", "nbr_p"}


def test_coOccurrencePairs_finds_markers_pressed_together():
    pressSetsByGroup = {
        "g1": {"parlent": frozenset({"pers_3", "nbr_p"}), "parle": frozenset()},
    }
    assert coOccurrencePairs(pressSetsByGroup) == {frozenset({"pers_3", "nbr_p"})}


def test_coOccurrencePairs_empty_when_every_press_is_a_singleton():
    assert coOccurrencePairs(_parler_press_sets()) == set()


def test_wouldCollideIfMergedPairs_flags_singletons_that_differ_by_swapping_one_marker():
    # parle={pers_1} vs parles={pers_2}: T=∅ both sides -- merging pers_1/pers_2 would
    # make both induce {pers_1, pers_2}, indistinguishable.
    pairs = wouldCollideIfMergedPairs(_parler_press_sets())
    assert frozenset({"pers_1", "pers_2"}) in pairs
    assert frozenset({"pers_1", "nbr_p"}) in pairs
    assert frozenset({"pers_2", "nbr_p"}) in pairs


def test_wouldCollideIfMergedPairs_allows_the_plans_own_worked_example():
    """The plan's own example: pers_2 (parles) and nbr_p (only ever inside parlent's
    pers_3:nbr_p) MAY share a keypress, because nbr_p is never pressed alone -- so no
    T-matching pair (T union {pers_2} vs T union {nbr_p}) exists."""
    pressSetsByGroup = {
        "parler_VER": {
            "parle": frozenset(),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"pers_3", "nbr_p"}),
        }
    }
    pairs = wouldCollideIfMergedPairs(pressSetsByGroup)
    assert frozenset({"pers_2", "nbr_p"}) not in pairs


def test_wouldCollideIfMergedPairs_only_compares_within_the_same_group():
    """Two spellings in DIFFERENT groups differing by one marker must not be flagged --
    marker chords only ever compete inside one cluster (different sound-strokes never
    collide, per the plan's vocabulary)."""
    pressSetsByGroup = {
        "g1": {"a": frozenset({"m1"})},
        "g2": {"b": frozenset({"m2"})},
    }
    assert wouldCollideIfMergedPairs(pressSetsByGroup) == set()


# ── greedyColorMarkers / inducedPressSet / verifyKeypressAssignment ──────────

def test_greedyColorMarkers_gives_every_edges_endpoints_different_colors():
    markers = {"a", "b", "c"}
    edges = {frozenset({"a", "b"}), frozenset({"b", "c"})}
    colorOf = greedyColorMarkers(markers, edges)
    assert colorOf["a"] != colorOf["b"]
    assert colorOf["b"] != colorOf["c"]


def test_greedyColorMarkers_lets_non_adjacent_markers_share_a_color():
    markers = {"a", "b"}
    colorOf = greedyColorMarkers(markers, set())
    assert colorOf["a"] == colorOf["b"]


def test_inducedPressSet_pulls_in_the_whole_keypress_bundle():
    colorOf = {"m1": 0, "m2": 0, "m3": 1}
    markersByKeypress = {0: frozenset({"m1", "m2"}), 1: frozenset({"m3"})}
    # Only m1 is truly needed, but m1 and m2 share a keypress -- pressing it asserts both.
    assert inducedPressSet(frozenset({"m1"}), colorOf, markersByKeypress) == frozenset({"m1", "m2"})
    assert inducedPressSet(frozenset({"m3"}), colorOf, markersByKeypress) == frozenset({"m3"})


def test_verifyKeypressAssignment_flags_a_collision_from_an_unsafe_merge():
    pressSetsByGroup = _parler_press_sets()
    # Force pers_1 and pers_2 onto the same keypress -- an unsafe merge per the earlier test.
    colorOf = {"pers_1": 0, "pers_2": 0, "nbr_p": 1}
    conflicts = verifyKeypressAssignment(pressSetsByGroup, colorOf)
    assert len(conflicts) == 1
    assert conflicts[0].groupId == "parler_VER"
    assert set(conflicts[0].orthos) == {"parle", "parles"}


def test_verifyKeypressAssignment_clean_when_every_marker_gets_its_own_keypress():
    pressSetsByGroup = _parler_press_sets()
    colorOf = {"pers_1": 0, "pers_2": 1, "nbr_p": 2}
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


# ── runPhaseG (integration) ───────────────────────────────────────────────────

def test_runPhaseG_finds_a_conflict_free_assignment_for_the_parler_cluster():
    result = runPhaseG(_parler_press_sets())
    assert result.conflicts == []
    assert result.keypressCount == 3  # all three markers mutually incompatible
    assert result.unpressableMarkers == frozenset()


def test_runPhaseG_reports_unpressable_markers():
    result = runPhaseG(_parler_press_sets(), allAtoms={"pers_1", "pers_2", "nbr_p", "subjonctif"})
    assert result.unpressableMarkers == frozenset({"subjonctif"})


def test_runPhaseG_allows_sharing_when_safe():
    pressSetsByGroup = {
        "parler_VER": {
            "parle": frozenset(),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"pers_3", "nbr_p"}),
        }
    }
    result = runPhaseG(pressSetsByGroup)
    assert result.conflicts == []
    # pers_3 and nbr_p co-occur (parlent) so must be separate; pers_2 is free to share
    # a keypress with either one (which one is an unspecified tie-break) -- 2 keypresses
    # suffice either way, confirmed conflict-free by the verification step above.
    assert result.keypressCount == 2
