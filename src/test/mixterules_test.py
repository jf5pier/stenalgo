from typing import Any

import pytest

from src.diffsignature import graphemesOf, unitTriples
from src.lexicondecisions import ACCEPT, Decision, Decisions
from src.mixterules import (GLIDE_RULE_ID, GLIDE_RULE_SIGNATURE, MIXTE_RULES, STRAY_GLIDE_RULE_ID, activeRules,
                            dropStrayGlide, splitGlides)
from src.orthounits import spellingOf, stripMarks
from util.check_lexicon_features import check_units


def _row(ortho: str, phon: str, syll: str, letters: str, cgram: str = "VER", infover: str = "ind:imp:1p;") -> dict[str, Any]:
    return {"ortho": ortho, "phon": phon, "lemme": "x", "cgram": cgram, "infover": infover, "syll_cv": syll,
            "orthosyll_cv": letters}


# (ortho, phon, syll, letters) -> (phon, syll, letters), from LexiqueMixte.tsv before and after the rule
CASES = [
    # A: letters i + i, the glide opens the next syllable, phon unchanged
    (("appréciions", "apResij§", "a|p_R_e|s_ij_#|§", "a|pp_r_é|c_i_i|ons"),
     ("apResij§", "a|p_R_e|s_i|j_§", "a|pp_r_é|c_i|i_ons")),
    # B: y + i, the doubled glide
    (("ennuyions", "@n8ij§", "@|n_8_ij_#|§", "en|n_u_y_i|ons"),
     ("@n8ijj§", "@|n_8_ij|j_§", "en|n_u_y|i_ons")),
    (("appuyiez", "ap8ije", "a|p_8_ij_#|e", "a|pp_u_y_i|ez"),
     ("ap8ijje", "a|p_8_ij|j_e", "a|pp_u_y|i_ez")),
    # C: ill + i, y + i after a glide unit
    (("aillions", "aj§", "a|j_#_§", "a|ill_i_ons"), ("ajj§", "a_j|j_§", "a_ill|i_ons")),
    (("asseyiez", "asEje", "a|s_E|j_#_e", "a|ss_e|y_i_ez"), ("asEjje", "a|s_E_j|j_e", "a|ss_e_y|i_ez")),
    (("croyiez", "kRwaje", "k_R_wa|j_#_e", "c_r_o|y_i_ez"), ("kRwajje", "k_R_wa_j|j_e", "c_r_o_y|i_ez")),
    # F: lli, one j and the fused jj
    (("appareillions", "apaREj§", "a|p_a|R_E|j_§", "a|pp_a|r_ei|lli_ons"),
     ("apaREjj§", "a|p_a|R_E_j|j_§", "a|pp_a|r_ei_lli|=_ons")),
    (("surveillions", "syRvEjj§", "s_y_R|v_E_jj|§", "s_u_r|v_ei_lli|ons"),
     ("syRvEjj§", "s_y_R|v_E_j|j_§", "s_u_r|v_ei_lli|=_ons")),
    # E: one letter carrying a vowel and a glide
    (("cria", "kRija", "k_R_ij|a", "c_r_i|a"), ("kRija", "k_R_i|j_a", "c_r_i|=_a")),
    (("accablions", "akablij§", "a|k_a|b_l_ij|§", "a|cc_a|b_l_i|ons"), ("akablij§", "a|k_a|b_l_i|j_§", "a|cc_a|b_l_i|=_ons")),
    (("devrions", "d°vRij§", "d_°|v_R_ij|§", "d_e|v_r_i|ons"), ("d°vRij§", "d_°|v_R_i|j_§", "d_e|v_r_i|=_ons")),
    (("appuyais", "ap8ijE", "a|p_8_ij|E", "a|pp_u_y|ais"), ("ap8ijE", "a|p_8_i|j_E", "a|pp_u_y|=_ais")),
]


@pytest.mark.parametrize("before,after", CASES)
def testGlideCases(before: tuple[str, str, str, str], after: tuple[str, str, str]) -> None:
    new = splitGlides(_row(*before))
    assert (new["phon"], new["syll_cv"], new["orthosyll_cv"]) == after
    assert check_units(new["syll_cv"], new["orthosyll_cv"])
    assert spellingOf(new["orthosyll_cv"]) == before[0]
    assert splitGlides(new) == new      # idempotent


def testInputRowUntouched() -> None:
    row = _row("cria", "kRija", "k_R_ij|a", "c_r_i|a")
    splitGlides(row)
    assert row["syll_cv"] == "k_R_ij|a"


def testOnlyAlignedVerbs() -> None:
    nonVerb = _row("cria", "kRija", "k_R_ij|a", "c_r_i|a", cgram="NOM")
    assert splitGlides(nonVerb) == nonVerb
    misaligned = _row("assyiez", "asEje", "a|s_E|j_#_e", "a|ss_y_i_ez")
    assert splitGlides(misaligned) == misaligned
    breaksDiffer = _row("cria", "kRija", "k_R_ij|a", "c_r|i_a")
    assert splitGlides(breaksDiffer) == breaksDiffer


def testRowsWithoutAGlideAreUntouched() -> None:
    for before in [("marchions", "maRSj§", "m_a_R|S_j_§", "m_a_r|ch_i_ons"),
                   ("fuyions", "f8ijj§", "f_8_ij|j_§", "f_u_y|i_ons"),
                   ("brillons", "bRij§", "b_R_i|j_§", "b_r_i|ll_ons")]:
        row = _row(*before)
        assert splitGlides(row) == row


def testRegistrationAndDecision() -> None:
    assert MIXTE_RULES[GLIDE_RULE_ID] is splitGlides
    accepted = Decisions([Decision(GLIDE_RULE_ID, "mixte_rule", "-", GLIDE_RULE_SIGNATURE, ACCEPT)])
    assert [groupId for groupId, _ in activeRules(accepted)] == [GLIDE_RULE_ID]
    assert activeRules(Decisions()) == []


def testRepeatUnitInReaders() -> None:
    assert graphemesOf("c_r_i|=_a") == ["c", "r", "i", "i", "a"]
    assert unitTriples("kRija", "k_R_i|j_a", "c_r_i|=_a") == [
        ("c", "initial", "k"), ("r", "medial", "R"), ("i", "medial", "i"), ("i", "medial", "j"), ("a", "final", "a")]
    assert spellingOf("c_r_i|=_a") == "cria"
    assert stripMarks("i=") == "i"


def testCheckUnitsRepeatPlacement() -> None:
    assert check_units("k_R_i|j_a", "c_r_i|=_a")
    assert not check_units("k_R_i|j_a", "=_r_i|c_a")                # a repeat cannot start the word
    assert not check_units("k_R_i|=_a", "c_r_i|=_a")                # nor sit on the sound side
    assert not check_units("k_R_i|#_a", "c_r_i|=_a")                # nor repeat a silent unit
    assert not check_units("k_R_i|j_a", "c_r_i|=_=_a")              # nor follow another repeat


STRAY = [
    (("dévierait", "devijRE", "d_e|v_ij_#|R_E", "d_é|v_i_e|r_ait"), ("deviRE", "d_e|v_i_#|R_E")),
    (("sciera", "sijRa", "s_ij_#|R_a", "sc_i_e|r_a"), ("siRa", "s_i_#|R_a")),
    (("mésallies", "mezalij", "m_e|z_a|l_ij_#", "m_é|s_a|ll_i_es"), ("mezali", "m_e|z_a|l_i_#")),
]


@pytest.mark.parametrize("before,after", STRAY)
def testStrayGlide(before: tuple[str, str, str, str], after: tuple[str, str]) -> None:
    new = dropStrayGlide(_row(*before, infover="ind:fut:3s;"))
    assert (new["phon"], new["syll_cv"]) == after and new["orthosyll_cv"] == before[3]
    assert check_units(new["syll_cv"], new["orthosyll_cv"])
    assert dropStrayGlide(new) == new


def testStrayGlideLeavesOtherShapes() -> None:
    for before in [("cria", "kRija", "k_R_ij|a", "c_r_i|a"),                    # a vowel follows: a real glide
                   ("criions", "kRij§", "k_R_ij_#|§", "c_r_i_i|ons")]:           # the silent unit is the ending's i
        row = _row(*before)
        assert dropStrayGlide(row) == row
    nonVerb = _row("sciera", "sijRa", "s_ij_#|R_a", "sc_i_e|r_a", cgram="NOM")
    assert dropStrayGlide(nonVerb) == nonVerb
    assert MIXTE_RULES[STRAY_GLIDE_RULE_ID] is dropStrayGlide
