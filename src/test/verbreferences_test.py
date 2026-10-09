"""Unit tests for util/_verbreferences.py: the unified Wiktionary + GLÀFF reference index."""
from pathlib import Path

import pytest

from util._verbreferences import VerbReferences, isPlausibleIpa, loadVerbReferences

WIKTIONARY = (
    "lemme\tortho\ttags\tipa\n"
    "aimer\taime\tind:pre:1s;ind:pre:3s\tɛm\n"                    # agrees with GLÀFF (identical)
    "aimer\taimes\tind:pre:2s\tɛm\n"                              # equivalent: GLÀFF has e
    "créer\tcréions\tind:imp:1p\tkʁe.ij.jɔ̃\n"                   # equivalent: doubled glide
    "arguer\targuais\tind:imp:1s\taʁ.ɡɥɛ\n"                      # genuine conflict, both plausible
    "vouloir\tvoulons\tind:pre:1p\tvul§ouv9j§\n"                 # genuine conflict, Wiktionary garbled
    "chanter\tchantes\tind:pre:2s\tʃɑ̃t\n"                       # only Wiktionary
)
GLAFF = (
    "aime|Vmip3s-|aimer|ɛm|Em|0\n"
    "aimes|Vmip2s-|aimer|em|em|0\n"
    "créions|Vmii1p-|créer|kʁe.i.jɔ̃|kRei§|0\n"
    "arguais|Vmii1s-|arguer|aʁ.ɡy.ɛ|aRgyE|0\n"
    "voulons|Vmip1p-|vouloir|vu.lɔ̃|vul§|0\n"
    "chanterai|Vmif1s-|chanter|ʃɑ̃.tʁe|S@tRe|0\n"                # a slot Wiktionary lacks
    "beau|Afpms|beau|bo|bo|0\n"                                   # not a verb: ignored
    "mangé|Vmps-sm|manger|mɑ̃.ʒe|m@Ze|0\n"
)


@pytest.fixture
def paths(tmp_path: Path) -> tuple[str, str]:
    wik = tmp_path / "wik.tsv"
    wik.write_text(WIKTIONARY, encoding="utf-8")
    glaff = tmp_path / "glaff.txt"
    glaff.write_text(GLAFF, encoding="utf-8")
    return str(wik), str(glaff)


@pytest.fixture
def refs(paths: tuple[str, str]) -> VerbReferences:
    return loadVerbReferences(*paths)


class TestRefSet:

    def test_identical_is_agreement(self, refs: VerbReferences) -> None:
        ref = refs.get("aimer", "aime", "ind:pre:3s")
        assert ref is not None and not ref.conflict
        assert ref.variants == {"Em"} and ref.bySource == {"wiktionary": {"Em"}, "glaff": {"Em"}}

    def test_mid_vowel_equivalence_is_agreement_and_prefers_the_union(self, refs: VerbReferences) -> None:
        ref = refs.get("aimer", "aimes", "ind:pre:2s")
        assert ref is not None and not ref.conflict and ref.preferred == {"Em", "em"}

    def test_doubled_glide_is_agreement(self, refs: VerbReferences) -> None:
        ref = refs.get("créer", "créions", "ind:imp:1p")
        assert ref is not None and not ref.conflict and ref.variants == {"kReijj§", "kRei"+"j§"}

    def test_genuine_conflict_prefers_wiktionary(self, refs: VerbReferences) -> None:
        ref = refs.get("arguer", "arguais", "ind:imp:1s")
        assert ref is not None and ref.conflict
        assert ref.preferred == {"aRg8E"} and ref.variants == {"aRg8E", "aRgyE"}

    def test_implausible_wiktionary_falls_back_to_glaff(self, refs: VerbReferences) -> None:
        ref = refs.get("vouloir", "voulons", "ind:pre:1p")
        assert ref is not None and ref.conflict and ref.preferred == {"vul§"}

    def test_one_source_only_is_no_conflict(self, refs: VerbReferences) -> None:
        only = refs.get("chanter", "chantes", "ind:pre:2s")
        assert only is not None and not only.conflict and set(only.bySource) == {"wiktionary"}
        glaffOnly = refs.get("chanter", "chanterai", "ind:fut:1s")
        assert glaffOnly is not None and set(glaffOnly.bySource) == {"glaff"} and glaffOnly.preferred == {"S@tRe"}

    def test_unknown_slot_and_non_verb_rows(self, refs: VerbReferences) -> None:
        assert refs.get("aimer", "aimez", "ind:pre:2p") is None
        assert refs.get("beau", "beau", "ind:pre:1s") is None

    def test_participle_tag_is_decoded(self, refs: VerbReferences) -> None:
        ref = refs.get("manger", "mangé", "par:pas:ms")
        assert ref is not None and ref.variants == {"m@Ze"}


class TestRows:

    def test_for_row_unions_over_tags(self, refs: VerbReferences) -> None:
        ref = refs.forRow("aimer", "aime", ["ind:pre:1s", "ind:pre:3s", "sub:pre:1s"])
        assert ref is not None and ref.variants == {"Em"} and not ref.conflict
        assert refs.forRow("aimer", "aimez", ["ind:pre:2p"]) is None

    def test_match_row_is_the_checkers_wiktionary_then_glaff_rule(self, refs: VerbReferences) -> None:
        assert refs.matchRow("chanter", ["ind:pre:2s", "ind:fut:1s"]) == ("wiktionary", {"SAt".replace("A", "@")})
        assert refs.matchRow("chanter", ["ind:fut:1s"]) == ("glaff", {"S@tRe"})
        assert refs.matchRow("chanter", ["ind:fut:2s"]) is None

    def test_iter_conflicts(self, refs: VerbReferences) -> None:
        found = {(lemme, ortho, tag) for lemme, ortho, tag, _ref in refs.iterConflicts()}
        assert found == {("arguer", "arguais", "ind:imp:1s"), ("vouloir", "voulons", "ind:pre:1p")}


class TestPlausibility:

    def test_plausible(self) -> None:
        assert isPlausibleIpa("aʁ.ɡɥɛ", "arguais")
        assert isPlausibleIpa("a.bɛ.s(ə.)ʁa", "abaisserai")

    def test_unbalanced_symbols(self) -> None:
        assert not isPlausibleIpa("a.bɛ.s(ə.ʁa", "abaisserai")
        assert not isPlausibleIpa("a]b", "ab")

    def test_foreign_symbol(self) -> None:
        assert not isPlausibleIpa("défleuʁ", "défleurissais")

    def test_length(self) -> None:
        assert not isPlausibleIpa("vul§ouv9j§", "voulons")
        assert not isPlausibleIpa("a", "abaissaient")


class TestMissingGlaff:

    def test_warns_and_continues_with_wiktionary_only(self, paths: tuple[str, str], tmp_path: Path,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
        refs = loadVerbReferences(paths[0], str(tmp_path / "absent.txt"))
        assert "GLÀFF" in capsys.readouterr().err
        ref = refs.get("arguer", "arguais", "ind:imp:1s")
        assert ref is not None and not ref.conflict and ref.variants == {"aRg8E"}

    def test_required_glaff_raises_naming_the_readme(self, paths: tuple[str, str], tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="README"):
            loadVerbReferences(paths[0], str(tmp_path / "absent.txt"), requireGlaff=True)

    def test_empty_path_means_no_glaff_and_no_warning(self, paths: tuple[str, str], capsys: pytest.CaptureFixture[str]) -> None:
        loadVerbReferences(paths[0], "")
        assert capsys.readouterr().err == ""


def testForOrthoAnyTagAndInfinitive() -> None:
    from util._verbreferences import _Source, decodeGrace
    wiktionary, glaff = _Source(), _Source()
    wiktionary.add("crier", "criions", "ind:imp:1p", "kʁi.jjɔ̃")
    glaff.add("crier", "criions", "sub:pre:1p", "kʁi.jɔ̃")
    refs = VerbReferences(wiktionary, glaff)
    assert refs.tagsOf("crier", "criions") == ["ind:imp:1p", "sub:pre:1p"]
    union = refs.forOrtho("crier", "criions")
    assert union is not None and set(union.bySource) == {"wiktionary", "glaff"}
    assert refs.forRow("crier", "criions", ["sub:pre:2p"]) is None
    assert refs.forOrtho("crier", "inconnu") is None
    assert decodeGrace("Vmn----") == "inf"
