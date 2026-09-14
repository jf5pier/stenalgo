#!/usr/bin/python
# coding: utf-8
"""Tests for src/featureextractor.py"""

import pytest
from unittest.mock import MagicMock
from src.word import Word, GramCat
from src.featureextractor import (
    getAmbiguousMultiphonemes,
    extractDiscriminatingFeatures,
    buildFeasibleDiscriminatorOptions,
    selectFeaturesBySetCover,
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


def _mock_keyboard():
    """Create a mock keyboard with strokesToString returning a simple repr."""
    kb = MagicMock()
    kb.strokesToString.side_effect = lambda s: "/".join(
        "-".join(str(k) for k in stroke) for stroke in s
    )
    return kb


# ---------------------------------------------------------------------------
# getAmbiguousMultiphonemes
# ---------------------------------------------------------------------------

class TestGetAmbiguousMultiphonemes:

    def test_empty_theory(self):
        result = getAmbiguousMultiphonemes({}, _mock_keyboard())
        assert result == {}

    def test_no_ambiguous_entries(self):
        w1 = _make_word(ortho="chat")
        w2 = _make_word(ortho="bon", phonology="bO~", lemme="bon",
                        rawSyllCV="b_O~", rawOrthosyllCV="b_o_n")
        theory = {
            ((1, 2),): [w1],
            ((3, 4),): [w2],
        }
        result = getAmbiguousMultiphonemes(theory, _mock_keyboard())
        assert result == {}

    def test_ambiguous_entries_returned(self):
        w1 = _make_word(ortho="fait", phonology="fE", lemme="faire",
                        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
                        rawSyllCV="f_E", rawOrthosyllCV="f_ai_t",
                        infoVerb="ind:pre:3s")
        w2 = _make_word(ortho="fais", phonology="fE", lemme="faire",
                        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
                        rawSyllCV="f_E", rawOrthosyllCV="f_ai_s",
                        infoVerb="ind:pre:1s")
        theory = {
            ((1, 2),): [w1, w2],
        }
        kb = _mock_keyboard()
        result = getAmbiguousMultiphonemes(theory, kb)
        assert len(result) == 1
        key = list(result.keys())[0]
        assert result[key] == [w1, w2]
        kb.strokesToString.assert_called_once_with(((1, 2),))

    def test_mixed_ambiguous_and_not(self):
        w1 = _make_word(ortho="chat")
        w2 = _make_word(ortho="fait", phonology="fE", lemme="faire",
                        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
                        rawSyllCV="f_E", rawOrthosyllCV="f_ai_t",
                        infoVerb="ind:pre:3s")
        w3 = _make_word(ortho="fais", phonology="fE", lemme="faire",
                        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
                        rawSyllCV="f_E", rawOrthosyllCV="f_ai_s",
                        infoVerb="ind:pre:1s")
        theory = {
            ((1,),): [w1],
            ((2, 3),): [w2, w3],
        }
        result = getAmbiguousMultiphonemes(theory, _mock_keyboard())
        assert len(result) == 1

    def test_multiple_ambiguous_groups(self):
        w1 = _make_word(ortho="a1", phonology="a")
        w2 = _make_word(ortho="a2", phonology="a", lemme="a2")
        w3 = _make_word(ortho="b1", phonology="b", lemme="b1",
                        rawSyllCV="b", rawOrthosyllCV="b_1")
        w4 = _make_word(ortho="b2", phonology="b", lemme="b2",
                        rawSyllCV="b", rawOrthosyllCV="b_2")
        theory = {
            ((1,),): [w1, w2],
            ((2,),): [w3, w4],
        }
        result = getAmbiguousMultiphonemes(theory, _mock_keyboard())
        assert len(result) == 2


# ---------------------------------------------------------------------------
# extractDiscriminatingFeatures
# ---------------------------------------------------------------------------

class TestExtractDiscriminatingFeatures:

    def _make_verb(self, ortho, person_number, tense="pre", mode="ind", **extra):
        """Helper to create verb Words with distinct infoVerb."""
        defaults = dict(
            ortho=ortho, phonology="fE", lemme="faire",
            gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
            gender=None, number=None,
            rawSyllCV="f_E", rawOrthosyllCV=f"{'_'.join(ortho)}",
            frequencyBook=1.0, frequencyFilm=2.0,
            infoVerb=f"{mode}:{tense}:{person_number}",
        )
        defaults.update(extra)
        return Word(**defaults)

    def test_no_ambiguity_single_words_still_tagged(self):
        """When every stroke maps to a single word, features are still tagged
        as discriminators (single ortho in group means len(orthoWords)==1)."""
        w1 = _make_word(ortho="chat")
        w2 = _make_word(ortho="bon", phonology="bO~", lemme="bon",
                        rawSyllCV="b_O~", rawOrthosyllCV="b_o_n")
        theory = {
            ((1,),): [w1],
            ((2,),): [w2],
        }
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        # Single-word groups still get their features as discriminators
        # because orthoWords has only 1 entry (len==1 triggers the branch)
        total_discriminated = sum(len(ws) for ws in disc_by.values())
        assert total_discriminated > 0

    def test_same_lemme_different_ortho_discriminated(self):
        """Two verb forms sharing the same lemme should be discriminated by features."""
        w1 = self._make_verb("fais", "1s")
        w2 = self._make_verb("fait", "3s")
        theory = {
            ((1, 2),): [w1, w2],
        }
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        # At least one feature should discriminate some word
        total_discriminated = sum(len(ws) for ws in disc_by.values())
        assert total_discriminated > 0
        assert len(ordered) > 0

    def test_stroke_lemme_discriminators_preserves_multiple_features_per_word(self):
        """strokeLemmeDiscriminators must expose every discriminating feature for a
        word, not just the single greedily-picked one (Stage 1 of the undersampled
        verb paradigm plan relies on the full per-word feature list, not a flattened
        one-feature-per-word view)."""
        w1 = self._make_verb("regarnie", "part", tense="pp", mode="ind",
                              gender="f", number="s", lemme="regarnir")
        w2 = self._make_verb("regarnis", "part", tense="pp", mode="ind",
                              gender="m", number="p", lemme="regarnir")
        theory = {((1, 2),): [w1, w2]}
        _, _, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)
        wordFeatures = strokeLemmeDiscriminators[((1, 2),), "regarnir_VER"]
        assert len(wordFeatures[w1]) > 1
        assert len(wordFeatures[w2]) > 1

    def test_ordered_features_list_has_no_duplicates(self):
        """The ordered feature list should not contain duplicates."""
        w1 = self._make_verb("fais", "1s")
        w2 = self._make_verb("fait", "3s")
        theory = {((1, 2),): [w1, w2]}
        _, ordered, _sld = extractDiscriminatingFeatures(theory)
        assert len(ordered) == len(set(ordered))

    def test_different_lemmes_each_treated_independently(self):
        """Words sharing a stroke but with different lemmes are processed in
        separate lemme groups.  Each single-word group still marks its features."""
        w1 = _make_word(ortho="ver", phonology="vER", lemme="ver",
                        rawSyllCV="v_E_R", rawOrthosyllCV="v_e_r")
        w2 = _make_word(ortho="vert", phonology="vER", lemme="vert",
                        rawSyllCV="v_E_R", rawOrthosyllCV="v_e_r_t")
        theory = {((1, 2),): [w1, w2]}
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        # Each lemme group is size 1, so both words get tagged as discriminated
        total_discriminated = sum(len(ws) for ws in disc_by.values())
        assert total_discriminated > 0

    def test_three_forms_same_lemme(self):
        """Three homophones of the same lemme should all get discriminating features."""
        w1 = self._make_verb("fais", "1s")
        w2 = self._make_verb("fais", "2s",
                             rawOrthosyllCV="f_a_i_s")
        w3 = self._make_verb("fait", "3s")
        # w1 and w2 have same ortho, w3 has different ortho
        theory = {((1, 2),): [w1, w2, w3]}
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        total_discriminated = sum(len(ws) for ws in disc_by.values())
        assert total_discriminated > 0

    def test_gender_discriminates_nouns(self):
        """Masculine vs feminine nouns with same lemme should be discriminated by gender.
        Features use 'm_s'/'f_s' format (gender_number), not 'genre'."""
        w1 = _make_word(ortho="ami", phonology="ami", lemme="ami",
                        gender="m", number="s",
                        rawSyllCV="a_m_i", rawOrthosyllCV="a_m_i")
        w2 = _make_word(ortho="amie", phonology="ami", lemme="ami",
                        gender="f", number="s",
                        rawSyllCV="a_m_i", rawOrthosyllCV="a_m_i_e")
        theory = {((1, 2),): [w1, w2]}
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        # Gender-related features like "m_s", "f_s", "m", "f" should discriminate
        gender_features = [f for f in disc_by if f in ("m", "f", "m_s", "f_s")]
        discriminated_by_gender = sum(len(disc_by[f]) for f in gender_features)
        assert discriminated_by_gender > 0

    def test_number_discriminates(self):
        """Singular vs plural of same lemme should be discriminated by number.
        Features use 's'/'p' directly, not 'nombre'."""
        w1 = _make_word(ortho="chat", phonology="Sa", lemme="chat",
                        gender="m", number="s",
                        rawSyllCV="S_a", rawOrthosyllCV="ch_a_t")
        w2 = _make_word(ortho="chats", phonology="Sa", lemme="chat",
                        gender="m", number="p",
                        rawSyllCV="S_a", rawOrthosyllCV="ch_a_t_s")
        theory = {((1,),): [w1, w2]}
        disc_by, ordered, _ = extractDiscriminatingFeatures(theory)
        # Number features "s" and "p" should discriminate
        number_features = [f for f in disc_by if f in ("s", "p")]
        discriminated_by_number = sum(len(disc_by[f]) for f in number_features)
        assert discriminated_by_number > 0

    def test_returns_correct_types(self):
        """Return types match the signature."""
        w1 = _make_word(ortho="chat")
        theory = {((1,),): [w1]}
        disc_by, ordered, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)
        assert isinstance(disc_by, dict)
        assert isinstance(ordered, list)
        assert isinstance(strokeLemmeDiscriminators, dict)
        for feature, words in disc_by.items():
            assert isinstance(feature, str)
            assert isinstance(words, set)
        for f in ordered:
            assert isinstance(f, str)
        for (strokes, lemme), wordFeatures in strokeLemmeDiscriminators.items():
            assert isinstance(strokes, tuple)
            assert isinstance(wordFeatures, dict)

    def test_empty_theory(self):
        """Empty theory should return empty results without error."""
        disc_by, ordered, strokeLemmeDiscriminators = extractDiscriminatingFeatures({})
        assert disc_by == {}
        assert ordered == []
        assert strokeLemmeDiscriminators == {}


# ---------------------------------------------------------------------------
# buildFeasibleDiscriminatorOptions
# ---------------------------------------------------------------------------

class TestBuildFeasibleDiscriminatorOptions:

    def _make_verb(self, ortho, person_number, tense="pre", mode="ind", **extra):
        defaults = dict(
            ortho=ortho, phonology="fE", lemme="faire",
            gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
            gender=None, number=None,
            rawSyllCV="f_E", rawOrthosyllCV=f"{'_'.join(ortho)}",
            frequencyBook=1.0, frequencyFilm=2.0,
            infoVerb=f"{mode}:{tense}:{person_number}",
        )
        defaults.update(extra)
        return Word(**defaults)

    def test_single_word_groups_are_skipped(self):
        """A lemme with only one word in its homophone group needs no
        discriminating feature, so it should not appear in the result at all."""
        w1 = _make_word(ortho="chat")
        theory = {((1,),): [w1]}
        disc_by, _ordered, _sld = extractDiscriminatingFeatures(theory)
        result = buildFeasibleDiscriminatorOptions(theory, disc_by)
        assert result == {}

    def test_multi_word_group_lists_every_feasible_feature_per_word(self):
        w1 = self._make_verb("fais", "1s")
        w2 = self._make_verb("fait", "3s")
        theory = {((1, 2),): [w1, w2]}
        disc_by, _ordered, _sld = extractDiscriminatingFeatures(theory)
        result = buildFeasibleDiscriminatorOptions(theory, disc_by)
        key = (((1, 2),), "faire_VER")
        assert key in result
        assert set(result[key]) == {w1, w2}
        for word, features in result[key].items():
            assert features == {f for f, ws in disc_by.items() if word in ws}
            assert len(features) > 0

    def test_no_pairwise_blowup_for_large_shared_feature_group(self):
        """A feature shared by many unrelated lemmes must not cause the result
        to grow quadratically -- this is the scenario that caused the original
        out-of-memory crash in the pairwise collision-diff code."""
        theory: dict = {}
        for i in range(500):
            w1 = _make_word(ortho=f"mot{i}", phonology=f"m{i}", lemme=f"mot{i}",
                            gender="m", number="s",
                            rawSyllCV=f"m_{i}", rawOrthosyllCV=f"m_o_t_{i}")
            w2 = _make_word(ortho=f"mot{i}s", phonology=f"m{i}", lemme=f"mot{i}",
                            gender="m", number="p",
                            rawSyllCV=f"m_{i}", rawOrthosyllCV=f"m_o_t_{i}_s")
            theory[((i,),)] = [w1, w2]
        disc_by, _ordered, _sld = extractDiscriminatingFeatures(theory)
        result = buildFeasibleDiscriminatorOptions(theory, disc_by)
        assert len(result) == 500
        for wordFeasibleFeatures in result.values():
            assert len(wordFeasibleFeatures) == 2


# ---------------------------------------------------------------------------
# selectFeaturesBySetCover
# ---------------------------------------------------------------------------

class TestSelectFeaturesBySetCover:

    def test_empty_input(self):
        chosen, unresolved = selectFeaturesBySetCover({})
        assert chosen == {}
        assert unresolved == set()

    def test_feature_shared_across_unrelated_groups_gets_reused(self):
        """If the same feature can resolve words in two unrelated lemme
        groups, set-cover should pick it once and reuse it for both, rather
        than needing two different features."""
        w1 = _make_word(ortho="a1", lemme="a")
        w2 = _make_word(ortho="a2", lemme="a")
        w3 = _make_word(ortho="b1", lemme="b")
        w4 = _make_word(ortho="b2", lemme="b")
        groupFeasibleFeatures = {
            (((1,),), "a"): {w1: {"shared"}, w2: {"other_a"}},
            (((2,),), "b"): {w3: {"shared"}, w4: {"other_b"}},
        }
        chosen, unresolved = selectFeaturesBySetCover(groupFeasibleFeatures)
        assert unresolved == set()
        assert chosen[w1] == "shared"
        assert chosen[w3] == "shared"
        assert chosen[w2] == "other_a"
        assert chosen[w4] == "other_b"

    def test_word_with_no_feasible_feature_is_unresolved(self):
        w1 = _make_word(ortho="a1", lemme="a")
        w2 = _make_word(ortho="a2", lemme="a")
        groupFeasibleFeatures = {
            (((1,),), "a"): {w1: {"f1"}, w2: set()},
        }
        chosen, unresolved = selectFeaturesBySetCover(groupFeasibleFeatures)
        assert chosen == {w1: "f1"}
        assert unresolved == {w2}

    def test_tie_break_is_deterministic(self):
        """When two features resolve the same number of words (a genuine tie),
        the choice must not depend on dict/set iteration order."""
        w1 = _make_word(ortho="a1", lemme="a")
        w2 = _make_word(ortho="a2", lemme="a")
        w3 = _make_word(ortho="a3", lemme="a")

        def build(featureOrderW3):
            return {
                (((1,),), "a"): {w1: {"zeta"}, w2: {"alpha"}, w3: set(featureOrderW3)},
            }

        resultA = selectFeaturesBySetCover(build(["zeta", "alpha"]))
        resultB = selectFeaturesBySetCover(build(["alpha", "zeta"]))
        assert resultA == resultB
        # Alphabetically-first feature among the tied pair ("alpha") wins for w3
        chosen, unresolved = resultA
        assert unresolved == set()
        assert chosen[w3] == "alpha"
        assert chosen[w1] == "zeta"
        assert chosen[w2] == "alpha"
