#!/usr/bin/python
# coding: utf-8
"""Tests for src/ambiguitychecker.py — Phase 0 ambiguity checker."""

from unittest.mock import MagicMock

from src.word import Word, GramCat
from src.ambiguitychecker import (
    StrokeClusterReport,
    FeatureKeypressFeasibility,
    KeypressGroupPhysicalAssignment,
    STAR,
    HASH,
    STAR_HASH,
    STAR_KEY,
    HASH_KEY,
    assignStarHashCombos,
    assignStarHashMarks,
    assignStarHashPhysicalStrokes,
    classifyStrokeCluster,
    composeReservedKeyStrokes,
    decideStarHashMark,
    detectCrossCategoryClash,
    groupHomophonesByReservedStroke,
    loadReform1990DoubletPairs,
    rankHomophoneCluster,
    starHashCodeToStrokes,
    computeClusterSizeDistribution,
    computeOverflowFrequencyMass,
    buildAtomicFeatureToWords,
    buildKeypressGroupExtraAlternates,
    buildKeypressGroupToWords,
    buildWordsByOrthoLemme,
    buildWordToGroups,
    findFeatureKeypresses,
    findCollidingNewAdditions,
    findCollidingInducedStrokes,
    realizeKeypressGroupsAsExtraStroke,
    _isInScopeCollision,
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


def _mock_keyboard_for_keypresses(codaMap: dict[str, tuple[int, ...]]) -> MagicMock:
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


class TestDecideStarHashMark:

    def test_homograph_pair_needs_no_mark(self):
        a = _make_word(ortho="dîner", gramCat=GramCat.NOM, frequencyFilm=1.0)
        b = _make_word(ortho="dîner", gramCat=GramCat.VER, frequencyFilm=99.0)
        assert decideStarHashMark(a, b) is None

    def test_extreme_ratio_marks_the_rarer_reading_regardless_of_category(self):
        rare = _make_word(ortho="hiles", gramCat=GramCat.NOM, frequencyFilm=0.01)
        common = _make_word(ortho="ils", gramCat=GramCat["PRO:per"], frequencyFilm=3075.1)
        assert decideStarHashMark(rare, common) is rare
        assert decideStarHashMark(common, rare) is rare

    def test_same_category_residual_marks_rarer_word(self):
        a = _make_word(ortho="dors", gramCat=GramCat.VER, frequencyFilm=5.0)
        b = _make_word(ortho="dort", gramCat=GramCat.VER, frequencyFilm=2.0)
        assert decideStarHashMark(a, b) is b
        assert decideStarHashMark(b, a) is b

    def test_gramcat_priority_marks_lower_priority_category(self):
        # NOM (priority 30) beats VER (priority 20) -- VER gets marked -- and the ratio
        # between the two frequencies here is deliberately kept < 10x so Rule 1 doesn't
        # pre-empt the categorical rule being exercised.
        nom = _make_word(ortho="entrée", gramCat=GramCat.NOM, frequencyFilm=4.0)
        ver = _make_word(ortho="entré", gramCat=GramCat.VER, frequencyFilm=8.0)
        assert decideStarHashMark(nom, ver) is ver
        assert decideStarHashMark(ver, nom) is ver

    def test_unknown_category_pair_falls_back_to_frequency(self):
        a = _make_word(ortho="foo", gramCat=GramCat.CON, frequencyFilm=5.0)
        b = _make_word(ortho="bar", gramCat=GramCat.LIA, frequencyFilm=2.0)
        assert decideStarHashMark(a, b) is b

    def test_override_list_wins_over_categorical_rule(self):
        # "sales"(ADJ, freq=26.73) vs "salles"(NOM, freq=5.81): GRAMCAT_PRIORITY ranks
        # NOM above ADJ, so the plain categorical rule would mark "sales" -- exactly
        # the misfire (marking the FAR MORE FREQUENT word) that put this pair in
        # MARKING_OVERRIDES. The override should win and mark "salles" instead (the
        # true per-pair-optimal: mark whichever reading is individually rarer).
        sales = _make_word(ortho="sales", gramCat=GramCat.ADJ, frequencyFilm=26.73)
        salles = _make_word(ortho="salles", gramCat=GramCat.NOM, frequencyFilm=5.81)
        assert decideStarHashMark(sales, salles) is salles
        assert decideStarHashMark(salles, sales) is salles

    def test_doublet_pair_needs_no_mark(self):
        old = _make_word(ortho="boîte", lemme="boîte", gramCat=GramCat.NOM, frequencyFilm=1.0)
        new = _make_word(ortho="boite", lemme="boite", gramCat=GramCat.NOM, frequencyFilm=99.0)
        doubletPairs = frozenset({frozenset({"boîte", "boite"})})
        assert decideStarHashMark(old, new, doubletPairs) is None
        assert decideStarHashMark(new, old, doubletPairs) is None

    def test_doublet_exemption_is_opt_in_and_off_by_default(self):
        old = _make_word(ortho="boîte", lemme="boîte", gramCat=GramCat.NOM, frequencyFilm=1.0)
        new = _make_word(ortho="boite", lemme="boite", gramCat=GramCat.NOM, frequencyFilm=99.0)
        assert decideStarHashMark(old, new) is not None


class TestLoadReform1990DoubletPairs:

    def test_parses_pairs_and_excludes_exceptions(self, tmp_path):
        tsv = tmp_path / "reform1990.tsv"
        tsv.write_text(
            "# a comment line\n"
            "oldSpelling\tnewSpelling\tcategory\tappliesToLemmeNormalization\t"
            "appliesToOrthoRewrite\tappliesToPluralRewrite\tisException\tnote\n"
            "boîte\tboite\tcirconflexe\tTrue\tTrue\tFalse\tFalse\t\n"
            "fût\tfut\tcirconflexe\tFalse\tFalse\tFalse\tTrue\thomograph collision\n",
            encoding="utf-8",
        )
        pairs = loadReform1990DoubletPairs(str(tsv))
        assert pairs == frozenset({frozenset({"boîte", "boite"})})

    def test_real_file_loads_and_is_nonempty(self):
        pairs = loadReform1990DoubletPairs()
        assert len(pairs) > 0
        assert frozenset({"boîte", "boite"}) in pairs
        assert frozenset({"fût", "fut"}) not in pairs  # isException row, excluded


class TestAssignStarHashCombos:

    def test_size_1_is_canonical_only(self):
        assert assignStarHashCombos(1) == [()]

    def test_size_up_to_4_uses_single_stroke_states(self):
        assert assignStarHashCombos(4) == [(), (STAR,), (HASH,), (STAR_HASH,)]

    def test_size_2_and_3_are_prefixes_of_the_size_4_list(self):
        assert assignStarHashCombos(2) == [(), (STAR,)]
        assert assignStarHashCombos(3) == [(), (STAR,), (HASH,)]

    def test_beyond_4_escalates_to_repeated_star_hash_syllables(self):
        assert assignStarHashCombos(7) == [
            (), (STAR,), (HASH,), (STAR_HASH,),
            (STAR_HASH, STAR_HASH),
            (STAR_HASH, STAR_HASH, STAR_HASH),
            (STAR_HASH, STAR_HASH, STAR_HASH, STAR_HASH),
        ]

    def test_all_codes_distinct(self):
        codes = assignStarHashCombos(10)
        assert len(codes) == len(set(codes)) == 10


class TestRankHomophoneCluster:

    def test_ranks_by_gramcat_priority_when_ratio_is_moderate(self):
        nom = _make_word(ortho="entrée", gramCat=GramCat.NOM, frequencyFilm=4.0)
        ver = _make_word(ortho="entré", gramCat=GramCat.VER, frequencyFilm=8.0)
        assert rankHomophoneCluster([ver, nom]) == [nom, ver]

    def test_three_way_cluster_ranked_consistently_with_pairwise_decisions(self):
        # NOM(30) > VER(20) > ADJ(10) in GRAMCAT_PRIORITY -- ratios kept < 10x so Rule 1
        # doesn't pre-empt the categorical comparisons being exercised.
        nom = _make_word(ortho="nomword", gramCat=GramCat.NOM, frequencyFilm=5.0)
        ver = _make_word(ortho="verword", gramCat=GramCat.VER, frequencyFilm=5.0)
        adj = _make_word(ortho="adjword", gramCat=GramCat.ADJ, frequencyFilm=5.0)
        assert rankHomophoneCluster([adj, ver, nom]) == [nom, ver, adj]


class TestAssignStarHashMarks:

    def test_pair_matches_decideStarHashMark(self):
        nom = _make_word(ortho="entrée", gramCat=GramCat.NOM, frequencyFilm=4.0)
        ver = _make_word(ortho="entré", gramCat=GramCat.VER, frequencyFilm=8.0)
        marks = assignStarHashMarks([ver, nom])
        assert marks[nom] == ()
        assert marks[ver] == (STAR,)

    def test_homograph_pair_shares_one_code_and_does_not_consume_a_slot(self):
        # Same ortho as a 3rd, distinct-spelling reading -- the homograph pair should
        # collapse to a single ranked slot, so this 3-word cluster only needs 2 codes,
        # not 3.
        a = _make_word(ortho="dîner", gramCat=GramCat.NOM, frequencyFilm=1.0)
        b = _make_word(ortho="dîner", gramCat=GramCat.VER, frequencyFilm=99.0)
        c = _make_word(ortho="dînai", gramCat=GramCat.VER, frequencyFilm=0.5)
        marks = assignStarHashMarks([a, b, c])
        assert marks[a] == marks[b]
        assert marks[c] != marks[a]
        assert {marks[a], marks[c]} == {(), (STAR,)}

    def test_doublet_pair_shares_one_code_and_does_not_consume_a_slot(self):
        old = _make_word(ortho="boîte", lemme="boîte", gramCat=GramCat.NOM, frequencyFilm=1.0)
        new = _make_word(ortho="boite", lemme="boite", gramCat=GramCat.NOM, frequencyFilm=99.0)
        other = _make_word(ortho="boit", lemme="boire", gramCat=GramCat.VER, frequencyFilm=0.5)
        doubletPairs = frozenset({frozenset({"boîte", "boite"})})
        marks = assignStarHashMarks([old, new, other], doubletPairs)
        assert marks[old] == marks[new]
        assert marks[other] != marks[old]
        assert {marks[old], marks[other]} == {(), (STAR,)}

    def test_five_member_cluster_escalates_to_two_star_hash_syllables(self):
        words = [
            _make_word(ortho=f"w{i}", gramCat=GramCat.NOM, frequencyFilm=float(10 - i))
            for i in range(5)
        ]
        marks = assignStarHashMarks(words)
        assert sorted(marks.values()) == sorted(assignStarHashCombos(5))
        assert marks[words[0]] == ()
        assert marks[words[4]] == (STAR_HASH, STAR_HASH)


class TestStarHashCodeToStrokes:

    def test_key_assignment(self):
        assert STAR_KEY == 10
        assert HASH_KEY == 15

    def test_canonical_code_has_no_extra_stroke(self):
        assert starHashCodeToStrokes(()) == ()

    def test_single_symbol_codes_map_to_their_key(self):
        assert starHashCodeToStrokes((STAR,)) == ((10,),)
        assert starHashCodeToStrokes((HASH,)) == ((15,),)
        assert starHashCodeToStrokes((STAR_HASH,)) == ((10, 15),)

    def test_multi_syllable_code_repeats_the_stroke_in_order(self):
        assert starHashCodeToStrokes((STAR_HASH, STAR_HASH)) == ((10, 15), (10, 15))
        assert starHashCodeToStrokes((STAR_HASH, STAR_HASH, STAR_HASH)) == (
            (10, 15), (10, 15), (10, 15),
        )


class TestAssignStarHashPhysicalStrokes:

    def test_matches_symbolic_assignment_through_the_key_mapping(self):
        nom = _make_word(ortho="entrée", gramCat=GramCat.NOM, frequencyFilm=4.0)
        ver = _make_word(ortho="entré", gramCat=GramCat.VER, frequencyFilm=8.0)
        physical = assignStarHashPhysicalStrokes([ver, nom])
        assert physical[nom] == ()
        assert physical[ver] == ((10,),)


class TestGroupHomophonesByReservedStroke:

    def test_distinct_lemma_pair_sharing_a_stroke_is_grouped(self):
        a = _make_word(ortho="ver", lemme="ver", gramCat=GramCat.NOM, frequencyFilm=1.0)
        b = _make_word(ortho="verre", lemme="verre", gramCat=GramCat.NOM, frequencyFilm=5.0)
        finalInduced = {a: ((1, 2),), b: ((1, 2),)}
        groups = groupHomophonesByReservedStroke(finalInduced)
        assert groups == {((1, 2),): [a, b]}

    def test_same_lemmeGramCat_pair_is_excluded_as_phase_p_residual(self):
        # Same lemme AND same gramCat -> Phase P's own job, not a */# case, even
        # though they still coincidentally share a final stroke here.
        a = _make_word(ortho="dors", lemme="dormir", gramCat=GramCat.VER, frequencyFilm=1.0)
        b = _make_word(ortho="dort", lemme="dormir", gramCat=GramCat.VER, frequencyFilm=1.0)
        finalInduced = {a: ((1,),), b: ((1,),)}
        assert groupHomophonesByReservedStroke(finalInduced) == {}

    def test_all_homograph_group_is_excluded(self):
        a = _make_word(ortho="dîner", lemme="dîner", gramCat=GramCat.NOM, frequencyFilm=1.0)
        b = _make_word(ortho="dîner", lemme="dîner", gramCat=GramCat.VER, frequencyFilm=1.0)
        finalInduced = {a: ((1,),), b: ((1,),)}
        assert groupHomophonesByReservedStroke(finalInduced) == {}

    def test_singleton_stroke_is_excluded(self):
        a = _make_word(ortho="chat")
        assert groupHomophonesByReservedStroke({a: ((1,),)}) == {}

    def test_mixed_group_kept_when_at_least_one_pair_is_a_real_ambiguity(self):
        # Two homographs plus a third, distinctly-spelled, distinct-lemmeGramCat
        # reading -- the group as a whole is a real */# case even though one pair
        # within it isn't.
        a = _make_word(ortho="dîner", lemme="dîner", gramCat=GramCat.NOM, frequencyFilm=1.0)
        b = _make_word(ortho="dîner", lemme="dîner", gramCat=GramCat.VER, frequencyFilm=99.0)
        c = _make_word(ortho="dînai", lemme="dînai", gramCat=GramCat.VER, frequencyFilm=0.5)
        finalInduced = {a: ((1,),), b: ((1,),), c: ((1,),)}
        assert groupHomophonesByReservedStroke(finalInduced) == {((1,),): [a, b, c]}


class TestComposeReservedKeyStrokes:

    def test_appends_star_hash_extra_stroke_after_phase_p_stroke(self):
        nom = _make_word(ortho="entrée", gramCat=GramCat.NOM, frequencyFilm=4.0)
        ver = _make_word(ortho="entré", gramCat=GramCat.VER, frequencyFilm=8.0)
        finalInduced = {nom: ((1, 2), (16,)), ver: ((1, 2), (16,))}
        composed = composeReservedKeyStrokes(finalInduced)
        assert composed[nom] == ((1, 2), (16,))
        assert composed[ver] == ((1, 2), (16,), (10,))

    def test_words_outside_any_group_are_unchanged(self):
        solo = _make_word(ortho="chat")
        finalInduced = {solo: ((1,), (16,))}
        assert composeReservedKeyStrokes(finalInduced) == finalInduced

    def test_two_different_clusters_never_collide_after_composition(self):
        a1 = _make_word(ortho="ver", lemme="ver", gramCat=GramCat.NOM, frequencyFilm=1.0)
        a2 = _make_word(ortho="verre", lemme="verre", gramCat=GramCat.NOM, frequencyFilm=5.0)
        b1 = _make_word(ortho="pain", lemme="pain", gramCat=GramCat.NOM, frequencyFilm=2.0)
        b2 = _make_word(ortho="pin", lemme="pin", gramCat=GramCat.NOM, frequencyFilm=6.0)
        finalInduced = {a1: ((1,),), a2: ((1,),), b1: ((2,),), b2: ((2,),)}
        composed = composeReservedKeyStrokes(finalInduced)
        assert len(set(composed.values())) == 4


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
# buildAtomicFeatureToWords
# ---------------------------------------------------------------------------

class TestBuildAtomicFeatureToWords:

    def test_nofeature_and_singleton_filtered(self):
        w = _make_word()
        augmentedTheory = {
            ("nofeature",): [(w,)],
            ("s",): [(w,)],  # len < 2, no canonical/non-canonical split
        }
        assert buildAtomicFeatureToWords(augmentedTheory) == {}

    def test_canonical_excluded_noncanonical_split_into_atomic_features(self):
        """pers_3 (priority 70) beats pers_1 (priority 55): pers_3 is canonical (no keypress
        needed), pers_1 is the one that needs a feature keypress. atomicFeatures() splits
        only on ':', so "pers_1" stays one atom -- not {"pers", "1"}."""
        w3 = _make_word(ortho="w3")
        w1 = _make_word(ortho="w1")
        augmentedTheory = {("pers_3", "pers_1"): [(w3, w1)]}
        atomicFeatureToWords = buildAtomicFeatureToWords(augmentedTheory)
        assert set(atomicFeatureToWords.keys()) == {"pers_1"}
        assert atomicFeatureToWords["pers_1"] == [(w1, "pers_1")]


# ---------------------------------------------------------------------------
# findFeatureKeypresses
# ---------------------------------------------------------------------------

class TestFindFeatureKeypresses:

    def test_clean_single_key_keypress(self):
        w = _make_word()
        theory = {((1,),): [w]}
        atomicFeatureToWords = {"atomA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_keypresses({"t": (2,)})
        result = findFeatureKeypresses(atomicFeatureToWords, theory, kb)
        assert result["atomA"].feasibleSingleKeyPhonemes == ["t"]
        assert not result["atomA"].infeasible

    def test_escalates_to_combo_when_singles_collide(self):
        w = _make_word()
        theory = {
            ((1,),): [w],
            ((1, 2),): [_make_word(ortho="other1")],
            ((1, 3),): [_make_word(ortho="other2")],
        }
        atomicFeatureToWords = {"atomA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        result = findFeatureKeypresses(atomicFeatureToWords, theory, kb)
        assert result["atomA"].feasibleSingleKeyPhonemes == []
        assert ("t", "s") in result["atomA"].feasibleComboPhonemes
        assert not result["atomA"].infeasible

    def test_infeasible_even_with_combo(self):
        w = _make_word()
        theory = {((1,),): [w], ((1, 2),): [_make_word(ortho="other1")]}
        atomicFeatureToWords = {"atomA": [(w, "someFeature")]}
        kb = _mock_keyboard_for_keypresses({"t": (2,)})
        result = findFeatureKeypresses(atomicFeatureToWords, theory, kb)
        assert result["atomA"].infeasible


# ---------------------------------------------------------------------------
# checkComposedChords
# ---------------------------------------------------------------------------

class TestCheckComposedChords:

    def test_composed_chord_feasible(self):
        w = _make_word()
        theory = {((1,),): [w]}
        atomicFeatureToWords = {
            "pers_3": [(w, "pers_3:nbr_s")],
            "nbr_s": [(w, "pers_3:nbr_s")],
        }
        featureKeypresses = {
            "pers_3": FeatureKeypressFeasibility(atomicFeature="pers_3", feasibleSingleKeyPhonemes=["t"]),
            "nbr_s": FeatureKeypressFeasibility(atomicFeature="nbr_s", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        report = checkComposedChords(featureKeypresses, atomicFeatureToWords, theory, kb)
        assert w in report.feasibleWords
        assert w not in report.infeasibleWords

    def test_composed_chord_collides(self):
        w = _make_word()
        theory = {((1,),): [w], ((1, 2, 3),): [_make_word(ortho="other")]}
        atomicFeatureToWords = {
            "pers_3": [(w, "pers_3:nbr_s")],
            "nbr_s": [(w, "pers_3:nbr_s")],
        }
        featureKeypresses = {
            "pers_3": FeatureKeypressFeasibility(atomicFeature="pers_3", feasibleSingleKeyPhonemes=["t"]),
            "nbr_s": FeatureKeypressFeasibility(atomicFeature="nbr_s", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        report = checkComposedChords(featureKeypresses, atomicFeatureToWords, theory, kb)
        assert w in report.infeasibleWords

    def test_missing_keypress_marks_infeasible(self):
        w = _make_word()
        theory = {((1,),): [w]}
        atomicFeatureToWords = {
            "pers_3": [(w, "pers_3:nbr_s")],
            "nbr_s": [(w, "pers_3:nbr_s")],
        }
        featureKeypresses = {
            "pers_3": FeatureKeypressFeasibility(atomicFeature="pers_3"),  # no feasible keypress at all
            "nbr_s": FeatureKeypressFeasibility(atomicFeature="nbr_s", feasibleSingleKeyPhonemes=["s"]),
        }
        kb = _mock_keyboard_for_keypresses({"s": (3,)})
        report = checkComposedChords(featureKeypresses, atomicFeatureToWords, theory, kb)
        assert w in report.infeasibleWords

    def test_combo_union_uses_both_phonemes_keys(self):
        """Regression test for the half-combo bug: when the chosen feasibility for an
        atomic feature is a *combo* (not a single key), both phonemes' keys must be
        unioned into the composed chord, not just the first's."""
        w = _make_word()
        # If only p1's key ((2,)) were unioned in (the bug), the composed chord for this
        # word would be ((1, 2),), which is NOT in theory -- the bug would wrongly call
        # this feasible. With both phonemes' keys unioned, the composed chord is
        # ((1, 2, 3),), which IS already in theory as another word's stroke -- correctly
        # infeasible.
        theory = {((1,),): [w], ((1, 2, 3),): [_make_word(ortho="other")]}
        atomicFeatureToWords = {
            "pers_3": [(w, "pers_3:nbr_s")],
            "nbr_s": [(w, "pers_3:nbr_s")],
        }
        featureKeypresses = {
            "pers_3": FeatureKeypressFeasibility(atomicFeature="pers_3", feasibleComboPhonemes=[("t", "s")]),
            "nbr_s": FeatureKeypressFeasibility(atomicFeature="nbr_s", feasibleComboPhonemes=[("t", "s")]),
        }
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        report = checkComposedChords(featureKeypresses, atomicFeatureToWords, theory, kb)
        assert w in report.infeasibleWords
        assert w not in report.feasibleWords


# ---------------------------------------------------------------------------
# findCollidingNewAdditions
# ---------------------------------------------------------------------------

class TestFindCollidingNewAdditions:

    def test_two_words_collide_on_same_induced_stroke(self):
        w1 = _make_word(ortho="w1")
        w2 = _make_word(ortho="w2")
        wordToStrokes = {w1: ((5,),), w2: ((6,),)}
        collisions = findCollidingNewAdditions([w1, w2], (5, 6), wordToStrokes)
        assert collisions == [(w1, w2)]

    def test_no_collision_when_induced_strokes_differ(self):
        w1 = _make_word(ortho="w1")
        w2 = _make_word(ortho="w2")
        wordToStrokes = {w1: ((5,),), w2: ((7,),)}
        collisions = findCollidingNewAdditions([w1, w2], (6,), wordToStrokes)
        assert collisions == []

    def test_single_word_never_collides(self):
        w1 = _make_word(ortho="w1")
        wordToStrokes = {w1: ((5,),)}
        assert findCollidingNewAdditions([w1], (6,), wordToStrokes) == []


# ---------------------------------------------------------------------------
# buildKeypressGroupToWords
# ---------------------------------------------------------------------------

class TestBuildKeypressGroupToWords:

    def test_canonical_member_excluded_marked_member_included(self):
        """abaca/abacas share one base Strokes (true homophones); abaca's press-set is
        empty (canonical, no keypress group touches it), abacas' 'p' marker routes it
        into keypress group 0. Each ortho's press-sets is a LIST of alternates (see
        `src.elicitation.resolveGroupPressSets`); this function drives the search off
        the PRIMARY (first) alternate only."""
        wAbaca = _make_word(ortho="abaca", lemme="abaca", gramCat=GramCat.NOM)
        wAbacas = _make_word(ortho="abacas", lemme="abaca", gramCat=GramCat.NOM)
        sharedStrokes = ((12,), (3, 5, 12))
        wordToStrokes = {wAbaca: sharedStrokes, wAbacas: sharedStrokes}
        wordsByOrthoLemme = {
            ("abaca", "abaca_NOM"): [wAbaca], ("abacas", "abaca_NOM"): [wAbacas],
        }
        entry = {
            "strokes": [[12], [3, 5, 12]], "lemmeGramCat": "abaca_NOM",
            "pressSets": {"abaca": [[]], "abacas": [["p"]]},
        }
        markersByKeypress = {0: frozenset({"p", "nbr_p"})}
        groupToWords = buildKeypressGroupToWords([entry], markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        assert groupToWords == {0: [wAbacas]}

    def test_disambiguates_by_matching_existing_strokes(self):
        """Two Word objects can share (ortho, lemmeGramCat) but differ in existing
        strokes; the entry's own 'strokes' field picks the one that's actually this
        group's member."""
        sharedStrokes = ((12,), (3, 5, 12))
        wRight = _make_word(ortho="abacas", lemme="abaca", gramCat=GramCat.NOM)
        wWrong = _make_word(ortho="abacas", lemme="abaca", gramCat=GramCat.NOM, gender="f")
        wordToStrokes = {wRight: sharedStrokes, wWrong: ((99,),)}
        wordsByOrthoLemme = {("abacas", "abaca_NOM"): [wWrong, wRight]}
        entry = {
            "strokes": [[12], [3, 5, 12]], "lemmeGramCat": "abaca_NOM",
            "pressSets": {"abacas": [["p"]]},
        }
        markersByKeypress = {0: frozenset({"p"})}
        groupToWords = buildKeypressGroupToWords([entry], markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        assert groupToWords == {0: [wRight]}

    def test_only_the_primary_alternate_feeds_the_search(self):
        """"calmez"-shaped entry: two alternates, `impératif` (primary) and `pers_2`
        (extra). Only `impératif`'s group is populated here -- `pers_2`'s is the job of
        `buildKeypressGroupExtraAlternates`, not this function."""
        wCalmez = _make_word(ortho="calmez", lemme="calmer", gramCat=GramCat.VER)
        sharedStrokes = ((12,),)
        wordToStrokes = {wCalmez: sharedStrokes}
        wordsByOrthoLemme = {("calmez", "calmer_VER"): [wCalmez]}
        entry = {
            "strokes": [[12]], "lemmeGramCat": "calmer_VER",
            "pressSets": {"calmez": [["impératif"], ["pers_2"]]},
        }
        markersByKeypress = {0: frozenset({"impératif"}), 1: frozenset({"pers_2"})}
        groupToWords = buildKeypressGroupToWords([entry], markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        assert groupToWords == {0: [wCalmez]}


class TestBuildKeypressGroupExtraAlternates:

    def test_ignores_orthos_with_only_one_alternate(self):
        wAbacas = _make_word(ortho="abacas", lemme="abaca", gramCat=GramCat.NOM)
        wordToStrokes = {wAbacas: ((12,),)}
        wordsByOrthoLemme = {("abacas", "abaca_NOM"): [wAbacas]}
        entry = {
            "strokes": [[12]], "lemmeGramCat": "abaca_NOM",
            "pressSets": {"abacas": [["p"]]},
        }
        markersByKeypress = {0: frozenset({"p"})}
        assert buildKeypressGroupExtraAlternates(
            [entry], markersByKeypress, wordToStrokes, wordsByOrthoLemme
        ) == {}

    def test_returns_every_non_primary_alternates_group_set(self):
        """"calmez" = impératif (primary, consumed by buildKeypressGroupToWords) or
        pers_2 (extra) -- this function surfaces the extra one's own group-set."""
        wCalmez = _make_word(ortho="calmez", lemme="calmer", gramCat=GramCat.VER)
        wordToStrokes = {wCalmez: ((12,),)}
        wordsByOrthoLemme = {("calmez", "calmer_VER"): [wCalmez]}
        entry = {
            "strokes": [[12]], "lemmeGramCat": "calmer_VER",
            "pressSets": {"calmez": [["impératif"], ["pers_2"]]},
        }
        markersByKeypress = {0: frozenset({"impératif"}), 1: frozenset({"pers_2"})}
        extras = buildKeypressGroupExtraAlternates([entry], markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        assert extras == {wCalmez: [frozenset({1})]}


# ---------------------------------------------------------------------------
# findCollidingInducedStrokes / buildWordToGroups
# ---------------------------------------------------------------------------

class TestFindCollidingInducedStrokes:

    def test_two_words_same_stroke_collide(self):
        w1, w2 = _make_word(ortho="w1"), _make_word(ortho="w2")
        collisions = findCollidingInducedStrokes({w1: ((1, 2),), w2: ((1, 2),)})
        assert collisions == [(w1, w2)]

    def test_different_strokes_no_collision(self):
        w1, w2 = _make_word(ortho="w1"), _make_word(ortho="w2")
        assert findCollidingInducedStrokes({w1: ((1,),), w2: ((2,),)}) == []


class TestBuildWordToGroups:

    def test_inverts_group_to_words(self):
        w1, w2 = _make_word(ortho="w1"), _make_word(ortho="w2")
        groupToWords = {0: [w1, w2], 1: [w2]}
        wordToGroups = buildWordToGroups(groupToWords)
        assert wordToGroups[w1] == frozenset({0})
        assert wordToGroups[w2] == frozenset({0, 1})


# ---------------------------------------------------------------------------
# realizeKeypressGroupsAsExtraStroke
# ---------------------------------------------------------------------------

class TestIsInScopeCollision:

    def test_same_lemme_gram_cat_different_ortho_is_in_scope(self):
        w1 = _make_word(ortho="dors", lemme="dormir", gramCat=GramCat.VER)
        w2 = _make_word(ortho="dort", lemme="dormir", gramCat=GramCat.VER)
        assert _isInScopeCollision(w1, w2)

    def test_different_lemma_is_out_of_scope(self):
        """Cross-lemma homophones (e.g. abymes/abîmes) are the reserved */# keys' job,
        not Phase G/P's coda-bank groups."""
        w1 = _make_word(ortho="abymes", lemme="abyme")
        w2 = _make_word(ortho="abîmes", lemme="abîme")
        assert not _isInScopeCollision(w1, w2)

    def test_same_bare_lemme_different_gramcat_is_out_of_scope(self):
        """Same bare lemma, different gramCat (e.g. "dîner" the NOM vs "dîner" the VER)
        is the already-documented "aller"-style cross-category clash
        (detectCrossCategoryClash), a separate issue class -- not Phase G/P's job."""
        w1 = _make_word(ortho="dîners", lemme="dîner", gramCat=GramCat.NOM)
        w2 = _make_word(ortho="dînés", lemme="dîner", gramCat=GramCat.VER)
        assert not _isInScopeCollision(w1, w2)

    def test_identical_ortho_is_out_of_scope(self):
        """Same spelling produces identical typed output regardless of grammatical
        reading -- never a real ambiguity, even when the internal lemma tags differ
        (e.g. a VER-participle vs ADJ homograph reading of one written word)."""
        w1 = _make_word(ortho="abaissés", lemme="abaisser", gramCat=GramCat.VER)
        w2 = _make_word(ortho="abaissés", lemme="abaissé", gramCat=GramCat.ADJ)
        assert not _isInScopeCollision(w1, w2)


class TestRealizeKeypressGroupsAsExtraStroke:

    def test_two_groups_never_reuse_a_key_that_would_reunite_a_homophone_pair(self):
        """Regression test for the 'honnit'/'honnie' bug: Phase G already proved group 0
        and group 1 are distinct in the ABSTRACT (a word needing only group 0 induces a
        different abstract keypress set than a word needing only group 1) -- but if Phase
        P hands both groups the exact same PHYSICAL key, two words that share a base
        stroke (already homophones) and were relying on landing in different groups end
        up reunited. w3/w3b need only group 0 (padding so it's processed first); w5
        shares w3's base stroke and lemmeGramCat but needs only group 1. Group 1 must NOT
        pick group 0's key even though it looks individually cheaper."""
        sharedBase = ((1,),)
        w3 = _make_word(ortho="honnit", lemme="honnir", gramCat=GramCat.VER)
        w5 = _make_word(ortho="honnie", lemme="honnir", gramCat=GramCat.VER)
        w3b = _make_word(ortho="other", lemme="other")
        theory = {sharedBase: [w3, w5], ((9,),): [w3b]}
        groupToWords = {0: [w3, w3b], 1: [w5]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        costs = {(2,): 50, (3,): 100}
        kb.getStrokeCost.side_effect = lambda stroke, part: costs.get(stroke)
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (2,)
        assert assignment.chosenKeysByGroup[1] == (3,)
        assert assignment.residualCollisions == []

    def test_multi_group_composition_does_not_coincide_with_another_group(self):
        """Subtler version of the honnit/honnie bug: groups 0 and 1 individually get
        distinct key-sets (2,) and (3,) -- pairwise distinctness alone would call that
        safe -- but a word needing BOTH (w_multi) ends up with their union (2,3), which
        collides with group 2's own candidate (2,3) for a same-lemmeGramCat sibling
        (w_single) that shares w_multi's base stroke. Only checking against the real
        composed stroke of already-finalized words catches this; group 2 must be left
        unassigned rather than silently reusing (2,3)."""
        sharedBase = ((1,),)
        w_multi = _make_word(ortho="multi", lemme="x", gramCat=GramCat.VER)
        w_single = _make_word(ortho="single", lemme="x", gramCat=GramCat.VER)
        w0_pad = _make_word(ortho="pad0", lemme="pad0")
        w1_pad = _make_word(ortho="pad1", lemme="pad1")
        theory = {sharedBase: [w_multi, w_single], ((8,),): [w0_pad], ((9,),): [w1_pad]}
        groupToWords = {0: [w_multi, w0_pad], 1: [w_multi, w1_pad], 2: [w_single]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        costs = {(2,): 10, (3,): 20, (2, 3): 15}
        kb.getStrokeCost.side_effect = lambda stroke, part: costs.get(stroke)
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (2,)
        assert assignment.chosenKeysByGroup[1] == (3,)
        assert 2 in assignment.unassignedGroups
        assert assignment.residualCollisions == []

    def test_same_column_combo_bonus_prefers_cheaper_composed_candidate(self):
        """Two candidates for group 1 ((23,) and (24,)) are equally cheap on their OWN,
        but group 0 (processed first, bigger population) has already claimed key (22,)
        for a word both groups share. (22,23) is a same-column combo (cheap per
        Starboard's real cost model); (22,24) is cross-column (expensive). Ranking must
        price the REAL composed chord, not each candidate's isolated cost, to prefer
        (23,) -- the "bonus" for landing in the same column as an already-decided,
        frequently co-occurring group's key."""
        w_a_only = _make_word(ortho="a_only")
        w_common = _make_word(ortho="common")
        theory = {((1,),): [w_a_only], ((2,),): [w_common]}
        groupToWords = {0: [w_a_only, w_common], 1: [w_common]}
        kb = _mock_keyboard_for_keypresses({"R": (22,), "t": (23,), "s": (24,)})
        costs = {(22,): 50, (23,): 100, (24,): 100, (22, 23): 150, (22, 24): 300}
        kb.getStrokeCost.side_effect = lambda stroke, part: costs.get(stroke)
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (22,)
        assert assignment.chosenKeysByGroup[1] == (23,)
        assert assignment.costByGroup[1] == 150
        assert assignment.alternatesByGroup[1] == [((24,), 300)]

    def test_out_of_scope_collision_does_not_block_candidate(self):
        """A cross-lemma homophone collision (different lemma, different spelling) must
        not prevent a candidate from being chosen -- that's the */# reserved-key track's
        job, not this function's, and blocking on it would make Phase P's own coda-group
        search fail for reasons entirely outside its scope."""
        w1 = _make_word(ortho="abymes", lemme="abyme")
        w2 = _make_word(ortho="abîmes", lemme="abîme")
        theory = {((1,),): [w1, w2]}
        groupToWords = {0: [w1, w2]}
        kb = _mock_keyboard_for_keypresses({"t": (2,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (2,)
        assert assignment.residualCollisions == []
        assert len(assignment.crossLemmaCollisions) == 1
        assert assignment.crossCategoryClashCollisions == []

    def test_cross_category_clash_does_not_block_candidate(self):
        """Same bare lemma, different gramCat (dîner NOM vs dîner VER) is the
        already-documented "aller"-style cross-category clash, not Phase P's job."""
        w1 = _make_word(ortho="dîners", lemme="dîner", gramCat=GramCat.NOM)
        w2 = _make_word(ortho="dînés", lemme="dîner", gramCat=GramCat.VER)
        theory = {((1,),): [w1, w2]}
        groupToWords = {0: [w1, w2]}
        kb = _mock_keyboard_for_keypresses({"t": (2,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (2,)
        assert assignment.residualCollisions == []
        assert assignment.crossLemmaCollisions == []
        assert len(assignment.crossCategoryClashCollisions) == 1

    def test_identical_ortho_never_reported_anywhere(self):
        w1 = _make_word(ortho="abaissés", lemme="abaisser", gramCat=GramCat.VER)
        w2 = _make_word(ortho="abaissés", lemme="abaissé", gramCat=GramCat.ADJ)
        theory = {((1,),): [w1, w2]}
        groupToWords = {0: [w1, w2]}
        kb = _mock_keyboard_for_keypresses({"t": (2,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (2,)
        assert assignment.residualCollisions == []
        assert assignment.crossLemmaCollisions == []
        assert assignment.crossCategoryClashCollisions == []


    def test_chooses_cheapest_and_lists_alternates(self):
        """The marker is realized as a brand-new trailing stroke, not merged into the
        word's last existing one."""
        w = _make_word()
        theory = {((1,),): [w]}
        groupToWords = {0: [w]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: {(2,): 5, (3,): 2}.get(stroke)
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.chosenKeysByGroup[0] == (3,)
        assert assignment.costByGroup[0] == 2
        assert assignment.alternatesByGroup[0] == [((2,), 5)]
        assert assignment.unassignedGroups == []
        assert assignment.residualCollisions == []
        assert assignment.residualTheoryCollisions == []

    def test_group_left_unassigned_when_every_candidate_collides(self):
        w = _make_word()
        # Both single-key candidates, and the only viable combo, are already real
        # strokes elsewhere in the theory -- no legal extra stroke is collision-free.
        theory = {
            ((1,),): [w], ((1,), (2,)): [_make_word(ortho="o1")],
            ((1,), (3,)): [_make_word(ortho="o2")], ((1,), (2, 3)): [_make_word(ortho="o3")],
        }
        groupToWords = {0: [w]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert assignment.unassignedGroups == [0]
        assert 0 not in assignment.chosenKeysByGroup

    def test_word_needing_two_groups_composes_them_into_one_shared_stroke(self):
        """Regression test for the 'abaissée vs abaissées' mistake: w1 needs only group 0,
        w2 needs both group 0 and group 1. Checking group 0's candidate against w2 in
        isolation (ignoring w2's not-yet-decided group 1) would wrongly look identical to
        w1's induced stroke -- this must NOT reject group 0's candidate on that basis, and
        the two words must end up genuinely distinguished once group 1 is also composed in."""
        w1 = _make_word(ortho="w1")
        w2 = _make_word(ortho="w2")
        sharedStrokes = ((1,),)
        theory = {sharedStrokes: [w1, w2]}
        groupToWords = {0: [w1, w2], 1: [w2]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: {(2,): 1, (3,): 1}.get(stroke, 1)
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert 0 in assignment.chosenKeysByGroup
        assert 1 in assignment.chosenKeysByGroup
        assert assignment.residualCollisions == []
        assert assignment.residualTheoryCollisions == []
        # w1 only ever gets group 0's key; w2 gets both groups' keys unioned -- genuinely
        # different final strokes.
        keys0 = assignment.chosenKeysByGroup[0]
        keys1 = assignment.chosenKeysByGroup[1]
        assert set(keys0) != set(keys0) | set(keys1)

    def test_residual_collision_reported_when_differentiating_group_left_unassigned(self):
        """If the group that was supposed to tell w1 and w2 apart ends up unassigned, the
        final verification pass must surface the resulting real collision rather than
        silently accepting group 0's (individually fine) choice."""
        w1 = _make_word(ortho="w1")
        w2 = _make_word(ortho="w2")
        sharedStrokes = ((1,),)
        # Group 0 (the bigger group) is decided first and takes key (2,). Group 1's only
        # non-redundant candidate, (3,), composed with group 0's already-chosen (2,) for
        # w2, lands on ((1,), (2, 3)) -- block exactly that composed stroke via theory so
        # group 1 has no legal candidate left and ends up unassigned.
        theory = {sharedStrokes: [w1, w2], ((1,), (2, 3)): [_make_word(ortho="o1")]}
        groupToWords = {0: [w1, w2], 1: [w2]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, kb)
        assert 1 in assignment.unassignedGroups
        collidingPairs = [frozenset(pair) for pair in assignment.residualCollisions]
        assert frozenset({w1, w2}) in collidingPairs


class TestRealizeKeypressGroupsAsExtraStrokeWithExtraAlternates:
    """The real "calmez" regression (RESUME_2026-09-21-steno-trainer.md item 2): a
    self-homograph spelling's OTHER readings (`extraGroupSetsByWord`) must be realized
    as their own additional strokes -- checked against every OTHER word, but never
    flagged against the SAME word's own primary reading."""

    def test_extra_alternate_realized_without_a_spurious_self_collision(self):
        """"calmez" needs group 0 as its primary reading and group 1 as an extra
        (alternate) reading -- padding words populate both groups so each gets a real
        physical key. calmez's two readings landing on two DIFFERENT physical strokes is
        expected and must not be reported as a collision (same word, same output text)."""
        wCalmez = _make_word(ortho="calmez", lemme="calmer", gramCat=GramCat.VER)
        wPad0 = _make_word(ortho="pad0", lemme="pad0")
        wPad1 = _make_word(ortho="pad1", lemme="pad1")
        theory = {((1,),): [wCalmez], ((5,),): [wPad0], ((6,),): [wPad1]}
        groupToWords = {0: [wCalmez, wPad0], 1: [wPad1]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(
            groupToWords, theory, kb, extraGroupSetsByWord={wCalmez: [frozenset({1})]}
        )
        assert 0 in assignment.chosenKeysByGroup
        assert 1 in assignment.chosenKeysByGroup
        assert assignment.residualCollisions == []

    def test_extra_alternate_colliding_with_another_word_is_caught(self):
        """calmez's EXTRA reading (group 1) composes to the same physical stroke as
        "calmiez" (a same-lemmeGramCat sibling sharing calmez's base stroke, needing
        group 1 as ITS primary reading) -- a real in-scope collision the main search
        never sees (calmez isn't part of group 1's population at all; only its extra
        alternate touches it), so only the final verification pass catches it."""
        wCalmez = _make_word(ortho="calmez", lemme="calmer", gramCat=GramCat.VER)
        wOther = _make_word(ortho="calmiez", lemme="calmer", gramCat=GramCat.VER)
        sharedBase = ((1,),)
        theory = {sharedBase: [wCalmez, wOther]}
        groupToWords = {0: [wCalmez], 1: [wOther]}
        kb = _mock_keyboard_for_keypresses({"t": (2,), "s": (3,)})
        kb.getStrokeCost.side_effect = lambda stroke, part: 1
        assignment = realizeKeypressGroupsAsExtraStroke(
            groupToWords, theory, kb, extraGroupSetsByWord={wCalmez: [frozenset({1})]}
        )
        collidingPairs = [frozenset(pair) for pair in assignment.residualCollisions]
        assert frozenset({wCalmez, wOther}) in collidingPairs
