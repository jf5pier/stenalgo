from ..phaseg import (
    _findSharedKeypressPair,
    coOccurrencePairs,
    frequencyWeightedChordSizes,
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


# ── frequencyWeightedChordSizes ───────────────────────────────────────────────

def test_frequencyWeightedChordSizes_sums_true_press_frequency_per_keypress():
    """Each spelling's frequency is added to every keypress its TRUE press-set touches
    (not the induced one) -- parle (freq 5) only touches pers_1's keypress, parlent
    (freq 2) only nbr_p's."""
    pressSetsByGroup = _parler_press_sets()
    frequencyByGroup = {"parler_VER": {"parle": 5.0, "parles": 3.0, "parlent": 2.0}}
    colorOf = {"pers_1": 0, "pers_2": 1, "nbr_p": 2}
    assert frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf) == {0: 5.0, 1: 3.0, 2: 2.0}


def test_frequencyWeightedChordSizes_adds_frequency_to_every_touched_keypress():
    """A press-set spanning two keypresses contributes its full frequency to both --
    'abaisseraient' needing {pers_3, nbr_p} on separate keypresses touches both."""
    pressSetsByGroup = {"abaisser_VER": {"abaisseraient": frozenset({"pers_3", "nbr_p"})}}
    frequencyByGroup = {"abaisser_VER": {"abaisseraient": 4.0}}
    colorOf = {"pers_3": 0, "nbr_p": 1}
    assert frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf) == {0: 4.0, 1: 4.0}


def test_frequencyWeightedChordSizes_defaults_missing_frequency_to_zero():
    """A group or ortho absent from frequencyByGroup (e.g. an older artifact) contributes
    0.0 rather than raising."""
    pressSetsByGroup = _parler_press_sets()
    colorOf = {"pers_1": 0, "pers_2": 1, "nbr_p": 2}
    assert frequencyWeightedChordSizes(pressSetsByGroup, {}, colorOf) == {0: 0.0, 1: 0.0, 2: 0.0}


def test_runPhaseG_threads_frequency_weighting_through():
    frequencyByGroup = {"parler_VER": {"parle": 5.0, "parles": 3.0, "parlent": 2.0}}
    result = runPhaseG(_parler_press_sets(), frequencyByGroup=frequencyByGroup)
    assert sum(result.frequencyWeightedChordSizes.values()) == 10.0
    assert set(result.frequencyWeightedChordSizes) == set(result.markersByKeypress)


def test_runPhaseG_frequency_weighting_defaults_to_zero_when_unset():
    result = runPhaseG(_parler_press_sets())
    assert set(result.frequencyWeightedChordSizes.values()) == {0.0}


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


def test_runPhaseG_repairs_a_two_marker_bundle_collision_no_pairwise_check_catches():
    """Real failure found comparing two elicitation calibrations (abaisser_VER):
    'abaisseraient' needs {pers_3, nbr_p}, 'abaisserais' needs {pers_2, pers_1}. The hard
    co-occurrence rule forbids pers_3+nbr_p sharing and pers_1+pers_2 sharing (each pair
    IS pressed together), but says nothing about the CROSS pairing -- pers_3+pers_2 and
    nbr_p+pers_1 -- which `wouldCollideIfMergedPairs` also clears (neither press-set
    differs from another by swapping just one marker). Yet coloring pers_3/pers_2 onto
    one keypress and nbr_p/pers_1 onto another makes both words touch the same two
    keypresses and induce the identical union. Only a real verify-and-repair loop (not
    pairwise pre-filtering) catches this."""
    pressSetsByGroup = {
        "abaisser_VER": {
            "abaisseraient": frozenset({"pers_3", "nbr_p"}),
            "abaisserais": frozenset({"pers_2", "pers_1"}),
            "abaisserait": frozenset(),
        }
    }
    # Confirm the failure mode is real: the CROSS pairs are cleared by both pairwise checks.
    assert frozenset({"pers_3", "pers_2"}) not in wouldCollideIfMergedPairs(pressSetsByGroup)
    assert frozenset({"nbr_p", "pers_1"}) not in wouldCollideIfMergedPairs(pressSetsByGroup)

    result = runPhaseG(pressSetsByGroup)
    assert result.conflicts == []


def test_findSharedKeypressPair_locates_the_colliding_marker_pair():
    from ..phaseg import KeypressConflict

    pressSetsByGroup = {
        "abaisser_VER": {
            "abaisseraient": frozenset({"pers_3", "nbr_p"}),
            "abaisserais": frozenset({"pers_2", "pers_1"}),
        }
    }
    colorOf = {"pers_3": 0, "pers_2": 0, "nbr_p": 1, "pers_1": 1}
    conflict = KeypressConflict(
        groupId="abaisser_VER",
        inducedPressSet=frozenset({"pers_3", "pers_2", "nbr_p", "pers_1"}),
        orthos=("abaisseraient", "abaisserais"),
    )
    pair = _findSharedKeypressPair(conflict, pressSetsByGroup, colorOf)
    assert pair in ({"pers_3", "pers_2"}, {"nbr_p", "pers_1"})
