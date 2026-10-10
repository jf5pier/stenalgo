#!/usr/bin/python
# coding: utf-8
"""Tests for repairSpliceUnits / isWellFormedSplice in src/verbparadigm.py."""

from src.verbparadigm import isWellFormedSplice, reinsertLostNasalUnit, repairSpliceUnits, rewriteSplicePhon


def testRepairFusedUnit():
    assert repairSpliceUnits("k_l_u#|R_j_§") == "k_l_u_#|R_j_§"


def testRepairLeadingEmptyUnit():
    assert repairSpliceUnits("_a|l_e") == "#_a|l_e"


def testWellFormedRowUnchanged():
    assert repairSpliceUnits("k_l_u_#") == "k_l_u_#"
    assert isWellFormedSplice("klu", "k_l_u_#")


def testGuardRejectsLostPhoneme():
    assert not isWellFormedSplice("kluj§", "k_l_u#|R_j_§")
    assert isWellFormedSplice("kluRj§", repairSpliceUnits("k_l_u#|R_j_§"))


def testGuardRejectsEmptyUnit():
    assert not isWellFormedSplice("ale", "_a|l_e_#")
    assert isWellFormedSplice("ale", repairSpliceUnits("_a|l_e_#"))


def testRewritePhonInsertsLostR():
    assert rewriteSplicePhon("kluj§", "k_l_u_#|R_j_§") == "kluRj§"
    assert rewriteSplicePhon("tRuje", "t_R_u_#|R_j_e") == "tRuRje"


def testRewritePhonRefusesVowelGlideUnit():
    assert rewriteSplicePhon("ublijje", "u|b_l_ij_#|R_j_e") is None


def testRewritePhonRefusesDeletionOrSubstitution():
    assert rewriteSplicePhon("@nivR", "@|i_v_R_#") is None
    assert rewriteSplicePhon("kluRj§", "k_l_u_#|R_j_e") is None


def testReinsertLostNasalUnit():
    assert reinsertLostNasalUnit("@nivR", "@|i_v_R_#", "en|i_v_r_e") == ("@|n_i_v_R_#", "e|n_i_v_r_e")
    assert reinsertLostNasalUnit(
        "@nORg9ji", "@|O_R|g_9|j_i_#", "en|o_r|gu_e|ill_i_s"
    ) == ("@|n_O_R|g_9|j_i_#", "e|n_o_r|gu_e|ill_i_s")


def testReinsertLostNasalUnitRefusesOtherLosses():
    assert reinsertLostNasalUnit("5tERvjuve", "5|t_E_R|v_j_u_#_#", "in|t_e_r|v_i_ew_é_e") is None
    assert reinsertLostNasalUnit("@nivR", "@|n_i_v_R_#", "e|n_i_v_r_e") is None


class TestHiatusBoundary:
    """A hiatus -ir verb (trahir /t_R_a_#|i_R/) differs from the -ir suffix `_i_R` only by the syllable boundary: it is
    no outlier, and its splices keep its own boundary."""

    def test_ending_takes_the_infinitives_boundary(self) -> None:
        from src.verbparadigm import _endingWithOwnBoundary
        assert _endingWithOwnBoundary("_i|R_a", "t_R_a_#|i_R", 7, "_i_R") == "|i|R_a"

    def test_ending_unchanged_when_the_infinitive_agrees(self) -> None:
        from src.verbparadigm import _endingWithOwnBoundary
        assert _endingWithOwnBoundary("_i|R_a", "f_i_n_i_R", 5, "_i_R") == "_i|R_a"

    def test_ending_unchanged_when_it_starts_differently_from_the_suffix(self) -> None:
        from src.verbparadigm import _endingWithOwnBoundary
        assert _endingWithOwnBoundary("_a", "t_a|b_u|e", 7, "|e") == "_a"
