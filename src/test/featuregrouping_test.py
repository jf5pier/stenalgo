from ..featuregrouping import (
    frequencyWeightedChordSizes,
    inducedPressSet,
    liveMarkers,
    verifyKeypressAssignment,
)


def _parler_press_sets() -> dict[str, dict[str, list[frozenset[str]]]]:
    """The parler cluster's resolved press-sets (see elicitation_test.py's
    `_opposition_answers`): parle needs pers_1, parles needs pers_2, parlent needs
    nbr_p -- all three singleton and mutually distinct, so all three markers must end
    up on separate keypresses (any pairwise merge collapses two of them together).
    Every spelling here has exactly one alternate -- the common case."""
    return {
        "parler_VER": {
            "parle": [frozenset({"pers_1"})],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"nbr_p"})],
        }
    }


# ── liveMarkers ──────────────────────────────────────────────────────────────

def test_liveMarkers_is_the_union_of_every_press():
    pressSetsByGroup = _parler_press_sets()
    assert liveMarkers(pressSetsByGroup) == {"pers_1", "pers_2", "nbr_p"}


# ── inducedPressSet / verifyKeypressAssignment ───────────────────────────────

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


def test_verifyKeypressAssignment_allows_a_self_homographs_alternates_to_collide():
    """"calmez"'s own two alternates ({impératif}, {pers_2}) inducing the same value
    (both bundled onto the same keypress) is not a conflict -- only a DIFFERENT
    spelling reaching that same induced value would be."""
    pressSetsByGroup = {
        "calmer_VER": {
            "calmez": [frozenset({"impératif"}), frozenset({"pers_2"})],
            "calmer": [frozenset({"infinitif"})],
        }
    }
    colorOf = {"impératif": 0, "pers_2": 0, "infinitif": 1}
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


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
    pressSetsByGroup = {"abaisser_VER": {"abaisseraient": [frozenset({"pers_3", "nbr_p"})]}}
    frequencyByGroup = {"abaisser_VER": {"abaisseraient": 4.0}}
    colorOf = {"pers_3": 0, "nbr_p": 1}
    assert frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf) == {0: 4.0, 1: 4.0}


def test_frequencyWeightedChordSizes_counts_a_spellings_frequency_once_per_keypress_across_alternates():
    """A self-homograph spelling's frequency is attributed to every keypress touched by
    ANY of its alternates, but only once per keypress even if more than one alternate
    touches it."""
    pressSetsByGroup = {
        "calmer_VER": {"calmez": [frozenset({"impératif"}), frozenset({"pers_2"})]},
    }
    frequencyByGroup = {"calmer_VER": {"calmez": 6.0}}
    colorOf = {"impératif": 0, "pers_2": 0}
    assert frequencyWeightedChordSizes(pressSetsByGroup, frequencyByGroup, colorOf) == {0: 6.0}


def test_frequencyWeightedChordSizes_defaults_missing_frequency_to_zero():
    """A group or ortho absent from frequencyByGroup (e.g. an older artifact) contributes
    0.0 rather than raising."""
    pressSetsByGroup = _parler_press_sets()
    colorOf = {"pers_1": 0, "pers_2": 1, "nbr_p": 2}
    assert frequencyWeightedChordSizes(pressSetsByGroup, {}, colorOf) == {0: 0.0, 1: 0.0, 2: 0.0}
