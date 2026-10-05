"""Tests for src/affixproposals.py -- hand-built records on the real layout, no pickles."""
from typing import Any
import pytest

import src.affixes as A
import src.affixproposals as P
import src.affixrules as R
from src.affixdecisions import FUSED, SINGLE, AnchorDecision, Decisions, ScopeForm
from src.affixes import PREFIX, SUFFIX, Candidate, Carrier, SimContext, WordRecord
from src.keyboard import Starboard

NONE: Any = None  # deliberately untyped stand-in for an unused argument

KEYS = (4,)
STEMS = [(11,), (12,), (13,), (14,), (16,), (17,), (18,), (19,)]
_idx = [20000]


def _sb():
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


def _word(anchor, neighbour, nPhono, k, freq=100.0, nStroke=(5,)):
    _idx[0] += 1
    return WordRecord(
        idx=_idx[0], ortho=f"{anchor}{neighbour}{chr(97 + k)}", lemme=f"{anchor}{neighbour}{chr(97 + k)}", gramCat="NOM",
        frequency=freq, phonoSylls=("A", nPhono, f"s{k}"), orthoSylls=(anchor, neighbour, chr(97 + k)),
        base=((2,), nStroke, STEMS[k]), extra=(), isLemmaForm=True)


def _prefixPool(groups):
    """groups: [(anchorSpelling, neighbourSpelling, neighbourSound, neighbourStroke, count)]"""
    words = [_word(a, n, ph, k, nStroke=st) for a, n, ph, st, cnt in groups for k in range(cnt)]
    spellings = sorted({a for a, *_ in groups})
    root = Candidate(PREFIX, 1, "A", "|".join(spellings), carriers=[Carrier(w, 0, 1, "s") for w in words],
                     isAnchor=True, hasDecision=False)
    return root, words


def _decisions(root, growth=None):
    return Decisions([AnchorDecision(PREFIX, root.ortho, root.phono, FUSED if "|" in root.ortho else SINGLE, growth)])


class TestGrowth:
    def test_the_best_form_covers_the_helping_words_and_numbers_are_the_engines(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), 8), ("a", "ti", "ti", (6,), 6)])
        ctx = SimContext(_sb(), words)
        p = P.proposeGrowth(root, _decisions(root), KEYS, ctx)
        assert p is not None and p.kind == "growth" and p.net > 0
        assert p.entry.growth is not None
        (form,) = p.entry.growth
        assert form.matches("a", "ma", "ma") and form.matches("a", "ti", "ti")     # one general atom takes both groups
        assert p.helpsWords == 14 and p.hurtsFallbacks == 0 and p.hurtsExceptions == 0
        # net = score of the proposed config - score of the anchor alone, at the same keys, from the engine
        base = P.numbersAtKeys(P._growthRule(root, [], _decisions(root)), KEYS, ctx)
        new = P.numbersAtKeys(P._growthRule(root, p.entry.growth, _decisions(root)), KEYS, ctx)
        assert p.net == pytest.approx(new.score - base.score)
        assert p.net == pytest.approx(new.benefit - base.benefit - R.FORM_COST)

    def test_a_refused_label_is_not_proposed_again(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), 8), ("a", "ti", "ti", (6,), 6)])
        ctx = SimContext(_sb(), words)
        first = P.proposeGrowth(root, _decisions(root), KEYS, ctx)
        assert first is not None
        second = P.proposeGrowth(root, _decisions(root), KEYS, ctx, refused=frozenset({first.label}))
        assert second is None or second.label != first.label
        entryRefused = AnchorDecision(PREFIX, "a", "A", SINGLE, None, [first.label])        # the stored refusals count too
        third = P.proposeGrowth(root, Decisions([entryRefused]), KEYS, ctx)
        assert third is None or third.label != first.label

    def test_an_existing_form_is_offered_its_best_extension_for_free(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), 8), ("a", "ti", "ti", (6,), 6)])
        ctx = SimContext(_sb(), words)
        dec = _decisions(root, [ScopeForm("ma", None, A_re("ma"))])
        ext = P.proposeGrowth(root, dec, KEYS, ctx)
        assert ext is not None and ext.entry.growth is not None and len(ext.entry.growth) == 1 and ext.label.startswith("ma|")   # one more alternative
        assert ext.net > 0 and ext.helpsWords == 6                                              # the `ti` group, no new form price

    def test_nothing_is_proposed_below_the_minimum_words(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), P.MIN_WORDS - 1)])
        ctx = SimContext(_sb(), words)
        assert P.proposeGrowth(root, _decisions(root), KEYS, ctx) is None

    def test_a_merged_anchor_grows_per_spelling_and_a_sibling_spelling_is_offered(self):
        root, words = _prefixPool([("dez", "ma", "ma", (5,), 8), ("der", "ma", "ma", (5,), 8)])
        ctx = SimContext(_sb(), words)
        form = ScopeForm("dez:ma", frozenset({"dez"}), A_re("ma"))
        dec = _decisions(root, [form])
        p = P.proposeGrowth(root, dec, KEYS, ctx)
        assert p is not None and p.label == "dez:ma+der"                       # the `der` case: sibling of `dez`
        assert p.entry.growth is not None
        (f,) = p.entry.growth
        assert f.anchors == frozenset({"dez", "der"})

    def test_a_pattern_used_by_another_rule_is_flagged(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), 8)])
        ctx = SimContext(_sb(), words)
        other = AnchorDecision(PREFIX, "zz", "Z", SINGLE, [ScopeForm("ma", None, A_re("ma"))])
        p = P.proposeGrowth(root, Decisions([other]), KEYS, ctx)
        assert p is not None
        assert any("already used by `zz`" in f for f in p.flags)

    def test_line_format(self):
        p = P.Proposal("growth", PREFIX, "a", "A", "x", 10, 1000.0, 1, 5.0, 2, 7.0, 342.0,
                       AnchorDecision(PREFIX, "a", "A", SINGLE), ["similar rule: foo"])
        assert p.line() == "helps 10 words freq 1000 | hurts 1 fb freq 5, 2 exc | net +342 | similar rule: foo"


def A_re(rx):
    import re
    return re.compile(rx)


class TestFusion:
    def _setup(self, monkeypatch):
        """parts `a` (decided, one rule), `b` (an added spelling) and the merge `a|b`; scores are sum(f x span)."""
        def fake(rule, pk, ctx, keypresses):
            rule.exactDone, rule.keys = True, (4,)
            rule.results = [A.CarrierResult(c, gain=c.span) for c in A.poolCarriers(rule.forms)]
            rule.score, rule.strokeFreqSaved, *_ = R.ruleScoreFromResults(rule.results, 0, len(rule.forms))

        monkeypatch.setattr(R, "chooseRuleKeypress", fake)
        wa = [_word("a", "ma", "ma", k) for k in range(5)]
        wb = [_word("b", "ma", "ma", k, freq=50.0) for k in range(3)]
        a = Candidate(PREFIX, 1, "A", "a", carriers=[Carrier(w, 0, 1, "s") for w in wa], isAnchor=True, hasDecision=True)
        b = Candidate(PREFIX, 1, "A", "b", carriers=[Carrier(w, 0, 1, "s") for w in wb], isAnchor=True)
        m = Candidate(PREFIX, 1, "A", "a|b", carriers=a.carriers + b.carriers, isAnchor=True,
                      mergeParts=[R.candidateKey(a), R.candidateKey(b)])
        pool = {R.candidateKey(c): c for c in (a, b, m)}
        dec = Decisions([AnchorDecision(PREFIX, "a", "A", SINGLE, [])])
        return m, pool, dec

    def test_net_is_merged_minus_parts_and_helps_counts_the_added_words(self, monkeypatch):
        m, pool, dec = self._setup(monkeypatch)
        p = P.proposeFusion(m, pool, dec, NONE, NONE, [])
        assert p is not None
        assert p.kind == "fusion" and p.spellings == "a|b" and p.entry.verdict == FUSED
        assert (p.helpsWords, p.helpsFreq) == (3, 150.0)
        assert p.net == pytest.approx(150.0)             # the merge adds the `b` words, nothing else changes

    def test_two_decided_parts_are_flagged(self, monkeypatch):
        m, pool, dec = self._setup(monkeypatch)
        pool[(PREFIX, 1, "A", "b")].hasDecision = True
        p = P.proposeFusion(m, pool, dec, NONE, NONE, [])
        assert p is not None
        assert any("two decided rules on one key" in f for f in p.flags)

    def test_no_comparison_without_a_rule_part(self, monkeypatch):
        m, pool, dec = self._setup(monkeypatch)
        pool[(PREFIX, 1, "A", "a")].hasDecision = False
        assert P.proposeFusion(m, pool, dec, NONE, NONE, []) is None

    def test_growth_forms_stay_on_the_parts_own_spellings(self):
        part = Candidate(PREFIX, 1, "A", "tion|tions")
        form = ScopeForm("C*[ai]", None, A_re("x"))
        (r,) = P.restrictedGrowth(part, [form])
        assert r.anchors == frozenset({"tion", "tions"})
        (r2,) = P.restrictedGrowth(part, [ScopeForm("y", frozenset({"tion", "ssion"}), A_re("x"))])
        assert r2.anchors == frozenset({"tion"})
        assert P.restrictedGrowth(part, [ScopeForm("z", frozenset({"né"}), A_re("x"))]) == []


class TestRows:
    def test_growth_rows_group_the_newly_covered_words_by_anchor_spelling_and_neighbour_sound(self):
        root, words = _prefixPool([("a", "ma", "ma", (5,), 8), ("a", "ti", "ti", (6,), 6)])
        ctx = SimContext(_sb(), words)
        p = P.proposeGrowth(root, _decisions(root), KEYS, ctx)
        assert p is not None
        rows = {r.label: r for r in p.rows}
        assert set(rows) == {"a + /ma/", "a + /ti/"}
        assert (rows["a + /ma/"].words, rows["a + /ma/"].gainWords) == (8, 8)
        assert rows["a + /ma/"].benefit == 8 * 100.0 * 2          # grown carriers save 2 strokes each
        assert rows["a + /ti/"].net == pytest.approx(6 * 100.0 * 2)
        assert "a + /ma/: 8 words" in rows["a + /ma/"].line()

    def test_fusion_rows_are_per_added_spelling(self, monkeypatch):
        TestFusion()._setup(monkeypatch)             # installs the fake chooseRuleKeypress
        m, pool, dec = TestFusion()._setup(monkeypatch)
        p = P.proposeFusion(m, pool, dec, NONE, NONE, [])
        assert p is not None
        (row,) = p.rows
        assert row.label == "b" and row.words == 3 and row.freq == 150.0 and row.benefit == 150.0
        assert any(n.startswith("existing words:") for n in p.notes)


class TestFusionSubset:
    def test_a_sub_merge_keeps_only_the_accepted_spellings(self, monkeypatch):
        def fake(rule, pk, ctx, keypresses):
            rule.exactDone, rule.keys = True, (4,)
            rule.results = [A.CarrierResult(c, gain=c.span) for c in A.poolCarriers(rule.forms)]
            rule.score, rule.strokeFreqSaved, *_ = R.ruleScoreFromResults(rule.results, 0, len(rule.forms))

        monkeypatch.setattr(R, "chooseRuleKeypress", fake)
        wa = [_word("a", "ma", "ma", k) for k in range(5)]
        wb = [_word("b", "ma", "ma", k, freq=50.0) for k in range(3)]
        wc = [_word("c", "ma", "ma", k, freq=10.0) for k in range(2)]
        parts = [Candidate(PREFIX, 1, "A", s, carriers=[Carrier(w, 0, 1, "s") for w in ws], isAnchor=True)
                 for s, ws in (("a", wa), ("b", wb), ("c", wc))]
        parts[0].hasDecision = True
        m = A.unionMerge(parts)
        pool = {R.candidateKey(c): c for c in parts + [m]}
        p = P.proposeFusion(m, pool, Decisions([AnchorDecision(PREFIX, "a", "A", SINGLE, [])]), NONE, NONE, [])
        assert p is not None
        assert [r.label for r in p.rows] == ["b", "c"] and p.baseSpellings == ["a"]
        assert set(p.groups) == {"b", "c"}
        assert p.evaluateSubset is not None
        sub = p.evaluateSubset(["b"])
        assert sub.spellings == "a|b" and sub.entry.verdict == FUSED and sub.net == pytest.approx(150.0)
        assert [r.label for r in sub.rows] == ["b"]
        assert p.evaluateSubset(["b", "c"]) is p                   # all accepted = the full merge
