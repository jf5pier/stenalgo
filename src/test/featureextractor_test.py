#!/usr/bin/python
# coding: utf-8
"""Tests for src/featureextractor.py"""

import pytest
from unittest.mock import MagicMock
from src.word import Word, GramCat
from src.featureextractor import getAmbiguousMultiphonemes, extractDiscriminatingFeatures


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
        disc_by, ordered = extractDiscriminatingFeatures(theory)
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
        disc_by, ordered = extractDiscriminatingFeatures(theory)
        # At least one feature should discriminate some word
        total_discriminated = sum(len(ws) for ws in disc_by.values())
        assert total_discriminated > 0
        assert len(ordered) > 0

    def test_ordered_features_list_has_no_duplicates(self):
        """The ordered feature list should not contain duplicates."""
        w1 = self._make_verb("fais", "1s")
        w2 = self._make_verb("fait", "3s")
        theory = {((1, 2),): [w1, w2]}
        _, ordered = extractDiscriminatingFeatures(theory)
        assert len(ordered) == len(set(ordered))

    def test_different_lemmes_each_treated_independently(self):
        """Words sharing a stroke but with different lemmes are processed in
        separate lemme groups.  Each single-word group still marks its features."""
        w1 = _make_word(ortho="ver", phonology="vER", lemme="ver",
                        rawSyllCV="v_E_R", rawOrthosyllCV="v_e_r")
        w2 = _make_word(ortho="vert", phonology="vER", lemme="vert",
                        rawSyllCV="v_E_R", rawOrthosyllCV="v_e_r_t")
        theory = {((1, 2),): [w1, w2]}
        disc_by, ordered = extractDiscriminatingFeatures(theory)
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
        disc_by, ordered = extractDiscriminatingFeatures(theory)
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
        disc_by, ordered = extractDiscriminatingFeatures(theory)
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
        disc_by, ordered = extractDiscriminatingFeatures(theory)
        # Number features "s" and "p" should discriminate
        number_features = [f for f in disc_by if f in ("s", "p")]
        discriminated_by_number = sum(len(disc_by[f]) for f in number_features)
        assert discriminated_by_number > 0

    def test_returns_correct_types(self):
        """Return types match the signature."""
        w1 = _make_word(ortho="chat")
        theory = {((1,),): [w1]}
        disc_by, ordered = extractDiscriminatingFeatures(theory)
        assert isinstance(disc_by, dict)
        assert isinstance(ordered, list)
        for feature, words in disc_by.items():
            assert isinstance(feature, str)
            assert isinstance(words, set)
        for f in ordered:
            assert isinstance(f, str)

    def test_empty_theory(self):
        """Empty theory should return empty results without error."""
        disc_by, ordered = extractDiscriminatingFeatures({})
        assert disc_by == {}
        assert ordered == []
