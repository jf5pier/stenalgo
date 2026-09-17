#!/usr/bin/python
# coding: utf-8
"""Tests for src/ambiguitychecker.py — Phase 0 ambiguity checker."""

from unittest.mock import MagicMock

from src.word import Word, GramCat
from src.ambiguitychecker import (
    StrokeClusterReport,
    TokenAnchorFeasibility,
    classifyStrokeCluster,
    detectCrossCategoryClash,
    computeClusterSizeDistribution,
    computeOverflowFrequencyMass,
    buildTokenToWords,
    findTokenAnchors,
    checkComposedChords,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_word(**overrides) -> Word:
    defaults = dict(
        ortho="chat", phonology="Sa", lemme="chat",
        gramCat=GramCat.NOM, orthoGramCat=[GramCat.NOM],
        gender="m", number="s", infoVerb=None,
        rawSyllCV="S_a", rawOrthosyllCV="ch_a_t",
        frequencyBook=1.0, frequencyFilm=2.0,
    )
    defaults.update(overrides)
    return Word(**defaults)


def _mock_keyboard_for_anchors(codaMap: dict[str, tuple[int, ...]]) -> MagicMock:
    """Mock keyboard: only phonemes present in codaMap resolve to a coda stroke."""
    kb = MagicMock()
    kb.getStrokesOfPhoneme.side_effect = (
        lambda phoneme, part: [codaMap[phoneme]] if phoneme in codaMap else []
    )
    return kb


# ---------------------------------------------------------------------------
# classifyStrokeCluster
# ---------------------------------------------------------------------------

class TestClassifyStrokeCluster:

    def test_single_word_unambiguous(self):
        w = _make_word()
        report = classifyStrokeCluster((( 1,),), [w])
        assert not report.sameLemmaAmbiguous
        assert not report.lemmaHomophoneAmbiguous
        assert report.lemmaHomophoneLemmaCount == 1

    def test_same_lemma_only(self):
        """dors/dort: one lemme, two inflected homophones."""
        w1 = _make_word(ortho="dors", lemme="dormir", gramCat=GramCat.VER)
        w2 = _make_word(ortho="dort", lemme="dormir", gramCat=GramCat.VER)
        report = classifyStrokeCluster(((1,),), [w1, w2])
        assert report.sameLemmaAmbiguous
        assert not report.lemmaHomophoneAmbiguous
        assert report.lemmaHomophoneLemmaCount == 1

    def test_lemma_homophone_only(self):
        """verre/vert: two distinct lemmas, each with a single homophone form."""
        w1 = _make_word(ortho="verre", lemme="verre", gramCat=GramCat.NOM)
        w2 = _make_word(ortho="vert", lemme="vert", gramCat=GramCat.ADJ)
        report = classifyStrokeCluster(((1,),), [w1, w2])
        assert not report.sameLemmaAmbiguous
        assert report.lemmaHomophoneAmbiguous
        assert report.lemmaHomophoneLemmaCount == 2

    def test_same_bare_lemma_different_gramcat_not_lemma_homophone(self):
        """être_VER vs être_AUX ('est' as copula vs auxiliary): same bare lemma, different
        gramCat -- not a distinct-lemma clash for the */# track, even though lemmeGramCat
        differs."""
        ver = _make_word(ortho="est", lemme="être", gramCat=GramCat.VER)
        aux = _make_word(ortho="est", lemme="être", gramCat=GramCat.AUX)
        report = classifyStrokeCluster((( 1,),), [ver, aux])
        assert not report.lemmaHomophoneAmbiguous
        assert report.lemmaHomophoneLemmaCount == 1
        assert len(report.lemmeGramCatGroups) == 2  # sameLemmaAmbiguous track still sees both

    def test_both_ambiguities_at_once(self):
        """Not mutually exclusive: one lemma with 2 inflected forms, plus another lemma."""
        w1 = _make_word(ortho="dors", lemme="dormir", gramCat=GramCat.VER)
        w2 = _make_word(ortho="dort", lemme="dormir", gramCat=GramCat.VER)
        w3 = _make_word(ortho="dore", lemme="dorer", gramCat=GramCat.VER)
        report = classifyStrokeCluster(((1,),), [w1, w2, w3])
        assert report.sameLemmaAmbiguous
        assert report.lemmaHomophoneAmbiguous
        assert report.lemmaHomophoneLemmaCount == 2


# ---------------------------------------------------------------------------
# detectCrossCategoryClash
# ---------------------------------------------------------------------------

class TestDetectCrossCategoryClash:

    def test_aller_nom_ver_clash_is_flagged(self):
        """Regression test: 'aller' (NOM, 'un aller simple') vs 'va' (VER) -- two singleton
        lemmeGramCat groups sharing a bare lemme, differing in ortho, currently invisible to
        the existing len(lemmeWords) > 1 trigger."""
        nom = _make_word(ortho="aller", lemme="aller", gramCat=GramCat.NOM)
        ver = _make_word(ortho="va", lemme="aller", gramCat=GramCat.VER)
        clashes = detectCrossCategoryClash([nom, ver])
        assert clashes == ["aller"]

    def test_identical_ortho_not_flagged(self):
        """Same spelling across gramCat readings isn't a spelling-distinguishability problem."""
        a = _make_word(ortho="x", lemme="x", gramCat=GramCat.NOM)
        b = _make_word(ortho="x", lemme="x", gramCat=GramCat.VER)
        assert detectCrossCategoryClash([a, b]) == []

    def test_already_caught_sublemme_group_not_flagged(self):
        """If one gramCat reading already has len > 1 (already caught by the existing
        same-lemma trigger), detectCrossCategoryClash should not also flag it."""
        ver1 = _make_word(ortho="cours", lemme="courir", gramCat=GramCat.VER)
        ver2 = _make_word(ortho="court", lemme="courir", gramCat=GramCat.VER)
        nom = _make_word(ortho="course", lemme="courir", gramCat=GramCat.NOM)
        assert detectCrossCategoryClash([ver1, ver2, nom]) == []

    def test_single_lemme_gramcat_group_not_flagged(self):
        assert detectCrossCategoryClash([_make_word()]) == []


# ---------------------------------------------------------------------------
# computeClusterSizeDistribution / computeOverflowFrequencyMass
# ---------------------------------------------------------------------------

def _report(lemmaHomophoneLemmaCount: int, totalFrequency: float, sameLemmaGroups: dict | None = None) -> StrokeClusterReport:
    return StrokeClusterReport(
        strokes=((1,),), words=[], lemmeGramCatGroups=sameLemmaGroups or {}, lemmaGroups={},
        sameLemmaAmbiguous=bool(sameLemmaGroups and any(len(w) > 1 for w in sameLemmaGroups.values())),
        lemmaHomophoneAmbiguous=lemmaHomophoneLemmaCount > 1,
        lemmaHomophoneLemmaCount=lemmaHomophoneLemmaCount,
        crossCategoryClash=False, crossCategoryClashLemmas=[], totalFrequency=totalFrequency,
    )


class TestComputeOverflowFrequencyMass:

    def test_threshold_split(self):
        reports = {
            ((1,),): _report(3, 10.0),
            ((2,),): _report(4, 20.0),
            ((3,),): _report(5, 30.0),
            ((4,),): _report(6, 40.0),
        }
        overflowMass, totalMass, overflowKeys = computeOverflowFrequencyMass(reports, threshold=5)
        assert overflowMass == 70.0
        assert totalMass == 100.0
        assert set(overflowKeys) == {((3,),), ((4,),)}

    def test_no_overflow(self):
        reports = {((1,),): _report(2, 10.0), ((2,),): _report(3, 5.0)}
        overflowMass, totalMass, overflowKeys = computeOverflowFrequencyMass(reports, threshold=5)
        assert overflowMass == 0.0
        assert totalMass == 15.0
        assert overflowKeys == []


class TestComputeClusterSizeDistribution:

    def test_histograms(self):
        w1, w2 = _make_word(ortho="a"), _make_word(ortho="b")
        reports = {
            ((1,),): _report(1, 10.0, sameLemmaGroups={"lemme_NOM": [w1, w2]}),
            ((2,),): _report(3, 20.0),
        }
        dist = computeClusterSizeDistribution(reports)
        assert dist.sameLemmaGroupSizeCounts == {2: 1}
        assert dist.sameLemmaGroupSizeFrequency[2] == w1.frequency + w2.frequency
        assert dist.lemmaHomophoneCountCounts == {3: 1}
        assert dist.lemmaHomophoneCountFrequency == {3: 20.0}


# ---------------------------------------------------------------------------
# buildTokenToWords
# ---------------------------------------------------------------------------

class TestBuildTokenToWords:

    def test_nofeature_and_singleton_filtered(self):
        w = _make_word()
        augmentedTheory = {
            ("nofeature",): [(w,)],
            ("s",): [(w,)],  # len < 2, no canonical/non-canonical split
        }
        assert buildTokenToWords(augmentedTheory) == {}

    def test_canonical_excluded_noncanonical_tokenized(self):
        """pers_3 (priority 70) beats pers_1 (priority 55): pers_3 is canonical (no anchor
        needed), pers_1 is the one that needs a token anchor."""
        w3 = _make_word(ortho="w3")
        w1 = _make_word(ortho="w1")
        augmentedTheory = {("pers_3", "pers_1"): [(w3, w1)]}
        tokenToWords = buildTokenToWords(augmentedTheory)
        assert set(tokenToWords.keys()) == {"pers", "1"}
        assert tokenToWords["pers"] == [(w1, "pers_1")]
        assert tokenToWords["1"] == [(w1, "pers_1")]


# ---------------------------------------------------------------------------
# findTokenAnchors
# ---------------------------------------------------------------------------

class TestFindTokenAnchors:

    def test_clean_single_key_anchor(self):
        w = _make_word()
        theory = {((1,),): [w]}
        tokenToWords = {"tokA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_anchors({"t": (2,)})
        result = findTokenAnchors(tokenToWords, theory, kb)
        assert result["tokA"].feasibleSingleKeyPhonemes == ["t"]
        assert not result["tokA"].infeasible

    def test_escalates_to_combo_when_singles_collide(self):
        w = _make_word()
        theory = {
            ((1,),): [w],
            ((1, 2),): [_make_word(ortho="other1")],
            ((1, 3),): [_make_word(ortho="other2")],
        }
        tokenToWords = {"tokA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_anchors({"t": (2,), "s": (3,)})
        result = findTokenAnchors(tokenToWords, theory, kb)
        assert result["tokA"].feasibleSingleKeyPhonemes == []
        assert ("t", "s") in result["tokA"].feasibleComboPhonemes
        assert not result["tokA"].infeasible

    def test_infeasible_even_with_combo(self):
        w = _make_word()
        theory = {((1,),): [w], ((1, 2),): [_make_word(ortho="other1")]}
        tokenToWords = {"tokA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_anchors({"t": (2,)})
        result = findTokenAnchors(tokenToWords, theory, kb)
        assert result["tokA"].infeasible


# ---------------------------------------------------------------------------
# checkComposedChords
# ---------------------------------------------------------------------------

class TestCheckComposedChords:

    def test_composed_chord_feasible(self):
        w = _make_word()
        theory = {((1,),): [w]}
        tokenToWords = {
            "pers": [(w, "pers_3")],
            "3": [(w, "pers_3")],
        }
        tokenAnchors = {
            "pers": TokenAnchorFeasibility(token="pers", feasibleSingleKeyPhonemes=["t"]),
            "3": TokenAnchorFeasibility(token="3", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_anchors({"t": (2,), "s": (3,)})
        report = checkComposedChords(tokenAnchors, tokenToWords, theory, kb)
        assert w in report.feasibleWords
        assert w not in report.infeasibleWords

    def test_composed_chord_collides(self):
        w = _make_word()
        theory = {((1,),): [w], ((1, 2, 3),): [_make_word(ortho="other")]}
        tokenToWords = {"pers": [(w, "pers_3")], "3": [(w, "pers_3")]}
        tokenAnchors = {
            "pers": TokenAnchorFeasibility(token="pers", feasibleSingleKeyPhonemes=["t"]),
            "3": TokenAnchorFeasibility(token="3", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_anchors({"t": (2,), "s": (3,)})
        report = checkComposedChords(tokenAnchors, tokenToWords, theory, kb)
        assert w in report.infeasibleWords

    def test_missing_anchor_marks_infeasible(self):
        w = _make_word()
        theory = {((1,),): [w]}
        tokenToWords = {"pers": [(w, "pers_3")], "3": [(w, "pers_3")]}
        tokenAnchors = {
            "pers": TokenAnchorFeasibility(token="pers"),  # no feasible anchors at all
            "3": TokenAnchorFeasibility(token="3", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_anchors({"s": (3,)})
        report = checkComposedChords(tokenAnchors, tokenToWords, theory, kb)
        assert w in report.infeasibleWords
