"""Rule `glide-future-stem` (src/verbparadigm.py hasGlideFutureStem, vocalizeGlideBeforeFutureR; src/synthrules.py)."""
import pytest

from src.synthrules import SYNTH_RULES, isRuleActive
from src.verbparadigm import hasGlideFutureStem, vocalizeGlideBeforeFutureR


@pytest.mark.parametrize("lemme,code,expected", [
    ("affilier", "ind:fut", True), ("accentuer", "cnd:pre", True), ("allouer", "ind:fut", True),
    ("affilier", "ind:pre", False), ("distinguer", "ind:fut", False), ("attaquer", "cnd:pre", False),
    ("aimer", "ind:fut", False), ("bayer", "ind:fut", False), ("recroqueviller", "ind:fut", False),
])
def test_gate(lemme: str, code: str, expected: bool) -> None:
    assert hasGlideFutureStem(lemme, code) is expected


@pytest.mark.parametrize("raw,fixed", [
    # glide after a consonant: -ier, -uer, -ouer
    (("afilj°Ra", "a|f_i|l_j_°|R_a", "a|ff_i|l_i_e|r_a"), ("afiliRa", "a|f_i|l_i_#|R_a", "a|ff_i|l_i_e|r_a")),
    (("aks@t8°RE", "a_k|s_@|t_8_°|R_E", "a_c|c_en|t_u_e|r_ais"), ("aks@tyRE", "a_k|s_@|t_y_#|R_E", "a_c|c_en|t_u_e|r_ais")),
    (("alw°Rj§", "a|l_w_°|R_j_§", "a|ll_ou_e|r_i_ons"), ("aluRj§", "a|l_u_#|R_j_§", "a|ll_ou_e|r_i_ons")),
    # cluster + i + j: the glide and its repeat unit go
    (("ublij°Ra", "u|b_l_i|j_°|R_a", "ou|b_l_i|=_e|r_a"), ("ubliRa", "u|b_l_i_#|R_a", "ou|b_l_i_e|r_a")),
])
def test_vocalizes(raw: tuple[str, str, str], fixed: tuple[str, str, str]) -> None:
    assert vocalizeGlideBeforeFutureR(*raw) == fixed


@pytest.mark.parametrize("raw", [
    ("bRasEj°RE", "b_R_a|s_E_j_°|R_E", "b_r_a|ss_é_i_e|r_ais"),   # -éier: the glide follows a vowel
    ("alwe", "a|l_w_e", "a|ll_ou_er"),                           # no future ending
])
def test_leaves_alone(raw: tuple[str, str, str]) -> None:
    assert vocalizeGlideBeforeFutureR(*raw) == raw


def test_rule_registered_and_off_by_default() -> None:
    assert "glide-future-stem" in SYNTH_RULES
    assert isRuleActive("glide-future-stem", None, {}) == (False, "")
    assert isRuleActive("glide-future-stem", None, {"glide-future-stem": ""}) == (True, "")
