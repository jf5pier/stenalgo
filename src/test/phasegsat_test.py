#!/usr/bin/python
# coding: utf-8
"""Tests for src/phasegsat.py"""

from ..phaseg import verifyKeypressAssignment
from ..phasegsat import groupSignatures, minKeypressesSat


def _parler_press_sets() -> dict[str, dict[str, frozenset[str]]]:
    """Same fixture as phaseg_test.py's: three mutually singleton, mutually distinct
    markers -- must land on 3 separate keypresses no matter how cleverly colored."""
    return {
        "parler_VER": {
            "parle": frozenset({"pers_1"}),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"nbr_p"}),
        }
    }


def test_groupSignatures_dedups_orthography_and_stroke_identity():
    """Two different groups sharing the identical multiset of press-sets collapse to one
    signature -- orthography/stroke identity is irrelevant to the coloring problem."""
    pressSetsByGroup = {
        "parler_VER@(K1,)": {"parle": frozenset({"pers_1"}), "parles": frozenset({"pers_2"})},
        "chanter_VER@(K2,)": {"chante": frozenset({"pers_1"}), "chantes": frozenset({"pers_2"})},
    }
    assert groupSignatures(pressSetsByGroup) == [frozenset({frozenset({"pers_1"}), frozenset({"pers_2"})})]


def test_minKeypressesSat_finds_the_true_minimum_for_three_mutually_distinct_markers():
    numKeys, colorOf = minKeypressesSat(_parler_press_sets())
    assert numKeys == 3
    assert len({colorOf["pers_1"], colorOf["pers_2"], colorOf["nbr_p"]}) == 3


def test_minKeypressesSat_allows_sharing_when_safe():
    """The plan's own worked example: pers_2 and nbr_p may share a keypress because
    nbr_p is never pressed alone -- CP-SAT should find K=2, matching the greedy result
    (phaseg_test.py's test_runPhaseG_allows_sharing_when_safe)."""
    pressSetsByGroup = {
        "parler_VER": {
            "parle": frozenset(),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"pers_3", "nbr_p"}),
        }
    }
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    assert numKeys == 2
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSat_solves_the_two_marker_bundle_collision_pairwise_checks_miss():
    """Same abaisser_VER regression as phaseg_test.py's
    test_runPhaseG_repairs_a_two_marker_bundle_collision_no_pairwise_check_catches --
    CP-SAT's exact per-signature distinctness constraint should get this right in one
    shot, with no repair loop needed, and should find it's colorable with only 2 keys
    (pers_3 alone, {pers_1, pers_2, nbr_p} bundled) -- better than greedy's 3."""
    pressSetsByGroup = {
        "abaisser_VER": {
            "abaisseraient": frozenset({"pers_3", "nbr_p"}),
            "abaisserais": frozenset({"pers_2", "pers_1"}),
            "abaisserait": frozenset(),
        }
    }
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    assert numKeys == 2
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSat_result_is_a_valid_assignment_for_a_combined_lexicon_slice():
    """Combine both regression fixtures into one lexicon: CP-SAT's result must remain
    conflict-free against the FULL combined press-set data (the real ground-truth
    check), not just each fixture in isolation."""
    pressSetsByGroup = {
        "parler_VER": _parler_press_sets()["parler_VER"],
        "abaisser_VER": {
            "abaisseraient": frozenset({"pers_3", "nbr_p"}),
            "abaisserais": frozenset({"pers_2", "pers_1"}),
            "abaisserait": frozenset(),
        },
    }
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []
    assert numKeys >= 3  # parler_VER alone already forces 3 distinct keypresses
