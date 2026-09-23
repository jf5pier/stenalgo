#!/usr/bin/python
# coding: utf-8
"""Tests for src/featuregroupingsat.py"""

import pytest

from ..featuregrouping import verifyKeypressAssignment
from ..featuregroupingsat import (
    ExclusiveGroupPreference,
    SameKeyPreference,
    groupSignatures,
    minKeypressesSat,
    minKeypressesSatPreferring,
    minKeypressesSatWithPriorities,
    serializeAssignment,
)


def _parler_press_sets() -> dict[str, dict[str, list[frozenset[str]]]]:
    """Same fixture as featuregrouping_test.py's: three mutually singleton, mutually distinct
    markers -- must land on 3 separate keypresses no matter how cleverly colored."""
    return {
        "parler_VER": {
            "parle": [frozenset({"pers_1"})],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"nbr_p"})],
        }
    }


def test_groupSignatures_dedups_orthography_and_stroke_identity():
    """Two different groups sharing the identical multiset of per-spelling alternates
    collapse to one signature -- orthography/stroke identity is irrelevant to the
    coloring problem."""
    pressSetsByGroup = {
        "parler_VER@(K1,)": {"parle": [frozenset({"pers_1"})], "parles": [frozenset({"pers_2"})]},
        "chanter_VER@(K2,)": {"chante": [frozenset({"pers_1"})], "chantes": [frozenset({"pers_2"})]},
    }
    assert groupSignatures(pressSetsByGroup) == [
        frozenset({frozenset({frozenset({"pers_1"})}), frozenset({frozenset({"pers_2"})})})
    ]


def test_groupSignatures_keeps_a_spellings_several_alternates_in_one_bucket():
    """A self-homograph spelling's alternates ("calmez" = impératif reading or pers_2
    reading) stay together in one per-spelling bucket, distinct from other spellings'
    buckets -- this is what lets `_buildDistinctnessModel` exempt them from having to
    differ from each other while still requiring they differ from other spellings."""
    pressSetsByGroup = {
        "calmer_VER": {
            "calmez": [frozenset({"impératif"}), frozenset({"pers_2"})],
            "calmer": [frozenset({"infinitif"})],
        }
    }
    signatures = groupSignatures(pressSetsByGroup)
    assert len(signatures) == 1
    signature = signatures[0]
    assert frozenset({frozenset({"impératif"}), frozenset({"pers_2"})}) in signature
    assert frozenset({frozenset({"infinitif"})}) in signature


def test_minKeypressesSat_finds_the_true_minimum_for_three_mutually_distinct_markers():
    numKeys, colorOf = minKeypressesSat(_parler_press_sets())
    assert numKeys == 3
    assert len({colorOf["pers_1"], colorOf["pers_2"], colorOf["nbr_p"]}) == 3


def test_minKeypressesSat_lets_a_self_homographs_alternates_share_the_same_keypress():
    """The real "calmez" regression, proven at the exact CP-SAT level: calmez's two
    alternates (`impératif`, `pers_2`) may share ONE keypress with each other (nothing
    needs to keep a spelling's own readings apart), while still needing to differ from
    "calmer"'s `infinitif` -- so the true minimum here is K=2, not K=3."""
    pressSetsByGroup = {
        "calmer_VER": {
            "calmez": [frozenset({"impératif"}), frozenset({"pers_2"})],
            "calmer": [frozenset({"infinitif"})],
        }
    }
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    assert numKeys == 2
    assert colorOf["impératif"] == colorOf["pers_2"]
    assert colorOf["infinitif"] != colorOf["impératif"]
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSat_allows_sharing_when_safe():
    """The plan's own worked example: pers_2 and nbr_p may share a keypress because
    nbr_p is never pressed alone -- CP-SAT should find K=2, matching the greedy result
    (featuregrouping_test.py's test_runFeatureGrouping_allows_sharing_when_safe)."""
    pressSetsByGroup = {
        "parler_VER": {
            "parle": [frozenset()],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"pers_3", "nbr_p"})],
        }
    }
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup)
    assert numKeys == 2
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSat_solves_the_two_marker_bundle_collision_pairwise_checks_miss():
    """Same abaisser_VER regression as featuregrouping_test.py's
    test_runFeatureGrouping_repairs_a_two_marker_bundle_collision_no_pairwise_check_catches --
    CP-SAT's exact per-signature distinctness constraint should get this right in one
    shot, with no repair loop needed, and should find it's colorable with only 2 keys
    (pers_3 alone, {pers_1, pers_2, nbr_p} bundled) -- better than greedy's 3."""
    pressSetsByGroup = {
        "abaisser_VER": {
            "abaisseraient": [frozenset({"pers_3", "nbr_p"})],
            "abaisserais": [frozenset({"pers_2", "pers_1"})],
            "abaisserait": [frozenset()],
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
            "parle": [frozenset()],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"pers_3", "nbr_p"})],
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
        "parler_VER": {"parle": [frozenset({"pers_1"})], "parles": [frozenset({"pers_2"})]}
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
            "abaisseraient": [frozenset({"pers_3", "nbr_p"})],
            "abaisserais": [frozenset({"pers_2", "pers_1"})],
            "abaisserait": [frozenset()],
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
            "parle": [frozenset()],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"pers_3", "nbr_p"})],
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
        "parler_VER": {"parle": [frozenset({"pers_1"})], "parles": [frozenset({"pers_2"})]}
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


# ── aloneKeys / mustDifferGroups (hard structural constraints) ───────────────────────

def _safe_sharing_press_sets() -> dict[str, dict[str, frozenset[str]]]:
    """The plan's own worked example: pers_2 and nbr_p CAN safely share a keypress
    (nbr_p is never pressed alone) -- free minimum is K=2."""
    return {
        "parler_VER": {
            "parle": [frozenset()],
            "parles": [frozenset({"pers_2"})],
            "parlent": [frozenset({"pers_3", "nbr_p"})],
        }
    }


def test_aloneKeys_forces_the_marker_to_share_with_nothing():
    pressSetsByGroup = _safe_sharing_press_sets()
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup, aloneKeys=frozenset({"nbr_p"}))
    assert all(m == "nbr_p" or colorOf[m] != colorOf["nbr_p"] for m in colorOf)
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_mustDifferGroups_forces_every_pair_in_the_group_onto_different_keys():
    pressSetsByGroup = _safe_sharing_press_sets()
    group = frozenset({"pers_2", "pers_3", "nbr_p"})
    numKeys, colorOf = minKeypressesSat(pressSetsByGroup, mustDifferGroups=frozenset({group}))
    assert len({colorOf[m] for m in group}) == 3  # all three pairwise distinct
    assert numKeys == 3  # up from the free minimum of 2, since pers_2/nbr_p can no longer share
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_mustDifferGroups_does_not_constrain_markers_outside_the_group():
    """A mustDifferGroups pair only forces THOSE markers apart from EACH OTHER -- it
    says nothing about a marker outside the group, which remains free to share with
    either of them if otherwise safe."""
    pressSetsByGroup = _safe_sharing_press_sets()
    numKeys, colorOf = minKeypressesSat(
        pressSetsByGroup, mustDifferGroups=frozenset({frozenset({"pers_2", "nbr_p"})})
    )
    assert colorOf["pers_2"] != colorOf["nbr_p"]
    assert numKeys == 2  # pers_3 remains free to share with either -- no forced inflation
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSatPreferring_combines_hard_structural_constraints_with_soft_preference():
    """aloneKeys/mustDifferGroups remain HARD even inside the preferring search -- only
    preferSameKey is a tiebreaker."""
    pressSetsByGroup = _safe_sharing_press_sets()
    numKeys, colorOf, satisfied = minKeypressesSatPreferring(
        pressSetsByGroup,
        preferSameKey=frozenset({frozenset({"pers_2", "nbr_p"})}),
        mustDifferGroups=frozenset({frozenset({"pers_2", "nbr_p"})}),
    )
    # the hard mustDifferGroups constraint always wins over the soft preference for the
    # SAME pair -- they can never both be satisfied, so the preference goes unhonored.
    assert colorOf["pers_2"] != colorOf["nbr_p"]
    assert satisfied == 0
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


# ── minKeypressesSatWithPriorities (lexicographic multi-tier soft preferences) ───────

def test_minKeypressesSatWithPriorities_single_tier_matches_minKeypressesSatPreferring():
    pressSetsByGroup = _safe_sharing_press_sets()
    numKeysA, colorOfA, satisfiedA = minKeypressesSatPreferring(
        pressSetsByGroup, preferSameKey=frozenset({frozenset({"pers_2", "nbr_p"})})
    )
    numKeysB, colorOfB, achievedB = minKeypressesSatWithPriorities(
        pressSetsByGroup, [SameKeyPreference(frozenset({frozenset({"pers_2", "nbr_p"})}))]
    )
    assert numKeysB == numKeysA
    assert achievedB == [satisfiedA]
    # key LABELS are arbitrary between independent solves -- only check each result's
    # own internal consistency (pers_2/nbr_p sharing within itself), not cross-solve.
    assert colorOfA["pers_2"] == colorOfA["nbr_p"]
    assert colorOfB["pers_2"] == colorOfB["nbr_p"]


def test_minKeypressesSatWithPriorities_higher_tier_never_sacrificed_for_lower():
    """a can only ever match ONE of b/c's key (b and c are hard-forced apart) -- tier 0
    (prefer a~b) must win over tier 1 (prefer a~c), never partially compromised for it."""
    pressSetsByGroup = {
        "g1": {"w1": [frozenset()], "w2": [frozenset({"a"})]},
        "g2": {"w3": [frozenset()], "w4": [frozenset({"b"})]},
        "g3": {"w5": [frozenset()], "w6": [frozenset({"c"})]},
    }
    mustDifferGroups = frozenset({frozenset({"b", "c"})})
    preferences = [
        SameKeyPreference(frozenset({frozenset({"a", "b"})})),
        SameKeyPreference(frozenset({frozenset({"a", "c"})})),
    ]
    numKeys, colorOf, achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup, preferences, mustDifferGroups=mustDifferGroups
    )
    assert achieved == [1, 0]  # tier 0 fully satisfied; tier 1 necessarily not
    assert colorOf["a"] == colorOf["b"]
    assert colorOf["a"] != colorOf["c"]
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


def test_minKeypressesSatWithPriorities_exclusiveGroupPreference_keeps_outsiders_away():
    """d is completely free to land anywhere at the free-optimal K -- with an
    ExclusiveGroupPreference on {pers_2, nbr_p}, it should be steered away from their
    keypress rather than sharing it (which the solver might otherwise do arbitrarily)."""
    pressSetsByGroup = dict(_safe_sharing_press_sets())
    pressSetsByGroup["free_NOM"] = {"w1": [frozenset()], "w2": [frozenset({"d"})]}
    numKeys, colorOf, achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup,
        [
            SameKeyPreference(frozenset({frozenset({"pers_2", "nbr_p"})})),
            ExclusiveGroupPreference(frozenset({"pers_2", "nbr_p"})),
        ],
    )
    assert achieved[0] == 1  # pers_2/nbr_p still share
    assert achieved[1] == 0  # and nothing else intrudes on their keypress
    assert colorOf["d"] != colorOf["pers_2"]
    assert verifyKeypressAssignment(pressSetsByGroup, colorOf) == []


# ── breakTiesAlphabetically (deterministic canonicalization among remaining ties) ────

def test_breakTiesAlphabetically_picks_alphabetical_order_onto_ascending_keys():
    """Three markers forced pairwise apart, with nothing else distinguishing WHICH gets
    which keypress (fully symmetric otherwise) -- the tie-break should deterministically
    land the alphabetically-earliest marker on keypress 0, the next on 1, and so on."""
    pressSetsByGroup = {
        "g1": {"w1": [frozenset()], "w2": [frozenset({"z"})]},
        "g2": {"w3": [frozenset()], "w4": [frozenset({"y"})]},
        "g3": {"w5": [frozenset()], "w6": [frozenset({"x"})]},
    }
    mustDifferGroups = frozenset({frozenset({"x", "y", "z"})})
    numKeys, colorOf, _achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup, [], mustDifferGroups=mustDifferGroups
    )
    assert numKeys == 3
    assert colorOf == {"x": 0, "y": 1, "z": 2}


def test_breakTiesAlphabetically_is_reproducible_across_repeated_calls():
    pressSetsByGroup = {
        "g1": {"w1": [frozenset()], "w2": [frozenset({"z"})]},
        "g2": {"w3": [frozenset()], "w4": [frozenset({"y"})]},
        "g3": {"w5": [frozenset()], "w6": [frozenset({"x"})]},
    }
    mustDifferGroups = frozenset({frozenset({"x", "y", "z"})})
    results = [
        minKeypressesSatWithPriorities(pressSetsByGroup, [], mustDifferGroups=mustDifferGroups)
        for _ in range(5)
    ]
    assert len({tuple(sorted(colorOf.items())) for _numKeys, colorOf, _achieved in results}) == 1


def test_breakTiesAlphabetically_never_overrides_a_real_preference():
    """The tie-break is strictly lower priority than every real preference tier: 'a'
    prefers to share with 'b' (an explicit SameKeyPreference) even though alphabetical
    order alone would put 'a' before 'b' on separate ascending keys."""
    pressSetsByGroup = {
        "g1": {"w1": [frozenset()], "w2": [frozenset({"a"})]},
        "g2": {"w3": [frozenset()], "w4": [frozenset({"b"})]},
    }
    numKeys, colorOf, achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup, [SameKeyPreference(frozenset({frozenset({"a", "b"})}))]
    )
    assert achieved == [1]
    assert colorOf["a"] == colorOf["b"]


def test_breakTiesAlphabetically_can_be_disabled():
    pressSetsByGroup = {
        "g1": {"w1": [frozenset()], "w2": [frozenset({"z"})]},
        "g2": {"w3": [frozenset()], "w4": [frozenset({"y"})]},
    }
    mustDifferGroups = frozenset({frozenset({"y", "z"})})
    numKeys, colorOf, _achieved = minKeypressesSatWithPriorities(
        pressSetsByGroup, [], mustDifferGroups=mustDifferGroups, breakTiesAlphabetically=False
    )
    assert colorOf["y"] != colorOf["z"]  # still a valid assignment, just not canonicalized
