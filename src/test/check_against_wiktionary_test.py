"""Unit tests for util/_pronunciation.py (IPA conversion and tolerant comparison) and util/check_against_wiktionary.py."""
from util._pronunciation import compare, equivalenceKey, ipaToLexicon
from util._verbreferences import decodeGrace
from util.check_against_wiktionary import checkRow, rowTags, tagFamily


class TestIpaToLexicon:

    def test_basic_symbols_and_nasals(self):
        assert ipaToLexicon("kʁe.ʁjɔ̃") == {"kReRj§"}
        assert ipaToLexicon("ɑ̃.ni.vʁat") == {"@nivRat"}
        assert ipaToLexicon("lɛ̃.ʒɛ") == {"l5ZE"}
        assert ipaToLexicon("œ̃.ø.œ.ɥi.ɲ") == {"1" + "2" + "9" + "8" + "i" + "N"}

    def test_optional_parts_give_both_variants(self):
        assert ipaToLexicon("a.bɛ.s(ə.)ʁa") == {"abEsRa", "abEs°Ra"}

    def test_optional_h_is_dropped_and_semicolon_variants_are_all_kept(self):
        assert ipaToLexicon("a.(h)a.nʁ") == {"aanR"}
        assert ipaToLexicon("a.ba.zuʁ;a.ba.suʁ") == {"abazuR", "abasuR"}

    def test_script_g_and_turned_e_and_stress_marks(self):
        assert ipaToLexicon("ɡə.ʁ") == {"g°R"}
        assert ipaToLexicon("ˈpǝ") == {"p°"}


class TestCompare:

    def test_exact(self):
        assert compare("kReRj§", {"kReRj§"}) == ("exact", "")

    def test_doubled_glide_is_an_equivalence(self):
        assert compare("kRij§", ipaToLexicon("kʁij.jɔ̃")) == ("equivalent", "glide")

    def test_mid_vowel_direction_is_named(self):
        assert compare("delej", ipaToLexicon("de.lɛj")) == ("equivalent", "mid vowel (ours e, ref E)")
        assert compare("klOn", ipaToLexicon("klon")) == ("equivalent", "mid vowel (ours O, ref o)")

    def test_a_schwa_against_a_full_vowel_is_a_real_difference(self):
        status, detail = compare("pOm°l°R§", ipaToLexicon("pɔ.mɛ.l(ə.)ʁɔ̃"))
        assert status == "differs" and "°" in detail

    def test_schwa_only(self):
        assert compare("R°lE", {"RlE"}) == ("equivalent", "schwa")

    def test_equivalence_key_merges_everything_tolerated(self):
        assert equivalenceKey("pOm°ljj§") == equivalenceKey("pomlj§")


class TestGraceAndRows:

    def test_decode_grace_verb_tags(self):
        assert decodeGrace("Vmip3s-") == "ind:pre:3s"
        assert decodeGrace("Vmcp1p-") == "cnd:pre:1p"
        assert decodeGrace("Vmis2p-") == "ind:pas:2p"
        assert decodeGrace("Vmmp2s-") == "imp:pre:2s"
        assert decodeGrace("Vmsp3p-") == "sub:pre:3p"
        assert decodeGrace("Vmps-pf") == "par:pas:fp"
        assert decodeGrace("Vmpp---") == "par:pre" and decodeGrace("Ncms") is None

    def test_row_tags(self):
        assert rowTags("ind:pre:1s;ind:pre:3s;", "", "") == ["ind:pre:1s", "ind:pre:3s"]
        assert rowTags("par:pas;", "f", "p") == ["par:pas:fp"]
        assert rowTags("inf;", "", "") == []

    def test_tag_family(self):
        assert tagFamily("cnd:pre:1p;") == "cnd:pre" and tagFamily("par:pas;") == "par:pas"

    def test_wiktionary_wins_and_glaff_is_the_fallback(self):
        wik = {("créer", "cnd:pre:1p"): {"kReRj§"}}
        glaff = {("créer", "cnd:pre:1p"): {"WRONG"}, ("créer", "ind:pas:2s"): {"kRea"}}
        first = checkRow("créerions", "créer", "cnd:pre:1p;", "", "", "kReRj§", wik, glaff)
        assert (first.source, first.status) == ("wiktionary", "exact")
        second = checkRow("créas", "créer", "ind:pas:2s;", "", "", "kRea", wik, glaff)
        assert (second.source, second.status) == ("glaff", "exact")
        third = checkRow("créât", "créer", "sub:imp:3s;", "", "", "kRea", wik, glaff)
        assert third.status == "no reference"

    def test_a_row_matches_if_any_of_its_tags_does(self):
        wik = {("aimer", "ind:pre:1s"): {"Em"}, ("aimer", "sub:pre:1s"): {"Em"}}
        assert checkRow("aime", "aimer", "ind:pre:1s;sub:pre:1s;", "", "", "Em", wik, {}).status == "exact"
