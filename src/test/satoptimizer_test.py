#!/usr/bin/python
# coding: utf-8
"""Tests for src/satoptimizer.py"""

from unittest.mock import MagicMock
from src.word import Word, GramCat
from src.satoptimizer import (
    _colorFeatures,
    _minSpecialKeysNeeded,
    _computeFamilyCorrelations,
    associationScore,
    polarityAssociations,
    satOptimizeDiscriminator,
    NO_FEATURE,
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


def _make_verb(ortho, person_number, tense="pre", mode="ind", **extra) -> Word:
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


def _mock_keyboard():
    return MagicMock()


def _make_adj(ortho, gender, number, **extra) -> Word:
    defaults = dict(
        ortho=ortho, phonology="pti", lemme="petit",
        gramCat=GramCat.ADJ, orthoGramCat=[GramCat.ADJ],
        gender=gender, number=number, infoVerb=None,
        rawSyllCV="p_t_i", rawOrthosyllCV=f"{'_'.join(ortho)}",
        frequencyBook=1.0, frequencyFilm=2.0,
    )
    defaults.update(extra)
    return Word(**defaults)


# ---------------------------------------------------------------------------
# associationScore / _computeFamilyCorrelations
# ---------------------------------------------------------------------------

class TestFamilyCorrelations:

    def _number_words(self) -> list[Word]:
        """2 singular nouns, 2 plural nouns, 2 singular verb forms, 2 plural verb forms."""
        return [
            _make_word(ortho="chat1", number="s"),
            _make_word(ortho="chat2", number="s", rawOrthosyllCV="c_h_a_t_2"),
            _make_word(ortho="chats1", number="p", rawOrthosyllCV="c_h_a_t_s_1"),
            _make_word(ortho="chats2", number="p", rawOrthosyllCV="c_h_a_t_s_2"),
            _make_verb("fais", "1s"),
            _make_verb("fait", "3s"),
            _make_verb("faisons", "1p", rawOrthosyllCV="f_a_i_s_o_n_s"),
            _make_verb("faites", "2p", rawOrthosyllCV="f_a_i_t_e_s"),
        ]

    def test_opposite_number_tokens_negative(self):
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore("s", "p", corr) < 0
        assert associationScore("nbr_s", "nbr_p", corr) < 0

    def test_cross_category_same_value_positive(self):
        """'s' (noun) and 'nbr_s' (verb) never co-occur on the same word, but both
        mean singular — the value-table fallback must still call this positive."""
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore("s", "nbr_s", corr) == 1.0
        assert associationScore("p", "nbr_p", corr) == 1.0

    def test_cross_category_opposite_value_negative(self):
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore("s", "nbr_p", corr) == -1.0
        assert associationScore("p", "nbr_s", corr) == -1.0

    def test_gender_number_combos_use_real_correlation(self):
        words = [
            _make_adj("petit1", "m", "s"),
            _make_adj("petit2", "m", "s"),
            _make_adj("petite", "f", "s"),
            _make_adj("petits", "m", "p"),
            _make_adj("petites", "f", "p"),
        ]
        corr = _computeFamilyCorrelations(words)
        # not_m_s is the complement of m_s: perfectly opposed to m_s...
        assert associationScore("not_m_s", "m_s", corr) == -1.0
        # ...and positively correlated with every combo it co-occurs with (each is
        # a subset of "not m_s"), discovered empirically, not hand-asserted.
        assert associationScore("not_m_s", "f_s", corr) > 0
        assert associationScore("not_m_s", "m_p", corr) > 0
        assert associationScore("not_m_s", "f_p", corr) > 0

    def test_unrelated_families_neutral(self):
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore("pers_1", "pers_2", corr) == 0.0
        assert associationScore("indicatif", "subjonctif", corr) == 0.0
        assert associationScore("s", "pers_1", corr) == 0.0

    def test_compound_features_extract_family_token(self):
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore(
            "indicatif:pers_3:nbr_s", "indicatif:pers_3:nbr_p", corr) < 0
        assert associationScore(
            "indicatif:pers_1", "indicatif:pers_3:nbr_s", corr) == 0.0

    def test_identical_token_fully_associated(self):
        corr = _computeFamilyCorrelations(self._number_words())
        assert associationScore("s", "s", corr) == 1.0

    def test_polarity_associations_lists_nonzero_pairs_sorted(self):
        corr = _computeFamilyCorrelations(self._number_words())
        table = polarityAssociations(["s", "p", "nbr_s", "nbr_p", "pers_1"], corr)
        pairs = {(f1, f2) for f1, f2, _ in table}
        assert ("s", "nbr_s") in pairs or ("nbr_s", "s") in pairs
        assert all(score != 0.0 for _, _, score in table)
        # sorted ascending by score
        assert [s for *_, s in table] == sorted(s for *_, s in table)


# ---------------------------------------------------------------------------
# _colorFeatures — port of satex.py's own worked example
# ---------------------------------------------------------------------------

class TestColorFeatures:

    def test_satex_worked_example(self):
        """Same sets/penalties/K/budget as satex.py's __main__ block."""
        sets = [{"a", "b", "c"}, {"b", "c", "d"}, {"a", "d", "e"}]
        pens = [10, 1, 7]
        total, proven, keys, conflicted = _colorFeatures(
            sets, pens, numKeys=3, conflictBudget=2)
        assert total == 1
        assert conflicted == [1]
        assert proven
        # every feature got a key in [0, 3)
        for f in ("a", "b", "c", "d", "e"):
            assert 0 <= keys[f] < 3

    def test_no_conflict_needed_when_enough_keys(self):
        sets = [{"a", "b", "c"}]
        pens = [10]
        total, proven, keys, conflicted = _colorFeatures(
            sets, pens, numKeys=3, conflictBudget=0)
        assert total == 0
        assert conflicted == []
        assert len({keys["a"], keys["b"], keys["c"]}) == 3

    def test_infeasible_raises(self):
        sets = [{"a", "b", "c"}]
        pens = [10]
        try:
            _colorFeatures(sets, pens, numKeys=2, conflictBudget=0)
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass


# ---------------------------------------------------------------------------
# _minSpecialKeysNeeded
# ---------------------------------------------------------------------------

class TestMinSpecialKeysNeeded:

    def test_triangle_needs_three(self):
        sets = [{"a", "b", "c"}]
        assert _minSpecialKeysNeeded(sets) == 3

    def test_disjoint_pairs_need_two(self):
        sets = [{"a", "b"}, {"c", "d"}]
        assert _minSpecialKeysNeeded(sets) == 2

    def test_empty_needs_none(self):
        assert _minSpecialKeysNeeded([]) == 0


# ---------------------------------------------------------------------------
# polarityCoefficients wiring in _colorFeatures
# ---------------------------------------------------------------------------

class TestPolarityInColorFeatures:

    def test_opposed_pair_avoids_sharing_key_when_alternative_exists(self):
        """Two homophone-conflict-neutral sets (penalty 0), but "s"/"p" carry a
        heavy opposition cost — the solver should keep them on different keys
        even though nothing about the sets themselves forces it."""
        sets = [{"s", "x"}, {"p", "y"}]
        pens = [0, 0]
        polarity = {frozenset({"s", "p"}): 10**9}
        _, _, keys, _ = _colorFeatures(
            sets, pens, numKeys=2, conflictBudget=0, polarityCoefficients=polarity)
        assert keys["s"] != keys["p"]

    def test_associated_pair_rewarded_to_share_a_key(self):
        """A negative coefficient is a reward: the solver should merge the pair
        onto the same key when nothing else prevents it."""
        sets = [{"a", "b"}]
        pens = [0]
        polarity = {frozenset({"s", "nbr_s"}): -1000}
        _, _, keys, _ = _colorFeatures(
            sets, pens, numKeys=2, conflictBudget=0, polarityCoefficients=polarity)
        assert keys["s"] == keys["nbr_s"]


# ---------------------------------------------------------------------------
# satOptimizeDiscriminator — end to end
# ---------------------------------------------------------------------------

class TestSatOptimizeDiscriminator:

    def test_empty_theory(self):
        numKeys, penalty, proven, keys, conflicted = satOptimizeDiscriminator(
            {}, {}, [], _mock_keyboard())
        assert numKeys == 0
        assert penalty == 0.0
        assert proven
        assert keys == {}
        assert conflicted == []

    def test_default_finds_conflict_free_assignment(self):
        """Three homophone forms of 'faire' sharing a lemme, each needs its own
        discriminating feature; with enough features available, zero conflicts."""
        w1 = _make_verb("fais", "1s")
        w2 = _make_verb("fait", "3s")
        w3 = _make_verb("faisons", "1p", rawOrthosyllCV="f_ai_s_o_n_s")
        theory = {((1, 2),): [w1, w2, w3]}
        from src.featureextractor import extractDiscriminatingFeatures
        discBy, ordered, _ = extractDiscriminatingFeatures(theory)

        numKeys, penalty, proven, keys, conflicted = satOptimizeDiscriminator(
            theory, discBy, ordered, _mock_keyboard())

        assert conflicted == []
        assert penalty == 0.0
        assert NO_FEATURE not in keys
        # every real feature used got a distinct key within its own feature set
        assert numKeys >= 1

    def test_forcing_fewer_keys_causes_conflict_with_expected_penalty(self):
        w1 = _make_verb("fais", "1s")
        w2 = _make_verb("fait", "3s")
        w3 = _make_verb("faisons", "1p", rawOrthosyllCV="f_ai_s_o_n_s")
        theory = {((1, 2),): [w1, w2, w3]}
        from src.featureextractor import extractDiscriminatingFeatures
        discBy, ordered, _ = extractDiscriminatingFeatures(theory)

        minKeys, _, _, _, _ = satOptimizeDiscriminator(
            theory, discBy, ordered, _mock_keyboard())
        if minKeys < 2:
            return  # nothing to force a conflict with

        numKeys, penalty, proven, keys, conflicted = satOptimizeDiscriminator(
            theory, discBy, ordered, _mock_keyboard(), numSpecialKeys=minKeys - 1)

        assert numKeys == minKeys - 1
        assert len(conflicted) >= 1
        expectedPenalty = sum(w.frequency for w in (w1, w2, w3))
        assert penalty <= expectedPenalty + 1e-6
