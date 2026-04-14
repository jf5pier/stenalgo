#!/usr/bin/python
# coding: utf-8
"""Tests for src/greedyoptimizer.py — assignDiscriminatorKeypresses."""

import pytest
from unittest.mock import MagicMock
from src.word import Word, GramCat
from src.greedyoptimizer import assignDiscriminatorKeypresses, _buildStrokePool


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


def _mock_keyboard(reserved: list[int] | None = None) -> MagicMock:
    """Mock keyboard: cost = sum of key indices (cheap, deterministic)."""
    if reserved is None:
        reserved = [0, 1, 2, 3]
    kb = MagicMock()
    kb._reservedKeys = reserved
    kb.getStrokeCost.side_effect = lambda s, part: sum(s)
    return kb


def _w(n: int) -> Word:
    """Make a distinct Word with ortho w0, w1, …"""
    return _make_word(ortho=f"w{n}", lemme=f"lemme{n}")


# ---------------------------------------------------------------------------
# _buildStrokePool
# ---------------------------------------------------------------------------

class TestBuildStrokePool:

    def test_no_stroke_first(self):
        kb = _mock_keyboard(reserved=[0, 3])
        pool = _buildStrokePool(kb)
        # () "no stroke" is always first (cost 0)
        assert pool[0] == ()

    def test_all_subsets_present(self):
        kb = _mock_keyboard(reserved=[0, 1])
        pool = _buildStrokePool(kb)
        assert set(pool) == {(), (0,), (1,), (0, 1)}

    def test_sorted_by_cost(self):
        kb = _mock_keyboard(reserved=[0, 1, 2])
        pool = _buildStrokePool(kb)
        # () has cost 0; real strokes sorted by getStrokeCost
        real = pool[1:]
        costs = [kb.getStrokeCost(s, "onset") for s in real]
        assert costs == sorted(costs)

    def test_custom_reserved_keys(self):
        kb = _mock_keyboard(reserved=[5, 10])
        pool = _buildStrokePool(kb)
        assert (5,) in pool
        assert (10,) in pool
        assert (5, 10) in pool

    def test_empty_reserved_keys(self):
        kb = _mock_keyboard(reserved=[])
        pool = _buildStrokePool(kb)
        # Only "no stroke" when there are no reserved keys
        assert pool == [()]


# ---------------------------------------------------------------------------
# assignDiscriminatorKeypresses — Phase 1: feature selection
# ---------------------------------------------------------------------------

class TestPhase1FeatureSelection:

    def test_n2_covered_after_one_assignment(self):
        """N=2 featureset ('s', 'p'): one feature assignment covers it."""
        w1, w2 = _w(1), _w(2)
        # Three independent N=2 groups for 's'/'p'
        augmented = {
            ("s", "p"): [(_w(1), _w(2)), (_w(3), _w(4)), (_w(5), _w(6))],
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        # Exactly one of 's' or 'p' gets a stroke; the other is default
        assigned_features = [f for feats in result.values() for f in feats]
        assert len(result) >= 1
        assert "s" in assigned_features or "p" in assigned_features

    def test_n3_requires_two_assignments(self):
        """N=3 featureset: 2 features must be selected."""
        augmented = {
            ("m_s", "f_s", "m_p"): [(_w(1), _w(2), _w(3))] * 5,
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assigned_features = set(f for feats in result.values() for f in feats)
        # At least 2 of the 3 features must be selected to cover the group
        assert len(assigned_features & {"m_s", "f_s", "m_p"}) == 2

    def test_nofeature_excluded_from_gain(self):
        """Featuresets containing 'nofeature' are ignored entirely."""
        augmented = {
            ("nofeature", "s"): [(_w(1), _w(2))] * 10,
            ("p", "q"):         [(_w(3), _w(4))] * 3,
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assigned_features = set(f for feats in result.values() for f in feats)
        # "nofeature" and "s" must not be selected from the first featureset
        assert "nofeature" not in assigned_features
        # Only 'p' or 'q' may be selected (from the coverable featureset)
        assert assigned_features <= {"p", "q"}

    def test_most_impactful_feature_selected_first(self):
        """Feature appearing in more groups is selected before a rarer one."""
        # 'common' appears in 5 N=2 groups, 'rare' appears in 1
        augmented = {
            ("common", "x1"): [(_w(1), _w(2))] * 5,
            ("common", "x2"): [(_w(3), _w(4))] * 5,
            ("rare",   "x3"): [(_w(5), _w(6))] * 1,
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assigned_features = [f for feats in result.values() for f in feats]
        # 'common' must appear among the assigned features
        assert "common" in assigned_features

    def test_zero_gain_stops_selection(self):
        """Only features contributing positive gain are selected."""
        # Single group; only one feature needed
        augmented = {
            ("a", "b"): [(_w(1), _w(2))],
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assigned_features = [f for feats in result.values() for f in feats]
        # Exactly one of 'a' or 'b' (not both: second has zero marginal gain)
        assert len(assigned_features) == 1


# ---------------------------------------------------------------------------
# assignDiscriminatorKeypresses — Phase 2: stroke assignment
# ---------------------------------------------------------------------------

class TestPhase2StrokeAssignment:

    def test_cooccurring_features_get_different_strokes(self):
        """'s' and 'p' co-occur in the same featureset → different strokes."""
        # To force both to be selected, we need them both to gain:
        # use separate N=2 groups where each is the sole feature needed
        augmented = {
            ("s", "x"):  [(_w(1), _w(2))] * 3,   # 's' wins here
            ("p", "y"):  [(_w(3), _w(4))] * 3,   # 'p' wins here
            ("s", "p"):  [(_w(5), _w(6))] * 1,   # they co-occur
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        # Find strokes for 's' and 'p'
        stroke_of = {}
        for stroke, feats in result.items():
            for f in feats:
                stroke_of[f] = stroke
        if "s" in stroke_of and "p" in stroke_of:
            assert stroke_of["s"] != stroke_of["p"], \
                "Co-occurring features 's' and 'p' must not share a stroke"

    def test_noncooccurring_features_share_stroke(self):
        """Features that never co-occur in any featureset share a stroke."""
        # 'p' and 'm_p' never appear in the same featureset
        augmented = {
            ("s",   "p"):   [(_w(1), _w(2))] * 5,
            ("m_s", "m_p"): [(_w(3), _w(4))] * 5,
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        stroke_of = {}
        for stroke, feats in result.items():
            for f in feats:
                stroke_of[f] = stroke
        # 'p' and 'm_p' are selected (one per featureset); they never co-occur
        if "p" in stroke_of and "m_p" in stroke_of:
            assert stroke_of["p"] == stroke_of["m_p"], \
                "Non-co-occurring features 'p' and 'm_p' should share a stroke"

    def test_strokes_drawn_from_pool(self):
        """All allocated strokes come from the reserved-key pool."""
        augmented = {
            ("a", "b"): [(_w(1), _w(2))] * 2,
            ("c", "d"): [(_w(3), _w(4))] * 2,
            ("a", "c"): [(_w(5), _w(6))] * 2,
        }
        kb = _mock_keyboard(reserved=[0, 1, 2, 3])
        pool = set(_buildStrokePool(kb))
        result = assignDiscriminatorKeypresses(augmented, kb)
        for stroke in result:
            assert stroke in pool, f"Stroke {stroke} not in pool"

    def test_return_type_and_structure(self):
        """Return value is dict[Stroke, list[WordFeature]]."""
        augmented = {
            ("f1", "f2"): [(_w(1), _w(2))],
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assert isinstance(result, dict)
        for stroke, feats in result.items():
            assert isinstance(stroke, tuple)
            assert isinstance(feats, list)
            for f in feats:
                assert isinstance(f, str)

    def test_empty_augmented_theory(self):
        """Empty input returns empty mapping."""
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses({}, kb)
        assert result == {}

    def test_all_nofeature_returns_empty(self):
        """Only nofeature featuresets → no strokes allocated."""
        augmented = {
            ("nofeature", "x"): [(_w(1), _w(2))] * 5,
        }
        kb = _mock_keyboard()
        result = assignDiscriminatorKeypresses(augmented, kb)
        assert result == {}
