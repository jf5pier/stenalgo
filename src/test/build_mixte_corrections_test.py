import pytest
from typing import Any

from src.lexicondecisions import ACCEPT, PENDING, Decision, Decisions, groupIdFor
from src.mixtecorrections import Correction
from util.build_mixte_corrections import buildCorrections, correctedBreakdown


def test_substitution_inside_unit() -> None:
    # osija / osila: the j of the `ll` unit becomes l
    assert correctedBreakdown("osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a") == ("osila", "o|s_i|l_a", "o|sc_i|ll_a")


def test_insertion_fills_silent_unit() -> None:
    # criions kRij§ -> kRijj§: the 4th unit is `#`
    assert correctedBreakdown("kRij§", "kRijj§", "k_R_ij_#|§", "c_r_i_i|ons") == ("kRijj§", "k_R_ij_j|§", "c_r_i_i|ons")


def test_insertion_extends_unit() -> None:
    # no silent unit after `i`: the unit grows
    assert correctedBreakdown("kRi§", "kRij§", "k_R_i|§", "c_r_i|ons") == ("kRij§", "k_R_ij|§", "c_r_i|ons")


def test_deletion_partial_and_whole_unit() -> None:
    assert correctedBreakdown("kRij§", "kRi§", "k_R_ij|§", "c_r_ii|ons")[:2] == ("kRi§", "k_R_i|§")
    assert correctedBreakdown("kRij§", "kR§", "k_R_i_j|§", "c_r_i_i|ons")[:2] == ("kR§", "k_R_#_#|§")


def test_convention_edit_is_kept() -> None:
    # ours `o` vs ref `O` is a convention: only the real edit (j -> l) is applied
    phon, syll, _ = correctedBreakdown("kolija", "kOlila", "k_o|l_i|j_a", "c_o|l_i|ll_a")
    assert (phon, syll) == ("kolila", "k_o|l_i|l_a")


def test_no_real_edit_is_an_error() -> None:
    with pytest.raises(ValueError):
        correctedBreakdown("kolo", "kOlo", "k_o|l_o", "c_o|l_o")


def test_misaligned_breakdown_is_an_error() -> None:
    with pytest.raises(ValueError):
        correctedBreakdown("osija", "osila", "o|s_i|j_a_a", "o|sc_i|ll_a")


def _member(ortho: str, ours: str, ref: str, syll: str, orthosyll: str, key: str | None = None) -> dict[str, Any]:
    return {"ortho": ortho, "ours": ours, "ref": ref, "refSource": "glaff", "syllCV": syll, "orthosyllCV": orthosyll,
            "rowKey": key or f"{ortho} {ortho}er ind:pre:1s;"}


def _decision(kind: str = "mixte_rule", verdict: str = ACCEPT, param: str = "", sig: str = "x") -> Decision:
    return Decision(groupIdFor(kind, "L1", sig), kind, "L1", sig, verdict, param)


def test_build_param_overrides_reference() -> None:
    d = _decision(param="osila")
    sidecar = {d.groupId: {"members": [_member("osija", "osija", "osiLa", "o|s_i|j_a", "o|sc_i|ll_a")]}}
    corrections, failures = buildCorrections(Decisions([d]), sidecar)
    assert not failures
    assert corrections == [Correction("osija", "osijaer", "VER", "ind:pre:1s;", "", "", "osila", "o|s_i|l_a", "o|sc_i|ll_a", d.groupId)]


def test_build_validation_failure_stays_out_of_the_file() -> None:
    d = _decision()
    good = _member("osija", "osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a")
    bad = _member("xyz", "osija", "osila", "o|s_i|j_a_a", "o|sc_i|ll_a")
    nokey = {**_member("abc", "osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a"), "rowKey": ""}
    corrections, failures = buildCorrections(Decisions([d]), {d.groupId: {"members": [good, bad, nokey]}})
    assert [c.ortho for c in corrections] == ["osija"]
    assert sorted(f.ortho for f in failures) == ["abc", "xyz"]


def test_build_only_accepted_mixte_kinds() -> None:
    pend = _decision(verdict=PENDING, sig="a")
    synth = _decision(kind="synth_rule", sig="b")
    typo = _decision(kind="mixte_typo", sig="c")
    m = _member("osija", "osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a")
    sidecar = {d.groupId: {"members": [m]} for d in (pend, synth, typo)}
    corrections, failures = buildCorrections(Decisions([pend, synth, typo]), sidecar)
    assert [c.groupId for c in corrections] == [typo.groupId] and not failures


def test_build_accepted_group_without_members_fails() -> None:
    d = _decision()
    assert buildCorrections(Decisions([d]), {})[1]


def test_build_is_deterministic_and_sorted() -> None:
    d1, d2 = _decision(sig="a"), _decision(sig="b")
    ma = _member("osija", "osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a")
    mb = _member("asija", "asija", "asila", "a|s_i|j_a", "a|sc_i|ll_a")
    first = buildCorrections(Decisions([d1, d2]), {d1.groupId: {"members": [ma]}, d2.groupId: {"members": [mb]}})
    second = buildCorrections(Decisions([d2, d1]), {d2.groupId: {"members": [mb]}, d1.groupId: {"members": [ma]}})
    assert first == second
    assert [c.ortho for c in first[0]] == ["asija", "osija"]
