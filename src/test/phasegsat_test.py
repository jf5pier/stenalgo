#!/usr/bin/python
# coding: utf-8
"""Tests for src/phasegsat.py"""

import pytest

from ..phaseg import verifyKeypressAssignment
from ..phasegsat import groupSignatures, minKeypressesSat, minKeypressesSatPreferring, serializeAssignment


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


def test_minKeypressesSat_mustShareKey_forces_a_safe_pair_together():
    """The plan's own worked example (pers_2/nbr_p may share, since nbr_p is never
    pressed alone) -- forcing it explicitly should still land on K=2, matching what the
    solver already chooses freely (test_minKeypressesSat_allows_sharing_when_safe)."""
    pressSetsByGroup = {
        "parler_VER": {
            "parle": frozenset(),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"pers_3", "nbr_p"}),
        }
    }
    numKeys, colorOf = minKeypressesSat(
        pressSetsByGroup, mustShareKey=frozenset({frozenset({"pers_2", "nbr_p"})})
    )
    assert colorOf["pers_2"] == colorOf["nbr_p"]
    assert colorOf["pers_3"] != colorOf["pers_2"]  # pers_3/nbr_p co-occur -- must stay apart
    assert numKeys == 2
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSat_mustShareKey_infeasible_when_the_pair_cannot_safely_share():
    """parle needs pers_1 alone and parles needs pers_2 alone with nothing else in the
    group -- forcing pers_1/pers_2 onto the same keypress makes both spellings induce
    the identical set, an unresolvable collision at any K."""
    pressSetsByGroup = {
        "parler_VER": {"parle": frozenset({"pers_1"}), "parles": frozenset({"pers_2"})}
    }
    with pytest.raises(RuntimeError):
        minKeypressesSat(pressSetsByGroup, maxK=4, mustShareKey=frozenset({frozenset({"pers_1", "pers_2"})}))


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


# ── serializeAssignment ────────────────────────────────────────────────────────

def test_serializeAssignment_is_json_ready_and_groups_markers_by_keypress():
    colorOf = {"pers_1": 0, "pers_2": 1, "nbr_p": 1}
    artifact = serializeAssignment(
        numKeys=2,
        colorOf=colorOf,
        mustShareKey=frozenset({frozenset({"pers_2", "nbr_p"})}),
        unpressableMarkers=frozenset({"subjonctif"}),
        weightByKeypress={0: 5.0, 1: 3.0},
    )
    assert artifact["keypressCount"] == 2
    assert artifact["markersByKeypress"] == {"0": ["pers_1"], "1": ["nbr_p", "pers_2"]}
    assert artifact["mustShareKey"] == [["nbr_p", "pers_2"]]
    assert artifact["preferSameKey"] == []  # not given -- defaults empty, distinct from mustShareKey
    assert artifact["preferencesSatisfied"] == "0/0"
    assert artifact["unpressableMarkers"] == ["subjonctif"]
    assert artifact["frequencyWeightedChordSizes"] == {"0": 5.0, "1": 3.0}
    import json
    json.dumps(artifact)  # must not raise


def test_serializeAssignment_records_soft_preference_provenance_separately_from_mustShareKey():
    artifact = serializeAssignment(
        numKeys=2, colorOf={"pers_1": 0, "pers_2": 1},
        mustShareKey=frozenset(), unpressableMarkers=frozenset(), weightByKeypress={},
        preferSameKey=frozenset({frozenset({"pers_1", "pers_2"})}), preferencesSatisfied=0,
    )
    assert artifact["mustShareKey"] == []
    assert artifact["preferSameKey"] == [["pers_1", "pers_2"]]
    assert artifact["preferencesSatisfied"] == "0/1"


def test_serializeAssignment_defaults_missing_weight_to_zero():
    artifact = serializeAssignment(
        numKeys=2, colorOf={"pers_1": 0, "pers_2": 1},
        mustShareKey=frozenset(), unpressableMarkers=frozenset(), weightByKeypress={0: 4.0},
    )
    assert artifact["frequencyWeightedChordSizes"] == {"0": 4.0, "1": 0.0}


# ── minKeypressesSatPreferring (soft preference, vs. mustShareKey's hard one) ────────

def test_minKeypressesSatPreferring_never_inflates_K_and_satisfies_a_free_preference():
    """The plan's own safe-sharing example (pers_2/nbr_p can share without cost) --
    preferring it should still land on the true minimum K=2, with the preference
    actually honored since it costs nothing here."""
    pressSetsByGroup = {
        "parler_VER": {
            "parle": frozenset(),
            "parles": frozenset({"pers_2"}),
            "parlent": frozenset({"pers_3", "nbr_p"}),
        }
    }
    numKeys, colorOf, satisfied = minKeypressesSatPreferring(
        pressSetsByGroup, preferSameKey=frozenset({frozenset({"pers_2", "nbr_p"})})
    )
    assert numKeys == 2
    assert satisfied == 1
    assert colorOf["pers_2"] == colorOf["nbr_p"]
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSatPreferring_leaves_an_unsafe_preference_unsatisfied_rather_than_failing():
    """pers_1 and pers_2 can NEVER safely share in this fixture (test_minKeypressesSat_
    mustShareKey_infeasible_when_the_pair_cannot_safely_share's underlying case) --
    the soft version must still return a valid, conflict-free assignment (unlike
    mustShareKey, which would raise), just without honoring the preference."""
    pressSetsByGroup = {
        "parler_VER": {"parle": frozenset({"pers_1"}), "parles": frozenset({"pers_2"})}
    }
    numKeys, colorOf, satisfied = minKeypressesSatPreferring(
        pressSetsByGroup, preferSameKey=frozenset({frozenset({"pers_1", "pers_2"})})
    )
    assert satisfied == 0
    assert colorOf["pers_1"] != colorOf["pers_2"]
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSatPreferring_matches_minKeypressesSat_when_no_preference_given():
    numKeysPlain, _ = minKeypressesSat(_parler_press_sets())
    numKeysPreferring, colorOf, satisfied = minKeypressesSatPreferring(_parler_press_sets())
    assert numKeysPreferring == numKeysPlain
    assert satisfied == 0
    assert verifyKeypressAssignment(_parler_press_sets(), colorOf) == []
